#!/bin/bash
set -e  # arrête le script si une commande échoue

echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# echo "⚙️ Copie du fichier .env..."
# if [ ! -f .env ]; then
#     cp .env.example .env
#     echo ".env créé depuis .env.example"
# else
#     echo ".env existe déjà, pas de remplacement"
# fi

echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --no-input

echo "🗄️ Application des migrations..."
python manage.py migrate

echo "👤 Création du superuser..."
python create_superuser.py

echo "✅ Build terminé !"