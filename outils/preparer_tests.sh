#!/usr/bin/env bash
# Prépare l'environnement des tests sur une machine GitHub (mêmes chemins que pendant le développement).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
sudo mkdir -p /home/claude /tmp/claude-0 && sudo chown -R "$USER" /home/claude /tmp/claude-0
mkdir -p /home/claude/rendus /home/claude/depot
ln -sfn "$REPO" /home/claude/baldcoaching
ln -sfn "$REPO/tests" /home/claude/tests
ln -sfn "$REPO/tests" /home/claude/depot/tests
python3 "$REPO/outils/extraire_source.py" "$REPO/index.html" /home/claude/carnet.html
echo 'window.BALD_CONFIG={supabaseUrl:"",supabaseAnonKey:""};' > /home/claude/config.claude.js
cp "$REPO/tests/modeles-exemple.json" /tmp/claude-0/modeles.json
python3 -c "from PIL import Image;Image.new('RGB',(1600,2000),(200,150,120)).save('/tmp/claude-0/photo-test.jpg',quality=85)"
