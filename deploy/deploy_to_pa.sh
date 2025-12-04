#!/bin/bash
# Helper script to deploy the project on PythonAnywhere (run in a Bash console on PA)
# Usage on PythonAnywhere:
#   1) Edit REPO_URL below if you want to use SSH (git@github.com:...) or a different repo URL.
#   2) Paste this file into ~/Lading-formulario/deploy/deploy_to_pa.sh or clone the repo and run:
#        chmod +x deploy/deploy_to_pa.sh
#        ./deploy/deploy_to_pa.sh

set -euo pipefail

# Configure these variables if needed
REPO_URL="https://github.com/neotech2295-rgb/Sistemas.git"
APP_DIR="$HOME/Lading-formulario"
VENV_DIR="$APP_DIR/.venv"

echo "Deploy helper starting..."

if [ -d "$APP_DIR" ]; then
  echo "Project directory exists at $APP_DIR — pulling latest changes"
  cd "$APP_DIR"
  git pull || true
else
  echo "Cloning repo $REPO_URL to $APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
fi

echo "Creating virtualenv at $VENV_DIR (if missing)"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
echo "Installing Python dependencies from requirements.txt"
pip install -r requirements.txt

echo "Initializing SQLite DB (if not exists)"
python -c "from app import init_db; init_db(); print('DB initialized')"

echo "Creating/updating superuser (auto)"
python scripts/create_superuser_auto.py || true

echo "Done. Next steps (in PythonAnywhere Web UI):"
echo " - Set Virtualenv to: $VENV_DIR"
echo " - Paste the WSGI snippet from deploy/wsgi_snippet.txt into the WSGI config file"
echo " - Map /static/ -> $APP_DIR/static/ in Static Files"
echo " - Add environment variables (SECRET_KEY, SMTP_*, MAIL_TO, etc.)"
echo " - Reload the web app from the Web tab"

echo "Deploy helper finished."
