"""Parser GEDCOM → SQLite.

Supporte GEDCOM 5.5.1 et 7.0.
Extrait : individus, dates, filiation (père/mère/enfants).
"""
import sqlite3
import os
import re
import unicodedata
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
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _parse_date(date_str):
    """Parse une date GEDCOM (ex: ' 1 JAN 1900' ou ' 1 JAN 1900 BIRT)."""
    if not date_str:
        return ""
    date_str = date_str.strip()
    # GEDCOM date format: D MMM YYYY ou D MMM
    months = {
        "jan": "01", "janv": "01", "janvier": "01",
        "feb": "02", "fév": "02", "fev": "02", "fevr": "02", "fevrier": "02",
        "mar": "03", "mars": "03",
        "apr": "04", "avr": "04", "avr ": "04", "avril": "04",
        "may": "05", "mai": "05",
        "jun": "06", "juin": "06",
        "jul": "07", "juil": "07",
        "aug": "08", "août": "08", "aout": "08",
        "sep": "09", "sept": "09",
        "oct": "10", "octo": "10",
        "nov": "11", "novembre": "11",
        "dec": "12", "déc": "12", "decembre": "12",
    }
    parts = date_str.split()
    if len(parts) < 2:
        return date_str
    day = parts[0].zfill(2)
    month_name = parts[1].lower().strip(".")
    month = months.get(month_name, "00")
    year = parts[2] if len(parts) >= 3 else ""
    if month == "00":
        return date_str
    return f"{year}-{month}-{day}" if year else f"?-{month}-{day}"


def parse_gedcom(filepath):
    """Parse un fichier GEDCOM et retourne les données brutes.

    Returns:
        list of dicts with keys:
            id, given_name, family_name, sex, birth_date, death_date,
            father_id, mother_id, spouse_ids
    """
    individuals = {}
    families = {}
    current_id = None
    current_fam = None
    husband = None
    wife = None
    children = []

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")
        parts = line.split(" ", 2)

        if len(parts) < 2:
            i += 1
            continue

        level = int(parts[0])
        # Pour niveau 0, le format est "0 @ID@ TYPE" → tag = parts[2]
        # Pour niveau 1+, le format est "1 TAG valeur" → tag = parts[1]
        if level == 0 and len(parts) >= 3 and parts[1].startswith("@"):
            tag = parts[2].upper()
            id_value = parts[1].strip()
        else:
            tag = parts[1].upper()
            id_value = None
        value = parts[2] if len(parts) > 2 else ""

        # Niveau 0 : @ID@ INDI
        if level == 0 and tag == "INDI" and id_value:
            current_id = id_value
            individuals[current_id] = {
                "id": current_id,
                "given_name": "",
                "family_name": "",
                "sex": "",
                "birth_date": "",
                "death_date": "",
                "father_id": "",
                "mother_id": "",
            }
            i += 1
            continue

        # Niveau 0 : @ID@ FAMS
        if level == 0 and tag == "FAMS" and id_value:
            fam_id = id_value
            if current_id and current_id in individuals:
                individuals[current_id].setdefault("families", []).append(fam_id)
            i += 1
            continue

        # Niveau 0 : @ID@ FAM
        if level == 0 and tag == "FAM" and id_value:
            current_fam = id_value
            families[current_fam] = {
                "id": current_fam,
                "husband": "",
                "wife": "",
                "children": [],
            }
            husband = None
            wife = None
            children = []
            i += 1
            continue

        # Niveau 1 dans INDI
        if current_id and level == 1:
            ind = individuals.get(current_id, {})
            if tag == "NAME":
                # Format GEDCOM : "Prénom /NOM/"
                name_str = value.strip()
                # Extraire le nom de famille entre / /
                if "/" in name_str:
                    parts = name_str.split("/")
                    ind["given_name"] = parts[0].strip()
                    ind["family_name"] = parts[1].strip() if len(parts) > 1 else ""
                else:
                    # Pas de séparateur, tout est prénom
                    ind["given_name"] = name_str
                    ind["family_name"] = ""
            elif tag == "GIVN":
                # Prénom (peut être composé: "Prénom NOM")
                ind["given_name"] = value.strip()
            elif tag == "SURN":
                # Nom de famille
                if ind.get("family_name"):
                    ind["family_name"] += " " + value.strip()
                else:
                    ind["family_name"] = value.strip()
            elif tag == "SEX":
                ind["sex"] = value.strip()
            elif tag == "FAMS":
                ind.setdefault("families", []).append(value.strip())
            elif tag == "FAMC":
                ind["family_id"] = value.strip()
            elif tag == "BIRT" or tag == "DEAT":
                # Date de naissance/mort
                # Chercher la date dans les lignes suivantes (niveau 2)
                date_val = ""
                j = i + 1
                while j < len(lines):
                    sub_parts = lines[j].split(" ", 2)
                    if len(sub_parts) >= 2:
                        sub_level = int(sub_parts[0])
                        sub_tag = sub_parts[1].upper()
                        sub_val = sub_parts[2] if len(sub_parts) > 2 else ""
                        if sub_level == 2 and sub_tag == "DATE":
                            date_val = sub_val.strip()
                            break
                    if sub_level == 1:
                        break
                    j += 1
                if tag == "BIRT":
                    ind["birth_date"] = _parse_date(date_val)
                elif tag == "DEAT":
                    ind["death_date"] = _parse_date(date_val)
                i = j if j > i + 1 else i + 1
                continue

        # Niveau 1 dans FAM
        if current_fam and level == 1:
            fam = families.get(current_fam, {})
            if tag == "HUSB":
                husb_id = value.strip()
                fam["husband"] = husb_id
                husband = husb_id
            elif tag == "WIFE":
                wif_id = value.strip()
                fam["wife"] = wif_id
                wife = wif_id
            elif tag == "CHIL":
                chil_id = value.strip()
                fam["children"].append(chil_id)
                children.append(chil_id)

        i += 1

    # Associer père/mère aux enfants via les familles
    for fam in families.values():
        for child_id in fam["children"]:
            if child_id in individuals:
                if fam["husband"]:
                    individuals[child_id]["father_id"] = fam["husband"]
                if fam["wife"]:
                    individuals[child_id]["mother_id"] = fam["wife"]

    return list(individuals.values()), list(families.values())


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
            spouse_ids TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_a TEXT NOT NULL,
            person_b TEXT NOT NULL,
            rel_type TEXT NOT NULL,
            UNIQUE(person_a, person_b, rel_type)
        );

        CREATE INDEX IF NOT EXISTS idx_search_name ON individuals(search_name);
        CREATE INDEX IF NOT EXISTS idx_full_name ON individuals(full_name);
        CREATE INDEX IF NOT EXISTS idx_father ON individuals(father_id);
        CREATE INDEX IF NOT EXISTS idx_mother ON individuals(mother_id);
        CREATE INDEX IF NOT EXISTS idx_rel_a ON relationships(person_a);
        CREATE INDEX IF NOT EXISTS idx_rel_b ON relationships(person_b);
    """)
    conn.commit()
    return conn


def load_gedcom(filepath, db_path=None):
    """Parser un fichier GEDCOM et le charger dans SQLite.

    Returns:
        (conn, count) — connexion SQLite et nombre d'individus chargés.
    """
    if db_path is None:
        db_path = DB_PATH
    individuals, families = parse_gedcom(filepath)

    conn = init_db(db_path)

    # Coupler les époux via les familles
    spouse_map = {}
    for fam in families:
        if fam["husband"] and fam["wife"]:
            h, w = fam["husband"], fam["wife"]
            spouse_map.setdefault(h, []).append(w)
            spouse_map.setdefault(w, []).append(h)

    conn.execute("DELETE FROM individuals")
    conn.execute("DELETE FROM relationships")

    for ind in individuals:
        surn = strip_accents(ind.get("family_name", "")).upper()
        givn = strip_accents(ind.get("given_name", "")).upper()
        full = f"{ind.get('given_name', '')} {ind.get('family_name', '')}".strip()
        search = f"{givn} {surn}".strip()

        # Époux
        sp_ids = spouse_map.get(ind["id"], [])
        sp_str = ",".join(sp_ids) if sp_ids else ""

        conn.execute(
            """INSERT OR REPLACE INTO individuals
               (id, given_name, family_name, full_name, search_name, sex,
                birth_date, death_date, father_id, mother_id, spouse_ids)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                ind["id"],
                ind.get("given_name", ""),
                ind.get("family_name", ""),
                full,
                search,
                ind.get("sex", ""),
                ind.get("birth_date", ""),
                ind.get("death_date", ""),
                ind.get("father_id", ""),
                ind.get("mother_id", ""),
                sp_str,
            ),
        )

    # Charger les relations père/mère (uniquement enfant→parent)
    for ind in individuals:
        pid = ind["id"]
        if ind.get("father_id"):
            conn.execute(
                "INSERT OR IGNORE INTO relationships (person_a, person_b, rel_type) VALUES (?, ?, ?)",
                (pid, ind["father_id"], "father"),
            )
        if ind.get("mother_id"):
            conn.execute(
                "INSERT OR IGNORE INTO relationships (person_a, person_b, rel_type) VALUES (?, ?, ?)",
                (pid, ind["mother_id"], "mother"),
            )
        # Époux : stocker une seule fois (plus petit ID en premier)
        for sp in spouse_map.get(pid, []):
            if sp > pid:
                conn.execute(
                    "INSERT OR IGNORE INTO relationships (person_a, person_b, rel_type) VALUES (?, ?, ?)",
                    (pid, sp, "spouse"),
                )

    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM individuals").fetchone()[0]
    return conn, count
