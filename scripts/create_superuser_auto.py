import sqlite3, os, secrets
from werkzeug.security import generate_password_hash

DB_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'registrations.db'))
username = 'admin'
password = secrets.token_urlsafe(10)
ph = generate_password_hash(password)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
# insert or replace: if user exists, update password and set is_super
c.execute('SELECT id FROM users WHERE username=?', (username,))
row = c.fetchone()
if row:
    c.execute('UPDATE users SET password_hash=?, is_super=1 WHERE username=?', (ph, username))
else:
    c.execute('INSERT INTO users (username, password_hash, is_super) VALUES (?,?,1)', (username, ph))
conn.commit()
conn.close()
print('Superusuario creado/actualizado:')
print('username:', username)
print('password:', password)
print('Por seguridad, cambia esta contraseña después ejecutando scripts/create_superuser.py si lo prefieres.')
