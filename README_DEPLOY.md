# Despliegue a PythonAnywhere (guía rápida)

Este archivo resume los pasos para desplegar el proyecto en PythonAnywhere y dejarlo corriendo en producción.

1) Subir el repositorio a GitHub (o clonar a PythonAnywhere)

Desde tu máquina local (rellena `TU_REPO_URL`):

```powershell
git init
git add .
git commit -m "Prepare for deployment"
git remote add origin <TU_REPO_URL>
git push -u origin main
```

2) Crear cuenta y clonar en PythonAnywhere

- Regístrate en https://www.pythonanywhere.com y abre una consola Bash.
- Clona tu repo en tu home:

```bash
git clone https://github.com/TU_USUARIO/tu-repo.git ~/Lading-formulario
cd ~/Lading-formulario
```

3) Crear virtualenv e instalar dependencias

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4) WSGI configuration

- En el panel Web -> WSGI configuration file, edita para importar la app:

```python
import sys
sys.path.insert(0, '/home/yourusername/Lading-formulario')
from app import app as application
```

Si en `app.py` exponemos `application = app`, también puedes `from app import application`.

5) Static files

- En Web -> Static files, añade el mapeo `/static/` -> `/home/yourusername/Lading-formulario/static/`.

6) Variables de entorno

- En Web -> Environment variables añade las variables necesarias (no las guardes en el repo):
  - `SECRET_KEY` (valor seguro)
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `MAIL_TO`, `MAIL_FROM` (según necesites)
  - `FLASK_DEBUG=false`

7) Inicializar la DB y crear admin

En Bash (PythonAnywhere):

```bash
cd ~/Lading-formulario
. .venv/bin/activate
python -c "from app import init_db; init_db(); print('DB inicializada')"
python scripts/create_superuser_auto.py
```

8) Reload

- Pulsa el botón `Reload` en el Dashboard -> Web. Visita `https://yourusername.pythonanywhere.com`.

9) Logs y debugging

- Revisa `Server log` y `Error log` desde la sección Web para diagnosticar problemas.

Notas
- PythonAnywhere puede limitar el envío SMTP en cuentas gratuitas. Para producción usa SendGrid/Mailgun o un plan que permita SMTP.
- El proyecto ya incluye `.env.example` y `.gitignore`. No subas `.env` al repo.

---
Si quieres, puedo generar un archivo WSGI listo para copiar/pegar o preparar un `Dockerfile` si prefieres contenerizar en otro proveedor.
