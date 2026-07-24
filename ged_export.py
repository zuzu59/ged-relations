"""Export GED du sous-chemin de relation using python-gedcom."""


def generate_ged(conn, person_a_id, person_b_id, path):
    """Générer un fichier GED contenant uniquement le sous-chemin de relation.

    Règles :
    - Conserve les individus du chemin BFS
    - Conserve les parents manquants qui relient 2+ personnes du chemin
      (ex: I24 relie I25 et I27 → on l'inclus)
    - Ne conserve PAS les parents qui ne relient qu'une seule personne
    - Ne conserve PAS les spouses hors chemin

    Args:
        conn: connexion SQLite
        person_a_id: ID individu A
        person_b_id: ID individu B
        path: liste de (person_id, rel_label) depuis BFS

    Returns:
        str: contenu GEDCOM
    """
    # 1. Collecter les IDs du chemin BFS
    ids_in_path = set([person_a_id, person_b_id])
    for step in path:
        pid = step[0] if isinstance(step, (list, tuple)) else step
        ids_in_path.add(pid)

    # 2. Trouver les parents connecteurs (relient 2+ personnes du chemin)
    parent_children = {}
    for pid in ids_in_path:
        pr = conn.execute(
            "SELECT father_id, mother_id FROM individuals WHERE id=?", (pid,)
        ).fetchone()
        if pr:
            for p_id in (pr[0] or "", pr[1] or ""):
                if p_id and p_id not in ids_in_path:
                    parent_children.setdefault(p_id, set()).add(pid)

    for p_id, children in parent_children.items():
        if len(children) >= 2:
            ids_in_path.add(p_id)

    # 3. Récupérer les individus
    individuals = {}
    for pid in ids_in_path:
        row = conn.execute(
            "SELECT id, given_name, family_name, sex, birth_date, death_date "
            "FROM individuals WHERE id=?", (pid,)
        ).fetchone()
        if row:
            individuals[row[0]] = {
                "id": row[0],
                "given_name": row[1],
                "family_name": row[2],
                "sex": row[3],
                "birth_date": row[4],
                "death_date": row[5],
            }

    if not individuals:
        return ""

    # 4. Construire les familles
    #    Règle: créer une famille par paire de parents (ou seul parent) ayant
    #    au moins un enfant dans le set. Les parents doivent être dans le set.
    families = {}
    fam_id_map = {}  # (husband, wife) -> fam_id
    next_fam_id = 1

    def ensure_family(husband, wife):
        """Retourne l'ID de la famille pour (husband, wife), la crée si nécessaire."""
        key = (husband, wife)
        if key in fam_id_map:
            return fam_id_map[key]
        fid = f"@F{next_fam_id_local[0]:04d}@"
        next_fam_id_local[0] += 1
        fam_id_map[key] = fid
        families[fid] = {"husband": husband, "wife": wife, "children": []}
        return fid

    next_fam_id_local = [next_fam_id]

    def in_set(x):
        return bool(x) and x in ids_in_path

    # 4a. Couples : les DEUX époux dans le set
    for pid in sorted(ids_in_path):
        sp = conn.execute(
            "SELECT spouse_ids FROM individuals WHERE id=?", (pid,)
        ).fetchone()
        if sp and sp[0]:
            for sp_id in sp[0].split(","):
                sp_id = sp_id.strip()
                if sp_id and sp_id in ids_in_path:
                    h, w = sorted([pid, sp_id])
                    ensure_family(h, w)

    # 4b. Parent-enfant : créer famille pour chaque enfant avec ses parents
    for pid in sorted(ids_in_path):
        pr = conn.execute(
            "SELECT father_id, mother_id FROM individuals WHERE id=?", (pid,)
        ).fetchone()
        if not pr:
            continue
        father = pr[0] or ""
        mother = pr[1] or ""

        if in_set(father) and in_set(mother):
            fid = ensure_family(father, mother)
        elif in_set(father):
            fid = ensure_family(father, "")
        elif in_set(mother):
            fid = ensure_family("", mother)
        else:
            continue

        if pid not in families[fid]["children"]:
            families[fid]["children"].append(pid)

    # 5. Assigner FAMC et FAMS à chaque individu
    for pid in ids_in_path:
        ind = individuals[pid]
        ind["families"] = []
        ind["family_id"] = ""

        for fid, fam in families.items():
            if pid in fam["children"]:
                ind["family_id"] = fid
            if fam["husband"] == pid or fam["wife"] == pid:
                if fid not in ind["families"]:
                    ind["families"].append(fid)

    # 6. Générer le GEDCOM
    from io import StringIO
    output = StringIO()

    output.write("0 HEAD\n")
    output.write("1 SOUR GED Relations\n")
    output.write("1 CHAR UTF-8\n")
    output.write("1 GEDC\n")
    output.write("2 VERS 5.5.1\n")
    output.write("2 FORM LINEAGE-LINKED\n")
    output.write("1 FILE GED Relations Export\n")

    for pid in sorted(individuals.keys()):
        ind = individuals[pid]
        output.write(f"0 @{pid}@ INDI\n")
        output.write(f"1 NAME {ind['given_name']} /{ind['family_name']}/\n")
        if ind["sex"]:
            output.write(f"1 SEX {ind['sex']}\n")
        if ind["family_id"]:
            output.write(f"1 FAMC {ind['family_id']}\n")
        for fid in ind["families"]:
            output.write(f"1 FAMS {fid}\n")
        if ind["birth_date"]:
            output.write(f"1 BIRT\n")
            output.write(f"2 DATE {_format_gedcom_date(ind['birth_date'])}\n")
        if ind["death_date"]:
            output.write(f"1 DEAT\n")
            output.write(f"2 DATE {_format_gedcom_date(ind['death_date'])}\n")

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
