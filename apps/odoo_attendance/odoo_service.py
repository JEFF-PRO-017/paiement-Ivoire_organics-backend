"""
odoo_service.py
───────────────
Connexion XML-RPC à Odoo. UID mis en cache, reconnexion automatique.
Toutes les dates sont converties en UTC naïf (format Odoo).
"""

from xmlrpc import client as xmlrpclib
from datetime import timedelta, timezone as dt_timezone
from django.utils import timezone
from django.conf import settings

# ── Config (depuis .env via settings) ────────────────────────────────────────

URL      = settings.ODOO_URL
DB       = settings.ODOO_DB
USERNAME = settings.ODOO_USERNAME
PASSWORD = settings.ODOO_PASSWORD

ODOO_DT_FORMAT = "%Y-%m-%d %H:%M:%S"
_uid_cache: int | None = None

EMPLOYEE_FIELDS   = ["id", "active", "name", "department_id", "work_location",
                     "mobile_phone", "work_email"]
ATTENDANCE_FIELDS = ["employee_id", "action", "name", "worked_hours"]


# ── Helpers ───────────────────────────────────────────────────────────────────

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
    uid = xmlrpclib.ServerProxy(f"{URL}/xmlrpc/common").login(DB, USERNAME, PASSWORD)
    if not uid:
        raise ConnectionError("Authentification Odoo échouée.")
    _uid_cache = uid
    return _uid_cache


def _invalidate_uid():
    global _uid_cache
    _uid_cache = None


def _execute(model: str, method: str, *args):
    """Appel XML-RPC avec reconnexion automatique sur session expirée (Fault 3)."""
    try:
        return xmlrpclib.ServerProxy(f"{URL}/xmlrpc/object").execute(
            DB, _get_uid(), PASSWORD, model, method, *args
        )
    except xmlrpclib.Fault as f:
        if f.faultCode == 3:
            _invalidate_uid()
            return xmlrpclib.ServerProxy(f"{URL}/xmlrpc/object").execute(
                DB, _get_uid(), PASSWORD, model, method, *args
            )
        raise


def _search_read(model: str, domain: list, fields: list) -> list:
    return _execute(model, "search_read", domain, fields, 0, 0)


# ── Employés ──────────────────────────────────────────────────────────────────

def get_all_employees() -> list:
    return _search_read("hr.employee", [], EMPLOYEE_FIELDS)


def get_new_employees(since_minutes=30) -> list:
    return _search_read(
        "hr.employee",
        [("create_date", ">=", _utc_since(since_minutes))],
        EMPLOYEE_FIELDS,
    )


# ── Présences ─────────────────────────────────────────────────────────────────

def get_new_attendances(since_minutes=30) -> list:
    return _search_read(
        "hr.attendance",
        [("name", ">=", _utc_since(since_minutes))],
        ATTENDANCE_FIELDS,
    )


def get_last_days_attendances(days=10) -> list:
    """Présences des X derniers jours (défaut : 10)."""
    return _search_read(
        "hr.attendance",
        [("name", ">=", _utc_since_days(days))],
        ATTENDANCE_FIELDS,
    )