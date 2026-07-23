"""Export PDF du résultat de relation."""
from fpdf import FPDF
from datetime import datetime, timezone


class RelationPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "GED Relations - Rapport de parente", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", 0, 0, "C")


def _sanitize(text):
    """Remplacer les caractères non-ASCII par des équivalents ASCII."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def generate_pdf(person_a_name, person_b_name, relation_text, conn):
    """Générer un PDF du résultat de relation.

    Args:
        person_a_name: nom de l'individu A
        person_b_name: nom de l'individu B
        relation_text: texte formaté de la relation
        conn: connexion SQLite (pour récupérer les infos)

    Returns:
        bytes: contenu PDF
    """
    pdf = RelationPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # En-tête avec les deux individus
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"{person_a_name}  <->  {person_b_name}", 0, 1, "C")
    pdf.ln(3)

    # Date d'export
    now = datetime.now(timezone.utc)
    mois = {
        1: "janv.", 2: "fevr.", 3: "mars", 4: "avr.", 5: "mai", 6: "juin",
        7: "juil.", 8: "aout", 9: "sept.", 10: "oct.", 11: "nov.", 12: "dec."
    }
    date_str = f"{now.day:02d} {mois[now.month]} {now.year}"
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, f"Exporte le {date_str}", 0, 1, "C")
    pdf.ln(5)

    # Ligne séparatrice
    pdf.set_draw_color(200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # Contenu de la relation (sanitise les caracteres unicode)
    pdf.set_font("Courier", "", 10)
    for line in relation_text.split("\n"):
        safe_line = _sanitize(line)
        pdf.cell(0, 6, safe_line, 0, 1)

    return pdf.output()
