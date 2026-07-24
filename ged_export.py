"""Export GED du sous-chemin de relation using python-gedcom."""


def generate_ged(conn, person_a_id, person_b_id, path):
    """Générer un fichier GED contenant uniquement le sous-chemin de relation.

    Args:
        conn: connexion SQLite
        person_a_id: ID individu A
        person_b_id: ID individu B
        path: liste de (person_id, rel_label) depuis BFS

    Returns:
        str: contenu GEDCOM
    """
    from gedcom.parser import Parser

    # Collecter tous les IDs uniques du chemin
    ids_in_path = set([person_a_id, person_b_id])
    if path:
        for pid, _ in path:
            ids_in_path.add(pid)

    # Récupérer les individus du chemin
    individuals = {}
    for pid in ids_in_path:
        row = conn.execute(
            "SELECT id, given_name, family_name, sex, birth_date, death_date, "
            "father_id, mother_id, spouse_ids FROM individuals WHERE id=?", (pid,)
        ).fetchone()
        if row:
            individuals[row[0]] = {
                "id": row[0],
                "given_name": row[1],
                "family_name": row[2],
                "sex": row[3],
                "birth_date": row[4],
                "death_date": row[5],
                "father_id": row[6] or "",
                "mother_id": row[7] or "",
                "spouse_ids": [s.strip() for s in (row[8] or "").split(",") if s.strip()],
            }

    if not individuals:
        return ""

    # Construire les familles
    families = {}
    fam_counter = 1
    fam_by_parents = {}  # Map (pere, mere) -> fam_id

    # 1. Couples (époux)
    for pid in ids_in_path:
        ind = individuals[pid]
        for sp_id in ind["spouse_ids"]:
            if sp_id in ids_in_path:
                # Créer une famille couple
                parents = tuple(sorted([pid, sp_id]))
                if parents not in fam_by_parents:
                    fam_by_parents[parents] = f"@F{fam_counter:04d}@"
                    fam_counter += 1

    # 2. Parent-enfant
    for pid in ids_in_path:
        ind = individuals[pid]
        if ind["father_id"] and ind["father_id"] in ids_in_path:
            father = ind["father_id"]
            mother = ind["mother_id"] if ind["mother_id"] in ids_in_path else ""
            # Famille avec père et mère
            if mother:
                parents = tuple(sorted([father, mother]))
                if parents not in fam_by_parents:
                    fam_by_parents[parents] = f"@F{fam_counter:04d}@"
                    fam_counter += 1
                fam_id = fam_by_parents[parents]
            else:
                # Père seul
                fam_id = f"@F{fam_counter:04d}@"
                fam_counter += 1
                fam_by_parents[(father,)] = fam_id

            # Ajouter l'enfant à cette famille
            if fam_id not in families:
                families[fam_id] = {
                    "husband": father,
                    "wife": mother,
                    "children": []
                }
            if pid not in families[fam_id]["children"]:
                families[fam_id]["children"].append(pid)

    # Remplir families et family_id pour chaque individu
    for pid in ids_in_path:
        ind = individuals[pid]
        ind["families"] = []  # FAMS
        ind["family_id"] = ""  # FAMC

        # FAMC: famille où cet individu est enfant
        for fam_id, fam in families.items():
            if pid in fam["children"]:
                ind["family_id"] = fam_id
                break

        # FAMS: familles où cet individu est parent
        for fam_id, fam in families.items():
            if fam["husband"] == pid or fam["wife"] == pid:
                if fam_id not in ind["families"]:
                    ind["families"].append(fam_id)

    # Générer le fichier GED avec python-gedcom
    from io import StringIO
    output = StringIO()
    
    # Écrire le header GEDCOM standard
    output.write("0 HEAD\n")
    output.write("1 SOUR GED Relations\n")
    output.write("1 CHAR UTF-8\n")
    output.write("1 GEDC\n")
    output.write("2 VERS 5.5.1\n")
    output.write("2 FORM LINEAGE-LINKED\n")
    output.write("1 SUBM @SUBM@\n")
    output.write("1 FILE GED Relations Export\n")

    # Écrire les individus
    for pid in sorted(individuals.keys()):
        ind = individuals[pid]
        output.write(f"0 @{pid}@ INDI\n")
        name = f"{ind['given_name']} /{ind['family_name']}/"
        output.write(f"1 NAME {name}\n")
        if ind["sex"]:
            output.write(f"1 SEX {ind['sex']}\n")
        # FAMC
        if ind["family_id"]:
            output.write(f"1 FAMC {ind['family_id']}\n")
        # FAMS
        for fam_id in ind["families"]:
            output.write(f"1 FAMS {fam_id}\n")
        if ind["birth_date"]:
            output.write(f"1 BIRT\n")
            output.write(f"2 DATE {_format_gedcom_date(ind['birth_date'])}\n")
        if ind["death_date"]:
            output.write(f"1 DEAT\n")
            output.write(f"2 DATE {_format_gedcom_date(ind['death_date'])}\n")

    # Écrire les familles
    for fid, fam in sorted(families.items()):
        output.write(f"0 {fid} FAM\n")
        if fam["husband"]:
            output.write(f"1 HUSB @{fam['husband']}@\n")
        if fam["wife"]:
            output.write(f"1 WIFE @{fam['wife']}@\n")
        for child in fam["children"]:
            output.write(f"1 CHIL @{child}@\n")

    output.write("0 TRLR\n")
    return output.getvalue()


def _format_gedcom_date(date_str):
    """Formater une date ISO en format GEDCOM (ex: 1 JAN 1900)."""
    if not date_str or date_str == "":
        return ""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(date_str)
        mois = {
            1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN",
            7: "JUL", 8: "AUG", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"
        }
        return f"{dt.day:02d} {mois[dt.month]} {dt.year}"
    except:
        return date_str
