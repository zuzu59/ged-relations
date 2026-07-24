"""Parser GEDCOM → SQLite.

Utilise ged4py pour le parsing GEDCOM avec fallback.
Supporte GEDCOM 5.5.1 et 7.0.
Extrait : individus, dates, filiation (père/mère/enfants).
"""
import sqlite3
import os
import unicodedata
from contextlib import contextmanager

try:
    from ged4py import GedcomReader
    HAS_GED4PY = True
except ImportError:
    HAS_GED4PY = False

DB_PATH = os.path.join(os.path.dirname(__file__), "ged_data.db")

# Relations parent-enfant
REL_FATHER = "father"
REL_MOTHER = "mother"
REL_SPOUSE = "spouse"


def strip_accents(text):
    """Retire les accents d'une chaîne."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _parse_date(date_str):
    """Parse une date GEDCOM (ex: ' 1 JAN 1900')."""
    if not date_str:
        return ""
    date_str = date_str.strip()
    if not date_str:
        return ""
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
    return date_str


def _fix_double_encoding(raw_bytes):
    """Corriger un double encodage UTF-8 (ex: 'Ã©' -> 'é')."""
    try:
        # Decoder en UTF-8 (donne les caractères double-encodés)
        text = raw_bytes.decode("utf-8", errors="replace")
        # Encoder en Latin-1 (convertit chaque caractère en byte)
        # puis redecoder en UTF-8
        return text.encode("latin-1", errors="replace").decode("utf-8", errors="replace")
    except Exception:
        return raw_bytes.decode("utf-8", errors="replace")


def _parse_gedcom_simple(filepath):
    """Parser GEDCOM simple qui ignore les lignes corrompues."""
    individuals = {}
    families = {}
    current_id = None
    current_fam = None
    
    with open(filepath, "rb") as f:
        raw = f.read()
    # Supprimer le BOM
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    # Supprimer les BOM multiples
    while raw.startswith(b'\xc3\xaf\xc2\xbb\xc2\xbf'):
        raw = raw[6:]
    # Corriger le double encodage UTF-8
    lines = _fix_double_encoding(raw).splitlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line or not line[0].isdigit():
            i += 1
            continue
        
        try:
            level = int(line[0])
            rest = line[2:] if len(line) > 2 else ""
        except (ValueError, IndexError):
            i += 1
            continue
        
        # Pour niveau 0, le format est "0 @ID@ TYPE"
        if level == 0 and "@" in rest:
            at_parts = rest.split("@")
            if len(at_parts) >= 3:
                id_value = at_parts[1]
                tag_part = at_parts[2].strip()
                tag = tag_part.split(" ")[0].upper() if tag_part else ""
                value = " ".join(tag_part.split(" ")[1:]) if len(tag_part.split(" ")) > 1 else ""
            else:
                i += 1
                continue
        else:
            parts = rest.split(" ", 1)
            tag = parts[0].upper() if parts else ""
            value = parts[1] if len(parts) > 1 else ""
        
        # Niveau 0 : @ID@ INDI
        if level == 0 and tag == "INDI" and id_value:
            current_id = id_value  # Déjà sans les @
            if current_id:
                individuals[current_id] = {
                    "id": current_id,
                    "given_name": "",
                    "family_name": "",
                    "sex": "",
                    "birth_date": "",
                    "death_date": "",
                    "father_id": "",
                    "mother_id": "",
                    "families": [],
                    "family_id": "",
                }
            i += 1
            continue
        
        # Niveau 0 : @ID@ FAM
        if level == 0 and tag == "FAM" and "@" in rest:
            current_fam = rest.split("@")[1] if "@" in rest else None
            if current_fam:
                families[current_fam] = {
                    "id": current_fam,
                    "husband": "",
                    "wife": "",
                    "children": [],
                }
            i += 1
            continue
        
        # Niveau 1 dans INDI
        if current_id and level == 1 and individuals.get(current_id):
            ind = individuals[current_id]
            if tag == "NAME" and "/" in value:
                name_parts = value.split("/")
                ind["given_name"] = name_parts[0].strip()
                ind["family_name"] = name_parts[1].strip() if len(name_parts) > 1 else ""
            elif tag == "GIVN":
                ind["given_name"] = value.strip()
            elif tag == "SURN":
                ind["family_name"] = value.strip()
            elif tag == "SEX":
                ind["sex"] = value.strip()
            elif tag == "FAMS":
                ind["families"].append(value.strip())
            elif tag == "FAMC":
                ind["family_id"] = value.strip()
            elif tag in ("BIRT", "DEAT"):
                # Chercher la date dans les lignes suivantes
                j = i + 1
                while j < len(lines):
                    sub_line = lines[j].rstrip()
                    if not sub_line or not sub_line[0].isdigit():
                        break
                    try:
                        sub_level = int(sub_line[0])
                        sub_rest = sub_line[2:] if len(sub_line) > 2 else ""
                        sub_parts = sub_rest.split(" ", 1)
                        sub_tag = sub_parts[0].upper() if sub_parts else ""
                        sub_val = sub_parts[1] if len(sub_parts) > 1 else ""
                        if sub_level == 2 and sub_tag == "DATE":
                            if tag == "BIRT":
                                ind["birth_date"] = _parse_date(sub_val)
                            else:
                                ind["death_date"] = _parse_date(sub_val)
                            break
                    except (ValueError, IndexError):
                        pass
                    j += 1
                i = j
                continue
        
        # Niveau 1 dans FAM
        if current_fam and level == 1 and families.get(current_fam):
            fam = families[current_fam]
            if tag == "HUSB":
                fam["husband"] = value.strip().lstrip("@").rstrip("@")
            elif tag == "WIFE":
                fam["wife"] = value.strip().lstrip("@").rstrip("@")
            elif tag == "CHIL":
                chil_id = value.strip().lstrip("@").rstrip("@")
                fam["children"].append(chil_id)
        
        i += 1
    
    # Mettre à jour les individus avec FAMS et résoudre père/mère via FAMC
    for fam in families.values():
        for child_id in fam["children"]:
            if child_id in individuals:
                if fam["id"] not in individuals[child_id]["families"]:
                    individuals[child_id]["families"].append(fam["id"])
                # Résoudre père/mère
                if fam["husband"] and not individuals[child_id]["father_id"]:
                    individuals[child_id]["father_id"] = fam["husband"]
                if fam["wife"] and not individuals[child_id]["mother_id"]:
                    individuals[child_id]["mother_id"] = fam["wife"]
    
    return individuals, families


def parse_gedcom(filepath):
    """Parse un fichier GEDCOM et retourne les données brutes.
    
    Utilise ged4py si disponible, sinon fallback sur un parser simple.

    Returns:
        tuple: (individuals dict, families dict)
    """
    if HAS_GED4PY:
        try:
            individuals = {}
            families = {}
            
            with GedcomReader(filepath) as parser:
                # Parser les individus
                for indi in parser.records0("INDI"):
                    ind_id = str(indi.id)
                    
                    # Nom
                    given_name = ""
                    family_name = ""
                    name = indi.name
                    if name:
                        name_str = str(name)
                        if "/" in name_str:
                            parts = name_str.split("/")
                            given_name = parts[0].strip()
                            family_name = parts[1].strip() if len(parts) > 1 else ""
                        else:
                            given_name = name_str.strip()
                    
                    # Sexe
                    sex = ""
                    if indi.sex:
                        sex = str(indi.sex)
                    
                    # Dates
                    birth_date = ""
                    death_date = ""
                    
                    birt = indi.sub_tag("BIRT")
                    if birt:
                        date_val = birt.sub_tag_value("DATE")
                        if date_val:
                            birth_date = _parse_date(str(date_val))
                    
                    deat = indi.sub_tag("DEAT")
                    if deat:
                        date_val = deat.sub_tag_value("DATE")
                        if date_val:
                            death_date = _parse_date(str(date_val))
                    
                    # Famille d'origine (FAMC)
                    famc = indi.sub_tag("FAMC")
                    father_id = ""
                    mother_id = ""
                    family_id = ""
                    if famc:
                        family_id = str(famc.id)
                        fam_obj = famc
                        if fam_obj:
                            husband = fam_obj.sub_tag_value("HUSB")
                            wife = fam_obj.sub_tag_value("WIFE")
                            if husband:
                                father_id = str(husband)
                            if wife:
                                mother_id = str(wife)
                    
                    individuals[ind_id] = {
                        "id": ind_id,
                        "given_name": given_name,
                        "family_name": family_name,
                        "sex": sex,
                        "birth_date": birth_date,
                        "death_date": death_date,
                        "father_id": father_id,
                        "mother_id": mother_id,
                        "families": [],
                        "family_id": family_id,
                    }
                
                # Parser les familles
                for fam in parser.records0("FAM"):
                    fam_id = str(fam.id)
                    
                    husband = ""
                    wife = ""
                    children = []
                    
                    h = fam.sub_tag_value("HUSB")
                    w = fam.sub_tag_value("WIFE")
                    if h:
                        husband = str(h)
                    if w:
                        wife = str(w)
                    
                    for chil in fam.sub_tags("CHIL"):
                        children.append(str(chil.id))
                    
                    families[fam_id] = {
                        "id": fam_id,
                        "husband": husband,
                        "wife": wife,
                        "children": children,
                    }
                    
                    for child_id in children:
                        if child_id in individuals:
                            individuals[child_id]["families"].append(fam_id)
            
            return individuals, families
        
        except Exception as e:
            print(f"[WARN] ged4py failed: {e}, using simple parser")
    
    # Fallback
    return _parse_gedcom_simple(filepath)


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
    """Charger un fichier GEDCOM dans SQLite."""
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
