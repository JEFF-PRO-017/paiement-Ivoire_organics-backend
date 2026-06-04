#!/bin/bash
set -e

echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# echo "⚙️ Copie du fichier .env..."
# if [ ! -f .env ]; then
#     cp .env.example .env
# fi

echo "🗄️ Création de la base de données SQLite..."
touch db.sqlite3

echo "🗄️ Application des migrations..."
python manage.py migrate

echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --no-input

echo "👤 Création du superuser..."
python create_superuser.py

echo "✅ Build terminé !"