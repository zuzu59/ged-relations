"""Graphe de parenté + BFS pour calculer la relation la plus courte.

Le graphe est non-orienté (relation père↔enfant, mère↔enfant, époux↔époux).
BFS standard pour trouver le chemin le plus court.
"""
from collections import deque


REL_LABELS = {
    "father": "père",
    "mother": "mère",
    "child": "fils",
    "spouse": "époux",
}


def build_adjacency(conn):
    """Construire le graphe d'adjacence à partir de SQLite.

    Returns:
        dict: person_id → list of (neighbor_id, rel_type)
    """
    adj = {}
    rows = conn.execute(
        "SELECT person_a, person_b, rel_type FROM relationships"
    ).fetchall()

    for a, b, rel in rows:
        if rel == "father":
            # a → b = « père » (a a pour père b)
            # b → a : vérifier le sexe de a (l'enfant)
            sex_a = _get_sex(conn, a)
            adj.setdefault(a, []).append((b, "père"))
            adj.setdefault(b, []).append((a, "fils" if sex_a == "M" else "fille"))
        elif rel == "mother":
            # a → b = « mère » (a a pour mère b)
            sex_a = _get_sex(conn, a)
            adj.setdefault(a, []).append((b, "mère"))
            adj.setdefault(b, []).append((a, "fils" if sex_a == "M" else "fille"))
        elif rel == "spouse":
            # Relations époux bidirectionnelles
            adj.setdefault(a, []).append((b, "époux"))
            adj.setdefault(b, []).append((a, "épouse"))

    return adj


def _get_sex(conn, person_id):
    """Récupérer le sexe d'un individu."""
    row = conn.execute(
        "SELECT sex FROM individuals WHERE id=?", (person_id,)
    ).fetchone()
    return row[0] if row else ""


def get_individual(conn, person_id):
    """Récupérer les infos d'un individu."""
    row = conn.execute(
        "SELECT id, given_name, family_name, sex, birth_date, death_date "
        "FROM individuals WHERE id=?", (person_id,)
    ).fetchone()
    if row:
        return {
            "id": row[0],
            "given_name": row[1],
            "family_name": row[2],
            "sex": row[3],
            "birth_date": row[4],
            "death_date": row[5],
        }
    return None


def find_shortest_path(adj, start, end):
    """BFS pour trouver le chemin le plus court entre start et end.

    Returns:
        (path, degrees) where path is list of (person_id, rel_label) steps,
        or None if no path exists.
    """
    if start == end:
        return [], 0

    queue = deque([(start, [])])
    visited = {start}

    while queue:
        current, path = queue.popleft()
        for neighbor, rel_label in adj.get(current, []):
            if neighbor in visited:
                continue
            new_path = path + [(neighbor, rel_label)]
            if neighbor == end:
                return new_path, len(new_path)
            visited.add(neighbor)
            queue.append((neighbor, new_path))

    return None, -1


def get_parents(conn, person_id):
    """Récupérer les parents d'un individu."""
    row = conn.execute(
        "SELECT father_id, mother_id FROM individuals WHERE id=?", (person_id,)
    ).fetchone()
    if not row:
        return None, None
    
    father_id, mother_id = row
    father_name = ""
    mother_name = ""
    
    if father_id:
        f = get_individual(conn, father_id)
        if f:
            father_name = f"{f['given_name']} {f['family_name']}".strip()
    if mother_id:
        m = get_individual(conn, mother_id)
        if m:
            mother_name = f"{m['given_name']} {m['family_name']}".strip()
    
    return father_name, mother_name


def get_spouse(conn, person_id):
    """Récupérer le/la conjoint(e) d'un individu via les relations."""
    row = conn.execute(
        "SELECT person_b FROM relationships WHERE person_a=? AND rel_type='spouse'", (person_id,)
    ).fetchone()
    if not row:
        return None
    
    spouse_id = row[0]
    s = get_individual(conn, spouse_id)
    if s:
        return f"{s['given_name']} {s['family_name']}".strip()
    return None


def format_relation(conn, adj, person_a_id, person_b_id):
    """Formater la relation entre deux individus au format spécifié.

    Format linéaire : chaque saut sur une ligne avec indentation croissante.
    Affiche les dates de naissance/décès et les deux parents sur la même ligne.

    Returns:
        tuple: (degrees, formatted_text, error_message)
        - error_message != None si cas spécial (même personne, disjoints)
    """
    if person_a_id == person_b_id:
        return 0, "Il s'agit de la même personne.", None

    path, degrees = find_shortest_path(adj, person_a_id, person_b_id)
    if path is None:
        return -1, "Aucun lien de parenté trouvé entre ces deux individus.", None

    # Construire le texte formaté
    lines = [f"Lien de parenté : {degrees} degré(s)"]
    lines.append("")

    # Format arbre : monter = +1 tab, descendre = -1 tab
    # Relations "père"/"mère" = monter, "fils"/"fille" = descendre
    # Calculer d'abord toutes les indentations relatives
    indentations = [0]  # Individu 1 à 0
    current = 0
    for person_id, rel_label in path:
        if rel_label in ("père", "mère"):
            current += 1
        elif rel_label in ("fils", "fille"):
            current -= 1
        indentations.append(current)
    
    # Trouver le minimum et ajuster pour que tout soit >= 0
    min_indent = min(indentations)
    offset = -min_indent if min_indent < 0 else 0
    
    # Afficher avec l'offset
    # Les deux extrémités (person_a et person_b) n'ont pas de parents affichés
    all_person_ids = [person_a_id] + [p[0] for p in path]
    
    for i, person_id in enumerate(all_person_ids):
        ind = get_individual(conn, person_id)
        if not ind:
            lines.append("\t" * (indentations[i] + offset) + person_id)
            continue
        
        name = f"{ind['given_name']} {ind['family_name']}".strip()
        
        # Dates
        birth = _format_date(ind['birth_date']) if ind['birth_date'] else ""
        death = _format_date(ind['death_date']) if ind['death_date'] else ""
        dates = f" ({birth})" + (f" — ({death})" if death else "")
        
        # Époux(se) uniquement pour les personnes intermédiaires (pas les extrémités)
        # Personne à l'indice 0 = person_a, dernière personne = person_b
        is_intermediate = i > 0 and i < len(all_person_ids) - 1
        extra_info = ""
        if is_intermediate:
            spouse = get_spouse(conn, person_id)
            
            if spouse:
                sex = ind['sex']
                if sex == 'M':
                    extra_info = f" | épouse: {spouse}"
                elif sex == 'F':
                    extra_info = f" | époux: {spouse}"
        
        line = f"{name}{dates}{extra_info}"
        indent = indentations[i] + offset
        lines.append("\t" * indent + line)

    text = "\n".join(lines)
    return degrees, text, None


def search_individuals(conn, query):
    """Recherche full-text avec sous-chaînes sur nom + prénom.

    Args:
        conn: connexion SQLite
        query: chaîne de recherche (multi-mots)

    Returns:
        list of dicts with id, full_name, birth_date, death_date,
        father_name, mother_name, id
    """
    if not query or not query.strip():
        return []

    # Nettoyage : enlever les accents et mettre en majuscules
    from gedcom_parser import strip_accents
    clean_query = strip_accents(query).lower().strip()
    words = [w for w in clean_query.split() if w]

    if not words:
        return []

    # Construire la requête LIKE avec AND pour chaque mot
    conditions = []
    params = []
    for word in words:
        conditions.append("search_name LIKE ?")
        params.append(f"%{word}%")

    sql = f"""
        SELECT id, given_name, family_name, birth_date, death_date,
               father_id, mother_id
        FROM individuals
        WHERE {' AND '.join(conditions)}
        ORDER BY family_name, given_name
        LIMIT 50
    """

    rows = conn.execute(sql, params).fetchall()
    results = []

    # Charger les noms des parents
    father_cache = {}
    mother_cache = {}

    for row in rows:
        fid, givn, surn, birth, death, f_id, m_id = row
        full_name = f"{givn} {surn}".strip()

        # Père
        if f_id and f_id not in father_cache:
            f_row = conn.execute(
                "SELECT given_name, family_name FROM individuals WHERE id=?", (f_id,)
            ).fetchone()
            father_cache[f_id] = f"{f_row[0]} {f_row[1]}".strip() if f_row else ""
        father_name = father_cache.get(f_id, "")

        # Mère
        if m_id and m_id not in mother_cache:
            m_row = conn.execute(
                "SELECT given_name, family_name FROM individuals WHERE id=?", (m_id,)
            ).fetchone()
            mother_cache[m_id] = f"{m_row[0]} {m_row[1]}".strip() if m_row else ""
        mother_name = mother_cache.get(m_id, "")

        # Format dates
        birth_str = _format_date(birth)
        death_str = _format_date(death) if death else ""

        results.append({
            "id": fid,
            "full_name": full_name,
            "birth_date": birth_str,
            "death_date": death_str,
            "father_name": father_name,
            "mother_name": mother_name,
        })

    return results


def _format_date(date_str):
    """Formater une date YYYY-MM-DD → dd/mm/yy."""
    if not date_str:
        return ""
    parts = date_str.split("-")
    if len(parts) >= 3 and parts[0] != "?":
        # dd/mm/yy
        day = parts[2][-2:]
        month = parts[1]
        year = parts[0][-2:]
        return f"{day}/{month}/{year}"
    if len(parts) >= 2 and parts[0] != "?":
        return f"{parts[0]}-{parts[1]}"
    return date_str
