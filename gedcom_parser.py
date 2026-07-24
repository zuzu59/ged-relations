"""Parser GEDCOM → SQLite using python-gedcom library.

Uses python-gedcom for robust GEDCOM 5.5.1 parsing with proper UTF-8 support.
Extracts: individuals, dates, filiation (father/mother/children).
"""
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "ged_data.db")

# Relations parent-enfant
REL_FATHER = "father"
REL_MOTHER = "mother"
REL_SPOUSE = "spouse"


def strip_accents(text):
    """Retire les accents d'une chaîne."""
    if not text:
        return ""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _parse_gedcom_date(date_str):
    """Parse une date GEDCOM (ex: ' 1 JAN 1900')."""
    if not date_str:
        return ""
    date_str = date_str.strip()
    if not date_str:
        return ""
    
    # Format GEDCOM: J MOY AAAA
    parts = date_str.split()
    if len(parts) >= 3:
        day = parts[0].zfill(2)
        month_map = {
            "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04",
            "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08",
            "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"
        }
        month = month_map.get(parts[1].upper(), "01")
        year = parts[2]
        return f"{year}-{month}-{day}"
    
    # Format ISO possible
    if "-" in date_str and len(date_str) >= 10:
        return date_str[:10]
    
    return date_str


def parse_gedcom(filepath):
    """Parse un fichier GEDCOM et retourne les données brutes.
    
    Args:
        filepath: chemin vers le fichier GEDCOM
        
    Returns:
        tuple: (individuals dict, families dict)
    """
    from gedcom.parser import Parser
    
    individuals = {}
    families = {}
    
    parser = Parser()
    parser.parse_file(filepath, strict=False)
    
    elements = parser.get_element_list()
    
    # 1. Parser les individus
    for elem in elements:
        if elem.get_level() == 0 and elem.get_tag() == 'INDI':
            ind_id = elem.get_pointer()
            given_name = ""
            family_name = ""
            sex = ""
            birth_date = ""
            death_date = ""
            father_id = ""
            mother_id = ""
            families_list = []
            
            for child in elem.get_child_elements():
                tag = child.get_tag()
                value = child.get_value() or ""
                
                if tag == 'NAME':
                    # Format: Prénom /Nom/
                    if '/' in value:
                        parts = value.split('/')
                        given_name = parts[0].strip()
                        family_name = parts[1].strip() if len(parts) > 1 else ""
                    else:
                        given_name = value.strip()
                        
                elif tag == 'SEX':
                    sex = value.strip()
                    
                elif tag == 'FAMC':
                    father_id = value.strip().lstrip('@').rstrip('@')
                    
                elif tag == 'FAMS':
                    fam_id = value.strip().lstrip('@').rstrip('@')
                    families_list.append(fam_id)
                    
                elif tag == 'BIRT':
                    # Chercher la date dans les enfants
                    for sub_child in child.get_child_elements():
                        if sub_child.get_tag() == 'DATE':
                            birth_date = _parse_gedcom_date(sub_child.get_value())
                            
                elif tag == 'DEAT':
                    for sub_child in child.get_child_elements():
                        if sub_child.get_tag() == 'DATE':
                            death_date = _parse_gedcom_date(sub_child.get_value())
            
            individuals[ind_id] = {
                "id": ind_id,
                "given_name": given_name,
                "family_name": family_name,
                "sex": sex,
                "birth_date": birth_date,
                "death_date": death_date,
                "father_id": father_id,
                "mother_id": mother_id,
                "families": families_list,
            }
    
    # 2. Parser les familles
    for elem in elements:
        if elem.get_level() == 0 and elem.get_tag() == 'FAM':
            fam_id = elem.get_pointer()
            husband_id = ""
            wife_id = ""
            children_ids = []
            
            for child in elem.get_child_elements():
                tag = child.get_tag()
                value = child.get_value() or ""
                
                if tag == 'HUSB':
                    husband_id = value.strip().lstrip('@').rstrip('@')
                elif tag == 'WIFE':
                    wife_id = value.strip().lstrip('@').rstrip('@')
                elif tag == 'CHIL':
                    child_id = value.strip().lstrip('@').rstrip('@')
                    children_ids.append(child_id)
                    
                    # Mettre à jour les individus avec les parents
                    if child_id in individuals:
                        if not individuals[child_id]["father_id"] and husband_id:
                            individuals[child_id]["father_id"] = husband_id
                        if not individuals[child_id]["mother_id"] and wife_id:
                            individuals[child_id]["mother_id"] = wife_id
            
            families[fam_id] = {
                "id": fam_id,
                "husband": husband_id,
                "wife": wife_id,
                "children": children_ids,
            }
    
    return individuals, families


def init_db(db_path=None):
    """Créer la base SQLite avec les tables nécessaires."""
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS individuals (
            id TEXT PRIMARY KEY,
            given_name TEXT NOT NULL,
            family_name TEXT NOT NULL,
            full_name TEXT NOT NULL,
            search_name TEXT NOT NULL,
            sex TEXT,
            birth_date TEXT,
            death_date TEXT,
            father_id TEXT,
            mother_id TEXT,
            spouse_ids TEXT DEFAULT '',
            families TEXT DEFAULT ''
        );
        
        CREATE TABLE IF NOT EXISTS families (
            id TEXT PRIMARY KEY,
            husband_id TEXT,
            wife_id TEXT,
            children_ids TEXT DEFAULT '',
            marriage_date TEXT,
            marriage_place TEXT
        );
        
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_a TEXT NOT NULL,
            person_b TEXT NOT NULL,
            rel_type TEXT NOT NULL,
            UNIQUE(person_a, person_b, rel_type)
        );
        
        CREATE INDEX IF NOT EXISTS idx_individuals_search ON individuals(search_name);
        CREATE INDEX IF NOT EXISTS idx_relationships_person_a ON relationships(person_a);
        CREATE INDEX IF NOT EXISTS idx_relationships_person_b ON relationships(person_b);
    """)
    return conn


def load_gedcom(filepath, db_path=None):
    """Charger un fichier GEDCOM dans SQLite.
    
    Args:
        filepath: chemin vers le fichier GEDCOM
        db_path: chemin vers la base SQLite
        
    Returns:
        tuple: (conn, count)
    """
    if db_path is None:
        db_path = DB_PATH
    
    individuals, families_dict = parse_gedcom(filepath)
    
    conn = init_db(db_path)
    
    # Coupler les époux via les familles
    spouse_map = {}
    for fam in families_dict.values():
        if fam["husband"] and fam["wife"]:
            h, w = fam["husband"], fam["wife"]
            spouse_map.setdefault(h, []).append(w)
            spouse_map.setdefault(w, []).append(h)
    
    # Insérer les individus
    for ind in individuals.values():
        given = ind["given_name"]
        family = ind["family_name"]
        full = f"{given} {family}".strip()
        search = strip_accents(f"{given} {family}".lower())
        
        spouses = spouse_map.get(ind["id"], [])
        fams = ind.get("families", [])
        
        conn.execute(
            "INSERT OR REPLACE INTO individuals VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (ind["id"], given, family, full, search, ind["sex"],
             ind["birth_date"], ind["death_date"], ind["father_id"],
             ind["mother_id"], ",".join(spouses), ",".join(fams))
        )
    
    # Insérer les familles
    for fam in families_dict.values():
        children = ",".join(fam["children"])
        conn.execute(
            "INSERT OR REPLACE INTO families VALUES (?,?,?,?,?,?)",
            (fam["id"], fam["husband"], fam["wife"], children, "", "")
        )
    
    # Insérer les relations
    rel_set = set()
    for ind in individuals.values():
        pid = ind["id"]
        if ind["father_id"]:
            rel_set.add((pid, ind["father_id"], "father"))
        if ind["mother_id"]:
            rel_set.add((pid, ind["mother_id"], "mother"))
        for spouse_id in spouse_map.get(pid, []):
            rel_set.add((pid, spouse_id, "spouse"))
    
    for a, b, r in rel_set:
        conn.execute(
            "INSERT OR IGNORE INTO relationships (person_a, person_b, rel_type) VALUES (?,?,?)",
            (a, b, r)
        )
    
    conn.commit()
    return conn, len(individuals)


@contextmanager
def get_db(db_path=None):
    """Context manager pour la connexion SQLite."""
    conn = sqlite3.connect(db_path or DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()
