(function(){
  function buildMatrix(container, rows, cols){
    container.innerHTML = '';
    const table = document.createElement('table');
    table.className = 'matriz editable';
    for(let i=0;i<rows;i++){
      const tr = document.createElement('tr');
      for(let j=0;j<cols;j++){
        const td = document.createElement('td');
        const input = document.createElement('input');
        input.type = 'text';
        input.inputMode = 'numeric';
        input.placeholder = '0';
        td.appendChild(input);
        tr.appendChild(td);
      }
      table.appendChild(tr);
    }
    container.appendChild(table);
  }

  function serializeMatrix(table){
    const rows = [];
    table.querySelectorAll('tr').forEach(tr=>{
      const row = [];
      tr.querySelectorAll('input').forEach(inp=>{
        const val = inp.value.trim();
        row.push(val || '0');
      })
      rows.push(row.join(' '));
    });
    return rows.join('\n');
  }

  // --- Persistencia del estado del formulario (para no perder inputs) ---
  function getStateKey(form){
    return `lin-alg:form:${location.pathname}`;
  }
  function saveFormState(form){
    try{
      const key = getStateKey(form);
      const state = { controls:{}, matrices:{} };
      form.querySelectorAll('[data-target]').forEach(el=>{
        const k = el.getAttribute('data-target');
        if(k) state.controls[k] = el.value;
      });
      form.querySelectorAll('.matrix').forEach(box=>{
        const name = box.getAttribute('data-name');
        const table = box.querySelector('table');
        if(!name || !table) return;
        const rows = Array.from(table.querySelectorAll('tr'));
        const values = rows.map(tr=> Array.from(tr.querySelectorAll('input')).map(inp=> inp.value || ''));
        const cols = values.length ? values[0].length : 0;
        state.matrices[name] = { rows: rows.length, cols, values };
      });
      localStorage.setItem(key, JSON.stringify(state));
    }catch(e){ /* no-op */ }
  }
  function loadFormState(form){
    const key = getStateKey(form);
    let raw = null; try{ raw = localStorage.getItem(key); }catch(e){ raw = null; }
    if(!raw) return;
    try{
      const state = JSON.parse(raw);
      if(state && state.controls){
        Object.keys(state.controls).forEach(k=>{
          const el = form.querySelector(`[data-target="${k}"]`);
          if(el) el.value = state.controls[k];
        });
      }
      const resizeBtn = form.querySelector('[data-action="resize"]');
      resizeBtn?.click();
      setTimeout(()=>{
        if(state && state.matrices){
          Object.keys(state.matrices).forEach(name=>{
            const box = form.querySelector(`.matrix[data-name="${name}"]`);
            if(!box) return;
            const mat = state.matrices[name];
            const table = box.querySelector('table');
            const currentRows = table ? table.querySelectorAll('tr').length : 0;
            const currentCols = table ? (table.querySelector('tr')?.querySelectorAll('input').length || 0) : 0;
            if(currentRows !== mat.rows || currentCols !== mat.cols){
              buildMatrix(box, mat.rows, mat.cols);
            }
            const trs = box.querySelectorAll('tr');
            for(let i=0;i<mat.rows;i++){
              const inputs = trs[i]?.querySelectorAll('input') || [];
              for(let j=0;j<mat.cols;j++){
                if(inputs[j]) inputs[j].value = mat.values[i]?.[j] ?? '';
              }
            }
          });
        }
        updateHidden(form);
      }, 0);
    }catch(e){ /* no-op */ }
  }

  function updateHidden(form){
    form.querySelectorAll('.matrix').forEach(box=>{
      const name = box.getAttribute('data-name');
      const table = box.querySelector('table');
      if(!name || !table) return;
      const hidden = form.querySelector(`input[name="${name}"]`);
      if(hidden) hidden.value = serializeMatrix(table);
    });
    if(form.dataset.mode === 'aug'){
      // compose matrizAug from matrizA and vectorB adding a pipe
      const A = form.querySelector('input[name="matrizA"]').value.split('\n');
      const b = form.querySelector('input[name="vectorB"]').value.split('\n');
      const rows = Math.max(A.length, b.length);
      const out = [];
      for(let i=0;i<rows;i++){
        const left = (A[i]||'').trim();
        const right = (b[i]||'').trim();
        out.push(`${left} | ${right}`.trim());
      }
      const hiddenAug = form.querySelector('input[name="matrizAug"]');
      if(hiddenAug) hiddenAug.value = out.join('\n');
    }
  }
  function initForm(form){
    const mode = form.dataset.mode;
    const matrices = form.querySelectorAll('.matrix');
    const resizeBtn = form.querySelector('[data-action="resize"]');
    function doResize(){
      if(mode === 'sum'){
        const r = +form.querySelector('[data-target="rows"]').value || 2;
        const c = +form.querySelector('[data-target="cols"]').value || 2;
        matrices.forEach(box=>{
          const cols = +box.getAttribute('data-cols') || c;
          buildMatrix(box, r, cols);
        });
      } else if(mode === 'mul'){
        const rA = +form.querySelector('[data-target="rowsA"]').value || 2;
        const pc = +form.querySelector('[data-target="colsArowsB"]').value || 2;
        const colsBInput = form.querySelector('[data-target="colsB"]');
        let cB = +(colsBInput?.value) || 2;
        const symbolicChk = form.querySelector('input[name="vector_symbolic"]');
        const [boxA, boxB] = matrices;
        buildMatrix(boxA, rA, pc);
        if(symbolicChk && symbolicChk.checked){
          cB = 1; // vector columna
          if(colsBInput){
            colsBInput.value = '1';
            colsBInput.disabled = true;
            colsBInput.title = 'Bloqueado: vector simbólico fuerza 1 columna en B';
          }
        } else {
          if(colsBInput){
            colsBInput.disabled = false;
            colsBInput.title = '';
          }
        }
        buildMatrix(boxB, pc, cB);
        if(symbolicChk && symbolicChk.checked){
          // Colocar placeholders x1, x2, ... por fila
          let idx = 1;
          [...boxB.querySelectorAll('tr')].forEach(tr=>{
            const inp = tr.querySelector('input');
            if(inp){ inp.placeholder = 'x' + (idx++); inp.inputMode = 'text'; }
          });
        }
      } else if(mode === 'cramer'){
        // Cramer: A es n×n y b es n×1. El control data-target="rowsAcolsArowsB" define n.
        const nCtl = form.querySelector('[data-target="rowsAcolsArowsB"]');
        const n = +(nCtl?.value) || 2;
        const [boxA, boxb] = matrices;
        if(boxA) buildMatrix(boxA, n, n);
        if(boxb){ boxb.setAttribute('data-cols','1'); buildMatrix(boxb, n, 1); }
      } else if(mode === 'aug'){
        const r = +form.querySelector('[data-target="rows"]').value || 2;
        const c = +form.querySelector('[data-target="cols"]').value || 2;
        const [boxA, boxB] = matrices;
        buildMatrix(boxA, r, c);
        boxB.setAttribute('data-cols', '1');
        buildMatrix(boxB, r, 1);
      } else if(mode === 'simple') {
        const r = +form.querySelector('[data-target="rows"]').value || 2;
        const c = +form.querySelector('[data-target="cols"]').value || 2;
        const [boxA] = matrices;
        buildMatrix(boxA, r, c);
        // Render vector solución trivial (ceros) no editable
        const zeroBox = form.querySelector('.zero-vector');
        if(zeroBox){
          zeroBox.innerHTML = '';
          const table = document.createElement('table');
          table.className = 'matriz mini';
          for(let i=0;i<r;i++){
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.textContent = '0';
            tr.appendChild(td);
            table.appendChild(tr);
          }
          zeroBox.appendChild(table);
        }
      }
      else if(mode === 'compuestas'){
        // Construir A y B con controles separados
        const rA = +form.querySelector('[data-target="rows"][data-matrix="A"]').value || 2;
        const cA = +form.querySelector('[data-target="cols"][data-matrix="A"]').value || 2;
        const rB = +form.querySelector('[data-target="rows"][data-matrix="B"]').value || 2;
        const cB = +form.querySelector('[data-target="cols"][data-matrix="B"]').value || 2;
        const [boxA, boxB] = matrices;
        if(boxA) buildMatrix(boxA, rA, cA);
        if(boxB) buildMatrix(boxB, rB, cB);
      }
      updateHidden(form);
    }
    doResize();
    if(resizeBtn){
      resizeBtn.addEventListener('click', ()=>{ doResize(); saveFormState(form); });
    }
    form.addEventListener('input', ()=>{ updateHidden(form); saveFormState(form); });
    // En modo compuestas, redimensionar al cambiar cualquier control A/B
    if(mode === 'compuestas'){
      form.querySelectorAll('[data-matrix]').forEach(el=>{
        el.addEventListener('input', ()=>{ doResize(); saveFormState(form); });
        el.addEventListener('change', ()=>{ doResize(); saveFormState(form); });
      });
    }
    form.addEventListener('submit', ()=>{ updateHidden(form); saveFormState(form); });

    // Controls: clear, example, copy-result
    form.querySelectorAll('[data-action="clear"]').forEach(btn=>{
      btn.addEventListener('click', ()=>{
        form.querySelectorAll('.matrix input').forEach(inp=> inp.value='');
        updateHidden(form);
        try{ localStorage.removeItem(getStateKey(form)); }catch(e){}
      });
    });
    form.querySelectorAll('[data-action="example"]').forEach(btn=>{
      btn.addEventListener('click', ()=>{
        const ex = btn.getAttribute('data-example');
        // Generador entero aleatorio entre a y b inclusive
        const rnd = (a,b)=> Math.floor(Math.random()*(b-a+1))+a;
        if(mode==='sum' && ex==='sum'){
          const r = rnd(1,5); const c = rnd(1,5);
          form.querySelector('[data-target="rows"]').value = r;
          form.querySelector('[data-target="cols"]').value = c;
          doResize();
          const [boxA, boxB] = matrices;
          // Relleno secuencial por filas
          let val = 1;
          [...boxA.querySelectorAll('tr')].forEach(tr=> tr.querySelectorAll('input').forEach(inp=> inp.value = String(val++)));
          val = 1;
          [...boxB.querySelectorAll('tr')].forEach(tr=> tr.querySelectorAll('input').forEach(inp=> inp.value = String(val++)));
        }
        if(mode==='mul' && ex==='mul'){
          const rA = rnd(1,5), p = rnd(1,5), cB = rnd(1,5);
          form.querySelector('[data-target="rowsA"]').value = rA;
          form.querySelector('[data-target="colsArowsB"]').value = p;
          form.querySelector('[data-target="colsB"]').value = cB;
          doResize();
          const [boxA, boxB] = matrices;
          let val = 1;
          [...boxA.querySelectorAll('tr')].forEach(tr=> tr.querySelectorAll('input').forEach(inp=> inp.value = String(val++)));
          val = 1;
          [...boxB.querySelectorAll('tr')].forEach(tr=> tr.querySelectorAll('input').forEach(inp=> inp.value = String(val++)));
        }
        if(mode==='aug'){
          // Dimensiones aleatorias y relleno secuencial A y b
          const filas = rnd(1,5);
          const cols = rnd(1,5);
          form.querySelector('[data-target="rows"]').value = filas;
          form.querySelector('[data-target="cols"]').value = cols;
          const [boxA, boxB] = matrices;
          doResize();
          let val = 1;
          [...boxA.querySelectorAll('tr')].forEach(tr=> tr.querySelectorAll('input').forEach(inp=> inp.value = String(val++)));
          [...boxB.querySelectorAll('tr')].forEach(tr=> tr.querySelectorAll('input')[0].value = String(val++));
        }
        if(mode==='cramer'){
          // Ejemplo simple n=3
          const n = 3;
          const nCtl = form.querySelector('[data-target="rowsAcolsArowsB"]');
          if(nCtl) nCtl.value = String(n);
          doResize();
          const [boxA, boxb] = matrices;
          // A: 3x3 con valores secuenciales
          let val = 1;
          if(boxA){
            [...boxA.querySelectorAll('tr')].forEach(tr=> tr.querySelectorAll('input').forEach(inp=> inp.value = String(val++)));
          }
          // b: 3x1 con 1,2,3
          if(boxb){
            let vb = 1;
            [...boxb.querySelectorAll('tr')].forEach(tr=>{ const inp = tr.querySelector('input'); if(inp) inp.value = String(vb++); });
          }
        }
        if(mode==='simple' && ex==='simple'){
          const filas = rnd(1,5);
          const cols = rnd(1,5);
          form.querySelector('[data-target="rows"]').value = filas;
          form.querySelector('[data-target="cols"]').value = cols;
          doResize();
          const [boxA] = matrices;
          let val = 1;
          [...boxA.querySelectorAll('tr')].forEach(tr=> tr.querySelectorAll('input').forEach(inp=> inp.value = String(val++)));
        }
        updateHidden(form);
        saveFormState(form);
      });
    });

  }

  document.addEventListener('DOMContentLoaded', ()=>{
    document.querySelectorAll('form.matrix-form').forEach(initForm);
    // Intentar restaurar el estado guardado (mantiene inputs tras enviar)
    document.querySelectorAll('form.matrix-form').forEach(loadFormState);
    // Mostrar/Ocultar control de precisión según formato de resultado
    document.querySelectorAll('form.matrix-form').forEach(form=>{
      const fmt = form.querySelector('select[name="result_format"]');
      const precInput = form.querySelector('input[name="precision"]');
      if(!fmt || !precInput) return;
      const precCtl = precInput.closest('.control');
      const syncPrec = ()=>{
        if(fmt.value === 'dec') { precCtl.style.display = ''; }
        else { precCtl.style.display = 'none'; }
      };
      syncPrec();
      fmt.addEventListener('change', syncPrec);
    });
    // Sincronizar el toggle de vector simbólico con el tamaño de B y bloquear Columnas(B)
    document.querySelectorAll('form.matrix-form[data-mode="mul"]').forEach(form=>{
      const chk = form.querySelector('input[name="vector_symbolic"]');
      const colsBInput = form.querySelector('[data-target="colsB"]');
      const colsBCtl = colsBInput ? colsBInput.closest('.control') : null;
      if(!chk || !colsBInput) return;
      const resizeBtn = form.querySelector('[data-action="resize"]');
      const syncSymbolic = ()=>{
        if(chk.checked){
          colsBInput.value = '1';
          colsBInput.disabled = true;
          colsBInput.setAttribute('readonly','readonly');
          colsBInput.title = 'Bloqueado: vector simbólico fuerza 1 columna en B';
          if(colsBCtl) colsBCtl.style.display = 'none';
        } else {
          colsBInput.disabled = false;
          colsBInput.removeAttribute('readonly');
          colsBInput.title = '';
          if(colsBCtl) colsBCtl.style.display = '';
        }
        resizeBtn?.click();
      };
      // Si intentan escribir mientras está activo, forzar 1
      colsBInput.addEventListener('input', ()=>{
        if(chk.checked){
          colsBInput.value = '1';
        }
      });
      colsBInput.addEventListener('change', ()=>{
        if(chk.checked){ colsBInput.value = '1'; }
      });
      colsBInput.addEventListener('keydown', (e)=>{
        if(chk.checked){ e.preventDefault(); }
      });
      colsBInput.addEventListener('wheel', (e)=>{
        if(chk.checked){ e.preventDefault(); }
      }, { passive:false });
      chk.addEventListener('change', syncSymbolic);
      // Sincroniza estado inicial al cargar
      syncSymbolic();
    });

    // Guardia adicional: en formularios de multiplicación, si simbólico está activo, mantener colsB=1
    document.querySelectorAll('form.matrix-form[data-mode="mul"]').forEach(form=>{
      const chk = form.querySelector('input[name="vector_symbolic"]');
      const colsBInput = form.querySelector('[data-target="colsB"]');
      if(!chk || !colsBInput) return;
      form.addEventListener('input', ()=>{
        if(chk.checked){ colsBInput.value = '1'; }
      });
    });
    // Toggle switches activation style
    document.querySelectorAll('.toggle input[type="checkbox"]').forEach(chk=>{
      const root = chk.closest('.toggle');
      function sync(){
        if(chk.checked) root.classList.add('active'); else root.classList.remove('active');
      }
      chk.addEventListener('change', sync); sync();
    });
    // Theme toggle (switch)
    // Theme toggle (switch)
    const themeToggle = document.getElementById('themeToggle');
    const root = document.documentElement;
    const saved = localStorage.getItem('theme');
    if(saved && saved==='dark'){ root.setAttribute('data-theme','dark'); }
    themeToggle?.addEventListener('click', ()=>{
      const dark = root.getAttribute('data-theme')==='dark';
      if(dark){ root.removeAttribute('data-theme'); localStorage.setItem('theme','light'); }
      else { root.setAttribute('data-theme','dark'); localStorage.setItem('theme','dark'); }
    });
    // Toggle visual de mostrar/ocultar pasos sin recargar
    document.querySelectorAll('label.toggle input[name="show_steps"]').forEach(chk=>{
      chk.addEventListener('change', ()=>{
        const container = chk.closest('form').parentElement; // paneles estarán después del form
        if(!container) return;
        const stepsPanel = container.querySelector('details.panel, details');
        if(stepsPanel){
          if(chk.checked){ stepsPanel.style.display=''; stepsPanel.open = true; }
          else { stepsPanel.style.display='none'; }
        }
      });
    });

    // Dropdown menu: click-to-toggle for touch/mobile, hover works via CSS on desktop
    (function(){
      const menu = document.querySelector('.menu');
      if(!menu) return;
      const items = menu.querySelectorAll('.menu .has-dropdown');
      function closeAll(except){
        items.forEach(it=>{ if(it!==except) { it.classList.remove('open'); const btn = it.querySelector('.menu-link'); if(btn) btn.setAttribute('aria-expanded','false'); } });
      }
      items.forEach(it=>{
        const btn = it.querySelector('.menu-link');
        btn?.addEventListener('click', (e)=>{
          e.preventDefault();
          const isOpen = it.classList.contains('open');
          closeAll(isOpen ? null : it);
          it.classList.toggle('open');
          btn.setAttribute('aria-expanded', it.classList.contains('open') ? 'true' : 'false');
        });
      });
      document.addEventListener('click', (e)=>{
        const target = e.target;
        if(!menu.contains(target)){ closeAll(null); }
      });
      document.addEventListener('keydown', (e)=>{
        if(e.key === 'Escape'){ closeAll(null); }
      });
    })();

    // Mobile nav toggle (hamburger)
    const navToggle = document.getElementById('navToggle');
    const topbar = document.querySelector('.topbar');
    if(navToggle && topbar){
      navToggle.addEventListener('click', ()=>{
        const open = topbar.classList.toggle('nav-open');
        navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    }

    // Widget opcional: Ingreso de sistema de ecuaciones (para poblar A y b)
    (function(){
      function createSystemWidget(form){
        console.log('[sys-widget] createSystemWidget called for form', form && form.getAttribute ? form.getAttribute('action') || form.getAttribute('class') : form);
        // Panel contenedor
        const panel = document.createElement('section');
        panel.className = 'panel';
        panel.setAttribute('data-system-widget','true');
        panel.setAttribute('aria-labelledby','sys-title');

        // Header con título y toggle
        const header = document.createElement('div'); header.className = 'panel-header';
        const h3 = document.createElement('h3'); h3.className = 'panel-title'; h3.id='sys-title'; h3.textContent = 'Ingresar sistema de ecuaciones (opcional)';
        const actions = document.createElement('div'); actions.className = 'panel-actions';
  const toggle = document.createElement('label'); toggle.className = 'toggle';
  const chk = document.createElement('input'); chk.type='checkbox'; chk.name='system_enabled';
        const track = document.createElement('span'); track.className='toggle-track';
        const thumb = document.createElement('span'); thumb.className='toggle-thumb';
        const lbl = document.createElement('span'); lbl.className='toggle-label'; lbl.textContent='Usar sistema';
        toggle.appendChild(chk); toggle.appendChild(track); toggle.appendChild(thumb); toggle.appendChild(lbl);
        actions.appendChild(toggle);
        header.appendChild(h3); header.appendChild(actions);

        // Cuerpo: instrucciones + controles + grilla
        const body = document.createElement('div'); body.className = 'panel-body';
        const help = document.createElement('p'); help.className='help';
        help.textContent = 'Ingresa un sistema Ax = b. Los números que escribas en la tabla se convertirán en los coeficientes de la matriz A y del vector b.';
        const ctrls = document.createElement('div'); ctrls.className='controls';
        const ctlM = document.createElement('div'); ctlM.className='control';
        const lblM = document.createElement('label'); lblM.textContent='Ecuaciones (m)';
        const inpM = document.createElement('input'); inpM.type='number'; inpM.min='1'; inpM.value='2'; inpM.setAttribute('aria-label','Número de ecuaciones');
        ctlM.appendChild(lblM); ctlM.appendChild(inpM);
        const ctlN = document.createElement('div'); ctlN.className='control';
        const lblN = document.createElement('label'); lblN.textContent='Variables (n)';
        const inpN = document.createElement('input'); inpN.type='number'; inpN.min='1'; inpN.value='2'; inpN.setAttribute('aria-label','Número de variables');
        ctlN.appendChild(lblN); ctlN.appendChild(inpN);
        const btnResize = document.createElement('button'); btnResize.type='button'; btnResize.className='btn'; btnResize.textContent='Actualizar sistema';
        ctrls.appendChild(ctlM); ctrls.appendChild(ctlN); ctrls.appendChild(btnResize);

  const grid = document.createElement('div'); grid.className='sys-grid';

  body.appendChild(help); body.appendChild(ctrls); body.appendChild(grid);

        panel.appendChild(header); panel.appendChild(body);

        // Insertar panel de forma robusta: preferente antes del bloque de matrices; si no, al inicio del form
        const matricesPanel = form.querySelector('.grid.matrices');
        if(matricesPanel && matricesPanel.parentNode){
          matricesPanel.parentNode.insertBefore(panel, matricesPanel);
        } else {
          form.insertBefore(panel, form.firstElementChild || null);
        }

        // Construir N bloques de texto (uno por ecuación). Cada bloque es un textarea
        // donde el usuario puede pegar/editar la ecuación completa.
        // Si hay más de una ecuación, se generan múltiples textareas.
        function buildSysTable(m, n){
          console.log('[sys-widget] buildSysTable m=',m,' n=',n);
          grid.innerHTML = '';
          for(let i=0;i<m;i++){
            const block = document.createElement('div'); block.className = 'sys-block';
            const lbl = document.createElement('label'); lbl.textContent = `Ecuación ${i+1}`;
            const ta = document.createElement('textarea');
            ta.rows = 2;
            ta.className = 'sys-text';
            ta.placeholder = 'Ejemplo: 3 2 -1 | 5   ó   3 x1 + 2 x2 - x3 = 5';
            ta.setAttribute('data-idx', String(i));
            ta.setAttribute('aria-label', `Ecuación ${i+1}: coeficientes y término independiente`);
            block.appendChild(lbl);
            block.appendChild(ta);
            grid.appendChild(block);
          }
        }

        // Serializar textareas a strings para matrizA y vectorB.
        // Se aceptan varios formatos: "a b c | d", "a b c = d", o expresiones con x (se extraen números).
        function parseNumericTokens(s){
          // Encuentra fracciones como -3/2 o números decimales y enteros con signo opcional
          const re = /[-+]?\d+\/\d+|[-+]?\d*\.?\d+/g;
          const matches = s.match(re);
          return matches || [];
        }

        function serializeToHidden(){
          console.log('[sys-widget] serializeToHidden called; enabled=', chk.checked);
          if(!chk.checked) return;
          const textareas = Array.from(grid.querySelectorAll('.sys-text'));
          if(textareas.length === 0) return;
          const m = textareas.length;
          const n = Math.max(1, +inpN.value || 1);
          const A_rows = [];
          const b_rows = [];
          textareas.forEach((ta, idx)=>{
            const raw = (ta.value || '').trim();
            if(raw === ''){
              // fila vacía -> ceros
              A_rows.push(Array(n).fill('0').join(' '));
              b_rows.push('0');
              return;
            }
            // separar por '|' o '=' preferentemente
            let left = raw;
            let right = null;
            if(raw.indexOf('|') >= 0){ const parts = raw.split('|'); left = parts[0]; right = parts.slice(1).join('|'); }
            else if(raw.indexOf('=') >= 0){ const parts = raw.split('='); left = parts[0]; right = parts.slice(1).join('='); }

            // extraer tokens numéricos
            let leftTokens = parseNumericTokens(left);
            let rightTokens = right ? parseNumericTokens(right) : [];

            // Si no hay tokens en left pero hay tokens en todo el string, intentar extraer todos
            if(leftTokens.length === 0){ leftTokens = parseNumericTokens(raw); }

            // Decidir cuáles son coeficientes y cuál el término independiente
            let coeffs = [];
            let bval = '0';
            if(rightTokens.length > 0){ coeffs = leftTokens; bval = rightTokens.join(' '); }
            else if(leftTokens.length >= n + 1){ coeffs = leftTokens.slice(0, n); bval = leftTokens.slice(n).join(' '); }
            else if(leftTokens.length === n){ coeffs = leftTokens; bval = '0'; }
            else {
              // Si hay menos tokens, rellenar con ceros
              coeffs = leftTokens.slice(0, n);
            }
            // Normalizar length of coeffs
            for(let k = coeffs.length; k < n; k++) coeffs.push('0');
            A_rows.push(coeffs.join(' '));
            b_rows.push((bval || '0').toString());
          });

          const A_str = A_rows.join('\n');
          const b_str = b_rows.join('\n');
          const hiddenA = form.querySelector('input[name="matrizA"]'); if(hiddenA) hiddenA.value = A_str;
          const hiddenb = form.querySelector('input[name="vectorB"], input[name="vectorb"]'); if(hiddenb) hiddenb.value = b_str;
          // Si el formulario usa modo aumentado, la función updateHidden creará matrizAug a partir de A y b
          try{ updateHidden(form); }catch(e){}
        }

        // Eventos
        function toggleMatrixInputs(disable){
          // Desactivar/activar todos los inputs dentro de .matrix
          const mats = form.querySelectorAll('.matrix');
          mats.forEach(box=>{
            box.querySelectorAll('input, textarea, select').forEach(el=>{ el.disabled = !!disable; });
          });
        }

        // Mantener la apariencia visual del toggle consistente con otros toggles
        function syncToggleVisual(){
          if(chk.checked) toggle.classList.add('active'); else toggle.classList.remove('active');
        }

        function syncVisibility(){
          console.log('[sys-widget] syncVisibility checked=', chk.checked);
          body.style.display = chk.checked ? '' : 'none';
          panel.setAttribute('data-enabled', chk.checked ? 'true':'false');
          // Visual del toggle
          syncToggleVisual();
          // Cuando está activo, desactivar entradas en las matrices para evitar conflicto
          toggleMatrixInputs(chk.checked);
        }

  chk.addEventListener('change', ()=>{ syncVisibility(); if(chk.checked) serializeToHidden(); else updateHidden(form); });
        btnResize.addEventListener('click', ()=>{ const m = Math.max(1, +inpM.value||2); const n = Math.max(1, +inpN.value||2); buildSysTable(m,n); serializeToHidden(); });
        // Cambios en las textareas
        grid.addEventListener('input', (e)=>{ if(e.target && e.target.classList && e.target.classList.contains('sys-text')) serializeToHidden(); });

        // Inicialización
        syncVisibility();
        buildSysTable(+inpM.value||2, +inpN.value||2);
        // Al enviar, aseguramos override de hidden si está activo
        form.addEventListener('submit', ()=> serializeToHidden());

        return panel;
      }

      // Inyectar en todos los formularios con matrices
      document.querySelectorAll('form.matrix-form').forEach(form=>{
        // Evitar duplicados buscando el atributo del propio widget
        if(form.querySelector('[data-system-widget="true"]')) return;
        createSystemWidget(form);
      });
    })();

    // Composer: bloques arrastrables para Operaciones compuestas
    (function(){
      const page = document.querySelector('[data-page="compuestas"]');
      if(!page) return;
      const palette = page.querySelector('#blocksPalette');
      const canvas = page.querySelector('#sequenceCanvas');
      const list = page.querySelector('#seqList');
      const form = page.querySelector('form.matrix-form');
      const hidden = page.querySelector('#sequenceJson');
      const srcSel = form?.querySelector('select[name="source"]');

      // Helpers para etiquetar según la fuente (A o B)
      function currentSrc(){ return (srcSel?.value === 'B') ? 'B' : 'A'; }
      function typeToLabel(type, src){
        const t = (type||'').toLowerCase();
        if(t === 'transpose') return `Transpuesta (${src}^T)`;
        if(t === 'scale') return `Escalar (c·${src})`;
        if(t === 'lincomb' || t === 'combinacion') return `Combinación lineal (a·A + b·B)`;
        if(t === 'abcomb') return `a·A + b·B`;
    if(t === 'sumb') return `Sumar con B (${src}+B)`;
    if(t === 'sumbesc') return `Sumar b·B (${src} + b·B)`;
        if(t === 'mulb') return `Multiplicar por B (${src}·B)`;
        if(t === 'inverse') return `Inversa (${src}^{-1})`;
        return type;
      }
      function refreshBlockLabels(){
        const src = currentSrc();
        // Actualiza etiquetas de la paleta
  const pT = palette?.querySelector('[data-type="transpose"]'); if(pT) pT.textContent = typeToLabel('transpose', src);
  const pS = palette?.querySelector('[data-type="scale"]'); if(pS) pS.textContent = typeToLabel('scale', src);
  const pAB = palette?.querySelector('[data-type="abcomb"]'); if(pAB) pAB.textContent = typeToLabel('abcomb', src);
  const pSum = palette?.querySelector('[data-type="sumB"]'); if(pSum) pSum.textContent = typeToLabel('sumB', src);
  const pM = palette?.querySelector('[data-type="mulB"]'); if(pM) pM.textContent = typeToLabel('mulB', src);
        const pI = palette?.querySelector('[data-type="inverse"]'); if(pI) pI.textContent = typeToLabel('inverse', src);
        // Actualiza etiquetas de ítems ya añadidos
        list?.querySelectorAll('.seq-item').forEach(item=>{
          const type = item.getAttribute('data-type');
          const labelEl = item.querySelector('.seq-label');
          if(type && labelEl){ labelEl.textContent = typeToLabel(type, src); }
        });
      }

      function createSeqItem(type){
        const li = document.createElement('li');
        li.className = 'seq-item';
        li.setAttribute('data-type', type);

        // Sección izquierda: asa de arrastre + etiqueta + parámetros
        const left = document.createElement('div');
        left.className = 'seq-left';
        const drag = document.createElement('span');
        drag.className = 'seq-drag';
        drag.textContent = '↕';
        drag.setAttribute('title','Arrastrar para reordenar');
        drag.setAttribute('aria-label','Arrastrar para reordenar');
        drag.setAttribute('draggable','true');

        const label = document.createElement('div');
        label.className = 'seq-label';
        const ctrlWrap = document.createElement('div');
        ctrlWrap.className = 'seq-params';

        // Controles a la derecha
        const controls = document.createElement('div');
        controls.className = 'seq-controls';
        const btnUp = document.createElement('button'); btnUp.type='button'; btnUp.className='btn ghost'; btnUp.textContent='↑';
        const btnDown = document.createElement('button'); btnDown.type='button'; btnDown.className='btn ghost'; btnDown.textContent='↓';
        const btnDel = document.createElement('button'); btnDel.type='button'; btnDel.className='btn secondary'; btnDel.textContent='Quitar';

        btnUp.addEventListener('click', ()=>{ const prev = li.previousElementSibling; if(prev){ list.insertBefore(li, prev); sync(); }});
        btnDown.addEventListener('click', ()=>{ const next = li.nextElementSibling?.nextElementSibling; list.insertBefore(li, next || null); sync(); });
        btnDel.addEventListener('click', ()=>{ li.remove(); sync(); });

        let paramInput = null;
        if(type === 'transpose'){
          label.textContent = typeToLabel('transpose', currentSrc());
        } else if(type === 'scale'){
          label.textContent = typeToLabel('scale', currentSrc());
          const p = document.createElement('input'); p.type='text'; p.placeholder='c (ej. 3/5)'; p.setAttribute('data-param','c'); paramInput=p;
          ctrlWrap.appendChild(p);
        } else if(type === 'lincomb' || type === 'combinacion' || type === 'abcomb'){
          label.textContent = typeToLabel('abcomb', currentSrc());
          const a = document.createElement('input'); a.type='text'; a.placeholder='a (ej. 4)'; a.setAttribute('data-param','a');
          const b = document.createElement('input'); b.type='text'; b.placeholder='b (ej. -3/2)'; b.setAttribute('data-param','b');
          ctrlWrap.appendChild(a); ctrlWrap.appendChild(b);
          a.addEventListener('input', sync); b.addEventListener('input', sync);
        } else if(type === 'sumB'){
          label.textContent = typeToLabel('sumB', currentSrc());
        } else if(type === 'sumBesc'){
          label.textContent = typeToLabel('sumBesc', currentSrc());
          const p = document.createElement('input'); p.type='text'; p.placeholder='b (ej. 2/3)'; p.setAttribute('data-param','b'); paramInput=p;
          ctrlWrap.appendChild(p);
        } else if(type === 'mulB'){
          label.textContent = typeToLabel('mulB', currentSrc());
        } else if(type === 'inverse'){
          label.textContent = typeToLabel('inverse', currentSrc());
        } else {
          label.textContent = type;
        }

        left.appendChild(drag);
        left.appendChild(label);
        left.appendChild(ctrlWrap);
        li.appendChild(left);
        controls.appendChild(btnUp); controls.appendChild(btnDown); controls.appendChild(btnDel);
        li.appendChild(controls);

        if(paramInput){ paramInput.addEventListener('input', sync); }

        // Drag&drop de reordenamiento usando el asa
        drag.addEventListener('dragstart', (e)=>{
          li.classList.add('dragging');
          e.dataTransfer?.setData('text/plain', 'reorder');
          try{ e.dataTransfer.effectAllowed = 'move'; }catch(_e){}
        });
        drag.addEventListener('dragend', ()=>{ li.classList.remove('dragging'); });
        return li;
      }

      function serialize(){
        const steps = [];
        list.querySelectorAll('.seq-item').forEach(item=>{
          const type = item.getAttribute('data-type');
          const step = { type, params:{} };
          item.querySelectorAll('[data-param]').forEach(inp=>{ step.params[inp.getAttribute('data-param')] = inp.value; });
          steps.push(step);
        });
        return steps;
      }
      function sync(){
        const seq = serialize();
        if(hidden){ hidden.value = JSON.stringify(seq); }
        // Persistir en localStorage
        try{ localStorage.setItem('lin-alg:compuestas:sequence', hidden.value || '[]'); }catch(e){}
      }
      function restore(){
        let raw = null; try{ raw = localStorage.getItem('lin-alg:compuestas:sequence'); }catch(e){ raw = null; }
        if(!raw) return;
        try{
          const arr = JSON.parse(raw);
          if(Array.isArray(arr)){
            list.innerHTML = '';
            arr.forEach(s=>{
              const li = createSeqItem(s.type);
              // Rellenar parámetros
              li.querySelectorAll('[data-param]').forEach(inp=>{
                const k = inp.getAttribute('data-param');
                if(s.params && s.params[k] != null) inp.value = s.params[k];
              });
              list.appendChild(li);
            });
            sync();
          }
        }catch(e){}
      }

      // Drag desde la paleta
      palette?.querySelectorAll('.block').forEach(el=>{
        el.addEventListener('dragstart', (e)=>{
          e.dataTransfer?.setData('text/plain', el.getAttribute('data-type'));
          e.dataTransfer?.setDragImage?.(el, 10, 10);
        });
        // Fallback: click/tocar para añadir
        el.addEventListener('click', ()=>{
          const type = el.getAttribute('data-type');
          if(!type) return; const li = createSeqItem(type); list.appendChild(li); sync();
        });
        el.addEventListener('keydown', (e)=>{
          if(e.key==='Enter' || e.key===' '){ e.preventDefault(); el.click(); }
        });
      });
      // Cambiar etiquetas cuando varía la fuente inicial (A/B)
      srcSel?.addEventListener('change', refreshBlockLabels);
      // Reordenar elementos existentes de la secuencia con drag&drop
      function getAfterElement(y){
        const items = [...list.querySelectorAll('.seq-item:not(.dragging)')];
        let closest = { offset: Number.NEGATIVE_INFINITY, element: null };
        items.forEach(child=>{
          const box = child.getBoundingClientRect();
          const offset = y - box.top - box.height / 2;
          if(offset < 0 && offset > closest.offset){ closest = { offset, element: child }; }
        });
        return closest.element;
      }
      list.addEventListener('dragover', (e)=>{
        const dragging = list.querySelector('.seq-item.dragging');
        if(!dragging) return; e.preventDefault();
        const after = getAfterElement(e.clientY);
        if(after == null){ list.appendChild(dragging); }
        else { list.insertBefore(dragging, after); }
      });
      list.addEventListener('drop', (e)=>{ e.preventDefault(); sync(); });
      // Drop en el canvas
      canvas?.addEventListener('dragover', (e)=>{ e.preventDefault(); canvas.classList.add('drag-over'); });
      canvas?.addEventListener('dragleave', ()=>{ canvas.classList.remove('drag-over'); });
      canvas?.addEventListener('drop', (e)=>{
        e.preventDefault(); canvas.classList.remove('drag-over');
        const type = e.dataTransfer?.getData('text/plain');
        if(!type) return;
        const li = createSeqItem(type);
        list.appendChild(li);
        sync();
      });

  // Inicializar estado
      restore();
  refreshBlockLabels();
      sync();

      // Asegurar que al enviar se sincronice
      form?.addEventListener('submit', ()=> sync());
    })();
  });
})();
