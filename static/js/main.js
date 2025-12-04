// Pequeñas interacciones: smooth scroll for anchors
document.addEventListener('DOMContentLoaded', function(){
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor){
    anchor.addEventListener('click', function(e){
      var target = document.querySelector(this.getAttribute('href'));
      if(target){
        e.preventDefault();
        target.scrollIntoView({behavior:'smooth', block:'start'});
      }
    });
  });

  // Client-side form validation for better UX
  const form = document.getElementById('inscripcionForm');
  const errorsDiv = document.getElementById('form-errors');

  if (!form) return;

  const validators = {
    nombre: v => /^[A-Za-zÀ-ÖØ-öø-ÿ '\-]{2,60}$/.test(v.trim()),
    apellido: v => /^[A-Za-zÀ-ÖØ-öø-ÿ '\-]{2,60}$/.test(v.trim()),
    telefono: v => { const d=v.replace(/[^0-9]/g,''); return d.length>=8 && d.length<=15 },
    mensaje: v => v.length <= 1000
  };

  // Show errors inline per field
  function clearFieldErrors(){
    ['nombre','apellido','identificacion','telefono','mensaje'].forEach(id => {
      const el = document.getElementById(id);
      const err = document.getElementById('err-' + id);
      if (el) { el.classList.remove('is-invalid'); el.classList.remove('is-valid'); }
      if (err) { err.textContent = ''; }
      const st = document.getElementById('status-' + id);
      if (st){ const i = st.querySelector('.bi'); if (i) i.className = 'bi'; }
    });
    if (errorsDiv) errorsDiv.innerHTML = '';
  }

  function showFieldErrors(map){
    // map: { fieldName: [message,...], _global: [...] }
    clearFieldErrors();
    let any=false;
    Object.keys(map||{}).forEach(k => {
      if (k === '_global') return;
      const messages = map[k];
      const el = document.getElementById(k);
      const err = document.getElementById('err-' + k);
      if (messages && messages.length){
        any = true;
        if (el) el.classList.add('is-invalid');
        if (err) err.textContent = messages.join(' ');
        const st = document.getElementById('status-' + k);
        if (st){ const i = st.querySelector('.bi'); if (i) i.className = 'bi bi-x-circle-fill'; }
      } else {
        if (el) el.classList.add('is-valid');
        const st = document.getElementById('status-' + k);
        if (st){ const i = st.querySelector('.bi'); if (i) i.className = 'bi bi-check-circle-fill'; }
      }
    });
    // global messages (non-field specific)
    if (map && map._global && map._global.length && errorsDiv){
      const wrapper = document.createElement('div');
      wrapper.className = 'alert alert-danger';
      const ul = document.createElement('ul');
      map._global.forEach(m => { const li = document.createElement('li'); li.textContent = m; ul.appendChild(li); });
      wrapper.appendChild(ul);
      errorsDiv.appendChild(wrapper);
      wrapper.scrollIntoView({behavior:'smooth', block:'center'});
      any = true;
    }
    return any;
  }

  form.addEventListener('submit', function(e){
    const data = new FormData(form);
    const fieldErrors = {};

    const nombre = (data.get('nombre')||'').toString();
    const apellido = (data.get('apellido')||'').toString();
    const telefono = (data.get('telefono')||'').toString();
    const mensaje = (data.get('mensaje')||'').toString();

    if (!validators.nombre(nombre)) fieldErrors.nombre = ['Nombre inválido (2-60 letras).'];
    if (!validators.apellido(apellido)) fieldErrors.apellido = ['Apellido inválido (2-60 letras).'];
    if (!validators.telefono(telefono)) fieldErrors.telefono = ['Teléfono inválido (8-15 dígitos).'];
    if (mensaje.length > 1000) fieldErrors.mensaje = ['Mensaje demasiado largo (máx. 1000 caracteres).'];

    if (Object.keys(fieldErrors).length){
      e.preventDefault();
      showFieldErrors(fieldErrors);
      return false;
    }

    // Before submitting, check duplicates on server (only telefono now)
    e.preventDefault();
    const telefonoVal = telefono;
    fetch('/check-duplicate?telefono=' + encodeURIComponent(telefonoVal))
      .then(r => r.json())
      .then(json => {
        const dupMap = {};
        if (json.exists_phone) dupMap.telefono = ['Ya existe una inscripción con ese teléfono.'];
        if (Object.keys(dupMap).length){
          const msgs = [];
          if (dupMap.telefono) msgs.push(dupMap.telefono.join(' '));
          showDupModal(msgs, 'telefono');
          return;
        }
        form.submit();
      })
      .catch(() => { form.submit(); });
    return false;
  });

  // Clear errors as user types
  form.querySelectorAll('input,textarea,select').forEach(input => {
    input.addEventListener('input', () => {
      const id = input.id;
      const err = document.getElementById('err-' + id);
      if (err) err.textContent = '';
      input.classList.remove('is-invalid');
      input.classList.remove('is-valid');
      if (errorsDiv) errorsDiv.innerHTML = '';
    });
  });

  // Also check duplicates on blur for immediate feedback
  const telefonoInput = document.getElementById('telefono');
  // doDupCheck accepts optional field key to focus afterwards ('email' or 'telefono')
  let dupFocusField = null;
  function doDupCheck(fieldKey){
    const telefonoVal = (telefonoInput && telefonoInput.value) ? telefonoInput.value.trim() : '';
    if (!telefonoVal) return;
    fetch('/check-duplicate?telefono=' + encodeURIComponent(telefonoVal))
      .then(r => r.json())
      .then(json => {
        const dupErrors = [];
        if (json.exists_phone) dupErrors.push('Ya existe una inscripción con ese teléfono.');
        if (dupErrors.length) showDupModal(dupErrors, fieldKey);
      }).catch(()=>{});
  }
  if (telefonoInput) telefonoInput.addEventListener('blur', function(){ doDupCheck('telefono'); });

  // character counter for mensaje
  const msg = document.getElementById('mensaje');
  const msgCount = document.getElementById('msg-count');
  if (msg && msgCount){
    function updateCounter(){
      const len = msg.value.length;
      msgCount.textContent = `${len} / ${msg.getAttribute('maxlength') || 1000}`;
      if (len > (msg.getAttribute('maxlength') || 1000)) msg.classList.add('is-invalid');
      else msg.classList.remove('is-invalid');
    }
    msg.addEventListener('input', updateCounter);
    // initialize
    updateCounter();
  }

  // Helper to show duplicate modal
  function showDupModal(messages, focusField){
    try{
      dupFocusField = focusField || null;
      const dupBody = document.getElementById('dupModalBody');
      if (dupBody) dupBody.textContent = messages.join('\n');
      const dupEl = document.getElementById('dupModal');
      const dupEditBtn = document.getElementById('dupEditBtn');
      if (dupEditBtn){
        if (dupFocusField){
          // configure edit button label
          const label = dupFocusField === 'email' ? 'Editar correo' : (dupFocusField === 'telefono' ? 'Editar teléfono' : 'Editar');
          dupEditBtn.textContent = label;
          dupEditBtn.classList.remove('d-none');
          // set click handler to clear and focus field
          dupEditBtn.onclick = function(){
            const target = document.getElementById(dupFocusField);
            if (target){ target.value = ''; target.focus(); }
            // hide button after use
            dupEditBtn.classList.add('d-none');
            dupEditBtn.onclick = null;
            // also clear inline error for that field
            const err = document.getElementById('err-' + dupFocusField);
            if (err) err.textContent = '';
            const el = document.getElementById(dupFocusField);
            if (el){ el.classList.remove('is-invalid'); el.classList.remove('is-valid'); }
            // close modal
            const bm = bootstrap.Modal.getInstance(dupEl);
            if (bm) bm.hide();
          };
        } else {
          dupEditBtn.classList.add('d-none');
          dupEditBtn.onclick = null;
        }
      }
      if (dupEl){
        const m = new bootstrap.Modal(dupEl);
        m.show();
        // when modal hidden, ensure we remove any leftover backdrop and body class
        // and scroll to top so the full home is visible. Do NOT auto-focus the
        // duplicated field on close (the 'Editar' button handles focusing).
        dupEl.addEventListener('hidden.bs.modal', function handler(){
          try{
            // remove leftover backdrops if any
            document.querySelectorAll('.modal-backdrop').forEach(b => b.remove());
            // ensure body doesn't keep modal-open
            if (document.body.classList.contains('modal-open')) document.body.classList.remove('modal-open');
            // dispose the bootstrap modal instance to free internal state
            try{ m.dispose(); }catch(e){}
            // scroll to top so the hero/home is visible again, then focus the form
            try{ 
              window.scrollTo({ top: 0, behavior: 'smooth' }); 
              // after a short delay, scroll the form into view and focus its first control
              setTimeout(function(){
                const formEl = document.getElementById('inscripcionForm');
                if (formEl){
                  try{ formEl.scrollIntoView({ behavior: 'smooth', block: 'center' }); }catch(e){}
                  const first = formEl.querySelector('input,textarea,select,button');
                  if (first) try{ first.focus(); }catch(e){}
                }
              }, 450);
            }catch(e){}
          }catch(e){ console.warn('error during modal hidden cleanup', e); }
          dupEl.removeEventListener('hidden.bs.modal', handler);
        });
      }
    }catch(e){ console.warn('dup modal failed', e); }
  }

  // Convert any existing server flashes into modals: success -> successModal, duplicate danger -> dupModal
  try{
    const successAlert = document.querySelector('.alert.alert-success');
    if (successAlert){
      const message = successAlert.textContent.trim();
      const modalBody = document.getElementById('successModalBody');
      if (modalBody) modalBody.textContent = message;
      const successModalEl = document.getElementById('successModal');
      if (successModalEl){
        const modal = new bootstrap.Modal(successModalEl);
        modal.show();
      }
      successAlert.remove();
    }

    // check for duplicate flash messages that the server may have emitted
    const dangerAlerts = Array.from(document.querySelectorAll('.alert.alert-danger'));
    dangerAlerts.forEach(alertEl => {
      const txt = (alertEl.textContent || '').toLowerCase();
      if (txt.includes('ya existe una inscripción')){
        // show duplicate modal with the message(s) and try to detect which field
        const lines = txt.split(/\n|\r|\.|\!|\?/).map(s=>s.trim()).filter(Boolean);
        let focus = null;
        if (txt.includes('correo') || txt.includes('email')) focus = 'email';
        else if (txt.includes('tel') || txt.includes('telefono')) focus = 'telefono';
        showDupModal(lines, focus);
        alertEl.remove();
      }
    });
  }catch(e){console.warn('modal init failed', e)}
});
