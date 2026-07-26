#!/bin/bash
# Script de redémarrage propre du serveur GED Relations

echo "🔄 Redémarrage du serveur GED Relations..."

# 1. Tuer proprement le serveur
pkill -9 -f "app.py" 2>/dev/null
sleep 2

# 2. Vérifier que le port 8082 est libre
for i in {1..5}; do
    if ! lsof -i :8082 > /dev/null 2>&1; then
        break
    fi
    echo "   Attente libération du port 8082..."
    sleep 1
done

# 3. Redémarrer le serveur
cd /home/ubuntu/dev/ged-relations
GED_FILE="${1:-/home/ubuntu/dev/bourgeoisie_extraction_78_individus.ged}"
nohup .venv/bin/python app.py "$GED_FILE" > /tmp/srv.log 2>&1 &

# 4. Attendre que le serveur démarrer
echo "   Démarrage en cours..."
for i in {1..10}; do
    if curl -s http://localhost:8082/ > /dev/null 2>&1; then
        echo "✅ Serveur démarré sur http://0.0.0.0:8082"
        curl -s http://localhost:8082/ | grep -oE "v[0-9]+\.[0-9]+\.[0-9]+"
        exit 0
    fi
    sleep 1
done

echo "❌ Erreur: le serveur n'a pas démarré"
tail -20 /tmp/srv.log
exit 1
