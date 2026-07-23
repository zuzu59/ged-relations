"""Gestion de la version de l'application."""
import os
from datetime import datetime, timezone

VERSION_FILE = os.path.join(os.path.dirname(__file__), "version.txt")
DEFAULT_VERSION = "0.0.1"


def _read_version():
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return DEFAULT_VERSION


def _increment_version():
    """Incrémente le patch : 0.0.x → 0.0.(x+1)"""
    ver = _read_version()
    parts = ver.split(".")
    parts[2] = str(int(parts[2]) + 1)
    new_ver = ".".join(parts)
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(new_ver)
    return new_ver


def get_version():
    """Retourne la version actuelle."""
    return _read_version()


def get_version_and_date():
    """Retourne (version, date_formatee) au démarrage."""
    ver = _read_version()
    # Incrémenter la version au démarrage de chaque exécution
    ver = _increment_version()
    now = datetime.now(timezone.utc)
    # Format: dd mmm yyyy (ex: 15 juil. 2025)
    mois = {
        1: "janv.", 2: "févr.", 3: "mars", 4: "avr.", 5: "mai", 6: "juin",
        7: "juil.", 8: "août", 9: "sept.", 10: "oct.", 11: "nov.", 12: "déc."
    }
    date_str = f"{now.day:02d} {mois[now.month]} {now.year}"
    return ver, date_str


def get_version_info():
    """Retourne un dict avec version et date de build."""
    ver = get_version()
    now = datetime.now()
    mois = {
        1: "janv.", 2: "févr.", 3: "mars", 4: "avr.", 5: "mai", 6: "juin",
        7: "juil.", 8: "août", 9: "sept.", 10: "oct.", 11: "nov.", 12: "déc."
    }
    date_str = f"{now.day:02d} {mois[now.month]} {now.year}"
    return {"version": ver, "build_date": date_str}


def reset_version():
    """Réinitialise la version à 0.0.1 (utile pour les tests)."""
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write("0.0.1")
