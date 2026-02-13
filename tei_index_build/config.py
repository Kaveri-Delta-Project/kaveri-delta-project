import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
MS_DIR = os.path.join(DATA_DIR, "manuscripts")
PERSONS_DIR = os.path.join(DATA_DIR, "persons")
WORKS_DIR = os.path.join(DATA_DIR, "works")
PLACES_DIR = os.path.join(DATA_DIR, "places")

# === TEI namespace for XPath queries ===
NS_TEI = "http://www.tei-c.org/ns/1.0"
NSMAP = {"tei": NS_TEI}

XML_CACHE = {}