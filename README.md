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
python -m venv venv
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
python manage.py makemigrations accounts employes portefeuilles
python manage.py migrate

# 7. Superuser admin
python manage.py createsuperuser

# 8. Lancer
python manage.py runserver
```

---

## Déploiement (VPS Linux)

```bash
# 1. Installer les dépendances système
sudo apt update && sudo apt install python3.12 python3.12-venv python3-pip mysql-server nginx -y

# 2. Créer la base MySQL
sudo mysql -e "CREATE DATABASE paiement_db CHARACTER SET utf8mb4;
               CREATE USER 'paiement'@'localhost' IDENTIFIED BY 'motdepasse';
               GRANT ALL ON paiement_db.* TO 'paiement'@'localhost';"

# 3. Cloner et installer
git clone <repo> /var/www/paiement_backend
cd /var/www/paiement_backend
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. Configurer .env (DEBUG=False, ALLOWED_HOSTS=ton-domaine.com)
cp .env.example .env && nano .env

# 5. Préparer les statics et migrer
python manage.py collectstatic --noinput
python manage.py migrate

# 6. Gunicorn (serveur WSGI)
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
