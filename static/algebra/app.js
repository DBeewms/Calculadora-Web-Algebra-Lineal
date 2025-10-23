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
        if(boxb) buildMatrix(boxb, n, 1);
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
      updateHidden(form);
    }
    doResize();
    if(resizeBtn){
      resizeBtn.addEventListener('click', ()=>{ doResize(); });
    }
    form.addEventListener('input', ()=> updateHidden(form));
    form.addEventListener('submit', ()=> updateHidden(form));

    // Controls: clear, example, copy-result
    form.querySelectorAll('[data-action="clear"]').forEach(btn=>{
      btn.addEventListener('click', ()=>{
        form.querySelectorAll('.matrix input').forEach(inp=> inp.value='');
        updateHidden(form);
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
      });
    });

  }

  document.addEventListener('DOMContentLoaded', ()=>{
    document.querySelectorAll('form.matrix-form').forEach(initForm);
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
  });
})();
