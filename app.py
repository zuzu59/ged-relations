"""GED Relations — Application Flask.

Serveur web pour calculer et afficher la relation la plus courte
entre deux individus d'un arbre généalogique GEDCOM.
"""
import os
import io
import argparse
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, Response
from version import get_version_and_date
from gedcom_parser import load_gedcom, DB_PATH
from graph import (
    build_adjacency, search_individuals, format_relation,
    get_individual, find_shortest_path, format_relation_direct,
)
from pdf_export import generate_pdf
from ged_export import generate_ged

app = Flask(__name__)

# --- Estado global ---
_lock = threading.Lock()
_db = None
_adj = None
_ged_file = None
_version = None
_date = None
_github_repo = "zuzu59/ged-relations"


def _load_db(ged_path=None):
    """Charger le fichier GED et initialiser la base."""
    global _db, _adj, _ged_file, _version, _date
    _version, _date = get_version_and_date()

    if ged_path:
        _ged_file = ged_path
        conn, count = load_gedcom(ged_path)
        _db = conn
        fam_count = _db.execute('SELECT COUNT(*) FROM families').fetchone()[0]
        print(f"[GED] Chargé {count} individus, {fam_count} familles depuis {ged_path}")
    else:
        # Essayer le fichier par défaut
        default_ged = os.path.join(os.path.dirname(__file__), "test_data.ged")
        if os.path.exists(default_ged):
            conn, count = load_gedcom(default_ged)
            _db = conn
            _ged_file = default_ged
            fam_count = _db.execute('SELECT COUNT(*) FROM families').fetchone()[0]
            print(f"[GED] Chargé {count} individus, {fam_count} familles depuis {default_ged}")
        else:
            # Base vide — on crée quand même la connexion
            from gedcom_parser import init_db
            _db = init_db()
            print("[GED] Aucun fichier GED trouvé, base vide.")

    _adj = build_adjacency(_db)
    print(f"[Graph] Graphe construit, {_db.execute('SELECT COUNT(DISTINCT person_a) FROM relationships').fetchone()[0]} relations.")


# Rate limiting simple par IP
_rate_limits = {}
_rate_lock = threading.Lock()
MAX_REQUESTS = 200  # Généreux pour usage familial (200 req/min)
RATE_WINDOW = 60  # secondes
RATE_LIMIT_ENABLED = True  # Activé pour éviter les abus


def _check_rate_limit(ip):
    """Vérifier le rate limiting. Retourne True si autorisé."""
    if not RATE_LIMIT_ENABLED:
        return True  # Désactivé
    with _rate_lock:
        import time
        limits = _rate_limits.get(ip, [])
        cutoff = time.time() - RATE_WINDOW
        limits = [t for t in limits if t > cutoff]
        if len(limits) >= MAX_REQUESTS:
            return False
        limits.append(time.time())
        _rate_limits[ip] = limits
        return True


# --- Routes HTML ---

@app.route("/")
def index():
    """Page principale."""
    ver, date = _version, _date
    # Récupérer la branche git actuelle
    import subprocess
    try:
        current_branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=os.path.dirname(__file__),
            stderr=subprocess.STDOUT
        ).decode().strip()
    except:
        current_branch = "unknown"
    github_url = f"https://github.com/{_github_repo}/tree/{current_branch}"
    return render_template(
        "index.html",
        version=ver,
        date=date,
        github_url=github_url,
        current_branch=current_branch,
    )


@app.route("/about")
def about():
    """Page À propos."""
    ver, date = _version, _date
    # Lire la licence
    license_text = ""
    lic_path = os.path.join(os.path.dirname(__file__), "LICENSE")
    if os.path.exists(lic_path):
        with open(lic_path, "r", encoding="utf-8") as f:
            license_text = f.read().strip()
    # Récupérer la branche git actuelle
    import subprocess
    try:
        current_branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=os.path.dirname(__file__),
            stderr=subprocess.STDOUT
        ).decode().strip()
    except:
        current_branch = "unknown"

    github_url = f"https://github.com/{_github_repo}/tree/{current_branch}"
    # Mettre à jour l'URL GitHub avec la branche actuelle
    github_url = f"https://github.com/{_github_repo}/tree/{current_branch}"
    return render_template(
        "about.html",
        version=ver,
        date=date,
        github_url=github_url,
        license_text=license_text,
        current_branch=current_branch,
    )


@app.route("/help")
def help_page():
    """Page Aide."""
    ver, date = _version, _date
    return render_template(
        "help.html",
        version=ver,
        date=date,
    )


# --- API ---

@app.route("/api/search", methods=["GET"])
def api_search():
    """Recherche d'individus."""
    if not _check_rate_limit(request.remote_addr):
        return jsonify({"error": "Trop de requêtes. Réessayez dans 1 minute."}), 429

    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    results = search_individuals(_db, query)
    return jsonify(results)


@app.route("/api/relation", methods=["POST"])
def api_relation():
    """Calculer la relation entre deux individus."""
    if not _check_rate_limit(request.remote_addr):
        return jsonify({"error": "Trop de requêtes. Réessayez dans 1 minute."}), 429

    data = request.get_json()
    if not data:
        return jsonify({"error": "Données manquantes"}), 400

    id_a = data.get("id_a")
    id_b = data.get("id_b")

    if not id_a or not id_b:
        return jsonify({"error": "IDs manquants"}), 400

    degrees, text, error = format_relation(_db, _adj, id_a, id_b)

    if error:
        return jsonify({"error": error, "degrees": degrees, "text": text})

    return jsonify({"degrees": degrees, "text": text})


@app.route("/api/relation-direct", methods=["POST"])
def api_relation_direct():
    """Calculer la relation directe (chemin sans époux/se) entre deux individus."""
    if not _check_rate_limit(request.remote_addr):
        return jsonify({"error": "Trop de requêtes. Réessayez dans 1 minute."}), 429

    data = request.get_json()
    if not data:
        return jsonify({"error": "Données manquantes"}), 400

    id_a = data.get("id_a")
    id_b = data.get("id_b")

    if not id_a or not id_b:
        return jsonify({"error": "IDs manquants"}), 400

    degrees, text, error = format_relation_direct(_db, _adj, id_a, id_b)

    if error:
        return jsonify({"error": error, "degrees": degrees, "text": text})

    return jsonify({"degrees": degrees, "text": text})


@app.route("/api/export/pdf", methods=["POST"])
def api_export_pdf():
    """Exporter la relation en PDF (2 pages : directes + avec parents)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données manquantes"}), 400

    id_a = data.get("id_a")
    id_b = data.get("id_b")

    if not id_a or not id_b:
        return jsonify({"error": "IDs manquants"}), 400

    # Calculer les deux formats
    degrees_full, text_full, error = format_relation(_db, _adj, id_a, id_b)
    if error:
        return jsonify({"error": error}), 400

    degrees_direct, text_direct, error = format_relation_direct(_db, _adj, id_a, id_b)
    if error:
        return jsonify({"error": error}), 400

    ind_a = get_individual(_db, id_a)
    ind_b = get_individual(_db, id_b)
    name_a = f"{ind_a['given_name']} {ind_a['family_name']}".strip() if ind_a else id_a
    name_b = f"{ind_b['given_name']} {ind_b['family_name']}".strip() if ind_b else id_b

    # Générer le PDF avec nom de fichier personnalisé
    now = datetime.now()
    date_str = now.strftime("%y%m%d.%H%M")
    filename = f"{name_a}-{name_b}-{date_str}.pdf".replace(" ", "_")
    pdf_bytes = generate_pdf(name_a, name_b, text_full, text_direct, _db)

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/api/export/ged", methods=["POST"])
def api_export_ged():
    """Exporter la relation en GED."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données manquantes"}), 400

    id_a = data.get("id_a")
    id_b = data.get("id_b")

    if not id_a or not id_b:
        return jsonify({"error": "IDs manquants"}), 400

    path, degrees = find_shortest_path(_adj, id_a, id_b)
    if path is None:
        return jsonify({"error": "Aucun lien trouvé"}), 400

    # Récupérer les noms pour le nom de fichier
    ind_a = get_individual(_db, id_a)
    ind_b = get_individual(_db, id_b)
    name_a = f"{ind_a['given_name']} {ind_a['family_name']}".strip() if ind_a else id_a
    name_b = f"{ind_b['given_name']} {ind_b['family_name']}".strip() if ind_b else id_b

    # Générer le GED avec nom de fichier personnalisé
    now = datetime.now()
    date_str = now.strftime("%y%m%d.%H%M")
    filename = f"{name_a}-{name_b}-{date_str}.ged".replace(" ", "_")
    ged_content = generate_ged(_db, id_a, id_b, path)

    return Response(
        ged_content,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# --- Démarrage ---

def create_app(ged_path=None):
    """Créer l'app Flask avec chargement GED."""
    _load_db(ged_path)
    return app


def _parse_args():
    parser = argparse.ArgumentParser(description="GED Relations web app")
    parser.add_argument("ged_path", nargs="?", default=None, help="Chemin du fichier GED")
    parser.add_argument("--port", type=int, default=8082, help="Port d'écoute")
    return parser.parse_args()


# Lancement direct
if __name__ == "__main__":
    args = _parse_args()
    app = create_app(args.ged_path)
    print(f"\n🚀 GED Relations démarré sur http://0.0.0.0:{args.port}")
    print("   Appuyez Ctrl+C pour arrêter.\n")
    app.run(host="0.0.0.0", port=args.port, threaded=True)
