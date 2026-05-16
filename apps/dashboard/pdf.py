from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def generer_pdf_historique(lignes) -> bytes:
    buf    = BytesIO()
    doc    = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=20, rightMargin=20)
    styles = getSampleStyleSheet()
    elems  = [Paragraph('Historique des Paiements', styles['Title']), Spacer(1, 10)]

    header = ['Date', 'Employé', 'Matricule', 'Département', 'Jours', 'Montant (FCFA)', 'Statut']
    rows   = [header] + [
        [
            str(l.date_paiement),
            l.employe.nom_complet,
            l.employe.odoo_id,
            l.employe.departement,
            str(l.nombre_jours),
            f"{l.montant_total:,.0f}",
            l.portefeuille.statut if l.portefeuille else '—',
        ]
        for l in lignes
    ]

    if len(rows) == 1:
        elems.append(Paragraph('Aucune donnée pour les filtres sélectionnés.', styles['Normal']))
    else:
        t = Table(rows, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1, 0),  colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR',      (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',       (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',       (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4f0')]),
            ('GRID',           (0, 0), (-1, -1), 0.4, colors.grey),
            ('PADDING',        (0, 0), (-1, -1), 5),
            ('ALIGN',          (4, 1), (5, -1),  'RIGHT'),
        ]))
        elems.append(t)

    doc.build(elems)
    return buf.getvalue()