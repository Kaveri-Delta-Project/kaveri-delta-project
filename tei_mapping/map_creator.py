import pandas as pd
import geopandas as gpd

from utils import (
    get_xml_files,
    soup_objects,
    build_df,
)

from config import (
    DATA_PATHS,
    PLACE_SCHEMA,
    PERSON_SCHEMA,
    WORK_SCHEMA,
    ISC_SCHEMA,
    GIS_PATH
)

from map_utils import create_kaveri_map, generate_popup_html

#paths to the geographic data used for the map
RIVERS_PATH = GIS_PATH / "kaveri_delta_rivers_final.gpkg"
TAMIL_NADU_PATH = GIS_PATH / "tamil_nadu.gpkg"


#load and parse the TEI XML files for each data category
place_objects = soup_objects(get_xml_files(DATA_PATHS["places"]))
person_objects = soup_objects(get_xml_files(DATA_PATHS["persons"]))
work_objects = soup_objects(get_xml_files(DATA_PATHS["works"]))
inscription_objects = soup_objects(get_xml_files(DATA_PATHS["inscriptions"]))

#convert the parsed TEI objects into dataframes using the relevant schemas
places_df = build_df(place_objects, PLACE_SCHEMA)
persons_df = build_df(person_objects, PERSON_SCHEMA)
works_df = build_df(work_objects, WORK_SCHEMA)
inscriptions_df = build_df(inscription_objects, ISC_SCHEMA)

#build person-place affiliations from the person data
affiliations_df = (
    persons_df[["person_id", "place_id", "place_role"]]
    .explode(["place_id", "place_role"])
    .dropna(subset=["place_id"])
)

#keep only "resided" relationships between people and places
resided_df = affiliations_df[
    affiliations_df["place_role"].str.lower() == "resided"
]

#build a lookup mapping each person to their residence place IDs
resided_map = (
    resided_df.groupby("person_id")["place_id"]
    .apply(list)
)

#expand works so each author can be mapped to their residence places
works_exploded = works_df.explode(["person_id", "person_role"])

#keep only authors of each work
works_exploded = works_exploded[works_exploded["person_role"] == "aut"]

#attach each author's residence place IDs using the residence lookup
works_exploded["resided_places"] = works_exploded["person_id"].map(resided_map)

#aggregate author residence places back to each work,
#combining the residence places of all of its authors
resided_agg = (
    works_exploded.groupby(level=0)["resided_places"]
    .apply(lambda s: sum([x for x in s if isinstance(x, list)], []))
)

#append the derived residence places to the work's existing place IDs
#thus each work contains data on directly associated places and
#places associated via author residences
works_df["place_id"] = works_df["place_id"] + resided_agg.reindex(works_df.index, fill_value=[])

#prepare place data by expanding multiple place types and removing places without coordinates
places_df = (
    places_df
    .explode("type")
    .dropna(subset=["coords"])
)

#prepare work-place relationships by expanding works with multiple place IDs
works_place_df = (
    works_df
    .explode("place_id")
    .dropna(subset=["place_id"])
)

#prepare inscription-place relationships by expanding inscriptions with multiple place IDs
inscriptions_place_df = (
    inscriptions_df
    .explode("place_id")
    .dropna(subset="place_id")
)


def aggregate_with_metadata(df, group_key, id_col, metadata_df):
    """
    Group associated records by a key and attach their metadata.

    Args:
        df (pandas.DataFrame): Dataframe containing the relationships
            between the grouping key and associated item IDs.
        group_key (str): Column used to group the associated items,
            such as a place ID.
        id_col (str): Column containing the IDs of the associated items,
            such as a work, person, or inscription ID.
        metadata_df (pandas.DataFrame): Dataframe containing the full
            metadata for the associated items.

    Returns:
        pandas.DataFrame:
            Dataframe indexed by the grouping key, containing a list
            of associated metadata records and their total count.
    """
    
    #remove duplicate group-to-item relationships
    df = df.drop_duplicates(subset=[group_key, id_col])

    #group item IDs by the relevant place or other grouping key
    grouped = df.groupby(group_key).agg(
        ids=(id_col, list)
    )

    #build a lookup dictionary to retrieve metadata for each item ID
    metadata_lookup = metadata_df.set_index(id_col).to_dict(orient="index")

    #replace the item IDs with their corresponding metadata
    grouped["items"] = [
        [metadata_lookup[i] for i in ids if i in metadata_lookup]
        for ids in grouped["ids"]
    ]

    #count the number of associated items in each group
    grouped["count"] = grouped["items"].apply(len)

    #remove the temporary ID column before returning the results
    return grouped.drop(columns=["ids"])


#aggregate associated works, people, and inscriptions for each place
works_agg = aggregate_with_metadata(
    works_place_df,
    group_key="place_id",
    id_col="work_id",
    metadata_df=works_df
)

people_agg = aggregate_with_metadata(
    affiliations_df,
    group_key="place_id",
    id_col="person_id",
    metadata_df=persons_df
)

inscriptions_agg = aggregate_with_metadata(
    inscriptions_place_df,
    group_key="place_id",
    id_col="inscription_id",
    metadata_df=inscriptions_df
    )


#rename the aggregation columns to identify the associated entity type
works_agg = works_agg.rename(columns={
    "count": "num_works",
    "items": "works"
})

people_agg = people_agg.rename(columns={
    "count": "num_people",
    "items": "people"
})

inscriptions_agg = inscriptions_agg.rename(columns={
    "count": "num_inscriptions",
    "items": "inscriptions"
})

#combine place data with the aggregated works, people, and inscriptions
nodes_df = (
    places_df
    .merge(works_agg, on="place_id", how="left")
    .merge(people_agg, on="place_id", how="left")
    .merge(inscriptions_agg, on="place_id", how="left")
)


#replace missing association counts with zero
nodes_df["num_works"] = nodes_df["num_works"].fillna(0).astype(int)
nodes_df["num_people"] = nodes_df["num_people"].fillna(0).astype(int)
nodes_df["num_inscriptions"] = nodes_df["num_inscriptions"].fillna(0).astype(int)

#replace missing association lists with empty lists
nodes_df["works"] = nodes_df["works"].apply(lambda x: x if isinstance(x, list) else [])
nodes_df["people"] = nodes_df["people"].apply(lambda x: x if isinstance(x, list) else [])
nodes_df["inscriptions"] = nodes_df["inscriptions"].apply(lambda x: x if isinstance(x, list) else [])

#split coordinate strings into separate latitude and longitude values
nodes_df["lat"] = nodes_df["coords"].apply(lambda x: float(x.split(",")[0].strip()))
nodes_df["lon"] = nodes_df["coords"].apply(lambda x: float(x.split(",")[1].strip()))

#use "other" when a place has no recorded type
nodes_df["type_filled"] = nodes_df["type"].fillna("other")

#generate the HTML popup for each place
for idx, row in nodes_df.iterrows():
    nodes_df.at[idx, "popup_html"] = generate_popup_html(row)

#load the geographic layers and convert them to WGS84 coordinates
rivers_gdf = gpd.read_file(RIVERS_PATH).to_crs(epsg=4326)
tamil_nadu_gdf = gpd.read_file(TAMIL_NADU_PATH).to_crs(epsg=4326)

#store the geographic layers together for use when creating the map
gdf_layers = {"rivers_gdf": rivers_gdf, "tamil_nadu_gdf": tamil_nadu_gdf}

#create the Kaveri map using the prepared place and geographic data
create_kaveri_map(nodes_df, gdf_layers)

