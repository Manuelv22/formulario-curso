from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import smtplib
from email.message import EmailMessage
import os
import sqlite3
from datetime import datetime
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Use SECRET_KEY from environment in production; fall back to a dev value
app.secret_key = os.getenv('SECRET_KEY', 'cambio-secreto-123')  # Cambia esto en producción
DB_PATH = os.path.join(os.path.dirname(__file__), "registrations.db")


def send_email(subject: str, body: str, html: str = None, to_addrs=None) -> bool:
    """
    Send an email using SMTP server configured via environment variables:
    SMTP_HOST, SMTP_PORT (int), SMTP_USER, SMTP_PASS, MAIL_TO (comma-separated)
    Returns True on success, False on failure.
    """
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    mail_to = os.getenv('MAIL_TO')
    mail_from = os.getenv('MAIL_FROM', smtp_user)

    if not smtp_host or not smtp_user or not smtp_pass or not mail_to:
        app.logger.warning('SMTP not configured fully; skipping sending email')
        return False

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = mail_from
        recipients = to_addrs if to_addrs is not None else [m.strip() for m in mail_to.split(',')]
        msg['To'] = ', '.join(recipients)
        msg.set_content(body)
        if html:
            msg.add_alternative(html, subtype='html')

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        app.logger.info('Notification email sent to %s', recipients)
        return True
    except Exception as e:
        app.logger.exception('Failed to send email: %s', e)
        return False


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            apellido TEXT,
            identificacion TEXT,
            telefono TEXT,
            direccion TEXT,
            email TEXT,
            experiencia TEXT,
            mensaje TEXT,
            created_at TEXT
        )
    ''')
    # users table for admin access
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            is_super INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()


def valid_email(email: str) -> bool:
    # Simple but practical regex for common emails
    pattern = r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def valid_phone(phone: str) -> bool:
    # Allow + and digits, length between 8 and 15 digits (after removing non-digits)
    digits = re.sub(r"[^0-9]", "", phone)
    return 8 <= len(digits) <= 15


def valid_name(name: str) -> bool:
    # Allow letters, spaces and common punctuation in names
    return 2 <= len(name) <= 60 and re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s'-]+$", name)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        identificacion = request.form.get("identificacion", "").strip()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()
        email = request.form.get("email", "").strip()
        experiencia = request.form.get("experiencia", "").strip()
        mensaje = request.form.get("mensaje", "").strip()

        errors = []

        # Required fields
        if not nombre:
            errors.append("El nombre es obligatorio.")
        elif not valid_name(nombre):
            errors.append("Nombre inválido. Sólo letras y espacios, 2-60 caracteres.")

        if not apellido:
            errors.append("El apellido es obligatorio.")
        elif not valid_name(apellido):
            errors.append("Apellido inválido. Sólo letras y espacios, 2-60 caracteres.")

        if not telefono:
            errors.append("El teléfono es obligatorio.")
        elif not valid_phone(telefono):
            errors.append("Teléfono inválido. Use sólo números y opcionalmente '+', 8-15 dígitos.")

        if not email:
            errors.append("El correo electrónico es obligatorio.")
        elif not valid_email(email):
            errors.append("Correo electrónico inválido.")

        # Length constraints
        if len(direccion) > 200:
            errors.append("La dirección es demasiado larga (máx. 200 caracteres).")
        if len(mensaje) > 1000:
            errors.append("El mensaje es demasiado largo (máx. 1000 caracteres).")

        if errors:
            for e in errors:
                flash(e, "danger")
            return redirect(url_for("index") + "#formulario")

        # Check current registrations count and duplicates (email or telefono)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM registrations')
        current_count = c.fetchone()[0] or 0
        # Allow disabling the registration limit via environment variable
        enable_limit = os.getenv('ENABLE_REGISTRATION_LIMIT', '1')
        try:
            enable_limit_bool = str(enable_limit).lower() not in ('0', 'false', 'no', 'off')
        except Exception:
            enable_limit_bool = True
        LIMIT = int(os.getenv('REGISTRATION_LIMIT', '30'))
        if enable_limit_bool and current_count >= LIMIT:
            conn.close()
            flash(f"Lo sentimos — ya se alcanzó el límite de {LIMIT} inscripciones. No se aceptan más.", "warning")
            return redirect(url_for("index") + "#formulario")
        dup_msgs = []
        if email:
            c.execute("SELECT id FROM registrations WHERE lower(email)=lower(?) LIMIT 1", (email,))
            if c.fetchone():
                dup_msgs.append("Ya existe una inscripción con ese correo electrónico.")
        if telefono:
            c.execute("SELECT id FROM registrations WHERE telefono=? LIMIT 1", (telefono,))
            if c.fetchone():
                dup_msgs.append("Ya existe una inscripción con ese teléfono.")

        if dup_msgs:
            conn.close()
            for m in dup_msgs:
                flash(m, "danger")
            return redirect(url_for("index") + "#formulario")

        # All validations passed; insert into DB
        c.execute('''
            INSERT INTO registrations (nombre, apellido, identificacion, telefono, direccion, email, experiencia, mensaje, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nombre, apellido, identificacion, telefono, direccion, email, experiencia, mensaje, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()

        # send notification email (best-effort)

        created_at = datetime.utcnow().isoformat()

        # Render email templates (HTML) and plain bodies
        try:
            notif_html = render_template('email/notification.html', nombre=nombre, apellido=apellido, identificacion=identificacion, telefono=telefono, direccion=direccion, email=email, experiencia=experiencia, mensaje=mensaje, created_at=created_at)
            conf_html = render_template('email/confirmation.html', nombre=nombre, apellido=apellido, telefono=telefono, email=email, experiencia=experiencia, mensaje=mensaje)
            notif_body = f"Nueva inscripción: {nombre} {apellido} ({email})\nFecha: {created_at}\n\nMensaje:\n{mensaje}"
            conf_body = f"Hola {nombre} {apellido},\n\nHemos recibido tu inscripción. Gracias."
        except Exception:
            # Fallback plain text
            notif_html = None
            conf_html = None
            notif_body = f"Nueva inscripción: {nombre} {apellido} ({email})\nFecha: {created_at}\n\nMensaje:\n{mensaje}"
            conf_body = f"Hola {nombre} {apellido},\n\nHemos recibido tu inscripción. Gracias."

        # Send notification to configured admin recipient(s)
        sent_admin = send_email(f"Nueva inscripción: {nombre} {apellido}", notif_body, html=notif_html)

        # Note: confirmation email to the registrant has been disabled.
        if not sent_admin:
            flash('Inscripción guardada pero no se pudo enviar notificación por correo (configurar SMTP).', 'warning')

        flash("Gracias por inscribirte. Tu inscripción fue recibida.", "success")
        return redirect(url_for("index") + "#formulario")

    # GET — fetch current count so the template can show status/disable form when full
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM registrations')
    current_count = c.fetchone()[0] or 0
    conn.close()
    # If the limit feature is disabled, pass None so template shows form normally
    enable_limit = os.getenv('ENABLE_REGISTRATION_LIMIT', '1')
    enable_limit_bool = str(enable_limit).lower() not in ('0', 'false', 'no', 'off')
    LIMIT = int(os.getenv('REGISTRATION_LIMIT', '30')) if enable_limit_bool else None
    return render_template("index.html", registrations_count=current_count, registrations_limit=LIMIT)


@app.route('/check-duplicate', methods=['GET'])
def check_duplicate():
    email = request.args.get('email', '').strip()
    telefono = request.args.get('telefono', '').strip()
    exists_email = False
    exists_phone = False
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if email:
            c.execute("SELECT id FROM registrations WHERE lower(email)=lower(?) LIMIT 1", (email,))
            exists_email = c.fetchone() is not None
        if telefono:
            c.execute("SELECT id FROM registrations WHERE telefono=? LIMIT 1", (telefono,))
            exists_phone = c.fetchone() is not None
        conn.close()
    except Exception:
        # On error, return conservative false positives as False
        exists_email = False
        exists_phone = False

    return jsonify({
        'exists_email': exists_email,
        'exists_phone': exists_phone
    })


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, password_hash, is_super FROM users WHERE username=? LIMIT 1', (username,))
        row = c.fetchone()
        conn.close()
        if row and check_password_hash(row[1], password):
            session['admin_logged'] = True
            session['admin_user'] = username
            flash('Ingreso exitoso.', 'success')
            return redirect(url_for('admin_panel'))
        else:
            flash('Usuario o contraseña inválidos.', 'danger')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged', None)
    session.pop('admin_user', None)
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('index'))


@app.route('/admin')
@login_required
def admin_panel():
    # show registrations
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id,nombre,apellido,identificacion,telefono,direccion,email,experiencia,mensaje,created_at FROM registrations ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    return render_template('admin_panel.html', rows=rows)


@app.route('/admin/delete/<int:reg_id>', methods=['POST'])
@login_required
def admin_delete(reg_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM registrations WHERE id=?', (reg_id,))
    conn.commit()
    conn.close()
    flash('Registro eliminado.', 'info')
    # if request is fetch/ajax, return json
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'ok': True})
    return redirect(url_for('admin_panel'))


@app.route('/admin/edit/<int:reg_id>', methods=['GET', 'POST'])
@login_required
def admin_edit(reg_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        nombre = request.form.get('nombre','').strip()
        apellido = request.form.get('apellido','').strip()
        identificacion = request.form.get('identificacion','').strip()
        telefono = request.form.get('telefono','').strip()
        direccion = request.form.get('direccion','').strip()
        email = request.form.get('email','').strip()
        experiencia = request.form.get('experiencia','').strip()
        mensaje = request.form.get('mensaje','').strip()

        # Server-side validation
        errors = []
        if not nombre or not valid_name(nombre):
            errors.append('Nombre inválido. Sólo letras y espacios, 2-60 caracteres.')
        if not apellido or not valid_name(apellido):
            errors.append('Apellido inválido. Sólo letras y espacios, 2-60 caracteres.')
        if telefono and not valid_phone(telefono):
            errors.append('Teléfono inválido. Use sólo números y opcionalmente "+", 8-15 dígitos.')
        if not email or not valid_email(email):
            errors.append('Correo electrónico inválido.')
        if len(direccion) > 200:
            errors.append('La dirección es demasiado larga (máx. 200 caracteres).')
        if len(mensaje) > 1000:
            errors.append('El mensaje es demasiado largo (máx. 1000 caracteres).')

        if errors:
            for e in errors:
                flash(e, 'danger')
            # preserve entered values in the form
            # fetch created_at to mimic original row shape
            c.execute('SELECT created_at FROM registrations WHERE id=?', (reg_id,))
            created_at_row = c.fetchone()
            created_at = created_at_row[0] if created_at_row else ''
            row = (reg_id, nombre, apellido, identificacion, telefono, direccion, email, experiencia, mensaje, created_at)
            conn.close()
            return render_template('admin_edit.html', row=row)

        # All validations passed; update DB
        c.execute('''
            UPDATE registrations SET nombre=?, apellido=?, identificacion=?, telefono=?, direccion=?, email=?, experiencia=?, mensaje=? WHERE id=?
        ''', (nombre, apellido, identificacion, telefono, direccion, email, experiencia, mensaje, reg_id))
        conn.commit()
        conn.close()
        flash('Registro actualizado.', 'success')
        return redirect(url_for('admin_panel'))
    else:
        c.execute('SELECT id,nombre,apellido,identificacion,telefono,direccion,email,experiencia,mensaje,created_at FROM registrations WHERE id=?', (reg_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            flash('Registro no encontrado.', 'warning')
            return redirect(url_for('admin_panel'))
        return render_template('admin_edit.html', row=row)


@app.route('/admin/api/row/<int:reg_id>')
@login_required
def admin_row_api(reg_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id,nombre,apellido,identificacion,telefono,direccion,email,experiencia,mensaje,created_at FROM registrations WHERE id=?', (reg_id,))
    r = c.fetchone()
    conn.close()
    if not r:
        return jsonify({'ok': False, 'error': 'not_found'}), 404
    keys = ['id','nombre','apellido','identificacion','telefono','direccion','email','experiencia','mensaje','created_at']
    return jsonify({k: r[i] for i,k in enumerate(keys)})


@app.route('/admin/api/edit/<int:reg_id>', methods=['POST'])
@login_required
def admin_edit_api(reg_id):
    data = request.get_json() or {}
    nombre = data.get('nombre','').strip()
    apellido = data.get('apellido','').strip()
    identificacion = data.get('identificacion','').strip()
    telefono = data.get('telefono','').strip()
    direccion = data.get('direccion','').strip()
    email = data.get('email','').strip()
    experiencia = data.get('experiencia','').strip()
    mensaje = data.get('mensaje','').strip()
    errors = []
    if not nombre or not valid_name(nombre):
        errors.append('nombre')
    if not apellido or not valid_name(apellido):
        errors.append('apellido')
    if telefono and not valid_phone(telefono):
        errors.append('telefono')
    if not email or not valid_email(email):
        errors.append('email')
    if errors:
        return jsonify({'ok': False, 'error': 'validation', 'fields': errors}), 400
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE registrations SET nombre=?, apellido=?, identificacion=?, telefono=?, direccion=?, email=?, experiencia=?, mensaje=? WHERE id=?
    ''', (nombre, apellido, identificacion, telefono, direccion, email, experiencia, mensaje, reg_id))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@app.route('/admin/export')
@login_required
def admin_export():
    import csv
    from io import StringIO
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id,nombre,apellido,identificacion,telefono,direccion,email,experiencia,mensaje,created_at FROM registrations ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['id','nombre','apellido','identificacion','telefono','direccion','email','experiencia','mensaje','created_at'])
    for r in rows:
        writer.writerow(r)
    output = si.getvalue()
    from flask import Response
    res = Response(output, mimetype='text/csv')
    res.headers['Content-Disposition'] = 'attachment; filename=inscripciones.csv'
    return res


if __name__ == "__main__":
    init_db()
    # Read debug and port from environment for flexibility in production
    debug_env = os.getenv('FLASK_DEBUG', 'False').lower()
    debug = debug_env in ('1', 'true', 'yes')
    port = int(os.getenv('PORT', '5000'))
    app.run(host='0.0.0.0', port=port, debug=debug)

# Expose WSGI application variable for hosts like PythonAnywhere
application = app
