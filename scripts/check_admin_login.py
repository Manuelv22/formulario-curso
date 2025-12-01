import sys, os
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
from importlib import import_module
mod = import_module('app')
app = mod.app
client = app.test_client()
resp = client.get('/admin/login')
print('GET /admin/login ->', resp.status_code)
print('Content length:', len(resp.data))
print(resp.data.decode('utf-8', errors='replace')[:2000])
