"""
services.py
───────────
Persistance des données Odoo en base locale.
Toute la logique métier est ici — le scheduler appelle uniquement ces fonctions.
"""

import logging
from datetime import datetime, timezone as dt_timezone

logger = logging.getLogger(__name__)


# ── Employés ──────────────────────────────────────────────────────────────────

def save_employees(employees: list):
    from apps.employes.models import Employe
    from apps.accounts.models import Site

    logger.info(f"[Odoo] {len(employees)} employé(s) à traiter.")

    for emp in employees:
        # Employé déjà en base → skip (pas d'écrasement des données manuelles)
        if Employe.objects.filter(odoo_id=emp["id"]).exists():
            continue

        site_id = None
        nom_site = emp.get("work_location")
        if nom_site:
            site = Site.objects.filter(nom__iexact=nom_site).first()
            site_id = site.id if site else None
            if not site:
                logger.warning(f"[Odoo] Site introuvable : '{nom_site}' (employé {emp.get('name')})")

        Employe.objects.create(
            odoo_id      = emp["id"],
            nom_complet  = emp["name"],
            departement  = emp["department_id"][1] if emp.get("department_id") else "",
            site_travail = nom_site or "",
            statut       = "INACTIF",  # activation manuelle dans l'admin
        )
        logger.info(f"[Odoo] Employé créé : {emp['name']} (odoo_id={emp['id']})")


# ── Présences ─────────────────────────────────────────────────────────────────

def save_attendances(attendances: list):
    from apps.employes.models import Employe
    from apps.portefeuilles.models import Portefeuille

    logger.info(f"[Odoo] {len(attendances)} présence(s) à traiter.")
    print(f"Présences à traiter : {len(attendances)}")
    for att in attendances:
        # 1. Valider : sign_out + worked_hours > 2 (présence complète)
        if att.get("action") != "sign_out":
            continue
        if (att.get("worked_hours") or 0) <= 2:
            continue

        # 2. Trouver l'employé local
        odoo_emp_id = att["employee_id"][0]
        employe = Employe.objects.filter(odoo_id=odoo_emp_id).first()
        if not employe:
            logger.warning(f"[Odoo] Employé odoo_id={odoo_emp_id} introuvable en base.")
            continue

        # 3. Extraire la date UTC de la présence (format Odoo : "2026-05-05 20:02:54")
        try:
            dt_utc    = datetime.strptime(att["name"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt_timezone.utc)
            date_str  = dt_utc.date().isoformat()   # "2026-05-05"
        except (ValueError, KeyError):
            logger.warning(f"[Odoo] Date invalide pour présence : {att}")
            continue

        # 4. Chercher un portefeuille EN_ATTENTE ou IMPAYE pour cet employé
        portefeuille = Portefeuille.objects.filter(
            employe=employe,
            statut__in=["EN_ATTENTE"]
        ).first()

        if portefeuille:
            # Éviter les doublons de date dans periodes_paiement
            if date_str in portefeuille.periodes_paiement:
                logger.info(f"[Odoo] Présence {date_str} déjà enregistrée pour {employe.nom_complet}.")
                continue
            portefeuille.periodes_paiement.append(date_str)
            portefeuille.nombre_jours_impayes += 1
            portefeuille.save(update_fields=["periodes_paiement", "nombre_jours_impayes", "modifie_le"])
            logger.info(f"[Odoo] Portefeuille #{portefeuille.id} mis à jour : +1 jour ({date_str}).")
        else:
            # Créer un nouveau portefeuille
            pf = Portefeuille.objects.create(
                employe              = employe,
                nombre_jours_impayes = 1,
                montant_journalier   = 3000,   # valeur par défaut — à paramétrer
                periodes_paiement    = [date_str],
                statut               = "EN_ATTENTE",
            )
            logger.info(f"[Odoo] Portefeuille créé #{pf.id} pour {employe.nom_complet} ({date_str}).")