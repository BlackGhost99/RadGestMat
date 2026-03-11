#!/bin/bash
# Script de déploiement automatisé pour RadGestMat
# Utilisation: ./deploy.sh

set -e

echo "🚀 Déploiement de RadGestMat sur 10.105.42.118"
echo "================================================"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier les prérequis
echo -e "\n${YELLOW}[1/7]${NC} Vérification des prérequis..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker n'est pas installé${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose n'est pas installé${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker et Docker Compose trouvés${NC}"

# Vérifier le fichier .env
echo -e "\n${YELLOW}[2/7]${NC} Vérification de la configuration..."
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Fichier .env manquant${NC}"
    echo "Créez-le à partir de .env.example"
    exit 1
fi

echo -e "${GREEN}✓ Fichier .env détecté${NC}"

# Arrêter les services existants
echo -e "\n${YELLOW}[3/7]${NC} Arrêt des services existants..."
docker-compose down --remove-orphans || true
echo -e "${GREEN}✓ Services arrêtés${NC}"

# Construire l'image
echo -e "\n${YELLOW}[4/7]${NC} Construction de l'image Docker..."
docker-compose build --no-cache
echo -e "${GREEN}✓ Image construite${NC}"

# Démarrer les services
echo -e "\n${YELLOW}[5/7]${NC} Démarrage des services..."
docker-compose up -d
echo -e "${GREEN}✓ Services démarrés${NC}"

# Attendre que Django soit prêt
echo -e "\n${YELLOW}[6/7]${NC} Initialisation de la base de données..."
sleep 5

# Vérifier que le service web est prêt
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T web python manage.py migrate 2>/dev/null; then
        break
    fi
    attempt=$((attempt + 1))
    if [ $attempt -lt $max_attempts ]; then
        echo "Attente du service web... ($attempt/$max_attempts)"
        sleep 2
    fi
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ Timeout: Django ne répond pas${NC}"
    docker-compose logs web
    exit 1
fi

echo -e "${GREEN}✓ Migrations appliquées${NC}"

# Collecter les static files
echo -e "\n${YELLOW}[7/7]${NC} Collecte des fichiers statiques..."
docker-compose exec -T web python manage.py collectstatic --noinput
echo -e "${GREEN}✓ Fichiers statiques collectés${NC}"

# Résumé final
echo -e "\n${GREEN}✅ Déploiement réussi!${NC}"
echo "================================================"
echo "Services déployés:"
echo "  - Django (Gunicorn): http://10.105.42.118:8000"
echo "  - Nginx (Reverse Proxy): http://10.105.42.118"
echo "  - Redis (Cache): localhost:6379"
echo ""
echo "Prochaines étapes:"
echo "  1. Créer un superutilisateur:"
echo "     docker-compose exec web python manage.py createsuperuser"
echo ""
echo "  2. Accéder à l'admin:"
echo "     http://10.105.42.118/admin/"
echo ""
echo "  3. Voir les logs:"
echo "     docker-compose logs -f web"
echo "================================================"
