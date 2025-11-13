(function(){
  // MathLive helpers
  // Balanced extractors to handle nested braces/brackets in \frac and \sqrt
  function extractBalanced(s, start, openChar, closeChar){
    let depth = 0;
    let i = start;
    if(s[i] !== openChar) return null;
    i++; // skip opening
    const begin = i;
    while(i < s.length){
      const ch = s[i];
      if(ch === openChar) depth++;
      else if(ch === closeChar){
        if(depth === 0){
          return { content: s.slice(begin, i), end: i }; // end at the index of the closing char
        }
        depth--;
      }
      i++;
    }
    return null; // unbalanced
  }
  function replaceAllFracs(input){
    let s = input;
    let guard = 0;
    while(guard++ < 500){
      const i = s.indexOf('\\frac');
      if(i === -1) break;
      // expect \frac{...}{...}
      let j = i + 5;
      // skip optional spaces
      while(j < s.length && /\s/.test(s[j])) j++;
      if(s[j] !== '{'){ // not a standard frac, skip this occurrence
        // move past this to avoid infinite loop
        s = s.slice(0, i) + 'frac' + s.slice(i+5);
        continue;
      }
      const num = extractBalanced(s, j, '{', '}');
      if(!num) break;
      j = num.end + 1; // position after first '}'
      while(j < s.length && /\s/.test(s[j])) j++;
      if(s[j] !== '{') { s = s.slice(0, i) + '(' + num.content + ')/(' + s.slice(j) ; break; }
      const den = extractBalanced(s, j, '{', '}');
      if(!den) break;
      const replaceEnd = den.end + 1;
      const rep = '(' + num.content + ')/(' + den.content + ')';
      s = s.slice(0, i) + rep + s.slice(replaceEnd);
    }
    return s;
  }
  function replaceAllSqrt(input){
    let s = input;
    let guard = 0;
    while(guard++ < 500){
      const i = s.indexOf('\\sqrt');
      if(i === -1) break;
      let j = i + 5;
      // optional index [n]
      while(j < s.length && /\s/.test(s[j])) j++;
      let idx = null;
      if(s[j] === '['){
        const idxRes = extractBalanced(s, j, '[', ']');
        if(!idxRes) break;
        idx = idxRes.content;
        j = idxRes.end + 1;
      }
      while(j < s.length && /\s/.test(s[j])) j++;
      if(s[j] !== '{'){ // malformed, strip command
        s = s.slice(0, i) + 'sqrt' + s.slice(i+5);
        continue;
      }
      const rad = extractBalanced(s, j, '{', '}');
      if(!rad) break;
      const end = rad.end + 1;
      const rep = idx ? '(' + rad.content + ')^(1/(' + idx + '))' : 'sqrt(' + rad.content + ')';
      s = s.slice(0, i) + rep + s.slice(end);
    }
    return s;
  }
  function replaceAllPowers(input){
    let s = input;
    let i = 0;
    let guard = 0;
    while(i < s.length && guard++ < 2000){
      const hat = s.indexOf('^', i);
      if(hat === -1) break;
      let j = hat + 1;
      // skip spaces
      while(j < s.length && /\s/.test(s[j])) j++;
      if(j >= s.length){ i = j; continue; }
      if(s[j] === '{'){
        const grp = extractBalanced(s, j, '{', '}');
        if(!grp){ i = j+1; continue; }
        const inner = replaceAllPowers(grp.content);
        const rep = '**(' + inner + ')';
        s = s.slice(0, hat) + rep + s.slice(grp.end + 1);
        i = hat + rep.length;
        continue;
      }
      if(s[j] === '('){
        const grp = extractBalanced(s, j, '(', ')');
        if(!grp){ i = j+1; continue; }
        const inner = replaceAllPowers(grp.content);
        const rep = '**(' + inner + ')';
        s = s.slice(0, hat) + rep + s.slice(grp.end + 1);
        i = hat + rep.length;
        continue;
      }
      // number or variable token, also detect simple rational like 1/2 immediately after
      const rest = s.slice(j);
      const mfrac = rest.match(/^(\d+(?:\.\d+)?)\s*\/\s*(\d+(?:\.\d+)?)/);
      if(mfrac){
        const rep = '**(' + mfrac[1] + '/' + mfrac[2] + ')';
        s = s.slice(0, hat) + rep + s.slice(j + mfrac[0].length);
        i = hat + rep.length;
        continue;
      }
      const m = rest.match(/^[A-Za-z0-9\.]+/);
      if(m && m[0]){
        const token = m[0];
        const rep = '**' + token;
        s = s.slice(0, hat) + rep + s.slice(j + token.length);
        i = hat + rep.length;
      }else{
        i = j + 1;
      }
    }
    return s;
  }
  function latexToPlain(latex){
    if(!latex) return '';
    let s = String(latex);
    // Remove sizing directives but keep braces for fraction handling
    s = s.replace(/\\left|\\right/g, '');

    // Robust handling for \frac and \sqrt (nested)
    s = replaceAllFracs(s);
    s = replaceAllSqrt(s);
    // Unicode root symbol
    s = s.replace(/√\s*\(([^()]+)\)/g, 'sqrt($1)');

    // Absolute value: \lvert ... \rvert or |...| -> abs(...)
    s = s.replace(/\\lvert\s*([\s\S]*?)\s*\\rvert/g, 'abs($1)');
    s = s.replace(/\|([^|]+)\|/g, 'abs($1)');

    // Replace common vulgar fraction characters (½, ¼, ¾) with ascii form
    s = s.replace(/\u00BD/g, '1/2') // ½
         .replace(/\u00BC/g, '1/4') // ¼
         .replace(/\u00BE/g, '3/4'); // ¾

    // Normalize some LaTeX fraction variants to \frac
    s = s.replace(/\\d?frac/g, '\\frac').replace(/\\tfrac/g, '\\frac');

    // (legacy simple \frac replace removed; handled by replaceAllFracs)

    // Convert unicode division slash to ASCII '/'
    s = s.replace(/\u2215/g, '/');

    // Common LaTeX -> ascii conversions
  // (legacy simple sqrt replaced by replaceAllSqrt above)
  s = s.replace(/\\sqrt\{([^{}]+)\}/g, 'sqrt($1)')
         .replace(/\\cdot|\\times/g, '*')
         .replace(/\\div/g, '/')
         .replace(/\\pi/g, 'pi');

  // Decimal comma -> dot (e.g., 3,5 -> 3.5)
  s = s.replace(/(\d),(\d)/g, '$1.$2');

  // Superscripts: robust conversion to **(...) supporting nesting
  s = replaceAllPowers(s);

    // Remove stray backslash escapes for symbols we already handled
    s = s.replace(/\\=/g, '=')
         .replace(/\\[a-zA-Z]+/g, function(m){ return m.slice(1); });

    // Handle log base via LaTeX-style subscripts: log_{10}(x) or log_2(x)
    s = s.replace(/log_\{?\s*10\s*\}?\s*\(/g, 'log10(')
      .replace(/log_\{?\s*2\s*\}?\s*\(/g, 'log2(');

    // Normalize variants of equals and minus sign
    s = s.replace(/\uFF1D/g, '=').replace(/\u2261/g, '=');
    s = s.replace(/−/g, '-');

    // Remove remaining curly braces (they should be unnecessary now)
    s = s.replace(/[{}]/g, '');

    // Trim extra spaces
    return s.trim();
  }
  // Convert LaTeX-like input for function parsing (bisection): map ^ -> **, functions names, etc.
  function latexToFunction(latex){
    let s = latexToPlain(latex);
    if(!s) return '';
    // Map common function names (keep plain names)
    s = s.replace(/\bln\b/g, 'log');
    s = s.replace(/\blg\b/g, 'log10');
    // Spanish aliases
    s = s.replace(/\bsen\b/g, 'sin');
    s = s.replace(/\btg\b/g, 'tan');
    s = s.replace(/\bsin\b|\\sin/g, 'sin');
    s = s.replace(/\bcos\b|\\cos/g, 'cos');
    s = s.replace(/\btan\b|\\tan/g, 'tan');
    s = s.replace(/\\exp/g, 'exp');
    // keep abs if produced from |x|
    s = s.replace(/\\abs/g, 'abs');

    // Normalize caret-like powers that may remain: ^( -> **( ; ^number -> **number
    s = s.replace(/\^\s*\(/g, '**(');
    s = s.replace(/\^(\-?\d+(?:\.\d+)?)/g, '**$1');

    // If someone used the MathLive token exponentialE, map to e
    s = s.replace(/exponentialE/g, 'e');

    // Collapse repeated parentheses like ((1)) -> (1)
  s = s.replace(/\(\s*\(/g, '(').replace(/\)\s*\)/g, ')');

  // Insert explicit multiplication where users write implicit forms like '6x', ')(', '2(', 'x2'.
  // 1) number followed by letter or '(' -> 6x -> 6*x, 2( -> 2*(
  s = s.replace(/(\d)\s*([a-zA-Z\(])/g, '$1*$2');
  // 2) single-letter variable before '(' (avoid function names like sin(), sqrt(), Math.sin())
  s = s.replace(/\b(?!sin|cos|tan|exp|log|sqrt|abs|asin|acos|atan|sinh|cosh|tanh|asinh|acosh|atanh|log10|log2)([a-zA-Z])\s*\(/g, '$1*(');
  // 3) closing paren before '(' or alnum -> )( -> )*( ; )x -> )*x ; )2 -> )*2
  s = s.replace(/\)\s*\(/g, ')*(');
  s = s.replace(/\)\s*([a-zA-Z0-9])/g, ')*$1');
  // 4) letter followed by digit -> x2 -> x*2
  s = s.replace(/([a-zA-Z])\s*(\d)/g, '$1*$2');

  // Collapse repeated operator sequences like '* *' or '** *(' -> '**(' or '* *(' -> '*('
  // Be permissive with whitespace between stars and before parentheses.
  s = s.replace(/\*\s*\*\s*\(/g, '**(');
  s = s.replace(/\*\s*\*/g, '**');
  s = s.replace(/\*\s*\(/g, '*(');
  s = s.replace(/\*{3,}/g, '**');
    return s.trim();
  }
  // Map normalized function string to a JS-evaluable expression with Math.* and constants
  function toJSExpr(expr){
    if(!expr) return '';
    let s = String(expr);
    // Ensure powers are JS-friendly
    s = s.replace(/\^/g, '**');
    // Map common function names to Math.*
    s = s.replace(/\b(sin|cos|tan|asin|acos|atan|sinh|cosh|tanh|asinh|acosh|atanh|exp|log|sqrt|abs|log10|log2|pow)\s*\(/g, 'Math.$1(');
    // Constants: pi -> Math.PI, standalone e -> Math.E
    s = s.replace(/\bpi\b/g, 'Math.PI');
    s = s.replace(/\be\b/g, 'Math.E');
  // As a safety, insert explicit multiplication for implicit cases, avoiding function calls
  s = s.replace(/(\d)\s*([a-zA-Z\(])/g, '$1*$2');
  s = s.replace(/\b(?!sin|cos|tan|exp|log|sqrt|abs|asin|acos|atan|sinh|cosh|tanh|asinh|acosh|atanh|log10|log2)([a-zA-Z])\s*\(/g, '$1*(');
  s = s.replace(/\)\s*\(/g, ')*(');
  s = s.replace(/\)\s*([a-zA-Z0-9])/g, ')*$1');
  s = s.replace(/([a-zA-Z])\s*(\d)/g, '$1*$2');
    return s;
  }

  // Lazy-load Plotly the first time it's needed
  let __plotlyLoading = null;
  function ensurePlotly(){
    if(window.Plotly) return Promise.resolve(window.Plotly);
    if(__plotlyLoading) return __plotlyLoading;
    __plotlyLoading = new Promise((resolve, reject)=>{
      const script = document.createElement('script');
      script.src = 'https://cdn.plot.ly/plotly-2.35.2.min.js';
      script.onload = ()=> resolve(window.Plotly);
      script.onerror = ()=> reject(new Error('No se pudo cargar Plotly.'));
      document.head.appendChild(script);
    });
    return __plotlyLoading;
  }
  
  // Try to evaluate a numeric expression safely on the client for numeric fields.
  // We only allow digits, operators, parentheses, decimal points, slash and 'e' for exponents.
  function tryEvalNumeric(expr){
    if(!expr || typeof expr !== 'string') return null;
    // First, convert LaTeX-like content to function/plain form
    let s = latexToFunction(expr);
    // Replace Unicode vulgar fractions again, just in case
    s = s.replace(/\u00BD/g, '1/2').replace(/\u00BC/g, '1/4').replace(/\u00BE/g, '3/4');
    // Convert caret to JS power operator if present
    s = s.replace(/\^/g, '**');
    // Allow only safe characters: digits, operators, parentheses, dot, slash, whitespace and e/E
    if(!/^[0-9eE\.\+\-\*\/\(\)\s]+$/.test(s)) return null;
    try{
      // Use Function to evaluate arithmetic; this is run-only on client and guarded by the regex above.
      // Replace '**' with Math.pow fallback if engine doesn't support '**' (older browsers), but most modern do.
      let evalExpr = s;
      if(evalExpr.indexOf('**') !== -1){
        // Convert a**b into Math.pow(a,b) for safer cross-browser handling
        evalExpr = evalExpr.replace(/([0-9\)\.\s]+)\*\*([0-9\(\.\-\s]+)/g, 'Math.pow($1,$2)');
      }
      // eslint-disable-next-line no-new-func
      const fn = new Function('return (' + evalExpr + ')');
      const v = fn();
      if(typeof v === 'number' && isFinite(v)) return v;
    }catch(e){
      return null;
    }
    return null;
  }
  // Expose selected helpers for use in other inline scripts (legacy blocks)
  try{ window.latexToFunction = latexToFunction; window.tryEvalNumeric = tryEvalNumeric; window.toJSExpr = toJSExpr; }catch(_e){}
  function isMathField(el){ return el && el.tagName === 'MATH-FIELD'; }
  function getFieldPlain(el){
    if(!el) return '';
    if(isMathField(el)) return latexToPlain(el.value || '');
    return (el.value || '').trim();
  }

  function buildMatrix(container, rows, cols){
    container.innerHTML = '';
    const table = document.createElement('table');
    table.className = 'matriz editable';
    const useMath = container.hasAttribute('data-use-math') || container.getAttribute('data-math') === 'true';
    for(let i=0;i<rows;i++){
      const tr = document.createElement('tr');
      for(let j=0;j<cols;j++){
        const td = document.createElement('td');
        if(useMath){
          const mf = document.createElement('math-field');
          // For matrices, keep VK off by default to avoid intrusive popups
          mf.setAttribute('virtualkeyboardmode','off');
          mf.setAttribute('virtualkeyboardtogglevisible','false');
          mf.placeholder = '0';
          try{
            if(typeof mf.setOptions === 'function') mf.setOptions({ menuItems: [] });
            if('menuToggleVisible' in mf) mf.menuToggleVisible = false;
            if('virtualKeyboardToggleVisible' in mf) mf.virtualKeyboardToggleVisible = false;
          }catch(_e){}
          td.appendChild(mf);
        } else {
          const inp = document.createElement('input');
          inp.type = 'text';
          inp.placeholder = '0';
          td.appendChild(inp);
        }
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
      tr.querySelectorAll('math-field, input').forEach(inp=>{
        const val = getFieldPlain(inp);
        row.push(val || '0');
      });
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
        const values = rows.map(tr=> Array.from(tr.querySelectorAll('math-field, input')).map(inp=> inp.value || ''));
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
    // Priorizar el estado guardado en localStorage para preservar siempre
    // los valores que el usuario haya introducido, incluso si el servidor
    // re-renderiza el formulario tras un POST con valores por defecto.
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
            const currentCols = table ? (table.querySelector('tr')?.querySelectorAll('math-field, input').length || 0) : 0;
            if(currentRows !== mat.rows || currentCols !== mat.cols){
              buildMatrix(box, mat.rows, mat.cols);
            }
            const trs = box.querySelectorAll('tr');
            for(let i=0;i<mat.rows;i++){
              const inputs = trs[i]?.querySelectorAll('math-field, input') || [];
              for(let j=0;j<mat.cols;j++){
                if(inputs[j]) inputs[j].value = mat.values[i]?.[j] ?? '';
              }
            }
          });
        }
        // Re-apply controls so dynamically created equation inputs receive saved values
        if(state && state.controls){
          Object.keys(state.controls).forEach(k=>{
            const el = form.querySelector(`[data-target="${k}"]`);
            if(el) el.value = state.controls[k];
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
    const mode = form.dataset.mode;
    // Per-mode hidden sync for dimensions and augmented matrix
    if(mode === 'aug'){
      const A = (form.querySelector('input[name="matrizA"]').value || '').split('\n');
      const b = (form.querySelector('input[name="vectorB"]').value || '').split('\n');
      const rows = Math.max(A.length, b.length);
      const out = [];
      for(let i=0;i<rows;i++){
        const left = (A[i]||'').trim();
        const right = (b[i]||'').trim();
        out.push(`${left} | ${right}`.trim());
      }
      const hiddenAug = form.querySelector('input[name="matrizAug"]');
      if(hiddenAug) hiddenAug.value = out.join('\n');
      const rCtl = form.querySelector('[data-target="rows"]');
      const cCtl = form.querySelector('[data-target="cols"]');
      const rHidden = form.querySelector('input[name="rows"]');
      const cHidden = form.querySelector('input[name="cols"]');
      if(rCtl && rHidden){ rHidden.value = String(+rCtl.value || 0); }
      if(cCtl && cHidden){ cHidden.value = String(+cCtl.value || 0); }
    } else if(mode === 'cramer'){
      const nCtl = form.querySelector('[data-target="rowsAcolsArowsB"]');
      const rHidden = form.querySelector('input[name="rows"]');
      const cHidden = form.querySelector('input[name="cols"]');
      const n = +(nCtl?.value) || 0;
      if(rHidden) rHidden.value = String(n);
      if(cHidden) cHidden.value = String(n);
    } else if(mode === 'simple'){
      const rCtl = form.querySelector('[data-target="rows"]');
      const cCtl = form.querySelector('[data-target="cols"]');
      const rHidden = form.querySelector('input[name="rows"]');
      const cHidden = form.querySelector('input[name="cols"]');
      if(rCtl && rHidden){ rHidden.value = String(+rCtl.value || 0); }
      if(cCtl && cHidden){ cHidden.value = String(+cCtl.value || 0); }
    }
    // Update equations meta badges and hint if present (generic)
    (function(){
      const eqCountEl = form.querySelector('#eqCountBadge strong');
      const varCountEl = form.querySelector('#varCountBadge strong');
      const hintEl = form.querySelector('#eqHint');
      let rVal = 0, cVal = 0;
      if(mode === 'aug' || mode === 'simple'){
        rVal = +form.querySelector('[data-target="rows"]')?.value || 0;
        cVal = +form.querySelector('[data-target="cols"]')?.value || 0;
      } else if(mode === 'cramer'){
        const nCtl = form.querySelector('[data-target="rowsAcolsArowsB"]');
        const n = +(nCtl?.value) || 0; rVal = n; cVal = n;
      }
      if(eqCountEl) eqCountEl.textContent = String(rVal || 0);
      if(varCountEl) varCountEl.textContent = String(cVal || 0);
      if(hintEl){
        const varsPreview = cVal <= 3 ? ['x','y','z'].slice(0, Math.max(1,cVal)).join(', ') : `x1…x${cVal}`;
        hintEl.textContent = `Ingresa ${rVal||0} ecuaciones con ${cVal||0} variables (p. ej., ${varsPreview}). Formato: a1·x1 + a2·x2 + … = b. Acepta fracciones (3/4), potencias (^), y raíces (√() o sqrt()).`;
      }
      // Compose equations hidden from per-line inputs if present
      const eqList = form.querySelector('#equationsList');
      const eqHidden = form.querySelector('input[name="equations"]');
      if(eqList && eqHidden){
        const lines = Array.from(eqList.querySelectorAll('math-field.eq-line, input.eq-line')).map(inp=> getFieldPlain(inp));
        while(lines.length && lines[lines.length-1] === ''){ lines.pop(); }
        eqHidden.value = lines.join('\n');
      }
    })();
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
            const inp = tr.querySelector('math-field, input');
            if(inp){ inp.placeholder = 'x' + (idx++); }
          });
        }
      } else if(mode === 'cramer'){
        // Cramer: A es n×n y b es n×1. El control data-target="rowsAcolsArowsB" define n.
        const nCtl = form.querySelector('[data-target="rowsAcolsArowsB"]');
        const n = +(nCtl?.value) || 2;
        const [boxA, boxb] = matrices;
        if(boxA) buildMatrix(boxA, n, n);
        if(boxb){ boxb.setAttribute('data-cols','1'); buildMatrix(boxb, n, 1); }
        // Build equation input lines to match n
        const eqList = form.querySelector('#equationsList');
        if(eqList){
          const prevVals = Array.from(eqList.querySelectorAll('math-field.eq-line, input.eq-line')).map(inp=> inp.value);
          eqList.innerHTML = '';
          for(let i=0;i<n;i++){
            const wrap = document.createElement('div');
            wrap.className = 'eq-item';
            const badge = document.createElement('span');
            badge.className = 'eq-index';
            badge.setAttribute('aria-hidden','true');
            badge.textContent = String(i+1);
            const inp = document.createElement('math-field');
            inp.className = 'eq-line';
            inp.setAttribute('virtualkeyboardmode','onfocus');
            inp.setAttribute('virtualkeyboardtogglevisible','false');
            try{
              if(typeof inp.setOptions === 'function') inp.setOptions({ menuItems: [] });
              if('menuToggleVisible' in inp) inp.menuToggleVisible = false;
              if('virtualKeyboardToggleVisible' in inp) inp.virtualKeyboardToggleVisible = false;
            }catch(_e){}
            const c = n;
            let example = 'x + 2y = 5';
            if(c <= 1){ example = '3x = 6'; }
            else if(c === 2){ example = 'x + 2y = 5'; }
            else if(c === 3){ example = 'x + 2y - z = 7'; }
            else { example = 'x1 + 2x2 + … = 7'; }
            inp.placeholder = `Ecuación ${i+1} (ej: ${example})`;
            inp.setAttribute('data-target', `eq${i}`);
            inp.setAttribute('aria-label', `Ecuación ${i+1} de ${n}`);
            if(prevVals[i] != null) inp.value = prevVals[i];
            inp.addEventListener('input', ()=>{ updateHidden(form); saveFormState(form); });
            wrap.appendChild(badge);
            wrap.appendChild(inp);
            eqList.appendChild(wrap);
          }
        }
      } else if(mode === 'aug'){
        const r = +form.querySelector('[data-target="rows"]').value || 2;
        const c = +form.querySelector('[data-target="cols"]').value || 2;
        const [boxA, boxB] = matrices;
        buildMatrix(boxA, r, c);
        boxB.setAttribute('data-cols', '1');
        buildMatrix(boxB, r, 1);
        // Build equation input lines to match r
        const eqList = form.querySelector('#equationsList');
        if(eqList){
          const prevVals = Array.from(eqList.querySelectorAll('math-field.eq-line, input.eq-line')).map(inp=> inp.value);
          eqList.innerHTML = '';
          for(let i=0;i<r;i++){
            const wrap = document.createElement('div');
            wrap.className = 'eq-item';
            const badge = document.createElement('span');
            badge.className = 'eq-index';
            badge.setAttribute('aria-hidden','true');
            badge.textContent = String(i+1);
            const inp = document.createElement('math-field');
            inp.className = 'eq-line';
            inp.setAttribute('virtualkeyboardmode','onfocus');
            inp.setAttribute('virtualkeyboardtogglevisible','false');
            try{
              if(typeof inp.setOptions === 'function') inp.setOptions({ menuItems: [] });
              if('menuToggleVisible' in inp) inp.menuToggleVisible = false;
              if('virtualKeyboardToggleVisible' in inp) inp.virtualKeyboardToggleVisible = false;
            }catch(_e){}
            // Example placeholder according to variable count
            let example = 'x + 2y = 5';
            if(c <= 1){ example = '3x = 6'; }
            else if(c === 2){ example = 'x + 2y = 5'; }
            else if(c === 3){ example = 'x + 2y - z = 7'; }
            else { example = 'x1 + 2x2 + … = 7'; }
            inp.placeholder = `Ecuación ${i+1} (ej: ${example})`;
            inp.setAttribute('data-target', `eq${i}`);
            inp.setAttribute('aria-label', `Ecuación ${i+1} de ${r}`);
            if(prevVals[i] != null) inp.value = prevVals[i];
            inp.addEventListener('input', ()=>{ updateHidden(form); saveFormState(form); });
            wrap.appendChild(badge);
            wrap.appendChild(inp);
            eqList.appendChild(wrap);
          }
        }
        // Sync meta after building list
        updateHidden(form);
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
        // Build equation input lines to match r
        const eqList = form.querySelector('#equationsList');
        if(eqList){
          const prevVals = Array.from(eqList.querySelectorAll('math-field.eq-line, input.eq-line')).map(inp=> inp.value);
          eqList.innerHTML = '';
          for(let i=0;i<r;i++){
            const wrap = document.createElement('div');
            wrap.className = 'eq-item';
            const badge = document.createElement('span');
            badge.className = 'eq-index';
            badge.setAttribute('aria-hidden','true');
            badge.textContent = String(i+1);
            const inp = document.createElement('math-field');
            inp.className = 'eq-line';
            inp.setAttribute('virtualkeyboardmode','onfocus');
            inp.setAttribute('virtualkeyboardtogglevisible','false');
            try{
              if(typeof inp.setOptions === 'function') inp.setOptions({ menuItems: [] });
              if('menuToggleVisible' in inp) inp.menuToggleVisible = false;
              if('virtualKeyboardToggleVisible' in inp) inp.virtualKeyboardToggleVisible = false;
            }catch(_e){}
            let example = 'x + 2y = 0';
            if(c <= 1){ example = '3x = 0'; }
            else if(c === 2){ example = 'x + 2y = 0'; }
            else if(c === 3){ example = 'x + 2y - z = 0'; }
            else { example = 'x1 + 2x2 + … = 0'; }
            inp.placeholder = `Ecuación ${i+1} (ej: ${example})`;
            inp.setAttribute('data-target', `eq${i}`);
            inp.setAttribute('aria-label', `Ecuación ${i+1} de ${r}`);
            if(prevVals[i] != null) inp.value = prevVals[i];
            inp.addEventListener('input', ()=>{ updateHidden(form); saveFormState(form); });
            wrap.appendChild(badge);
            wrap.appendChild(inp);
            eqList.appendChild(wrap);
          }
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
        form.querySelectorAll('.matrix input, .matrix math-field').forEach(inp=> inp.value='');
        form.querySelectorAll('#equationsList input.eq-line, #equationsList math-field.eq-line').forEach(inp=> inp.value='');
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
          [...boxA.querySelectorAll('tr')].forEach(tr=> tr.querySelectorAll('math-field, input').forEach(inp=> inp.value = String(val++)));
          val = 1;
          [...boxB.querySelectorAll('tr')].forEach(tr=> tr.querySelectorAll('math-field, input').forEach(inp=> inp.value = String(val++)));
        }
        if(mode==='mul' && ex==='mul'){
          const rA = rnd(1,5), p = rnd(1,5), cB = rnd(1,5);
          form.querySelector('[data-target="rowsA"]').value = rA;
          form.querySelector('[data-target="colsArowsB"]').value = p;
          form.querySelector('[data-target="colsB"]').value = cB;
          doResize();
          const [boxA, boxB] = matrices;
          let val = 1;
          [...boxA.querySelectorAll('tr')].forEach(tr=> tr.querySelectorAll('math-field, input').forEach(inp=> inp.value = String(val++)));
          val = 1;
          [...boxB.querySelectorAll('tr')].forEach(tr=> tr.querySelectorAll('math-field, input').forEach(inp=> inp.value = String(val++)));
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
            [...boxA.querySelectorAll('tr')].forEach(tr=> tr.querySelectorAll('math-field, input').forEach(inp=> inp.value = String(val++)));
          }
          // b: 3x1 con 1,2,3
          if(boxb){
            let vb = 1;
            [...boxb.querySelectorAll('tr')].forEach(tr=>{ const inp = tr.querySelector('math-field, input'); if(inp) inp.value = String(vb++); });
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
          [...boxA.querySelectorAll('tr')].forEach(tr=> tr.querySelectorAll('math-field, input').forEach(inp=> inp.value = String(val++)));
        }
        updateHidden(form);
        saveFormState(form);
      });
    });

  }

  document.addEventListener('DOMContentLoaded', ()=>{
    // Detectar soporte de hover real: evita hovers pegajosos en dispositivos táctiles
    (function(){
      const root = document.documentElement;
      let applied = false;
      function enable(){ if(!applied){ root.classList.add('has-hover'); applied = true; } }
      function disable(){ root.classList.remove('has-hover'); }
      window.addEventListener('mousemove', enable, { once:true });
      window.addEventListener('touchstart', disable, { passive:true });
    })();
    document.querySelectorAll('form.matrix-form').forEach(initForm);
    // Intentar restaurar el estado guardado (mantiene inputs tras enviar)
    document.querySelectorAll('form.matrix-form').forEach(loadFormState);
    // Aplicar prefill derivado de ecuaciones (servidor) para vistas compatibles (aug, cramer, simple)
    document.querySelectorAll('form.matrix-form').forEach(form=>{
      const script = form.querySelector('#prefillData');
      if(!script) return;
      let data = null;
      try{ data = JSON.parse(script.textContent||''); }catch(e){ data = null; }
      if(!data || !Array.isArray(data.A)) return;
      const rows = data.A.length;
      const cols = rows ? (data.A[0]?.length||0) : 0;
      const mode = form.dataset.mode;
      // Ajustar controles de dimensiones por modo
      if(mode === 'aug' || mode === 'simple'){
        const rCtl = form.querySelector('[data-target="rows"]');
        const cCtl = form.querySelector('[data-target="cols"]');
        if(rCtl) rCtl.value = String(rows||0);
        if(cCtl) cCtl.value = String(cols||0);
      } else if(mode === 'cramer'){
        const nCtl = form.querySelector('[data-target="rowsAcolsArowsB"]');
        if(nCtl) nCtl.value = String(rows||0); // asume cuadrada
      }
      // Redimensionar acorde
      form.querySelector('[data-action="resize"]')?.click();
      // Rellenar A
      const boxA = form.querySelector('.matrix[data-name="matrizA"]');
      const tableA = boxA?.querySelector('table');
      if(tableA && rows && cols){
        const trs = tableA.querySelectorAll('tr');
        for(let i=0;i<rows;i++){
          const inputs = trs[i]?.querySelectorAll('math-field, input')||[];
          for(let j=0;j<cols;j++){
            if(inputs[j]) inputs[j].value = String(data.A[i]?.[j] ?? '0');
          }
        }
      }
      // Rellenar b si corresponde
      const boxB1 = form.querySelector('.matrix[data-name="vectorB"]');
      const boxB2 = form.querySelector('.matrix[data-name="vectorb"]');
      const boxB = boxB1 || boxB2;
      const tableB = boxB?.querySelector('table');
      if(tableB && Array.isArray(data.b)){
        const trsB = tableB.querySelectorAll('tr');
        for(let i=0;i<rows;i++){
          const inp = trsB[i]?.querySelector('math-field, input');
          if(inp) inp.value = String(data.b?.[i] ?? '0');
        }
      }
      updateHidden(form);
      saveFormState(form);
    });

    // Ecuaciones: abrir/cerrar popup lateral izquierdo (en formularios que lo incluyan)
    document.querySelectorAll('form.matrix-form').forEach(form=>{
      const popup = form.querySelector('.eq-popup');
      const openBtn = form.querySelector('[data-action="open-eq"]');
      if(!popup || !openBtn) return;
      const overlay = popup.querySelector('.eq-overlay');
      function open(){ popup.classList.add('show'); popup.setAttribute('aria-hidden','false'); updateHidden(form); }
      function close(){ popup.classList.remove('show'); popup.setAttribute('aria-hidden','true'); }
      openBtn.addEventListener('click', open);
      popup.addEventListener('click', (e)=>{
        const btn = e.target.closest('[data-action="close-eq"]');
        if(btn || e.target === overlay){ close(); }
      });
      document.addEventListener('keydown', (e)=>{ if(e.key === 'Escape') close(); });

      // Resolver desde el popup
      popup.addEventListener('click', (e)=>{
        const actionBtn = e.target.closest('[data-action]');
        if(!actionBtn) return;
        const action = actionBtn.getAttribute('data-action');
        if(action === 'eq-solve'){
          updateHidden(form);
          saveFormState(form);
          close();
          // Enviar el formulario
          try{ form.requestSubmit ? form.requestSubmit() : form.submit(); }catch(_e){ form.submit(); }
          return;
        }
      });
    });
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

    // Floating toggle for MathLive virtual keyboard
    (function(){
      const btn = document.getElementById('vkToggle');
      if(!btn) return;
      function ensureTargetMathField(){
        const active = document.activeElement;
        if(active && active.tagName === 'MATH-FIELD') return active;
        const eq = document.querySelector('math-field.eq-line');
        if(eq) { try{ eq.focus(); }catch(_e){} return eq; }
        return null;
      }
      btn.addEventListener('click', ()=>{
        const vk = window.mathVirtualKeyboard;
        if(!vk){ return; }
        try{
          // Try API methods if present
          if(typeof vk.toggle === 'function'){ vk.toggle(); return; }
          if(typeof vk.show === 'function' && typeof vk.hide === 'function'){
            if(vk.visible){ vk.hide(); } else { ensureTargetMathField(); vk.show(); }
            return;
          }
        }catch(_e){}
        // Fallback: toggle visible flag
        try{
          vk.visible = !vk.visible;
          if(vk.visible){ ensureTargetMathField(); }
        }catch(_e){}
      });
    })();
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
      // Buscar los items con dropdown dentro del menú (clase .has-dropdown)
      const items = menu.querySelectorAll('.has-dropdown');
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
      // Cerrar dropdowns cuando el puntero sale del menú (comportamiento esperado en escritorio)
      menu.addEventListener('mouseleave', ()=>{ closeAll(null); });
      // Cerrar dropdowns cuando el foco sale del menú (soporte para teclado/AT)
      menu.addEventListener('focusout', (e)=>{
        // Esperar un tick por si el foco se mueve a otro elemento dentro del menú
        setTimeout(()=>{
          if(!menu.contains(document.activeElement)){
            closeAll(null);
          }
        }, 10);
      });
      document.addEventListener('click', (e)=>{
        const target = e.target;
        if(!menu.contains(target)){ closeAll(null); }
      });
      document.addEventListener('keydown', (e)=>{
        if(e.key === 'Escape'){ closeAll(null); }
      });
      // Cerrar también al hacer scroll (evita dropdowns persistentes)
      window.addEventListener('scroll', ()=> closeAll(null), { passive:true });
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

    // --- Popup Keyboard ---
    (function(){
      const kb = document.getElementById('kbPopup');
      const toggleBtn = document.getElementById('kbToggle');
      if(!kb || !toggleBtn) return;

      const tabs = kb.querySelectorAll('.kb-tab');
      const panes = kb.querySelectorAll('.kb-pane');
      const closeBtn = kb.querySelector('.kb-close');
      const hiddenClass = 'show';

      function show(){ kb.classList.add('show'); toggleBtn.setAttribute('aria-label','Ocultar teclado'); }
      function hide(){ kb.classList.remove('show'); toggleBtn.setAttribute('aria-label','Mostrar teclado'); }
      function toggle(){ kb.classList.contains('show') ? hide() : show(); }

      toggleBtn.addEventListener('click', toggle);
      closeBtn?.addEventListener('click', hide);

      tabs.forEach(tab=>{
        tab.addEventListener('click', ()=>{
          const name = tab.getAttribute('data-tab');
          tabs.forEach(t=> t.classList.remove('active'));
          panes.forEach(p=> p.classList.remove('active'));
          tab.classList.add('active');
          const pane = kb.querySelector(`.kb-pane[data-pane="${name}"]`);
          pane?.classList.add('active');
        });
      });

      let targetInput = null;
      document.addEventListener('focusin', (e)=>{
        const el = e.target;
        if(el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'MATH-FIELD')){
          targetInput = el;
        }
      });
      // Prefer matrix inputs if available at init
      targetInput = document.querySelector('.matrix math-field, .matrix input') || document.activeElement;

      function ensureTarget(){
        if(targetInput && (targetInput.tagName === 'INPUT' || targetInput.tagName === 'TEXTAREA' || targetInput.tagName === 'MATH-FIELD')) return targetInput;
        const fallback = document.querySelector('.matrix math-field, .matrix input, input[type="text"], textarea');
        if(fallback){ targetInput = fallback; }
        return targetInput;
      }

      function insertAtCursor(el, text){
        if(!el) return;
        if(el.tagName === 'MATH-FIELD'){
          // Insert LaTeX-friendly equivalents
          let latex = text;
          if(text === '√()'){ latex = '\\sqrt{}'; }
          else if(text === '()'){ latex = '()'; }
          else if(text === '| |'){ latex = '\\lvert\\rvert'; }
          else if(text === '^2'){ latex = '^{2}'; }
          // common operators
          else if(text === '×'){ latex = '\\times '}
          else if(text === '÷'){ latex = '\\div '}
          else if(text === 'π'){ latex = '\\pi '}
          try{ el.insert ? el.insert(latex) : (el.value = (el.value||'') + latex); }catch(_e){ el.value = (el.value||'') + latex; }
          // attempt to move cursor inside braces for sqrt, abs, etc.
          if(text === '√()' || text === '| |' || text === '()'){
            try{ el.executeCommand && el.executeCommand('moveToPreviousChar'); }catch(_e){}
          }
          el.dispatchEvent(new Event('input', { bubbles:true }));
          el.focus();
          return;
        }
        try{
          const start = el.selectionStart ?? el.value.length;
          const end = el.selectionEnd ?? el.value.length;
          const v = el.value || '';
          el.value = v.slice(0, start) + text + v.slice(end);
          const pos = start + text.length;
          el.setSelectionRange?.(pos, pos);
          el.dispatchEvent(new Event('input', { bubbles:true }));
        }catch(err){
          // fallback: append
          el.value = (el.value||'') + text;
          el.dispatchEvent(new Event('input', { bubbles:true }));
        }
        el.focus();
      }
      function backspaceAtCursor(el){
        if(!el) return;
        if(el.tagName === 'MATH-FIELD'){
          try{ el.executeCommand && el.executeCommand('deleteBackward'); }catch(_e){}
          el.dispatchEvent(new Event('input', { bubbles:true }));
          el.focus();
          return;
        }
        const start = el.selectionStart ?? 0;
        const end = el.selectionEnd ?? 0;
        const v = el.value || '';
        if(start === end && start > 0){
          el.value = v.slice(0, start-1) + v.slice(end);
          const pos = start - 1;
          el.setSelectionRange?.(pos, pos);
        } else {
          el.value = v.slice(0, start) + v.slice(end);
          el.setSelectionRange?.(start, start);
        }
        el.dispatchEvent(new Event('input', { bubbles:true }));
        el.focus();
      }

      kb.addEventListener('click', (e)=>{
        const btn = e.target.closest('button');
        if(!btn) return;
        if(btn.dataset.action === 'close'){ hide(); return; }
        const action = btn.dataset.action;
        if(action === 'backspace'){ backspaceAtCursor(ensureTarget()); return; }
        if(action === 'left'){
          const ti = ensureTarget();
          if(ti?.tagName === 'MATH-FIELD'){
            try{ ti.executeCommand && ti.executeCommand('moveToPreviousChar'); ti.focus(); }catch(_e){}
          } else {
            try{ const s = ti?.selectionStart||0; const pos = Math.max(0, s-1); ti?.setSelectionRange?.(pos, pos); ti?.focus(); }catch(e){}
          }
          return;
        }
        if(action === 'right'){
          const ti = ensureTarget();
          if(ti?.tagName === 'MATH-FIELD'){
            try{ ti.executeCommand && ti.executeCommand('moveToNextChar'); ti.focus(); }catch(_e){}
          } else {
            try{ const s = ti?.selectionEnd||0; const len = (ti?.value||'').length; const pos = len ? Math.min(len, s+1) : s+1; ti?.setSelectionRange?.(pos, pos); ti?.focus(); }catch(e){}
          }
          return;
        }
        if(action === 'enter'){
          const ti = ensureTarget();
          // Mover foco al siguiente input/textarea (como Tab)
          const focusables = Array.from(document.querySelectorAll('math-field, input, textarea')); // orden en DOM
          const idx = focusables.indexOf(ti);
          if(idx >= 0 && idx < focusables.length - 1){
            const next = focusables[idx+1];
            next?.focus();
            try{ if(next.setSelectionRange){ const len = (next.value||'').length; next.setSelectionRange(len, len); } }catch(e){}
          }
          return;
        }
        // Template insertion with cursor positioning
        const ti = ensureTarget();
        const ins = btn.dataset.ins;
        if(ins != null){
          insertAtCursor(ti, ins);
          const move = parseInt(btn.dataset.cursor||'0', 10);
          if(move !== 0 && ti.tagName !== 'MATH-FIELD'){
            try{
              const s = ti.selectionStart||0; const pos = s + move; // move can be negative
              const len = (ti.value||'').length; const clamped = Math.max(0, Math.min(len, pos));
              ti.setSelectionRange?.(clamped, clamped);
            }catch(e){}
          }
          return;
        }
        const k = btn.dataset.k;
        if(k != null){ insertAtCursor(ti, k); }
      });

      // Cerrar teclado al cambiar de ruta interna (navegación dentro del sitio)
      document.querySelectorAll('a[href]').forEach(a=>{
        a.addEventListener('click', ()=>{ hide(); });
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

    // Bisección: hook math-field inputs to hidden fields with proper conversion
    document.querySelectorAll('form[data-page="biseccion"]').forEach(form=>{
      const map = [
        { mf:'#mf-function', hid:'#hid-function', conv: latexToFunction },
        { mf:'#mf-a', hid:'#hid-a', conv: latexToFunction },
        { mf:'#mf-b', hid:'#hid-b', conv: latexToFunction },
        { mf:'#mf-tol', hid:'#hid-tol', conv: latexToFunction },
        { mf:'#mf-maxit', hid:'#hid-maxit', conv: latexToFunction },
      ];
      function syncAll(){
        map.forEach(({mf,hid,conv})=>{
          const m = form.querySelector(mf);
          const h = form.querySelector(hid);
          if(!m || !h) return;
          const rawConv = conv(m.value||'');
          // For numeric hidden fields (a, b, tol, maxit) try to evaluate
          // the expression client-side to a decimal number so nested
          // fractions and parenthesized divisions become valid numeric
          // strings that the server will parse reliably.
          const numericHids = ['#hid-a','#hid-b','#hid-tol','#hid-maxit'];
          if(numericHids.includes(hid)){
            try{
              // Try to evaluate with JS. Replace '^' with '**' for JS power.
              const evalExpr = String(rawConv).replace(/\^/g,'**');
              const val = Function('return (' + evalExpr + ')')();
              if(typeof val === 'number' && isFinite(val)){
                h.value = String(val);
                return;
              }
            }catch(e){
              // if evaluation fails, fall back to the converted text
            }
          }
          h.value = rawConv;
        });
      }

      // Client-side lightweight validation + preview for equation input
      const previewText = form.querySelector('#biseccion-preview-text');
      const previewOk = form.querySelector('#biseccion-preview-ok');
      const previewErr = form.querySelector('#biseccion-preview-err');
      const previewErrTxt = form.querySelector('#biseccion-preview-err-txt');
      const submitBtn = form.querySelector('button[type="submit"]');

      function showError(msg){ if(previewErrTxt) previewErrTxt.textContent = msg; if(previewErr) previewErr.style.display = ''; if(previewOk) previewOk.style.display = 'none'; if(submitBtn) submitBtn.disabled = true; }
      function showPreview(text){ if(previewText) previewText.textContent = text; if(previewOk) previewOk.style.display = ''; if(previewErr) previewErr.style.display = 'none'; if(submitBtn) submitBtn.disabled = false; }

      function doValidateAndPreview(){
        const mf = form.querySelector('#mf-function');
        const hid = form.querySelector('#hid-function');
        if(!mf || !previewText) return true;
        const raw = String(mf.value || '');
        const plain = latexToPlain(raw);
        // Accept two forms:
        // 1) equation with '=': left = right --> treat as left - (right)
        // 2) single expression (no '='): treat as f(x) directly
        try{
          if(plain.includes('=')){
            const parts = plain.split('=');
            // allow some benign extra '=' (join rest) but prefer first two parts
            const left = parts.slice(0,1).join('=').trim();
            const right = parts.slice(1).join('=').trim();
            if(!left || !right){ throw new Error('Ambos lados de la ecuación deben existir.'); }
            const lnorm = latexToFunction(left);
            const rnorm = latexToFunction(right);
            const expr = `${lnorm} - (${rnorm})`;
            if(hid) hid.value = expr;
            showPreview(expr);
            return true;
          } else {
            // No '=' provided: accept the expression as-is (user wrote f(x) directly)
            const exprNorm = latexToFunction(plain);
            if(!exprNorm || String(exprNorm).trim()==='') throw new Error('Expresión vacía.');
            if(hid) hid.value = exprNorm;
            showPreview(exprNorm);
            return true;
          }
        }catch(e){
          showError('No se pudo normalizar la ecuación/expresión: ' + (e && e.message ? e.message : String(e)));
          return false;
        }
      }
      map.forEach(({mf,hid,conv})=>{
        const m = form.querySelector(mf);
        const h = form.querySelector(hid);
        if(!m || !h) return;
        // initial sync
        try{ h.value = conv(m.value||''); }catch(_e){}
        m.addEventListener('input', ()=>{ try{ h.value = conv(m.value||''); }catch(_e){} });
      });
      // Validate and preview before submit; prevent submit if client validation fails
      form.addEventListener('submit', (e)=>{
        const ok = doValidateAndPreview();
        if(!ok){ e.preventDefault(); e.stopPropagation(); return false; }
        syncAll();
      });
      // Quick-plot: graficar función solo con la ecuación
      (function(){
        const btn = form.querySelector('[data-action="plot-func"]');
        const panel = document.getElementById('biseccionPreviewPanel');
        const plotEl = document.getElementById('plotBiseccionPreview');
        if(!btn || !panel || !plotEl) return;

        function safeEvalFunc(exprJS, x){
          // Basic guards against injection
          const forbidden = /(constructor|prototype|__proto__|=>|new\s+Function|Function\s*\()/;
          if(forbidden.test(exprJS)) throw new Error('Expresión inválida.');
          // eslint-disable-next-line no-new-func
          const fn = new Function('Math','x', 'return ( ' + exprJS + ' )');
          const y = fn(Math, x);
          if(typeof y !== 'number' || !isFinite(y)) return null;
          return y;
        }

        async function plotPreview(){
          // Normalize and validate; updates hidden as a side effect
          const ok = doValidateAndPreview();
          if(!ok){ panel.style.display = 'none'; return; }
          const hid = form.querySelector('#hid-function');
          const expr = (hid?.value || '').trim();
          if(!expr){ panel.style.display = 'none'; return; }

          const exprJS = toJSExpr(expr);
          try{
            await ensurePlotly();
          }catch(err){
            showError('No se pudo cargar la librería de gráficos (Plotly).');
            panel.style.display = 'none';
            return;
          }
          // Global sampling (X_MIN..X_MAX), finite mask, near-zero band selection, local crop
          const X_MIN = -10, X_MAX = 10, N = 2000;
          const Y_HARD_LIMIT = 1e8;   // descartar |y| > 1e8
          const T_MIN = 0.1, T_MAX = 10; // banda cerca de cero acotada
          const P_NEAR = 0.30;        // percentil para banda |f(x)|
          const P_Y_LOW = 0.05, P_Y_HIGH = 0.95; // percentiles para eje Y
          const MIN_NEAR_POINTS = 50; // puntos mínimos en banda; si no, fallback

          const dxEst = (X_MAX - X_MIN) / (N - 1);
          const xsAll = new Array(N);
          const ysAll = new Array(N);
          for(let i=0;i<N;i++){
            const x = X_MIN + (X_MAX - X_MIN) * (i/(N-1));
            xsAll[i] = +x.toFixed(6);
            let y = null;
            try{ y = safeEvalFunc(exprJS, x); }catch(_e){ y = null; }
            if(y==null || !isFinite(y) || Math.abs(y) > Y_HARD_LIMIT){ ysAll[i] = null; }
            else { ysAll[i] = +y.toFixed(12); }
          }

          // Finite mask
          const xs = [];
          const ys = [];
          for(let i=0;i<N;i++){
            const yv = ysAll[i];
            if(typeof yv === 'number' && isFinite(yv)){
              xs.push(xsAll[i]); ys.push(yv);
            }
          }
          if(!ys.length){
            showError('No se encontraron valores finitos de f(x) en el rango global.');
            panel.style.display = 'none';
            return;
          }

          // Percentile helper
          function percentile(arr, p){
            if(!arr.length) return NaN;
            const a = arr.slice().sort((u,v)=> u-v);
            const idx = Math.max(0, Math.min(a.length-1, Math.floor(p * (a.length-1))));
            return a[idx];
          }

          // Near-zero band selection
          const absY = ys.map(v=> Math.abs(v));
          let T = percentile(absY, P_NEAR);
          if(!isFinite(T)) T = 1;
          T = Math.min(T, T_MAX);
          T = Math.max(T, T_MIN);

          const nearIdx = [];
          for(let i=0;i<ys.length;i++) if(Math.abs(ys[i]) <= T) nearIdx.push(i);

          let x0 = X_MIN, x1 = X_MAX;
          if(nearIdx.length >= MIN_NEAR_POINTS){
            let xminLocal = Infinity, xmaxLocal = -Infinity;
            for(const k of nearIdx){
              const xv = xs[k];
              if(xv < xminLocal) xminLocal = xv;
              if(xv > xmaxLocal) xmaxLocal = xv;
            }
            const w = Math.max(1e-9, (xmaxLocal - xminLocal));
            const margin = 0.1 * w;
            x0 = xminLocal - margin; x1 = xmaxLocal + margin;
            // clamp to global
            x0 = Math.max(X_MIN, x0); x1 = Math.min(X_MAX, x1);
          }

          // Crop xs, ys to [x0, x1]
          const xsPlot = [];
          const ysPlot = [];
          for(let i=0;i<xs.length;i++){
            const xv = xs[i];
            if(xv >= x0 && xv <= x1){ xsPlot.push(xv); ysPlot.push(ys[i]); }
          }
          if(!ysPlot.length){
            showError('No hay suficientes puntos para graficar en la banda seleccionada.');
            panel.style.display = 'none';
            return;
          }

          // Robust Y range from 5%..95% percentiles + margin
          let ylow = percentile(ysPlot, P_Y_LOW);
          let yhigh = percentile(ysPlot, P_Y_HIGH);
          if(!isFinite(ylow) || !isFinite(yhigh) || ylow === yhigh){ ylow = (ylow||0)-1; yhigh = (yhigh||0)+1; }
          const ypad = 0.1 * (yhigh - ylow);
          let ymin = ylow - ypad;
          let ymax = yhigh + ypad;

          const styles = getComputedStyle(document.documentElement);
          const primary = (styles.getPropertyValue('--primary')||'#7E57C2').trim();
          const muted = (styles.getPropertyValue('--muted')||'#6b7280').trim();
          const border = (styles.getPropertyValue('--border')||'#e3e5f0').trim();
          const card = (styles.getPropertyValue('--card')||'#ffffff').trim();

          const xmin = x0, xmax = x1;
          const pad = (xmax - xmin) * 0.04;
          // Split xsPlot/ysPlot into contiguous segments (avoid connecting gaps)
          const traces = [];
          let segX = [], segY = [];
          for(let i=0;i<xsPlot.length;i++){
            if(i>0 && Math.abs(xsPlot[i] - xsPlot[i-1]) > dxEst*1.5){
              if(segX.length){
                traces.push({ x: segX, y: segY, mode:'lines', name: traces.length? `f(x) seg ${traces.length+1}`:'f(x)', line:{ color: primary, width: 2.2 }, hovertemplate:'x=%{x:.6f}<br>f(x)=%{y:.6f}<extra></extra>' });
                segX = []; segY = [];
              }
            }
            segX.push(xsPlot[i]); segY.push(ysPlot[i]);
          }
          if(segX.length){
            traces.push({ x: segX, y: segY, mode:'lines', name: traces.length? `f(x) seg ${traces.length+1}`:'f(x)', line:{ color: primary, width: 2.2 }, hovertemplate:'x=%{x:.6f}<br>f(x)=%{y:.6f}<extra></extra>' });
          }
          const traceAxis = { x:[xmin, xmax], y:[0,0], mode:'lines', name:'y = 0', line:{ color: muted, dash:'dot', width:1.2 }, hoverinfo:'skip' };
          const traceAxisY = { x:[0,0], y:[ymin-ypad, ymax+ypad], mode:'lines', name:'x = 0', line:{ color: muted, dash:'dot', width:1.2 }, hoverinfo:'skip' };
          const layout = {
            margin:{ l:50, r:20, t:10, b:40 }, paper_bgcolor: card, plot_bgcolor: card,
            hovermode:'closest', showlegend:true, dragmode:'pan', title:{ text:'Vista previa de f(x)' },
            // 1:1 squares on the grid
            xaxis:{ title:'x', gridcolor:border, zerolinecolor:border, showgrid:true, dtick:1, tick0:0, range:[xmin - pad, xmax + pad], zeroline:true },
            yaxis:{ title:'f(x)', gridcolor:border, zerolinecolor:border, showgrid:true, dtick:1, tick0:0, scaleanchor:'x', scaleratio:1, range:[ymin - ypad, ymax + ypad], zeroline:true },
            legend:{ orientation:'h', x:0, y:1.1 }
          };
          panel.style.display = '';
          window.Plotly.newPlot(plotEl, [...traces, traceAxis, traceAxisY], layout, { displayModeBar:true, responsive:true, scrollZoom:true });
        }

        btn.addEventListener('click', ()=>{ plotPreview(); });
      })();
      // Clear button
      const clr = form.querySelector('[data-action="clear"]');
      clr?.addEventListener('click', ()=>{
        map.forEach(({mf,hid})=>{
          const m = form.querySelector(mf);
          const h = form.querySelector(hid);
          if(m) m.value = '';
          if(h) h.value = '';
        });
        // clear preview
        if(previewText) previewText.textContent = '';
        if(previewOk) previewOk.style.display = 'none';
        if(previewErr) previewErr.style.display = 'none';
        if(submitBtn) submitBtn.disabled = false;
        const panel = document.getElementById('biseccionPreviewPanel');
        if(panel) panel.style.display = 'none';
      });
    });
  });
})();

// Pre-submit normalization for the bisection form: normalize function and numeric fields
document.addEventListener('DOMContentLoaded', ()=>{
  document.querySelectorAll('form.matrix-form[data-page="biseccion"]').forEach(form=>{
    form.addEventListener('submit', (ev)=>{
      try{
        // Normalize function text for server
        const mfFn = document.getElementById('mf-function');
        const hidFn = document.getElementById('hid-function');
        if(mfFn && hidFn){
          const fnText = (mfFn.value || mfFn.getAttribute('data-value') || '').toString().trim();
          hidFn.value = latexToFunction(fnText) || latexToPlain(fnText) || hidFn.value || '';
        }

        // Numeric fields: a, b, tol, maxit
        ['a','b','tol','maxit'].forEach(name=>{
          const mf = document.getElementById('mf-' + name);
          const hid = document.getElementById('hid-' + name);
          if(!mf || !hid) return;
          const raw = (mf.value || mf.getAttribute('data-value') || '').toString().trim();
          if(!raw) return;
          const v = tryEvalNumeric(raw);
          if(v !== null){
            if(name === 'maxit') hid.value = String(Math.round(v)); else hid.value = String(v);
          }else{
            // Preserve plain textual input so the server receives exactly what user typed
            hid.value = latexToPlain(raw) || hid.value || raw;
          }
        });
      }catch(e){
        console.warn('Pre-submit normalization failed:', e);
      }
    });
  });
});
