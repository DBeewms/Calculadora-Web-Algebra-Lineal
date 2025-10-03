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
        const cB = +form.querySelector('[data-target="colsB"]').value || 2;
        const [boxA, boxB] = matrices;
        buildMatrix(boxA, rA, pc);
        buildMatrix(boxB, pc, cB);
      } else if(mode === 'aug'){
        const r = +form.querySelector('[data-target="rows"]').value || 2;
        const c = +form.querySelector('[data-target="cols"]').value || 2;
        const [boxA, boxB] = matrices;
        buildMatrix(boxA, r, c);
        boxB.setAttribute('data-cols', '1');
        buildMatrix(boxB, r, 1);
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
        if(mode==='sum' && ex==='sum'){
          // A= [[1,2],[3,4]]; B= [[5,6],[7,8]]
          const [boxA, boxB] = matrices;
          doResize();
          const fillsA = ['1','2','3','4'];
          const fillsB = ['5','6','7','8'];
          [...boxA.querySelectorAll('input')].forEach((i,idx)=> i.value=fillsA[idx]||'0');
          [...boxB.querySelectorAll('input')].forEach((i,idx)=> i.value=fillsB[idx]||'0');
        }
        if(mode==='mul' && ex==='mul'){
          const [boxA, boxB] = matrices;
          form.querySelector('[data-target="rowsA"]').value = 2;
          form.querySelector('[data-target="colsArowsB"]').value = 2;
          form.querySelector('[data-target="colsB"]').value = 2;
          doResize();
          const fillsA = ['1','2','3','4'];
          const fillsB = ['5','6','7','8'];
          [...boxA.querySelectorAll('input')].forEach((i,idx)=> i.value=fillsA[idx]||'0');
          [...boxB.querySelectorAll('input')].forEach((i,idx)=> i.value=fillsB[idx]||'0');
        }
        if(mode==='aug'){
          const [boxA, boxB] = matrices;
          form.querySelector('[data-target="rows"]').value = 2;
          form.querySelector('[data-target="cols"]').value = 2;
          doResize();
          const fillsA = ['1','2','3','4'];
          const fillsb = ['5','11'];
          [...boxA.querySelectorAll('input')].forEach((i,idx)=> i.value=fillsA[idx]||'0');
          [...boxB.querySelectorAll('input')].forEach((i,idx)=> i.value=fillsb[idx]||'0');
        }
        updateHidden(form);
      });
    });

    form.querySelectorAll('[data-action="copy-result"]').forEach(btn=>{
      btn.addEventListener('click', ()=>{
        const table = btn.closest('.panel').querySelector('table.matriz');
        if(!table) return;
        const text = Array.from(table.querySelectorAll('tr')).map(tr=>
          Array.from(tr.querySelectorAll('td')).map(td=> td.innerText.trim()).join(' ')
        ).join('\n');
        navigator.clipboard.writeText(text).catch(()=>{});
        btn.textContent = 'Copiado';
        setTimeout(()=> btn.textContent='Copiar', 1200);
      });
    });
  }

  document.addEventListener('DOMContentLoaded', ()=>{
    document.querySelectorAll('form.matrix-form').forEach(initForm);
  // Keypad behavior
  const kp = document.getElementById('keypad');
  const fab = document.getElementById('keypadToggle');
    let currentInput = null;
    document.addEventListener('focusin', (e)=>{
      const t = e.target;
      if(t && t.tagName==='INPUT' && t.closest('.matrix')){
        currentInput = t;
        kp?.classList.remove('hidden');
      }
    });
    kp?.addEventListener('click', (e)=>{
      const btn = e.target.closest('button');
      if(!btn || !currentInput) return;
      const k = btn.getAttribute('data-k');
      if(k==='hide'){ kp.classList.add('hidden'); return; }
      if(k==='back'){
        currentInput.value = currentInput.value.slice(0, -1);
      }else{
        currentInput.value += k;
      }
      currentInput.dispatchEvent(new Event('input', {bubbles:true}));
      currentInput.focus();
    });
    // Toggle keypad via keyboard shortcut or future button
    document.addEventListener('keydown', (e)=>{
      if(e.key==='F2'){
        kp?.classList.toggle('hidden');
      }
    });
    fab?.addEventListener('click', ()=> kp?.classList.toggle('hidden'));

    // Theme toggle
    const themeToggle = document.getElementById('themeToggle');
    const root = document.documentElement;
    const saved = localStorage.getItem('theme');
    if(saved){ root.setAttribute('data-theme', saved); }
    themeToggle?.addEventListener('click', ()=>{
      const current = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      if(current==='light') root.removeAttribute('data-theme');
      else root.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', current);
      themeToggle.textContent = current==='dark' ? '☀️' : '🌙';
    });
    if(root.getAttribute('data-theme')==='dark'){ themeToggle.textContent = '☀️'; }
  });
})();
