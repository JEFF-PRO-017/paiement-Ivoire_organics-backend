"""
services.py
───────────
Persistance des données Odoo en base locale.
"""

import logging
from datetime import datetime, timezone 
from django.conf import settings
from django.utils import timezone
from apps.accounts.models import Site
from apps.odoo_attendance.models import Attendance, Employe

logger = logging.getLogger(__name__)
IS_DEV = settings.DEBUG


def _dev(msg: str):
    if IS_DEV:
        print(f"[DEV] {msg}")


# ── Employés ──────────────────────────────────────────────────────────────────

def update_or_create_employees(employees: list):
    created = updated = 0

    for emp in employees:
        nom_site = emp.get("work_location")
        if nom_site and not Site.objects.filter(nom__iexact=nom_site).exists():
            logger.warning(
                f"[Services] Site introuvable : '{nom_site}' "
                f"(employé {emp.get('name')} odoo_id={emp['id']})"
            )

        obj, was_created = Employe.objects.update_or_create(
            odoo_id=emp["id"],
            defaults={
                "nom_complet": emp["name"],
                "departement": emp["department_id"][1] if emp.get("department_id") else "",
                "site_travail": nom_site or "",
                "mobile_phone": emp["mobile_phone"] or "",
            },
        )

        if was_created:
            created += 1
            logger.debug(f"[Services] Employé créé : {emp['name']} (odoo_id={emp['id']})")
        else:
            updated += 1
            logger.debug(f"[Services] Employé mis à jour : {emp['name']} (odoo_id={emp['id']})")

    logger.info(f"[Services] Employés — {created} créés, {updated} mis à jour.")
    _dev(f"save_employees : {created} créés / {updated} mis à jour.")


# ── Présences ─────────────────────────────────────────────────────────────────
def save_attendances(attendances: list):
    created = skipped = errors = portefeuilles_ok = 0

    for att in attendances:
        odoo_id = att.get("id")
        if not odoo_id:
            errors += 1
            continue

        odoo_emp_id = att["employee_id"][0]
        employe = Employe.objects.filter(odoo_id=odoo_emp_id).first()
        if not employe:
            continue

        # on vérifie le statut au lieu de l'écraser
        if employe.statut != 'ACTIF':
            skipped += 1
            continue

        try:
            naive_dt = datetime.strptime(att["name"], "%Y-%m-%d %H:%M:%S")
            aware_dt = timezone.make_aware(naive_dt)
        except (ValueError, KeyError):
            errors += 1
            continue

        if att.get("action") != "sign_out":
            continue

        if Attendance.objects.filter(odoo_attendance_id=odoo_id).exists():
            skipped += 1
            continue

        # un employé ne peut avoir qu'une seule présence par jour
        if Attendance.objects.filter(
            employee_id=odoo_emp_id,
            date_work__date=aware_dt
        ).exists():
            skipped += 1
            continue

        Attendance.objects.create(
            employe        = employe,
            action             = att["action"],
            date_work          = aware_dt,
            worked_hours       = att.get("worked_hours"),
            odoo_attendance_id = odoo_id,
            montant_journalier = 3000
        )
        created += 1
        portefeuilles_ok += 1
        logger.debug(f"[Services] Portefeuille traité : {employe.nom_complet} — {date_str}")

    logger.info(
        f"[Services] Présences — {created} créées, {skipped} ignorées, "
        f"{errors} erreurs, {portefeuilles_ok} portefeuilles mis à jour."
    )
    _dev(
        f"save_attendances : {created} créées / {skipped} skippées / "
        f"{errors} erreurs / {portefeuilles_ok} portefeuilles OK."
    )