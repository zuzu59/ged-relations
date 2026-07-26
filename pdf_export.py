"""Export PDF du résultat de relation."""
from fpdf import FPDF
from datetime import datetime, timezone
import os
import sys

# Ajouter le dossier parent au path pour importer version
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from version import get_version_info


class RelationPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "GED Relations - Rapport de parenté", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", 0, 0, "C")


def _sanitize(text):
    """Remplacer les caractères non-ASCII par des équivalents ASCII."""
    import unicodedata
    # Remplacer d'abord les caractères spécifiques
    text = text.replace("—", "-")  # Tiret cadratin -> tiret simple
    text = text.replace("–", "-")  # Tiret demi-cadre -> tiret simple
    text = text.replace("…", "...")  # Points de suspension
    # Puis normaliser pour les accents
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _add_relation_block(pdf, title, relation_text):
    """Ajouter un bloc de relation avec titre, contenu et pied de page.

    Args:
        pdf: instance FPDF
        title: titre du bloc (ex: 'Relations directes', 'Relations avec parents')
        relation_text: texte de la relation à afficher
    """
    # Titre du bloc
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, title, 0, 1, "C")
    pdf.ln(3)

    # Date d'export avec heure
    now = datetime.now()
    mois = {
        1: "janv.", 2: "févr.", 3: "mars", 4: "avr.", 5: "mai", 6: "juin",
        7: "juil.", 8: "août", 9: "sept.", 10: "oct.", 11: "nov.", 12: "déc."
    }
    date_str = f"{now.day:02d} {mois[now.month]} {now.year} à {now.hour:02d}h{now.minute:02d}"
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, f"Exporté le {date_str}", 0, 1, "C")
    pdf.ln(5)

    # Ligne séparatrice
    pdf.set_draw_color(200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # Contenu de la relation (sanitise les caractères unicode)
    pdf.set_font("Helvetica", "", 10)
    for line in relation_text.split("\n"):
        safe_line = _sanitize(line)
        pdf.cell(0, 6, safe_line, 0, 1)

    # Version et date de l'application
    version_info = get_version_info()
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 6, f"Application GED Relations v{version_info['version']}", 0, 1, "C")
    pdf.cell(0, 6, f"Développé le {version_info['build_date']}", 0, 1, "C")


def generate_pdf(person_a_name, person_b_name, relation_full, relation_direct, conn):
    """Générer un PDF du résultat de relation avec 2 pages.

    Args:
        person_a_name: nom de l'individu A
        person_b_name: nom de l'individu B
        relation_full: texte formaté complet (avec parents et époux(se))
        relation_direct: texte formaté épuré (relations directes uniquement)
        conn: connexion SQLite (pour récupérer les infos)

    Returns:
        bytes: contenu PDF
    """
    pdf = RelationPDF()
    pdf.alias_nb_pages()
    pdf.add_page(orientation='L')  # Paysage (landscape)

    # Page 1 : Relations directes
    _add_relation_block(pdf, "Relations directes", relation_direct)

    # Page 2 : Relations avec parents
    pdf.add_page(orientation='L')
    _add_relation_block(pdf, "Relations avec parents", relation_full)

    return bytes(pdf.output(dest='S'))
