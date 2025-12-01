from playwright.sync_api import sync_playwright
import time

URL = 'http://127.0.0.1:5000/'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    print('Opening', URL)
    page.goto(URL, timeout=15000)
    # Fill form with a duplicate email/phone that exists in DB
    print('Filling form...')
    page.fill('input[name="nombre"]', 'Prueba')
    page.fill('input[name="apellido"]', 'Duplicado')
    page.fill('input[name="identificacion"]', '99999999-9')
    page.fill('input[name="telefono"]', '56999999999')
    page.fill('input[name="direccion"]', 'Calle Falsa 123')
    page.fill('input[name="email"]', 'prueba_duplicate@example.com')
    page.select_option('select[name="experiencia"]', 'No')
    page.fill('textarea[name="mensaje"]', 'Prueba automatizada para modal de duplicado')

    print('Submitting form...')
    # submit via button
    page.click('form#inscripcionForm button[type="submit"]')

    # Wait for duplicate modal to appear
    try:
        print('Waiting for duplicate modal to show...')
        # wait until the modal element is visible
        page.wait_for_selector('#dupModal', state='visible', timeout=5000)
        print('Duplicate modal is visible')
    except Exception as e:
        print('Modal did not appear:', e)
        browser.close()
        raise SystemExit(1)

    # Close the modal using the dismiss button or close icon
    try:
        # Prefer data-bs-dismiss buttons inside modal
        if page.query_selector('#dupModal [data-bs-dismiss="modal"]'):
            page.click('#dupModal [data-bs-dismiss="modal"]')
        elif page.query_selector('#dupModal .btn-close'):
            page.click('#dupModal .btn-close')
        else:
            # fallback: hide via JS
            page.eval_on_selector('#dupModal', 'el => bootstrap.Modal.getInstance(el).hide()')
    except Exception as e:
        print('Error closing modal:', e)

    # Wait a moment for cleanup and scroll behavior
    time.sleep(1)

    # Check there are no backdrops
    backdrops = page.query_selector_all('.modal-backdrop')
    print('Backdrop count after close:', len(backdrops))

    # Check body doesn't have modal-open
    has_modal_open = page.evaluate("() => document.body.classList.contains('modal-open')")
    print('body.modal-open present after close:', has_modal_open)

    # Check the form is in the viewport
    rect = page.evaluate("() => { const el = document.getElementById('inscripcionForm'); if(!el) return null; const r = el.getBoundingClientRect(); return {top:r.top,bottom:r.bottom,height:r.height,win:window.innerHeight}; }")
    print('Form rect:', rect)
    in_view = False
    if rect:
        try:
            in_view = (rect['top'] < rect['win']) and (rect['bottom'] > 0)
        except Exception:
            in_view = False
    print('Form visible in viewport:', bool(in_view))

    browser.close()
    if not in_view or len(backdrops) != 0 or has_modal_open:
        raise SystemExit(2)
    print('Automated check: OK')
