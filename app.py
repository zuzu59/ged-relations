"""GED Relations — Application Flask.

Serveur web pour calculer et afficher la relation la plus courte
entre deux individus d'un arbre généalogique GEDCOM.
"""
import os
import sys
import threading
from flask import Flask, render_template, request, jsonify, send_file, Response
from version import get_version_and_date
from gedcom_parser import load_gedcom, DB_PATH
from graph import (
    build_adjacency, search_individuals, format_relation,
    get_individual, find_shortest_path,
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
        print(f"[GED] Chargé {count} individus depuis {ged_path}")
    else:
        # Essayer le fichier par défaut
        default_ged = os.path.join(os.path.dirname(__file__), "test_data.ged")
        if os.path.exists(default_ged):
            conn, count = load_gedcom(default_ged)
            _db = conn
            _ged_file = default_ged
            print(f"[GED] Chargé {count} individus depuis {default_ged}")
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
MAX_REQUESTS = 10
RATE_WINDOW = 60  # secondes


def _check_rate_limit(ip):
    """Vérifier le rate limiting. Retourne True si autorisé."""
    now = int(threading.current_thread().ident)  # approximation
    with _rate_lock:
        limits = _rate_limits.get(ip, [])
        # Nettoyer les anciennes entrées
        import time
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
    github_url = f"https://github.com/{_github_repo}/tree/master"
    return render_template(
        "index.html",
        version=ver,
        date=date,
        github_url=github_url,
    )


@app.route("/about")
def about():
    """Page À propos."""
    ver, date = _version, _date
    github_url = f"https://github.com/{_github_repo}/tree/master"
    # Lire la licence
    license_text = ""
    lic_path = os.path.join(os.path.dirname(__file__), "LICENSE")
    if os.path.exists(lic_path):
        with open(lic_path, "r", encoding="utf-8") as f:
            license_text = f.read().strip()
    return render_template(
        "about.html",
        version=ver,
        date=date,
        github_url=github_url,
        license_text=license_text,
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


@app.route("/api/export/pdf", methods=["POST"])
def api_export_pdf():
    """Exporter la relation en PDF."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données manquantes"}), 400

    id_a = data.get("id_a")
    id_b = data.get("id_b")

    if not id_a or not id_b:
        return jsonify({"error": "IDs manquants"}), 400

    degrees, text, error = format_relation(_db, _adj, id_a, id_b)

    if error:
        return jsonify({"error": error}), 400

    ind_a = get_individual(_db, id_a)
    ind_b = get_individual(_db, id_b)
    name_a = f"{ind_a['given_name']} {ind_a['family_name']}".strip() if ind_a else id_a
    name_b = f"{ind_b['given_name']} {ind_b['family_name']}".strip() if ind_b else id_b

    pdf_bytes = generate_pdf(name_a, name_b, text, _db)

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=relation.pdf"},
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

    ged_content = generate_ged(_db, id_a, id_b, path)

    return Response(
        ged_content,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=relation.ged"},
    )


# --- Démarrage ---

def create_app(ged_path=None):
    """Créer l'app Flask avec chargement GED."""
    _load_db(ged_path)
    return app


# Lancement direct
if __name__ == "__main__":
    ged_path = sys.argv[1] if len(sys.argv) > 1 else None
    app = create_app(ged_path)
    print("\n🚀 GED Relations démarré sur http://0.0.0.0:8082")
    print("   Appuyez Ctrl+C pour arrêter.\n")
    app.run(host="0.0.0.0", port=8082, threaded=True)
