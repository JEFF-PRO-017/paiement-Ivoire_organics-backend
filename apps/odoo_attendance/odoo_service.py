"""
odoo_service.py
───────────────
Connexion XML-RPC à Odoo. UID mis en cache, reconnexion automatique.
Toutes les dates sont converties en UTC naïf (format Odoo).
"""

import logging
from xmlrpc import client as xmlrpclib
from datetime import timedelta, timezone as dt_timezone
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

URL      = settings.ODOO_URL
DB       = settings.ODOO_DB
USERNAME = settings.ODOO_USERNAME
PASSWORD = settings.ODOO_PASSWORD

DAYS_INITIAL_ATTENDANCE = settings.ODOO_DAYS_INITIAL_ATTENDANCE


ODOO_DT_FORMAT  = "%Y-%m-%d %H:%M:%S"
BATCH_SIZE      = 100       # Jamais limit=0 → XML tronqué garanti
_uid_cache: int | None = None

EMPLOYEE_FIELDS   = ["id", "active", "name", "department_id", "work_location",
                     "mobile_phone", "work_email"]
ATTENDANCE_FIELDS = ["id", "employee_id", "action", "name", "worked_hours"]


# ── Exceptions métier ─────────────────────────────────────────────────────────

class OdooConnectionError(Exception):
    """Réseau inaccessible, Odoo down, timeout."""

class OdooAuthError(Exception):
    """Mauvais credentials ou session expirée non récupérable."""

class OdooDataError(Exception):
    """Réponse XML malformée ou données inattendues."""


# ── Helpers dates ─────────────────────────────────────────────────────────────

def _utc_since(minutes: int) -> str:
    since_utc = (timezone.now() - timedelta(minutes=minutes)) \
                .astimezone(dt_timezone.utc).replace(tzinfo=None)
    return since_utc.strftime(ODOO_DT_FORMAT)


def _utc_since_days(days: int) -> str:
    since_utc = (timezone.now() - timedelta(days=days)) \
                .astimezone(dt_timezone.utc).replace(tzinfo=None)
    return since_utc.strftime(ODOO_DT_FORMAT)


# ── Connexion ─────────────────────────────────────────────────────────────────

def _get_uid() -> int:
    global _uid_cache
    if _uid_cache is not None:
        return _uid_cache
    try:
        uid = xmlrpclib.ServerProxy(f"{URL}/xmlrpc/common").login(DB, USERNAME, PASSWORD)
    except OSError as e:
        raise OdooConnectionError(f"Impossible de joindre Odoo ({URL}) : {e}") from e
    except Exception as e:
        raise OdooConnectionError(f"Erreur inattendue lors de la connexion Odoo : {e}") from e

    if not uid:
        raise OdooAuthError(f"Authentification Odoo échouée — vérifiez DB/USERNAME/PASSWORD.")

    _uid_cache = uid
    logger.debug(f"[Odoo] Connecté. UID={uid}")
    return _uid_cache


def _invalidate_uid():
    global _uid_cache
    _uid_cache = None


# ── Exécution XML-RPC ─────────────────────────────────────────────────────────

def _execute(model: str, method: str, *args):
    """
    Appel XML-RPC avec :
    - Reconnexion automatique sur session expirée (Fault code 3)
    - Conversion des erreurs réseau en OdooConnectionError
    - Conversion des XML malformés en OdooDataError
    """
    def _call(uid):
        return xmlrpclib.ServerProxy(f"{URL}/xmlrpc/object").execute(
            DB, uid, PASSWORD, model, method, *args
        )

    try:
        return _call(_get_uid())

    except xmlrpclib.Fault as f:
        if f.faultCode == 3:
            logger.warning("[Odoo] Session expirée — reconnexion automatique.")
            _invalidate_uid()
            try:
                return _call(_get_uid())
            except xmlrpclib.Fault as f2:
                raise OdooAuthError(f"Reconnexion échouée : {f2.faultString}") from f2
        raise OdooDataError(f"Odoo XML-RPC Fault [{f.faultCode}] : {f.faultString}") from f

    except Exception as e:
        msg = str(e)
        # XML tronqué → réponse trop grande ou coupée en transit
        if "unclosed token" in msg or "ExpatError" in msg or "syntax error" in msg:
            raise OdooDataError(
                f"Réponse XML malformée depuis Odoo (probablement tronquée). "
                f"Utilisez la pagination. Détail : {e}"
            ) from e
        # Réseau
        if any(k in msg for k in ("Errno 101", "Errno 110", "timed out",
                                   "unreachable", "ConnectionRefused")):
            raise OdooConnectionError(f"Réseau inaccessible : {e}") from e
        raise OdooConnectionError(f"Erreur connexion Odoo : {e}") from e


# ── Pagination ────────────────────────────────────────────────────────────────

def _search_read_paginated(model: str, domain: list, fields: list,
                           batch_size: int = BATCH_SIZE) -> list:
    """
    Charge tous les enregistrements par pages de `batch_size`.
    Ne fait JAMAIS limit=0 (= crash XML sur gros volumes).
    """
    all_records = []
    offset = 0

    while True:
        logger.debug(f"[Odoo] {model} — batch offset={offset} limit={batch_size}")
        batch = _execute(model, "search_read", domain, fields, offset, batch_size)

        if not batch:
            break

        all_records.extend(batch)
        logger.debug(f"[Odoo] {model} — {len(all_records)} enregistrements chargés.")

        if len(batch) < batch_size:
            break       # dernière page incomplète → on arrête

        offset += batch_size

    return all_records


def _search_read(model: str, domain: list, fields: list) -> list:
    """Appel simple sans pagination (pour les petits volumes filtrés)."""
    return _execute(model, "search_read", domain, fields, 0, BATCH_SIZE)


# ── Employés ──────────────────────────────────────────────────────────────────

def get_all_employees() -> list:
    """Charge TOUS les employés avec pagination — safe sur gros volumes."""
    logger.info("[Odoo] Chargement de tous les employés (paginé)...")
    records = _search_read_paginated("hr.employee", [], EMPLOYEE_FIELDS)
    logger.info(f"[Odoo] {len(records)} employés récupérés depuis Odoo.")
    return records


def get_new_employees(since_minutes=30) -> list:
    since = _utc_since(since_minutes)
    logger.debug(f"[Odoo] Nouveaux employés depuis {since}")
    return _search_read(
        "hr.employee",
        [("create_date", ">=", since)],
        EMPLOYEE_FIELDS,
    )


# ── Présences ─────────────────────────────────────────────────────────────────

def get_new_attendances(since_minutes=30) -> list:
    since = _utc_since(since_minutes)
    logger.debug(f"[Odoo] Nouvelles présences depuis {since}")
    return _search_read(
        "hr.attendance",
        [("name", ">=", since), ("action", "=", "sign_out")],
        ATTENDANCE_FIELDS,
    )


def get_last_days_attendances() -> list:
    days =DAYS_INITIAL_ATTENDANCE if DAYS_INITIAL_ATTENDANCE is not None else 1
    since = _utc_since_days(days)
    logger.info(f"[Odoo] Présences des {days} derniers jours depuis {since} (paginé)...")
    records = _search_read_paginated(
        "hr.attendance",
        [("name", ">=", since), ("action", "=", "sign_out")],
        ATTENDANCE_FIELDS,
    )
    logger.info(f"[Odoo] {len(records)} présences récupérées depuis Odoo.")
    return records