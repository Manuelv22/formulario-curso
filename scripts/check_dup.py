import urllib.request, json

for email in ['prueba@example.com','noexiste@example.com']:
    url = 'http://127.0.0.1:5000/check-duplicate?email=' + urllib.request.quote(email)
    try:
        r = urllib.request.urlopen(url, timeout=5)
        body = r.read().decode()
        parsed = json.loads(body)
        print(email, '->', parsed)
    except Exception as e:
        print('Error querying', email, '->', e)
