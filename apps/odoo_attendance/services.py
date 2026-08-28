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
from apps.odoo_attendance.models import Attendance, Employe, TarifJournalier

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
        #si nous somme en mode debug on met un numero de telephone par defaut pour eviter les erreurs de paiement
        mobile_phone = emp["mobile_phone"] if not settings.DEBUG else "+2250503456789"

        obj, was_created = Employe.objects.update_or_create(
            odoo_id=emp["id"],
            defaults={
                "nom_complet": emp["name"],
                "departement": emp["department_id"][1] if emp.get("department_id") else "",
                "site_travail": nom_site or "",
                "mobile_phone": mobile_phone,
            },
        )
        ## Force le recalcul ET la persistance de operateur_mobile / clientReferenceId
        obj.save()

        if was_created:
            created += 1
            logger.debug(f"[Services] Employé créé : {emp['name']} (odoo_id={emp['id']})")
        else:
            updated += 1
            logger.debug(f"[Services] Employé mis à jour : {emp['name']} (odoo_id={emp['id']})")

    logger.info(f"[Services] Employés — {created} créés, {updated} mis à jour.")
    _dev(f"save_employees : {created} créés / {updated} mis à jour.")


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
        if employe.statut != 'ACTIF' and not employe.permanent:
            employe.statut = 'ACTIF'
            employe.save()
        
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
            employe=employe,
            date=aware_dt.date()  # fix : comparer une date à une date, pas à un datetime
        ).exists():
            skipped += 1
            continue

        # récupère le tarif applicable à la date de la présence
        try:
            montant = get_montant_journalier(aware_dt.date()) if not settings.DEBUG else 15  # fix : nom de fonction corrigé
        except ValueError as e:
            # aucun tarif configuré pour cette date -> on log et on passe à la suivante
            logger.error(f"[Services] {e}")
            errors += 1
            continue

        Attendance.objects.create(
            employe             = employe,
            action              = att["action"],
            date_work           = aware_dt,
            worked_hours        = att.get("worked_hours"),
            odoo_attendance_id  = odoo_id,
            montant_journalier  = montant
        )
        created += 1
        portefeuilles_ok += 1
        logger.debug(
            f"[Services] Portefeuille traité : {employe.nom_complet} "
            f"(odoo_id={employe.odoo_id}) pour la date {aware_dt.date()}"
        )

    logger.info(
        f"[Services] Présences — {created} créées, {skipped} ignorées, "
        f"{errors} erreurs, {portefeuilles_ok} portefeuilles mis à jour."
    )
    _dev(
        f"save_attendances : {created} créées / {skipped} skippées / "
        f"{errors} erreurs / {portefeuilles_ok} portefeuilles OK."
    )


def get_montant_journalier(date_reference):
    #retourne le tarif applicable a une date donnee (le plus recent avant cette date)
    tarif = TarifJournalier.objects.filter(date_effet__lte=date_reference).order_by('-date_effet').first()
    if not tarif:
        #si aucun tarif n'est trouvé, creons un tarif par defaut
        tarif = TarifJournalier.objects.create(montant=3000.0, date_effet=date_reference)
    return tarif.montant
