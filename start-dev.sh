#!/bin/bash
# Script de démarrage propre du serveur GED Relations

echo "🔄 Démarrage du serveur GED Relations..."

# 1. Tuer proprement le serveur
pkill -9 -f "app.py" 2>/dev/null
sleep 2

PORT=8092

# 2. Vérifier que le port est libre
for i in {1..5}; do
    if ! lsof -i :$PORT > /dev/null 2>&1; then
        break
    fi
    echo "   Attente libération du port $PORT..."
    sleep 1
done

# 3. Redémarrer le serveur
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
GED_FILE="${1:-$SCRIPT_DIR/test_data.ged}"
nohup .venv/bin/python app.py "$GED_FILE" --port "$PORT" > /tmp/srv.log 2>&1 &

# 4. Attendre que le serveur démarre (augmenté pour gros fichiers GED)
echo "   Démarrage en cours..."
for i in {1..20}; do
    if curl -s http://localhost:$PORT/ > /dev/null 2>&1; then
        echo "✅ Serveur démarré sur http://0.0.0.0:$PORT"
        echo ""
        echo "📊 Statistiques chargées :"
        grep -E "Chargé|Graphe" /tmp/srv.log | tail -2 | while read line; do
            echo "   $line"
        done
        echo ""
        curl -s http://localhost:$PORT/ | grep -oE "v[0-9]+\.[0-9]+\.[0-9]+"
        exit 0
    fi
    sleep 1
done

echo "❌ Erreur: le serveur n'a pas démarré"
tail -20 /tmp/srv.log
exit 1
