import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
BUILD_DIR = os.path.join(BASE_DIR, "build")

NS_TEI = "http://www.tei-c.org/ns/1.0"
NS_XML = "http://www.w3.org/XML/1998/namespace"

NSMAP = {
    "tei": NS_TEI,
    "xml": NS_XML,
}


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


TEMPLATE_CONFIG = {
    "bibliographical_references": {
        "Ariav, Talia. ‘Nīlakaṇṭha Dīkṣita: An Independent Poet of the Kaveri Delta, or: The Forgotten Model of Genealogical Authorship.’ The Indian Economic and Social History Review 59, no. 3 (2022): 273-298.": {
        "html": "Ariav, Talia. ‘Nīlakaṇṭha Dīkṣita: An Independent Poet of the Kaveri Delta, or: The Forgotten Model of Genealogical Authorship.’ <i>The Indian Economic and Social History Review</i> 59, no. 3 (2022): 273-298.",
        "identifier": "ariav2022"
        },
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
        "Cerulli, Anthony. ‘Allegory and History, Life and Embodiment’. In Body and Cosmos: Studies in Early Indian Medical and Astral Sciences in Honor of Kenneth G. Zysk, edited by T. Knudsen, J. Schmidt-Madsen, and S. Speyer, pp. 209-232. Leiden: Brill, 2021.": {
        "html": "Cerulli, Anthony. ‘Allegory and History, Life and Embodiment’. In <i>Body and Cosmos: Studies in Early Indian Medical and Astral Sciences in Honor of Kenneth G. Zysk</i>, edited by T. Knudsen, J. Schmidt-Madsen, and S. Speyer, pp. 209-232. Leiden: Brill, 2021.",
        "identifier": "cerulli2021"
        },
        "Duquette, Jonathan. ‘Debating God in the Delta: Trimūrti, Transcendence, and Hierarchy in Late Advaita Vedānta.’ In Science and Society in the Sanskrit World, edited by C. Fleming, T. L. Knudsen, A. Misra and V. Sharma, pp. 401-447. Leiden/Boston: Brill, 2023.": {
        "html": "Duquette, Jonathan. ‘Debating God in the Delta: <i>Trimūrti</i>, Transcendence, and Hierarchy in Late Advaita Vedānta.’ In <i>Science and Society in the Sanskrit World</i>, edited by C. Fleming, T. L. Knudsen, A. Misra and V. Sharma, pp. 401-447. Leiden/Boston: Brill, 2023.",
        "identifier": "duquette2023"
        },
        "Raghavan, Venkataraman. Śāhendravilāsa of Śrīdhara Veṅkaṭeśa (A Poem on the Life of King Śāhaji of Tanjore, 1684-1710). Tiruchi: The Kalyan Press, 1952.": {
        "html": "Raghavan, Venkataraman. <i>Śāhendravilāsa of Śrīdhara Veṅkaṭeśa (A Poem on the Life of King Śāhaji of Tanjore, 1684-1710)</i>. Tiruchi: The Kalyan Press, 1952.",
        "identifier": "raghavan1952"
        },
        "Ramaswami Sastri, V. A. ‘Ānandarāyamakhin versus Appādhvarin’. Journal of Oriental Research Madras III (1929): 68-73.": {
        "html": "Ramaswami Sastri, V. A. ‘Ānandarāyamakhin versus Appādhvarin’. <i>Journal of Oriental Research Madras</i> III (1929): 68-73.",
        "identifier": "ramaswamisastri1929"
        },
        "Sastri, T. S. Kuppuswami Sastri. ‘Ramabhadra-Dikshita and the Southern Poets of his Time.’ Indian Antiquary, Vol. XXXIII, pp. 126-142 and pp. 176-196, 2004.": {
        "html": "Sastri, T. S. Kuppuswami Sastri. ‘Ramabhadra-Dikshita and the Southern Poets of his Time.’ Indian Antiquary, Vol. XXXIII, pp. 126-142 and pp. 176-196, 2004.",
        "identifier": "kuppuswamisastri2004"
        },
        "Thiruvengadathan, A. Rāmabhadra Dīkṣita and His Works: A Study. Chennai: The Kuppuswami Sastri Research Institute, 2002.": {
        "html": "Thiruvengadathan, A. <i>Rāmabhadra Dīkṣita and His Works: A Study</i>. Chennai: The Kuppuswami Sastri Research Institute, 2002.",
        "identifier": "thiruvengadathan2002"
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
        "New Catalogus Catalogorum (NCC). Vols 1-36.": {
        "html": "New Catalogus Catalogorum (NCC). Vols 1–36.",
        "identifier": "ncc"
        },
        "A Descriptive Catalogue of the Sanskrit Manuscripts in the Sarasvati Mahal Library, Tanjore (Tanjore). Vols. 1–19.": {
        "html": "A Descriptive Catalogue of the Sanskrit Manuscripts in the Sarasvati Mahal Library, Tanjore (Tanjore). Vols. 1–19.",
        "identifier": "sml-catalogue"
        },
        "Descriptive Catalogue of the Sanskrit Manuscripts in the Government Oriental Manuscripts Library, Madras (GOML). Vols. 1–25.": {
        "html": "Descriptive Catalogue of the Sanskrit Manuscripts in the Government Oriental Manuscripts Library, Madras (GOML). Vols. 1–25.",
        "identifier": "goml-catalogue"
        },
        "Lists of Sanskrit Manuscripts in Private Libraries of Southern India (Oppert). Vols 1–2": {
        "html": "Lists of Sanskrit Manuscripts in Private Libraries of Southern India (Oppert). Vols 1–2",
        "identifier": "oppert-private-libraries"
        },
        "Descriptive Catalogue of Sanskrit Manuscripts in the Adyar Library (Adyar). Vols. 1–13.": {
        "html": "Descriptive Catalogue of Sanskrit Manuscripts in the Adyar Library (Adyar). Vols. 1–13.",
        "identifier": "adyar-catalogue"
        },
        "A Descriptive Catalogue of Sanskrit Manuscripts in the Government Oriental Library, Mysore (Mysore). Vol. 3.": {
        "html": "A Descriptive Catalogue of Sanskrit Manuscripts in the Government Oriental Library, Mysore (Mysore). Vol. 3.",
        "identifier": "mysore-catalogue"
        }
    }
}

