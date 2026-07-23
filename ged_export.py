"""Export GED du sous-chemin de relation."""


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
            "father_id, mother_id FROM individuals WHERE id=?", (pid,)
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
            }

    if not individuals:
        return ""

    # Construire les familles
    families = {}
    fam_counter = 1
    used_families = set()  # Éviter les doublons

    # 1. Couples (époux)
    for pid in ids_in_path:
        sp_ids = conn.execute(
            "SELECT spouse_ids FROM individuals WHERE id=?", (pid,)
        ).fetchone()
        if sp_ids and sp_ids[0]:
            for sp_id in sp_ids[0].split(","):
                sp_id = sp_id.strip()
                if sp_id in ids_in_path:
                    # Créer une famille couple
                    fam_key = tuple(sorted([pid, sp_id]))
                    if fam_key not in used_families:
                        used_families.add(fam_key)
                        fid = f"@F{fam_counter:04d}@"
                        fam_counter += 1
                        families[fid] = {
                            "husband": pid if _get_sex_str(conn, pid) == "M" else sp_id,
                            "wife": sp_id if _get_sex_str(conn, pid) == "M" else pid,
                            "children": [],
                        }

    # 2. Parent-enfant
    for pid in ids_in_path:
        ind = individuals.get(pid)
        if not ind:
            continue
        # Père
        if ind["father_id"] and ind["father_id"] in ids_in_path:
            fam_key = tuple(sorted([ind["father_id"], pid]))
            if fam_key not in used_families:
                used_families.add(fam_key)
                fid = f"@F{fam_counter:04d}@"
                fam_counter += 1
                families[fid] = {
                    "husband": ind["father_id"],
                    "wife": ind["mother_id"] if ind["mother_id"] in ids_in_path else "",
                    "children": [pid],
                }
        # Mère (si pas déjà dans une famille avec le père)
        elif ind["mother_id"] and ind["mother_id"] in ids_in_path:
            fam_key = tuple(sorted([ind["mother_id"], pid]))
            if fam_key not in used_families:
                used_families.add(fam_key)
                fid = f"@F{fam_counter:04d}@"
                fam_counter += 1
                families[fid] = {
                    "husband": "",
                    "wife": ind["mother_id"],
                    "children": [pid],
                }

    # Générer le fichier GED
    lines = []
    lines.append("0 HEAD")
    lines.append("1 SOUR GED Relations Export")
    lines.append("1 CHAR UTF-8")
    lines.append("1 FILE GED Relations Export")
    lines.append("")

    # Individus
    for pid in sorted(individuals.keys()):
        ind = individuals[pid]
        lines.append(f"0 {pid} INDI")
        lines.append(f"1 NAME {ind['given_name']} {ind['family_name']}")
        if ind["sex"]:
            lines.append(f"1 SEX {ind['sex']}")
        if ind["birth_date"]:
            lines.append(f"1 BIRT")
            lines.append(f"2 DATE {_format_gedcom_date(ind['birth_date'])}")
        if ind["death_date"]:
            lines.append(f"1 DEAT")
            lines.append(f"2 DATE {_format_gedcom_date(ind['death_date'])}")
        lines.append("")

    # Familles
    for fid, fam in sorted(families.items()):
        lines.append(f"0 {fid} FAM")
        if fam["husband"]:
            lines.append(f"1 HUSB {fam['husband']}")
        if fam["wife"]:
            lines.append(f"1 WIFE {fam['wife']}")
        for child in fam["children"]:
            lines.append(f"1 CHIL {child}")
        lines.append("")

    lines.append("0 TRLR")
    return "\n".join(lines) + "\n"


def _get_sex_str(conn, pid):
    """Retourner le sexe d'un individu (M/F)."""
    row = conn.execute(
        "SELECT sex FROM individuals WHERE id=?", (pid,)
    ).fetchone()
    return row[0] if row else ""


def _add_to_family(families, counter, parent_id, child_id):
    """Ajouter une famille parent-enfant."""
    fid = f"@F{counter:04d}@"
    if parent_id == child_id:
        return
    # Déterminer HUSB/WIFE basé sur le sexe du parent
    if parent_id not in families:
        families[parent_id] = {
            "husband": parent_id,
            "wife": child_id,
            "children": [],
        }
    else:
        families[parent_id]["children"].append(child_id)


def _format_gedcom_date(date_str):
    """Convertir YYYY-MM-DD en format GEDCOM (ex: ' 1 JAN 2020')."""
    if not date_str:
        return ""
    parts = date_str.split("-")
    if len(parts) >= 3:
        month_map = {
            "01": "JAN", "02": "FEB", "03": "MAR", "04": "APR",
            "05": "MAY", "06": "JUN", "07": "JUL", "08": "AUG",
            "09": "SEP", "10": "OCT", "11": "NOV", "12": "DEC",
        }
        day = parts[2].lstrip("0") or "01"
        month = month_map.get(parts[1], "JAN")
        return f"{day} {month} {parts[0]}"
    return date_str
