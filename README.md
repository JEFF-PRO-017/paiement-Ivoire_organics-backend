# Paiement Backend

API REST Django 5.1 + MySQL pour la gestion des paiements journaliers, synchronisée avec Odoo via XML-RPC.

---

## Stack

- Python 3.12 / Django 5.1
- MySQL 8
- Django REST Framework + SimpleJWT
- APScheduler (sync Odoo toutes les 30 min)
- ReportLab (export PDF)

---

## Installation

```bash
# 1. Cloner et entrer dans le projet
git clone <repo> && cd paiement_backend

# 2. Environnement virtuel
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Dépendances
pip install -r requirements.txt

# 4. Variables d'environnement
cp .env.example .env
# Ouvrir .env et remplir : DB_PASSWORD, ODOO_PASSWORD, EMAIL_HOST_PASSWORD

# 5. Base de données MySQL
mysql -u root -p -e "CREATE DATABASE paiement_db CHARACTER SET utf8mb4;"

# 6. Migrations
python manage.py makemigrations 
python manage.py migrate

# 7. Superuser admin
python manage.py createsuperuser

# 8. Lancer
python manage.py runserver
```
