#!/usr/bin/env python3
import urllib.request, urllib.parse, sqlite3, sys, time

url = 'http://127.0.0.1:5000/'
data = {
    'nombre': 'Prueba',
    'apellido': 'Automatica',
    'identificacion': '11111111-1',
    'telefono': '56912345678',
    'direccion': 'Prueba 123',
    'email': 'prueba@example.com',
    'experiencia': 'No',
    'mensaje': 'Envio de prueba desde script'
}

post = urllib.parse.urlencode(data).encode()

print('Posting to', url)
try:
    req = urllib.request.Request(url, data=post)
    resp = urllib.request.urlopen(req, timeout=10)
    print('POST HTTP code:', resp.getcode())
except Exception as e:
    print('POST failed:', repr(e))
    # Continue to check DB even if POST failed

# small wait to ensure server wrote to DB
time.sleep(0.5)

db_path = 'registrations.db'
print('Checking DB at', db_path)
try:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id,nombre,apellido,identificacion,telefono,email,experiencia,mensaje,created_at FROM registrations ORDER BY id DESC LIMIT 3")
    rows = c.fetchall()
    if rows:
        print('Last rows:')
        for r in rows:
            print(r)
    else:
        print('DB empty or table missing')
    conn.close()
except Exception as e:
    print('DB check failed:', repr(e))
    sys.exit(2)

print('Done')
