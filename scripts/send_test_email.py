r"""Script de prueba para enviar un email usando la función `send_email` de app.py.

Uso (PowerShell):
    $env:SMTP_HOST='smtp.example.com'
    $env:SMTP_PORT='587'
    $env:SMTP_USER='user@example.com'
    $env:SMTP_PASS='app-password'
    $env:MAIL_TO='mi@correo.cl'
    C:/path/to/.venv/Scripts/python.exe .\scripts\send_test_email.py

El script intenta enviar dos correos: una notificación al admin (según MAIL_TO)
y una confirmación a un correo de prueba proporcionado en el script.
"""
import os
import sys

# Ensure project root is on sys.path so `from app import send_email` works
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import send_email
try:
    # Optional: load variables from a local .env file if present
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, '.env'))
except Exception:
    # python-dotenv may not be installed; that's fine — env vars can be set manually
    pass


def main():
    # Destinatario de prueba (cambiar si se desea enviar a otra dirección)
    test_user_email = os.getenv('TEST_USER_EMAIL', 'test@example.com')

    # Mensajes de prueba
    subject_admin = 'Prueba: copia de notificación (automática)'
    body_admin = 'Este es un correo de prueba para verificar el envío de notificaciones.'
    html_admin = '<p>Este es un <strong>correo de prueba</strong> (notificación al admin).</p>'

    subject_user = 'Prueba: confirmación de inscripción'
    body_user = 'Hola, este es un correo de prueba de confirmación.'
    html_user = '<p>Hola — este es un <em>correo de prueba</em> de confirmación.</p>'

    print('Leyendo configuración SMTP desde variables de entorno (incluye .env si existe)...')
    print(f"SMTP_HOST={os.getenv('SMTP_HOST')}")
    print(f"SMTP_PORT={os.getenv('SMTP_PORT')}")
    print(f"SMTP_USER={'***' if os.getenv('SMTP_USER') else None}")
    print(f"MAIL_TO={os.getenv('MAIL_TO')}")

    ok_admin = send_email(subject_admin, body_admin, html=html_admin)
    print('Resultado envío a admin:', ok_admin)

    if ok_admin:
        print('\nCorreo de notificación al admin enviado correctamente.')
        sys.exit(0)
    else:
        print('\nNo se pudo enviar el correo de notificación al admin. Revisa la configuración SMTP.')
        sys.exit(1)


if __name__ == '__main__':
    main()
