import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
BUILD_DIR = os.path.join(BASE_DIR, "build")


#namespace settings

NS_TEI = "http://www.tei-c.org/ns/1.0"
NS_XML = "http://www.w3.org/XML/1998/namespace"

NSMAP = {
    "tei": NS_TEI,
    "xml": NS_XML,
}


#entity extraction mappings
#
#each mapping describes how TEI elements and attributes are extracted into
#the internal dictionaries used by the rendering pipeline

PERSON_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"}, 
    "sex": {"attr": "sex"},
    "name": {"element": "persName", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
    "alt_names": {"element": "persName", "filter_attr": "type", "filter_value": "variant", "all_results": True},
    "relationship": {"parent_tag": "trait", "attributes": ["from", "to", "type", "key"], "child_elements": ["label"]},
    "idno_value": {"element": "idno", "all_results": True},
    "idno_type": {"element": "idno", "element_attr": "type", "all_results": True},
    "birth_text": {"element": "birth", "all_results": True},
    "birth_when": {"element": "birth", "element_attr": "when", "all_results": True},
    "death_text": {"element": "death", "all_results": True},
    "death_when": {"element": "death", "element_attr": "when", "all_results": True},
    "floruit_text": {"element": "floruit", "all_results": True},
    "floruit_from": {"element": "floruit", "element_attr": "from", "all_results": True},
    "floruit_to": {"element": "floruit", "element_attr": "to", "all_results": True},
    "affiliations": {"parent_tag": "affiliation", "attributes": ["from", "to", "key", "role"], "child_elements": ["placeName"]},
    "reference" : {
        "parent_tag": "bibl",  
        "attributes": ["subtype", "n"],
        "extract_parent_text": True, 
        "all_results": True
        }, 
    "notes": {"element": "note", "all_results": True},
    "record_contributor": {"parent_tag": "respStmt", "child_elements": ["name", "resp"], "from_root": True}
}

PLACE_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"},
    "name": {"element": "placeName", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
    "alt_names": {"element": "placeName", "filter_attr": "type", "filter_value": "variant", "all_results": True},
    "place_type": {"element": "desc", "filter_attr": "type", "filter_value": "function", "all_results": True},
    "idno_value": {"element": "idno", "all_results": True},
    "idno_type": {"element": "idno", "element_attr": "type", "all_results": True},
    "coords": {"element": "note", "filter_attr": "type", "filter_value": "coordinates", "all_results": True},
    "reference" : {
        "parent_tag": "bibl",  
        "attributes": ["subtype", "n"],
        "extract_parent_text": True, 
        "all_results": True
        },
    "notes": {"element": "note", "filter_attr": "type", "filter_value": "general", "all_results": True}
}

WORK_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"},
    "name": {"element": "title", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
    "alt_names": {"element": "title", "filter_attr": "type", "filter_value": "variant", "all_results": True},
    "idno_value": {"element": "idno", "all_results": True},
    "idno_type": {"element": "idno", "element_attr": "type", "all_results": True},
    "dates_text": {"element": "date", "all_results": True},
    "dates_from": {"element": "date", "element_attr": "from", "all_results": True},
    "dates_to": {"element": "date", "element_attr": "to", "all_results": True},
    "activity": {"element": "date", "element_attr": "type", "all_results": True},
    "editor_text": {"element": "editor", "all_results": True},
    "editor_key": {"element": "editor", "element_attr": "key", "all_results": True},
    "editor_role": {"element": "editor", "element_attr": "role", "all_results": True},
    "person_ref": {"parent_tag": "persName", "attributes": ["key", "role"], "child_elements": ["note"], "extract_parent_text": True},
    "work_ref": {"parent_tag": "rs", "attributes": ["key", "role"], "child_elements": ["note"], "extract_parent_text": True},
    "pub_place": {"parent_tag": "pubPlace", "attributes": ["key", "role"], "child_elements": ["placeName"]},
    "genre" : {
        "parent_tag": "note", 
        "filter_attr": "type", 
        "filter_value": "genre", 
        "attributes": ["type", "source", "key"],
        "extract_parent_text": True, 
        "all_results": True
        },    
    "subject": {"element": "note", "filter_attr": "type", "filter_value": "subject", "all_results": True},
    "reference" : {
        "parent_tag": "note", 
        "filter_attr": "type", 
        "filter_value": "bibliographical", 
        "attributes": ["type", "subtype", "n"],
        "extract_parent_text": True, 
        "all_results": True
        },
    "notes": {"element": "note", "filter_attr": "type", "filter_value": "general", "all_results": True},
    "record_contributor": {"parent_tag": "respStmt", "child_elements": ["name", "resp"], "from_root": True}
}

ISC_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"},
    "name":   {"element": "msName", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
    "alt_name": {"element": "msName", "filter_attr": "type", "filter_value": "variant", "all_results": True},
    "dates_text": {"element": "origDate", "all_results": True},
    "dates_from": {"element": "origDate", "element_attr": "from", "all_results": True},
    "dates_to": {"element": "origDate", "element_attr": "to", "all_results": True},
    "donor": {
        "parent_tag": "person",
        "filter_attr": "ana", 
        "filter_value": "donor",
        "child_elements": ["persName"], 
        "child_attributes": {"persName": ["key", "role"]}, 
        "from_root": True
        },
    "assoc_person": {
        "parent_tag": "person",
        "filter_attr": "ana", 
        "filter_value": "associated",
        "child_elements": ["persName"], 
        "child_attributes": {"persName": ["key", "role"]}, 
        "from_root": True
        },
    "recipient": {"element": "orgName", "filter_attr": "type", "filter_value": "recipient", "all_results": True},
    "language": {"element": "lang", "all_results": True},    
    "donation_type": {"element": "provenance", "all_results": True},
    "material": {"element": "material", "all_results": True},
    "location": {"element": "origPlace", "all_results": True},
    "location_key": {"element": "origPlace", "element_attr": "key", "all_results": True},
    "reference" : {
        "parent_tag": "note", 
        "filter_attr": "type", 
        "filter_value": "bibliographical", 
        "attributes": ["type", "subtype", "n"],
        "extract_parent_text": True, 
        "all_results": True
        },
    "notes": {"element": "note", "filter_attr": "type", "filter_value": "general", "all_results": True},
    "record_contributor": {"parent_tag": "respStmt", "child_elements": ["name", "resp"], "from_root": True}
}


#MARC relator codes mapped to human-readable role labels

ROLES = {
    "ann": "Annotator",
    "arr": "Arranger",
    "att": "Attributed Author",
    "aut": "Author",
    "att": "Attributed Author",
    "csl": "Advisor/Minister",
    "co-author": "Co-Author",
    "com": "Compiler",
    "ctb": "Contributor",
    "edt": "Editor",
    "hnr": "Honoree",
    "fmo": "Former owner",
    "mentor": "Mentor",
    "ill": "Illustrator",
    "oth": "Other",
    "own": "Owner",
    "pat": "Patron",
    "pbl": "Publisher",
    "scr": "Scribe",
    "trl": "Translator",
    "wac": "Writer of added commentary",
    "wst": "Writer of supplementary textual content"
}


#entity configs

ENTITY_CONFIG = {
    "person": {
        "dir": os.path.join(DATA_DIR, "persons"),
        "title_ent": "people",
        "mapping": PERSON_MAPPING,
        "child_order": ["person", "persName", "trait", "idno", "birth", "death", "floruit", "affiliation", "bibl", "note", "name", "resp"],
        "attribute_priority": {"preferred": 0, "variant": 1},
        "element_tag": "person",
        "name_tag": "persName",
        "container_tag": ".//tei:listPerson",
        "prefix": "p"
    },
    "place": {
        "dir": os.path.join(DATA_DIR, "places"),
        "title_ent": "place",
        "mapping": PLACE_MAPPING,
        "child_order": ["place", "placeName", "desc", "idno", "bibl", "note", "name", "resp"],
        "attribute_priority": {"preferred": 0, "variant": 1, "coordinates": 0, "general": 1},
        "element_tag": "place",
        "name_tag": "placeName",
        "container_tag": ".//tei:listPlace",
        "prefix": "l"

    },
    "work": {
        "dir": os.path.join(DATA_DIR, "works"),
        "title_ent": "work",
        "mapping": WORK_MAPPING,
        "child_order": ["title", "idno", "date", "editor", "pubPlace", "note", "name", "resp"],
        "attribute_priority": {"preferred": 0, "variant": 1, "genre": 0, "subject": 1, "bibliographical": 2, "general": 3},
        "element_tag": "bibl",
        "name_tag": "title",
        "container_tag": ".//tei:listBibl",
        "prefix": "w"

    },
        "inscription": {
        "dir": os.path.join(DATA_DIR, "inscriptions"),
        "title_ent": "inscription",
        "mapping": ISC_MAPPING,
        "child_order": ["msName", "orgName", "material", "origDate", "origPlace", "note", "lang", "origin", "provenance", "person", "name", "resp"],
        "attribute_priority": {"preferred": 0, "variant": 1, "bibliographical": 0, "general": 1, "donor": 0, "associated": 1},
        "element_tag": "msDesc",
        "name_tag": "msName",
        "container_tag": ".//tei:sourceDesc",
        "prefix": "isc"
    }
}


#Bibliographical reference templates

TEMPLATE_CONFIG = {
    "bibliographical_references": {
        "Duquette, Jonathan. Debates in the Delta: An Intellectual History of Late Advaita. Brill, forthcoming.": {
        "html": "Duquette, Jonathan. <i>Debates in the Delta: An Intellectual History of Late Advaita</i>. Brill, forthcoming.",
        "identifier": "duquette-forthcoming"
        },
        "Krishnamurthy, R. The Saints of the Cauvery Delta. New Delhi: Concept Publishing Company, 1979.": {
        "html": "Krishnamurthy, R. <i>The Saints of the Cauvery Delta</i>. New Delhi: Concept Publishing Company, 1979.",
        "identifier": "krishnamurthy1979"
        },
        "Krishnaswami Ayyangar, S. (1986). Sources of Vijayanagar History. Delhi: Gian Publishing House.": {
        "html": "Krishnaswami Ayyangar, S. (1986). <i>Sources of Vijayanagar History</i>. Delhi: Gian Publishing House.",
        "identifier": "krishnaswami1986"
        },
        "Nair, Savithri Preetha. Raja Serfoji II: Science, Medicine, and Enlightenment in Tanjore. Delhi: Routledge India, 2012.": {
        "html": "Nair, Savithri Preetha. <i>Raja Serfoji II: Science, Medicine, and Enlightenment in Tanjore</i>. Delhi: Routledge India, 2012.",
        "identifier": "nair2012"
        },
        "Narayana Rao, V., Shulman, D., and S. Subrahmanyam. Symbols of Substance: Court and State in Nāyaka Period Tamilnadu. Delhi: Oxford University Press, 1992.": {
        "html": "Narayana Rao, V., Shulman, D., and S. Subrahmanyam. <i>Symbols of Substance: Court and State in Nāyaka Period Tamilnadu</i>. Delhi: Oxford University Press, 1992.",
        "identifier": "narayana1992"
        },
        "Peterson, Indira Viswanathan. ‘The Schools of Serfoji II of Tanjore: Education and Princely Modernity in Early 19th–Century India.’ In Transcolonial Modernities in South Asia, edited by Michael S. Dodson and Brian A. Hatcher, pp. 15-44. Routledge Studies in the Modern History of South Asia, 2012.": {
        "html": "Peterson, Indira Viswanathan. ‘The Schools of Serfoji II of Tanjore: Education and Princely Modernity in Early 19th–Century India.’ In <i>Transcolonial Modernities in South Asia</i>, edited by Michael S. Dodson and Brian A. Hatcher, pp. 15-44. Routledge Studies in the Modern History of South Asia, 2012.",
        "identifier": "peterson2012"
        },
        "Subrahmanyam, Sanjay (2001). Penumbral Visions: Making Polities in Early Modern South India. Ann Arbor: The University of Michigan Press.": {
        "html": "Subrahmanyam, Sanjay (2001). <i>Penumbral Visions: Making Polities in Early Modern South India</i>. Ann Arbor: The University of Michigan Press.",
        "identifier": "subrahmanyam2001"
        },
        "Vriddhagirisan, V. The Nayaks of Tanjore. Annamalainagar, 1942; reprint, New Delhi, 2011.": {
        "html": "Vriddhagirisan, V. <i>The Nayaks of Tanjore</i>. Annamalainagar, 1942; reprint, New Delhi, 2011.",
        "identifier": "vriddhagirisan2011"
        },
        "Wujastyk, Dominik. ‘La bibliothèque de Thanjavur.’ In Lieux de savoir, Tome 1 : Espaces et communautés, edited by Christian Jacob, pp. 616-36. Paris: Albin Michel, 2007.": {
        "html": "Wujastyk, Dominik. ‘La bibliothèque de Thanjavur.’ In <i>Lieux de savoir, Tome 1 : Espaces et communautés</i>, edited by Christian Jacob, pp. 616-36. Paris: Albin Michel, 2007.",
        "identifier": "wujastyk2007"
        },
        "Ariav, Talia (2002). ‘Nīlakaṇṭha Dīkṣita: An Independent Poet of the Kaveri Delta, or: The Forgotten Model of Genealogical Authorship’. In The Indian Economic and Social History Review 59(3): 273–298.": {
        "html": "Ariav, Talia (2002). ‘Nīlakaṇṭha Dīkṣita: An Independent Poet of the Kaveri Delta, or: The Forgotten Model of Genealogical Authorship’. In <i>The Indian Economic and Social History Review</i> 59(3): 273–298.",
        "identifier": "ariav2002"
        },
        "Cerulli, Anthony. ‘Allegory and History, Life and Embodiment’. In Body and Cosmos: Studies in Early Indian Medical and Astral Sciences in Honor of Kenneth G. Zysk, edited by T. Knudsen, J. Schmidt-Madsen, and S. Speyer, pp. 209-232. Leiden: Brill, 2021.": {
        "html": "Cerulli, Anthony. ‘Allegory and History, Life and Embodiment’. In <i>Body and Cosmos: Studies in Early Indian Medical and Astral Sciences in Honor of Kenneth G. Zysk</i>, edited by T. Knudsen, J. Schmidt-Madsen, and S. Speyer, pp. 209-232. Leiden: Brill, 2021.",
        "identifier": "cerulli2021"
        },
        "Duquette, Jonathan. ‘Debating God in the Delta: Trimūrti, Transcendence, and Hierarchy in Late Advaita Vedānta.’ In Science and Society in the Sanskrit World, edited by C. Fleming, T. L. Knudsen, A. Misra and V. Sharma, pp. 401-447. Leiden/Boston: Brill, 2023.": {
        "html": "Duquette, Jonathan. ‘Debating God in the Delta: <i>Trimūrti</i>, Transcendence, and Hierarchy in Late Advaita Vedānta.’ In <i>Science and Society in the Sanskrit World</i>, edited by C. Fleming, T. L. Knudsen, A. Misra and V. Sharma, pp. 401-447. Leiden/Boston: Brill, 2023.",
        "identifier": "duquette2023"
        },
        "Filliozat, Pierre-Sylvain (1967). Oeuvres poétiques de Nīlakaṇṭha Dīkṣita. Pondichéry: Institut Français de Pondichéry.": {
        "html": "Filliozat, Pierre-Sylvain (1967). <i>Oeuvres poétiques de Nīlakaṇṭha Dīkṣita</i>. Pondichéry: Institut Français de Pondichéry.",
        "identifier": "filliozat1967"
        },
        "Krishnamacharya, V. (1946). ‘Śāstradīpikāvyākhyā: Prabhāmaṇḍala’. In The Adyar Library Bulletin 10: 63–68.": {
        "html": "Krishnamacharya, V. (1946). ‘Śāstradīpikāvyākhyā: Prabhāmaṇḍala’. In <i>The Adyar Library Bulletin</i> 10: 63–68.",
        "identifier": "krishnamacharya1946"
        },
        "Raghavan, Venkataraman. Śāhendravilāsa of Śrīdhara Veṅkaṭeśa (A Poem on the Life of King Śāhaji of Tanjore, 1684-1710). Tiruchi: The Kalyan Press, 1952.": {
        "html": "Raghavan, Venkataraman. <i>Śāhendravilāsa of Śrīdhara Veṅkaṭeśa (A Poem on the Life of King Śāhaji of Tanjore, 1684-1710)</i>. Tiruchi: The Kalyan Press, 1952.",
        "identifier": "raghavan1952"
        },
        "Ramaswami Sastri, V. A. ‘Ānandarāyamakhin versus Appādhvarin’. Journal of Oriental Research Madras III (1929): 68-73.": {
        "html": "Ramaswami Sastri, V. A. ‘Ānandarāyamakhin versus Appādhvarin’. <i>Journal of Oriental Research Madras</i> III (1929): 68-73.",
        "identifier": "ramaswamisastri1929"
        },
        "Sastri, Shyamdas, and Mishra, Ramapati (eds.) (1987). Nalacaritram [Nala] of Nīlakaṇṭha Dīkṣita. Varanasi: Caukhambha Samskrrita Samsthana.": {
        "html": "Sastri, Shyamdas, and Mishra, Ramapati (eds.) (1987). <i>Nalacaritram [Nala] of Nīlakaṇṭha Dīkṣita</i>. Varanasi: Caukhambha Samskrrita Samsthana.",
        "identifier": "sastri1987"
        },
        "Sastri, T. S. Kuppuswami Sastri. ‘Ramabhadra-Dikshita and the Southern Poets of his Time.’ Indian Antiquary, Vol. XXXIII, pp. 126-142 and pp. 176-196, 2004.": {
        "html": "Sastri, T. S. Kuppuswami Sastri. ‘Ramabhadra-Dikshita and the Southern Poets of his Time.’ Indian Antiquary, Vol. XXXIII, pp. 126-142 and pp. 176-196, 2004.",
        "identifier": "kuppuswamisastri2004"
        },
        "Thiruvengadathan, A. Rāmabhadra Dīkṣita and His Works: A Study. Chennai: The Kuppuswami Sastri Research Institute, 2002.": {
        "html": "Thiruvengadathan, A. <i>Rāmabhadra Dīkṣita and His Works: A Study</i>. Chennai: The Kuppuswami Sastri Research Institute, 2002.",
        "identifier": "thiruvengadathan2002"
        },
        "Unni, N. Parameswaran (1995). Nilakantha Diksita. Delhi: Sahitya Akademi.": {
        "html": "Unni, N. Parameswaran (1995). <i>Nilakantha Diksita</i>. Delhi: Sahitya Akademi.",
        "identifier": "unni1995"
        },
        "Wujastyk, Dominik. ‘Rāmasubrahmaṇya’s Manuscripts: Intellectual Networks in the Kaveri Delta, 1693-1922.’ In Aspects of Manuscript Culture in South India, edited by Saraju Rath, pp. 235-252. Leiden: Brill, 2012.": {
        "html": "Wujastyk, Dominik. ‘Rāmasubrahmaṇya’s Manuscripts: Intellectual Networks in the Kaveri Delta, 1693-1922.’ In <i>Aspects of Manuscript Culture in South India</i>, edited by Saraju Rath, pp. 235-252. Leiden: Brill, 2012.",
        "identifier": "wujastyk2012"
        },
        "Jackson, William J. ‘Name-devotion in Indian Religions and Kaveri Delta Namasiddhanta.’ Journal for the Study of Religion 7(2) (1994): 33-55.": {
        "html": "Jackson, William J. ‘Name-devotion in Indian Religions and Kaveri Delta Namasiddhanta.’ <i>Journal for the Study of Religion</i> 7(2) (1994): 33-55.",
        "identifier": "jackson1994"
        },
        "Jackson, William J. (ed.). The Power of the Sacred Name: Indian Spirituality Inspired by Mantras. Bloomington: World Wisdom, 2011.": {
        "html": "Jackson, William J. (ed.). <i>The Power of the Sacred Name: Indian Spirituality Inspired by Mantras</i>. Bloomington: World Wisdom, 2011.",
        "identifier": "jackson2011"
        },
        "Raghavan, Venkataraman. Prayers, Praises, and Psalms. Madras: G. A. Natesan and Co, 1938.": {
        "html": "Raghavan, Venkataraman. <i>Prayers, Praises, and Psalms</i>. Madras: G. A. Natesan and Co, 1938.",
        "identifier": "raghavan1938"
        },
        "Seetha, S. (2001). Tanjore as a Seat of Music (During the 17th, 18th and 19th Centuries). Madras: University of Madras.": {
        "html": "Seetha, S. (2001). <i>Tanjore as a Seat of Music (During the 17th, 18th and 19th Centuries)</i>. Madras: University of Madras.",
        "identifier": "seetha2001"
        },
        "Singer, Milton. When a Great Tradition Modernizes: An Anthropological Approach to Indian Civilization, specifically the chapter ‘The Rādhā-Krishna Bhajanas of Madras City’ (pp. 199-241). London: Pall Mall Press, 1972.": {
        "html": "Singer, Milton. <i>When a Great Tradition Modernizes: An Anthropological Approach to Indian Civilization</i>, specifically the chapter ‘The Rādhā-Krishna Bhajanas of Madras City’ (pp. 199-241). London: Pall Mall Press, 1972.",
        "identifier": "singer1972"
        },
        "Soneji, Davesh. ‘The Powers of Polyglossia: Marathi Kīrtan, Multilingualism, and the Making of a South Indian Devotional Tradition.’ International Journal of Hindu Studies 17 (3) (2014): 339-369": {
        "html": "Soneji, Davesh. ‘The Powers of Polyglossia: Marathi Kīrtan, Multilingualism, and the Making of a South Indian Devotional Tradition.’ <i>International Journal of Hindu Studies</i> 17 (3) (2014): 339-369",
        "identifier": "soneji2014"
        },
        "Venkateswaran, T. K. ‘Rādhā-Krishna Bhajanas of South India: A Phenomenological, Theological, and Philosophical Study.’ In Krishna: Myths, Rites, and Attitudes, edited by Milton Singer, pp. 139-72. Chicago: The University of Chicago Press/Vienna: University of Vienna, 1966.": {
        "html": "Venkateswaran, T. K. ‘Rādhā-Krishna Bhajanas of South India: A Phenomenological, Theological, and Philosophical Study.’ In <i>Krishna: Myths, Rites, and Attitudes</i>, edited by Milton Singer, pp. 139-72. Chicago: The University of Chicago Press/Vienna: University of Vienna, 1966.",
        "identifier": "venkateswaran1966"
        },
        "Venkatkrishnan, Anand. Love in the Time of Scholarship: The Bhāgavata Purāṇa in Indian Intellectual History. Oxford: Oxford University Press (Rocher Indology Series), 2024.": {
        "html": "Venkatkrishnan, Anand. <i>Love in the Time of Scholarship: The</i> Bhāgavata Purāṇa <i>in Indian Intellectual History</i>. Oxford: Oxford University Press (Rocher Indology Series), 2024.",
        "identifier": "venkatkrishnan2024"
        },
        "Aiyer, K. V. Subrahmanya. Historical Sketches of Ancient Dekhan. Madras: Modern Printing Works, 1917.": {
        "html": "Aiyer, K. V. Subrahmanya. <i>Historical Sketches of Ancient Dekhan</i>. Madras: Modern Printing Works, 1917.",
        "identifier": "aiyer1917"
        },
        "Béteille, André. ‘Sripuram: A Village in Tanjore District.’ The Economic Weekly, Annual number, February 1962, pp. 141-46.": {
        "html": "Béteille, André. ‘Sripuram: A Village in Tanjore District.’ <i>The Economic Weekly</i>, Annual number, February 1962, pp. 141-46.",
        "identifier": "beteille1962"
        },
        "Béteille, André. Caste, Class, and Power: Changing Patterns of Stratification in a Tanjore Village. Delhi: Oxford University Press (3rd ed.), 2012. First edition published in 1996.": {
        "html": "Béteille, André. <i>Caste, Class, and Power: Changing Patterns of Stratification in a Tanjore Village</i>. Delhi: Oxford University Press (3rd ed.), 2012. First edition published in 1996.",
        "identifier": "beteille2012"
        },
        "Bronkhorst, Johannes. ‘Āśramas, Agrahāras, and Monasteries.’ In On the Growth and Composition of the Sanskrit Epics and Purāṇas: Relationship to Kāvya, Social and Economic Context, edited by Ivan Andrijanić and Sven Sellmer (Proceedings of the Fifth Dubrovnik International Conference on the Sanskrit Epics and Purāṇas, 2008), 137-60. Zagreb: Croatian Academy of Sciences and Arts, XXXVI, 2016.": {
        "html": "Bronkhorst, Johannes. ‘Āśramas, Agrahāras, and Monasteries.’ In <i>On the Growth and Composition of the Sanskrit Epics and Purāṇas: Relationship to Kāvya, Social and Economic Context</i>, edited by Ivan Andrijanić and Sven Sellmer (Proceedings of the Fifth Dubrovnik International Conference on the Sanskrit Epics and Purāṇas, 2008), 137-60. Zagreb: Croatian Academy of Sciences and Arts, XXXVI, 2016.",
        "identifier": "bronkhorst2016"
        },
        "Champakalakshmi, R. ‘Reappraisal of a Brahmanical Institution: The Brahmadeya and its Ramifications in Early South India.’ In Structure and Society in Early South India, edited by Kenneth R. Hall, 59-84. Delhi: Oxford University Press, 2001.": {
        "html": "Champakalakshmi, R. ‘Reappraisal of a Brahmanical Institution: The Brahmadeya and its Ramifications in Early South India.’ In <i>Structure and Society in Early South India</i>, edited by Kenneth R. Hall, 59-84. Delhi: Oxford University Press, 2001.",
        "identifier": "champakalakshmi2001"
        },
        "Fuller, C. J. and Narasimhan, Haripriya. ‘The agraharam: The Transformation of Social Space and Brahman Status in Tamilnadu during the Colonial and Postcolonial periods.’ In Ritual, Caste, and Religion in Colonial South India, edited by Michael Bergunder, Heiko Freise and Ulrike Schröder, pp. 219-37. Halle: Neue Hallesche Berichte, 2010.": {
        "html": "Fuller, C. J. and Narasimhan, Haripriya. ‘The <i>agraharam</i>: The Transformation of Social Space and Brahman Status in Tamilnadu during the Colonial and Postcolonial periods.’ In <i>Ritual, Caste, and Religion in Colonial South India</i>, edited by Michael Bergunder, Heiko Freise and Ulrike Schröder, pp. 219-37. Halle: Neue Hallesche Berichte, 2010.",
        "identifier": "fuller-narasimhan2010"
        },
        "Gough, Kathleen. Rural Society in Southeast India. Cambridge: Cambridge University Press, 1981.": {
        "html": "Gough, Kathleen. <i>Rural Society in Southeast India</i>. Cambridge: Cambridge University Press, 1981.",
        "identifier": "gough1981"
        },
        "Gurumurthy, S. Education in South India (Ancient and Medieval Period). Madras: New Era Publications, 1979.": {
        "html": "Gurumurthy, S. <i>Education in South India (Ancient and Medieval Period)</i>. Madras: New Era Publications, 1979.",
        "identifier": "gurumurthy1979"
        },
        "Heitzman, James. Gifts of Power: Lordship in an Early Indian State. Delhi: Oxford University Press, 1997.": {
        "html": "Heitzman, James. <i>Gifts of Power: Lordship in an Early Indian State</i>. Delhi: Oxford University Press, 1997.",
        "identifier": "heitzman1997"
        },
        "Ludden, David. Peasant History in South India. Princeton: Princeton University Press, 1985": {
        "html": "Ludden, David. <i>Peasant History in South India</i>. Princeton: Princeton University Press, 1985",
        "identifier": "ludden1985"
        },
        "Shantakumari, S. Leela. History of the Agraharas, Karnataka, 400-1300. Madras: New Era Publications, 1986.": {
        "html": "Shantakumari, S. Leela. <i>History of the Agraharas, Karnataka, 400-1300</i>. Madras: New Era Publications, 1986.",
        "identifier": "shantakumari1986"
        },
        "Stein, Burton. Peasant State and Society in Medieval South India. Oxford: Oxford University Press, 1980.": {
        "html": "Stein, Burton. <i>Peasant State and Society in Medieval South India</i>. Oxford: Oxford University Press, 1980.",
        "identifier": "stein1980"
        },
        "Subbarayalu, Y. Historical and Political Geography of the Cōḻa Country. Delhi: Primus Books, 2026.": {
        "html": "Subbarayalu, Y. <i>Historical and Political Geography of the Cōḻa Country</i>. Delhi: Primus Books, 2026.",
        "identifier": "subbarayalu2026"
        },
        "Veluthat, Kesavan. <i>Brahman Settlements in Kerala: Historical Studies</i>. Sandhya Publications, 1978.": {
        "html": "Veluthat, Kesavan. <i>Brahman Settlements in Kerala: Historical Studies</i>. Sandhya Publications, 1978.",
        "identifier": "veluthat1978"
        },
        "Clark, Matthew. The Daśanāmī-Saṃnyāsīs: The Integration of Ascetic Lineages into an Order. Leiden/Boston: Brill, 2006.": {
        "html": "Clark, Matthew. <i>The Daśanāmī-Saṃnyāsīs: The Integration of Ascetic Lineages into an Order</i>. Leiden/Boston: Brill, 2006.",
        "identifier": "clark2006"
        },
        "Nowicka, Olga. ‘Vedic Ritualism and Advaita Vedānta Monastic Institutions in Kerala.’ Studia Religiologica 50, no. 2 (2017): 163-171.": {
        "html": "Nowicka, Olga. ‘Vedic Ritualism and Advaita Vedānta Monastic Institutions in Kerala.’ <i>Studia Religiologica</i> 50, no. 2 (2017): 163-171.",
        "identifier": "nowicka2017"
        },
        "Simmons, Caleb. ‘Maṭhas: Towards Understanding the Public Religious, Educational, and Political Ascetic Institution in South Asian religions’. Religion Compass 17 (2023): 1-9.": {
        "html": "Simmons, Caleb. ‘Maṭhas: Towards Understanding the Public Religious, Educational, and Political Ascetic Institution in South Asian religions’. <i>Religion Compass</i> 17 (2023): 1-9.",
        "identifier": "simmons2023"
        },
        "Stoker, Valerie. 'Darbār, Maṭha, Devasthānam: The Politics of Intellectual Commitment and Religious Organization in Sixteenth-Century South India’. South Asian History and Culture 6(1) (2015): 130-146.": {
        "html": "Stoker, Valerie. 'Darbār, Maṭha, Devasthānam: The Politics of Intellectual Commitment and Religious Organization in Sixteenth-Century South India’. <i>South Asian History and Culture</i> 6(1) (2015): 130-146.",
        "identifier": "stoker2015"
        },
        "Trento, Margherita. ‘Early Modern Tamil Prose: A Note on Some Manuscripts of the Tiruvāvaṭutuṟai Ātīṉam. In For the Love of Tamil: Essays in Honor of E. Annamalai, edited by Margherita Trento et al., pp. 455-477. Napoli, 2025.": {
        "html": "Trento, Margherita. ‘Early Modern Tamil Prose: A Note on Some Manuscripts of the Tiruvāvaṭutuṟai Ātīṉam. In <i>For the Love of Tamil: Essays in Honor of E. Annamalai</i>, edited by Margherita Trento et al., pp. 455-477. Napoli, 2025.",
        "identifier": "trento2025"
        },
        "Ariav, Talia and Whitney Cox. ‘On Unresolved Tensions in Rāmabhadra Dīkṣita’s Śṛṅgāratilakabhāṇa.’ Journal of South Asian Intellectual History 4 (2021): 47-71.": {
        "html": "Ariav, Talia and Whitney Cox. ‘On Unresolved Tensions in Rāmabhadra Dīkṣita’s <i>Śṛṅgāratilakabhāṇa</i>.’ <i>Journal of South Asian Intellectual History</i> 4 (2021): 47-71.",
        "identifier": "ariav2021"
        },
        "Ariav, Talia, and Keerthi, Naresh (2022). ‘Churning Selves: Intersecting Biographies in the Nīlakaṇṭhavijaya.’ In Cracow Indological Studies 24: 29–60.": {
        "html": "Ariav, Talia, and Keerthi, Naresh (2022). ‘Churning Selves: Intersecting Biographies in the <i>Nīlakaṇṭhavijaya</i>.’ In <i>Cracow Indological Studies</i> 24: 29–60.",
        "identifier": "ariav2022"
        },
        "Ariav, Talia (2025). ‘The Mohinīvilāsa Kuṟavañci: Performed Hybridity from Early Maratha Thanjavur’. In For the Love of Tamil: Essays in Honor of E. Annamalai, edited by Margherita Trento et al. Napoli: 67-85.": {
        "html": "Ariav, Talia (2025). ‘The <i>Mohinīvilāsa Kuṟavañci</i>: Performed Hybridity from Early Maratha Thanjavur’. In <i>For the Love of Tamil: Essays in Honor of E. Annamalai</i>, edited by Margherita Trento et al. Napoli: 67-85.",
        "identifier": "ariav2025"
        },
        "Ariav, Talia, and Trento, Margherita (2025). ‘A History of Sandeśa on Stage (and Its Aftermath): Sanskrit Padams from Eighteenth-Century Thanjavur’. In The Routledge Companion to Courier Poetry From South Asia and Beyond, edited by Yigal Bronner and David Shulman. Taylor and Francis, https://doi.org/10.4324/9781003639244.": {
        "html": "Ariav, Talia, and Trento, Margherita (2025). ‘A History of Sandeśa on Stage (and Its Aftermath): Sanskrit Padams from Eighteenth-Century Thanjavur’. In <i>The Routledge Companion to Courier Poetry From South Asia and Beyond</i>, edited by Yigal Bronner and David Shulman. Taylor and Francis, https://doi.org/10.4324/9781003639244.",
        "identifier": "ariavtrento2025"
        },
        "Bronner, Yigal, and David Shulman (2006). ‘ “A Cloud Turned Goose”: Sanskrit in the Vernacular Millennium.’ The Indian Economic & Social History Review 43 (1): 1–30.": {
        "html": "Bronner, Yigal, and David Shulman (2006). ‘ “A Cloud Turned Goose”: Sanskrit in the Vernacular Millennium.’ <i>The Indian Economic & Social History Review</i> 43 (1): 1–30.",
        "identifier": "bronner2006"
        },
        "Bronner, Yigal (2007). ‘Singing to God, Educating the People: Appayya Dīkṣita and the Function of Stotras.’ Journal of the American Oriental Society 127 (2): 113–30.": {
        "html": "Bronner, Yigal (2007). ‘Singing to God, Educating the People: Appayya Dīkṣita and the Function of Stotras.’ <i>Journal of the American Oriental Society</i> 127 (2): 113–30.",
        "identifier": "bronner2007"
        },
        "Bronner, Yigal, and David Shulman (2009). ‘Introduction to Poems and Prayers From South India.’ In ‘Self Surrender’, ‘Peace’, ‘Compassion’ & ‘Mission of the Goose’ of Appayya Dīkṣita, Nīlakaṇṭha Dīkṣita, and Vedānta Deśika, edited by Yigal Bronner and David Shulman. Clay Sanskrit Library. New York: NYC Press: xix–lxx.": {
        "html": "Bronner, Yigal, and David Shulman (2009). ‘Introduction to Poems and Prayers From South India.’ In <i>‘Self Surrender’, ‘Peace’, ‘Compassion’ & ‘Mission of the Goose’ of Appayya Dīkṣita, Nīlakaṇṭha Dīkṣita, and Vedānta Deśika</i>, edited by Yigal Bronner and David Shulman. Clay Sanskrit Library. New York: NYC Press: xix–lxx.",
        "identifier": "bronner2009"
        },
        "Ebeling, Sascha (2010). Colonizing the Realm of Words. New York: SUNY.": {
        "html": "Ebeling, Sascha (2010). <i>Colonizing the Realm of Words</i>. New York: SUNY.",
        "identifier": "ebeling2010"
        },
        "Fisher, Elaine M (2017). Hindu Pluralism: Religion and the Public Sphere in Early Modern South India. South Asia Across the Disciplines. California: University of California Press.": {
        "html": "Fisher, Elaine M (2017). <i>Hindu Pluralism: Religion and the Public Sphere in Early Modern South India</i>. South Asia Across the Disciplines. California: University of California Press.",
        "identifier": "fisher2017"
        },
        "Gomez, Kashi (2023). ‘Sanskrit and the Labour of Gender in Early Modern South India.’ Modern Asian Studies 57: 167-194.": {
        "html": "Gomez, Kashi (2023). ‘Sanskrit and the Labour of Gender in Early Modern South India.’ <i>Modern Asian Studies</i> 57: 167-194.",
        "identifier": "gomez2023"
        },
        "Goren-Arzony, Sivan (2022). ‘On Brewing Love Potions and Crafting Answers: Two Literary Techniques in an Early Modern Maṇipravāḷam Poem.’ Cracow Indological Studies 24 (1): 85–109.": {
        "html": "Goren-Arzony, Sivan (2022). ‘On Brewing Love Potions and Crafting Answers: Two Literary Techniques in an Early Modern Maṇipravāḷam Poem.’ <i>Cracow Indological Studies</i> 24 (1): 85–109.",
        "identifier": "goren2022"
        },
        "Hopkins, Steven Paul (2002). Singing the Body of God: The Hymns of Vedantadesika in Their South Indian Tradition. Oxford, New York: Oxford University Press.": {
        "html": "Hopkins, Steven Paul (2002). <i>Singing the Body of God: The Hymns of Vedantadesika in Their South Indian Tradition</i>. Oxford, New York: Oxford University Press.",
        "identifier": "hopkins2002"
        },
        "Peterson, Indira Viswanathan (1998). ‘The Evolution of the Kuravañci Dance Drama in Tamil Nadu: Negotiating the “Folk” and the “Classical” in the Bhārata Nātyam Canon.’ South Asia Research 18 (1): 39–72.": {
        "html": "Peterson, Indira Viswanathan (1998). ‘The Evolution of the Kuravañci Dance Drama in Tamil Nadu: Negotiating the “Folk” and the “Classical” in the Bhārata Nātyam Canon.’ <i>South Asia Research</i> 18 (1): 39–72.",
        "identifier": "peterson1998"
        },
        "Peterson, Indira Viswanathan (2011). ‘Multilingual Dramas at the Tanjavur Maratha Court and Literary Cultures in Early Modern South India.’ The Medieval History Journal 14 (2): 285–321.": {
        "html": "Peterson, Indira Viswanathan (2011). ‘Multilingual Dramas at the Tanjavur Maratha Court and Literary Cultures in Early Modern South India.’ <i>The Medieval History Journal</i> 14 (2): 285–321.",
        "identifier": "peterson2011"
        },
        "Rao, Velcheru Narayana, and David Dean Shulman (1998). A Poem at the Right Moment: Remembered Verses from Premodern South India. University of California Press.": {
        "html": "Rao, Velcheru Narayana, and David Dean Shulman (1998). <i>A Poem at the Right Moment: Remembered Verses from Premodern South India</i>. University of California Press.",
        "identifier": "rao1998"
        },
        "Rao, Velcheru Narayana, David Shulman, and Sanjay Subrahmanyam (1998). Symbols of Substance: Court and State in Nayaka Period Tamilnadu. Delhi: Oxford University Press.": {
        "html": "Rao, Velcheru Narayana, David Shulman, and Sanjay Subrahmanyam (1998). <i>Symbols of Substance: Court and State in Nayaka Period Tamilnadu</i>. Delhi: Oxford University Press.",
        "identifier": "raoshulman1998"
        },
        "Shulman, David (2001). <i>The Wisdom of Poets: Studies in Tamil, Telugu, and Sanskrit</i>. Oxford University Press.": {
        "html": "Shulman, David (2001). <i>The Wisdom of Poets: Studies in Tamil, Telugu, and Sanskrit</i>. Oxford University Press.",
        "identifier": "shulman2001"
        },
        "Shulman, David (2012). More than Real: A History of the Imagination in South India. Cambridge, Mass: Harvard University Press.": {
        "html": "Shulman, David (2012). <i>More than Real: A History of the Imagination in South India</i>. Cambridge, Mass: Harvard University Press.",
        "identifier": "shulman2012"
        },
        "Shulman, David (2016). Tamil: A Biography. Cambridge: Harvard University Press.": {
        "html": "Shulman, David (2016). <i>Tamil: A Biography</i>. Cambridge: Harvard University Press.",
        "identifier": "shulman2016"
        },
        "Shulman, David (2022). ‘The Early-Modern South Indian Prabandha.’ Journal of South Asian Intellectual History 4 (1): 1–21.": {
        "html": "Shulman, David (2022). ‘The Early-Modern South Indian Prabandha.’ <i>Journal of South Asian Intellectual History</i> 4 (1): 1–21.",
        "identifier": "shulman2022"
        },
        "Soneji, Davesh (2013). ‘The Powers of Polyglossia: Marathi Kīrtan, Multilingualism, and the Making of a South Indian Devotional Tradition.’ International Journal of Hindu Studies 17 (3): 339–69.": {
        "html": "Soneji, Davesh (2013). ‘The Powers of Polyglossia: Marathi Kīrtan, Multilingualism, and the Making of a South Indian Devotional Tradition.’ <i>International Journal of Hindu Studies</i> 17 (3): 339–69.",
        "identifier": "soneji2013"
        },
        "Soneji, Davesh (2012). Unfinished Gestures: Devadasis, Memory, and Modernity in South India. South Asia Across the Disciplines. Chicago, IL: University of Chicago Press.": {
        "html": "Soneji, Davesh (2012). <i>Unfinished Gestures: Devadasis, Memory, and Modernity in South India</i>. South Asia Across the Disciplines. Chicago, IL: University of Chicago Press.",
        "identifier": "soneji2012"
        },
        "A Catalogue of the Sanskrit Manuscripts in the Adyar Library. Parts 1–2, 1926–1928.": {
        "html": "A Catalogue of the Sanskrit Manuscripts in the Adyar Library. Parts 1–2, 1926–1928.",
        "identifier": "adyar-catalogue-2"
        },
        "A Classified Index to the Sanskrit Mss. In the Palace at Tanjore, A. C. Burnell, 1880.": {
        "html": "A Classified Index to the Sanskrit Mss. In the Palace at Tanjore, A. C. Burnell, 1880.",
        "identifier": "tanjore-catalogue"
        },
        "A Descriptive Catalogue of the Sanskrit Manuscripts, Advaita: Oriental Research Institute, Mysore. Vol. 3, 1967.": {
        "html": "A Descriptive Catalogue of the Sanskrit Manuscripts, Advaita: Oriental Research Institute, Mysore. Vol. 3, 1967.",
        "identifier": "advaita-catalogue"
        },
        "Descriptive Catalogue of the Sanskrit Manuscripts in the Government Oriental Manuscripts Library, Madras (GOML). Vols. 1–25.": {
        "html": "Descriptive Catalogue of the Sanskrit Manuscripts in the Government Oriental Manuscripts Library, Madras (GOML). Vols. 1–25.",
        "identifier": "goml-catalogue"
        },
        "A Descriptive Catalogue of the Sanskrit Manuscripts in the Tanjore Maharaja Serfoji’s Sarasvati Mahal Library, Tanjore (Tanjore). Vols. 1–19.": {
        "html": "A Descriptive Catalogue of the Sanskrit Manuscripts in the Tanjore Maharaja Serfoji’s Sarasvati Mahal Library, Tanjore (Tanjore). Vols. 1–19.",
        "identifier": "sml-catalogue"
        },
        "A Triennial Catalogue of Manuscripts, GOML Madras, Vol. II, Part I, Sanskrit C, 1917.": {
        "html": "A Triennial Catalogue of Manuscripts, GOML Madras, Vol. II, Part I, Sanskrit C, 1917.",
        "identifier": "goml-catalogue-2"
        },
        "A Triennial Catalogue of Manuscripts, GOML Madras, Vol. IV, Part I, Sanskrit A, 1927.": {
        "html": "A Triennial Catalogue of Manuscripts, GOML Madras, Vol. IV, Part I, Sanskrit A, 1927.",
        "identifier": "goml-catalogue-3"
        },
        "Catalogue of the Sanskrit Manuscripts in the British Museum, Cecil Bendall, 1902.": {
        "html": "Catalogue of the Sanskrit Manuscripts in the British Museum, Cecil Bendall, 1902.",
        "identifier": "british-catalogue"
        },
        "Catalogue of the Sanskrit Manuscripts in the Library of the India Office (IO). Part IV, 1984.": {
        "html": "Catalogue of the Sanskrit Manuscripts in the Library of the India Office (IO). Part IV, 1984.",
        "identifier": "india-office-catalogue"
        },
        "Catalogue of Sanskrit Manuscripts in the Govt. Oriental Library, Mysore, 1992.": {
        "html": "Catalogue of Sanskrit Manuscripts in the Govt. Oriental Library, Mysore, 1992.",
        "identifier": "oriental-catalogue"
        },
        "Descriptive Catalogue of Sanskrit Manuscripts, Advaita, Anubhavādvaita, Viśiṣṭādvaita: Oriental Research Institute, Mysore. Vol. 11, 1985": {
        "html": "Descriptive Catalogue of Sanskrit Manuscripts, Advaita, Anubhavādvaita, Viśiṣṭādvaita: Oriental Research Institute, Mysore. Vol. 11, 1985",
        "identifier": "advaita-catalogue-2"
        },
        "Descriptive Catalogue of Sanskrit Manuscripts in the Adyar Library (Adyar). Vols. 1–13.": {
        "html": "Descriptive Catalogue of Sanskrit Manuscripts in the Adyar Library (Adyar). Vols. 1–13.",
        "identifier": "adyar-catalogue"
        },
        "Lists of Sanskrit Manuscripts in Private Libraries of Southern India (Oppert). Vols 1–2.": {
        "html": "Lists of Sanskrit Manuscripts in Private Libraries of Southern India (Oppert). Vols 1–2.",
        "identifier": "oppert-private-libraries"
        },
        "New Catalogus Catalogorum (NCC). Vols 1–36.": {
        "html": "New Catalogus Catalogorum (NCC). Vols 1–36.",
        "identifier": "ncc"
        },
        "Thangaswami, R (1980). A Bibliographical Survey of Advaita Vedānta Literature. Madras: Rathnam Press": {
        "html": "Thangaswami, R (1980). <i>A Bibliographical Survey of Advaita Vedānta Literature</i>. Madras: Rathnam Press",
        "identifier": "thangaswami1980"
        },
        "The Diamond Jubilee Souvenir of the Advaita Sabha, Kumbakonam, Madras: Liberty Press, 1956.": {
        "html": "<i>The Diamond Jubilee Souvenir of the Advaita Sabha, Kumbakonam</i>, Madras: Liberty Press, 1956.",
        "identifier": "diamond1956"
        }
    }
}

