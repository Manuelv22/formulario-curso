import getpass
import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'registrations.db')
DB_PATH = os.path.normpath(DB_PATH)

if __name__ == '__main__':
    username = input('Usuario (ej: admin): ').strip()
    if not username:
        print('Usuario no puede estar vacío')
        raise SystemExit(1)
    pwd = getpass.getpass('Contraseña: ')
    pwd2 = getpass.getpass('Confirmar contraseña: ')
    if pwd != pwd2:
        print('Contraseñas no coinciden')
        raise SystemExit(1)
    ph = generate_password_hash(pwd)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (username, password_hash, is_super) VALUES (?,?,1)', (username, ph))
    conn.commit()
    conn.close()
    print('Superusuario creado (o ya existía).')
