from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from .models import Portefeuille


def generer_pdf_portefeuille(portefeuille: Portefeuille) -> bytes:
    buf    = BytesIO()
    doc    = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elems  = []

    # Titre
    elems.append(Paragraph(f'Fiche Portefeuille #{portefeuille.id}', styles['Title']))
    elems.append(Spacer(1, 12))

    # Infos employé
    emp = portefeuille.employe
    data = [
        ['Employé',       emp.nom_complet],
        ['Matricule',     emp.odoo_id],
        ['Département',   emp.departement],
        ['Site',          emp.site_travail],
        ['Statut',        portefeuille.statut],
        ['Jours impayés', str(portefeuille.nombre_jours_impayes)],
        ['Montant/jour',  f"{portefeuille.montant_journalier} FCFA"],
        ['Total',         f"{portefeuille.montant_total} FCFA"],
    ]

    t = Table(data, colWidths=[150, 300])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID',       (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME',   (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('PADDING',    (0, 0), (-1, -1), 6),
    ]))
    elems.append(t)
    doc.build(elems)
    return buf.getvalue()
