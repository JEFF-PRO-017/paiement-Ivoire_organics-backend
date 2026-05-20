"""
services.py
───────────
Persistance des données Odoo en base locale.
"""

import logging
from datetime import datetime, timezone as dt_timezone
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)
IS_DEV = settings.DEBUG


def _dev(msg: str):
    if IS_DEV:
        print(f"[DEV] {msg}")


# ── Employés ──────────────────────────────────────────────────────────────────

def save_employees(employees: list):
    from apps.employes.models import Employe
    from apps.accounts.models import Site

    created = skipped = 0

    for emp in employees:
        if Employe.objects.filter(odoo_id=emp["id"]).exists():
            skipped += 1
            continue

        nom_site = emp.get("work_location")
        if nom_site:
            site = Site.objects.filter(nom__iexact=nom_site).first()
            if not site:
                logger.warning(
                    f"[Services] Site introuvable : '{nom_site}' "
                    f"(employé {emp.get('name')} odoo_id={emp['id']})"
                )

        Employe.objects.create(
            odoo_id      = emp["id"],
            nom_complet  = emp["name"],
            departement  = emp["department_id"][1] if emp.get("department_id") else "",
            site_travail = nom_site or "",
        )
        created += 1
        logger.debug(f"[Services] Employé créé : {emp['name']} (odoo_id={emp['id']})")

    logger.info(f"[Services] Employés — {created} créés, {skipped} ignorés (déjà en base).")
    _dev(f"save_employees : {created} créés / {skipped} skippés.")


# ── Présences ─────────────────────────────────────────────────────────────────

def save_attendances(attendances: list):
    from apps.employes.models import Employe
    from apps.portefeuilles.models import Portefeuille
    from apps.odoo_attendance.models import Attendance

    created = skipped = errors = portefeuilles_ok = 0

    for att in attendances:
        odoo_id = att.get("id")
        if not odoo_id:
            logger.warning(f"[Services] Présence sans ID ignorée : {att}")
            errors += 1
            continue

        if Attendance.objects.filter(oodo_attendance_id=odoo_id).exists():
            skipped += 1
            continue

        try:
            naive_dt = datetime.strptime(att["name"], "%Y-%m-%d %H:%M:%S")
            aware_dt = timezone.make_aware(naive_dt)
        except (ValueError, KeyError) as e:
            logger.warning(f"[Services] Date invalide pour présence {odoo_id} : {e}")
            errors += 1
            continue

        Attendance.objects.create(
            employee_id        = att["employee_id"][0],
            employee_name      = att["employee_id"][1] if att.get("employee_id") else "Inconnu",
            action             = att["action"],
            name               = aware_dt,
            worked_hours       = att.get("worked_hours"),
            oodo_attendance_id = odoo_id,
        )
        created += 1

        # ── Portefeuille ──────────────────────────────────────────────────────
        if att.get("action") != "sign_out":
            continue
        if (att.get("worked_hours") or 0) <= 2:
            continue

        odoo_emp_id = att["employee_id"][0]
        employe = Employe.objects.filter(odoo_id=odoo_emp_id).first()
        if not employe:
            logger.debug(f"[Services] Employé odoo_id={odoo_emp_id} absent en base — portefeuille ignoré.")
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