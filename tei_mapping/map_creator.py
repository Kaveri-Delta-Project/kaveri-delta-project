
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
    GIS_PATH
)

from map_utils import create_kaveri_map, generate_popup_html

import pandas as pd
import geopandas as gpd

RIVERS_PATH = GIS_PATH / "kaveri_delta_rivers_final.gpkg"

place_objects = soup_objects(get_xml_files(DATA_PATHS["places"]))
person_objects = soup_objects(get_xml_files(DATA_PATHS["persons"]))
work_objects = soup_objects(get_xml_files(DATA_PATHS["works"]))


places_df = build_df(place_objects, PLACE_SCHEMA)
persons_df = build_df(person_objects, PERSON_SCHEMA)
works_df = build_df(work_objects, WORK_SCHEMA)


places_df = (
    places_df
    .explode("type")
    .dropna(subset=["coords"])
)

works_df = (
    works_df
    .explode("place_id")
    .dropna(subset=["place_id"])
)

affiliations_df = (
    persons_df[["person_id", "place_id"]]
    .explode("place_id")
    .dropna(subset=["place_id"])
)


def aggregate_with_metadata(df, group_key, id_col, metadata_df):
    grouped = df.groupby(group_key).agg(
        ids=(id_col, list)
    )

    # Build lookup dictionary
    metadata_lookup = metadata_df.set_index(id_col).to_dict(orient="index")

    # Convert IDs to metadata
    grouped["items"] = [
        [metadata_lookup[i] for i in ids if i in metadata_lookup]
        for ids in grouped["ids"]
    ]

    # Count items
    grouped["count"] = grouped["items"].apply(len)

    return grouped.drop(columns=["ids"])


works_agg = aggregate_with_metadata(
    works_df,
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

# Rename columns for clarity
works_agg = works_agg.rename(columns={
    "count": "num_works",
    "items": "works"
})

people_agg = people_agg.rename(columns={
    "count": "num_people",
    "items": "people"
})



nodes_df = (
    places_df
    .merge(works_agg, on="place_id", how="left")
    .merge(people_agg, on="place_id", how="left")
)


nodes_df["num_works"] = nodes_df["num_works"].fillna(0).astype(int)
nodes_df["num_people"] = nodes_df["num_people"].fillna(0).astype(int)

nodes_df["works"] = nodes_df["works"].apply(lambda x: x if isinstance(x, list) else [])
nodes_df["people"] = nodes_df["people"].apply(lambda x: x if isinstance(x, list) else [])

nodes_df["lat"] = nodes_df["coords"].apply(lambda x: float(x.split(",")[0].strip()))
nodes_df["lon"] = nodes_df["coords"].apply(lambda x: float(x.split(",")[1].strip()))
nodes_df["type_filled"] = nodes_df["type"].fillna("other")

for idx, row in nodes_df.iterrows():
    nodes_df.at[idx, "popup_html"] = generate_popup_html(row)

rivers_gdf = gpd.read_file(RIVERS_PATH).to_crs(epsg=4326)

create_kaveri_map(nodes_df, rivers_gdf)

