# Landing - Curso Paños Inmobiliarios

Proyecto Flask con una landing page y formulario de inscripción.

Estructura:
- `app.py` - aplicación Flask y manejo del formulario (guarda en `registrations.db`).
- `templates/` - plantillas HTML (Bootstrap).
- `static/css/` - estilos.
- `static/js/` - scripts.

Instrucciones rápidas (Windows PowerShell):

```powershell
# Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt

# Iniciar la app
.\.venv\Scripts\python app.py
```

Luego abre `http://127.0.0.1:5000` en tu navegador.
