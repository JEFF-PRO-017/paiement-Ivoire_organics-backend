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
        )
        logger.info(f"[Odoo] Employé créé : {emp['name']} (odoo_id={emp['id']})")


# ── Présences ─────────────────────────────────────────────────────────────────

def save_attendances(attendances: list):
    from apps.employes.models import Employe
    from apps.portefeuilles.models import Portefeuille
    from apps.odoo_attendance.models import Attendance
    from django.utils import timezone

    logger.info(f"[Odoo] {len(attendances)} présence(s) à traiter.")

    for att in attendances:
        odoo_id = att.get("id")
        if not odoo_id:
            logger.warning(f"[Odoo] Présence sans ID ignorée : {att}")
            continue  # ✅ skip si pas d'ID

        # Vérifier doublon
        if Attendance.objects.filter(oodo_attendance_id=odoo_id).exists():
            continue

        # Conversion date
        try:
            naive_dt = datetime.strptime(att["name"], "%Y-%m-%d %H:%M:%S")
            aware_dt = timezone.make_aware(naive_dt)
        except (ValueError, KeyError) as e:
            logger.warning(f"[Odoo] Date invalide pour présence {odoo_id} : {e}")
            continue  # ✅ skip si date invalide

        Attendance.objects.create(
            employee_id       = att["employee_id"][0],
            employee_name     = att["employee_id"][1] if att.get("employee_id") else "Inconnu",
            action            = att["action"],
            name              = aware_dt,
            worked_hours      = att.get("worked_hours"),
            oodo_attendance_id= odoo_id,  # ✅
        )

        # Suite logique portefeuille...
        if att.get("action") != "sign_out":
            continue
        if (att.get("worked_hours") or 0) <= 2:
            continue

        odoo_emp_id = att["employee_id"][0]
        employe = Employe.objects.filter(odoo_id=odoo_emp_id).first()
        if not employe:
            continue

        try:
            dt_utc   = datetime.strptime(att["name"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt_timezone.utc)
            date_str = dt_utc.date().isoformat()
        except (ValueError, KeyError):
            continue

        portefeuille = Portefeuille.objects.filter(
            employe=employe,
            statut__in=["EN_ATTENTE"]
        ).first()

        if portefeuille:
            if date_str in portefeuille.periodes_paiement:
                continue
            portefeuille.periodes_paiement.append(date_str)
            portefeuille.nombre_jours_impayes += 1
            portefeuille.save(update_fields=["periodes_paiement", "nombre_jours_impayes", "modifie_le"])
        else:
            Portefeuille.objects.create(
                employe              = employe,
                nombre_jours_impayes = 1,
                montant_journalier   = 3000,
                periodes_paiement    = [date_str],
                statut               = "EN_ATTENTE",
            )
        print(f"Portefeuille traité pour {employe.nom_complet} : {date_str}")