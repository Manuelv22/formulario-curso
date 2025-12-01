import sys, traceback
from importlib import import_module
import os, sys

# ensure project root is on sys.path
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

try:
    mod = import_module('app')
    app = getattr(mod, 'app')
    init_db = getattr(mod, 'init_db')
    print('Imported app module OK')
except Exception as e:
    print('Failed to import app:', e)
    traceback.print_exc()
    sys.exit(1)

# Initialize DB (idempotent)
try:
    init_db()
    print('init_db() OK')
except Exception as e:
    print('init_db failed:', e)
    traceback.print_exc()

# debug: print app paths
try:
    print('app.root_path =', app.root_path)
    print('app.template_folder =', app.template_folder)
    import os
    tdir = os.path.join(app.root_path, app.template_folder or 'templates')
    print('templates dir resolved ->', tdir)
    if os.path.isdir(tdir):
        print('templates list:', os.listdir(tdir)[:50])
    else:
        print('templates dir does not exist')
except Exception as e:
    print('Error printing template info:', e)

# Use test client
try:
    client = app.test_client()
    r = client.get('/')
    print('GET / ->', r.status_code)
    if r.status_code != 200:
        print('Response data snippet:', r.data[:2000].decode('utf-8', errors='replace'))

    # admin page (should redirect to login)
    r2 = client.get('/admin', follow_redirects=False)
    print('GET /admin ->', r2.status_code)
    if r2.status_code in (301,302):
        print('Admin redirected to', r2.headers.get('Location'))
    else:
        print('Admin response length', len(r2.data))

    # check-duplicate endpoint
    r3 = client.get('/check-duplicate?email=notexists@example.com')
    print('/check-duplicate ->', r3.status_code, r3.get_json())

except Exception as e:
    print('Test client error:', e)
    traceback.print_exc()
    sys.exit(1)

print('\nDiagnostics complete')
