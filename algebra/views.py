from django.shortcuts import render
from django.http import HttpRequest
from .logic import utilidades as u
from .logic import operaciones as op
import json

def index(request: HttpRequest):
    return render(request, "algebra/index.html")

def _parse_matriz_simple(texto: str):
    matriz = []
    for linea in (texto or "").strip().splitlines():
        if not linea.strip():
            continue
        fila = []
        for token in linea.strip().split():
            fila.append(u.crear_fraccion_desde_cadena(token))
        matriz.append(fila)
    # Validación rectangular
    if matriz:
        ancho = len(matriz[0])
        if any(len(f) != ancho for f in matriz):
            raise ValueError("Todas las filas deben tener la misma cantidad de columnas.")
    return matriz

def _parse_matriz_aumentada(texto: str):
    M = []
    for linea in (texto or "").strip().splitlines():
        if not linea.strip():
            continue
        if "|" not in linea:
            raise ValueError("Cada fila debe contener '|' para separar A y b, ej: 1 2 | 5")
        izq, der = linea.split("|", 1)
        A_vals = [u.crear_fraccion_desde_cadena(t) for t in izq.strip().split()]
        b_vals = [u.crear_fraccion_desde_cadena(t) for t in der.strip().split()]
        if len(b_vals) != 1:
            raise ValueError("El término independiente b debe ser una sola columna.")
        M.append(A_vals + b_vals)
    # Validación rectangular
    ancho = len(M[0])
    if any(len(f) != ancho for f in M):
        raise ValueError("Todas las filas deben tener la misma cantidad de columnas.")
    return M

def _make_text_fn(fmt: str, prec: int):
    fmt = (fmt or 'frac').lower()
    if fmt not in ("frac", "dec", "auto"):
        fmt = "frac"
    # clamp precision
    try:
        p = int(prec)
    except Exception:
        p = 6
    p = max(0, min(p, 12))
    return (lambda a: u.texto_numero(a, modo=fmt, decimales=p))

def _render_matriz(M, text_fn=None):
    tf = text_fn or u.texto_fraccion
    out = []
    for fila in (M or []):
        row = []
        for x in fila:
            if isinstance(x, str):
                row.append(x)
            else:
                row.append(tf(x))
        out.append(row)
    return out

def _is_symbol_token(tok: str) -> bool:
    t = (tok or "").strip()
    if not t:
        return False
    # Permit x1, x2, r, s, t, etc. Starts with letter
    return t[0].isalpha()

def _parse_vector_simbolico(texto: str):
    """Lee una 'matriz' de una columna y devuelve lista de símbolos o '0' para vacíos."""
    v = []
    for linea in (texto or "").strip().splitlines():
        tokens = linea.strip().split()
        if len(tokens) == 0:
            continue
        if len(tokens) != 1:
            raise ValueError("El vector simbólico debe tener una sola columna.")
        tok = tokens[0].strip()
        if not _is_symbol_token(tok):
            raise ValueError("El vector simbólico debe contener variables como x1, r, s, t (no números).")
        v.append(tok)
    return v

def suma(request: HttpRequest):
    ctx = {}
    if request.method == "POST":
        try:
            fmt = request.POST.get("result_format")
            prec = request.POST.get("precision") or 6
            text_fn = _make_text_fn(fmt, prec)
            A = _parse_matriz_simple(request.POST.get("matrizA"))
            B = _parse_matriz_simple(request.POST.get("matrizB"))
            C = op.sumar_matrices(A, B)
            ctx["resultado"] = _render_matriz(C, text_fn)
            if A:
                ctx["dims"] = {"A": f"{len(A)}×{len(A[0])}", "B": f"{len(B)}×{len(B[0])}", "C": f"{len(C)}×{len(C[0])}"}
            ctx["result_format"] = (fmt or 'frac')
            ctx["precision"] = int(prec)
        except Exception as e:
            ctx["error"] = str(e)
    return render(request, "algebra/suma.html", ctx)

def multiplicacion(request: HttpRequest):
    ctx = {}
    if request.method == "POST":
        try:
            fmt = request.POST.get("result_format")
            prec = request.POST.get("precision") or 6
            text_fn = _make_text_fn(fmt, prec)
            rawA = request.POST.get("matrizA")
            rawB = request.POST.get("matrizB")
            A = _parse_matriz_simple(rawA)
            # Detectar si B es vector simbólico (todas las filas no vacías con un símbolo)
            alpha_count = 0
            non_empty = 0
            es_vector_simbolico = True
            for linea in (rawB or "").strip().splitlines():
                tks = linea.strip().split()
                if not tks:
                    continue
                non_empty += 1
                if len(tks) != 1 or not _is_symbol_token(tks[0]):
                    es_vector_simbolico = False
                    break
                alpha_count += 1
            if non_empty == 0:
                es_vector_simbolico = False
            want_steps = bool(request.POST.get("show_steps"))
            if es_vector_simbolico:
                v = _parse_vector_simbolico(rawB)
                # Validaciones
                if len(A) == 0:
                    raise ValueError("La matriz A no puede ser vacía.")
                m = len(A); n = len(A[0])
                if len(v) != n:
                    raise ValueError("Para A·x, el vector debe tener tantas entradas como columnas tenga A.")
                C, pasos = op.multiplicar_matriz_vector_simbolico(A, v, registrar_pasos=want_steps, text_fn=text_fn)
                ctx["resultado"] = _render_matriz(C, text_fn)  # C es m×1 con strings
                if want_steps and pasos:
                    # En pasos, cada matriz puede tener strings/números
                    ctx["pasos"] = [
                        {"operacion": p.get("operacion"), "matriz": _render_matriz(p.get("matriz"), text_fn)}
                        for p in pasos
                    ]
                if A:
                    ctx["dims"] = {
                        "A": f"{len(A)}×{len(A[0])}",
                        "B": f"{len(v)}×1",
                        "C": f"{len(A)}×1"
                    }
            else:
                B = _parse_matriz_simple(rawB)
                if want_steps:
                    C, pasos = op.multiplicar_matrices(A, B, registrar_pasos=True, text_fn=text_fn)
                    ctx["resultado"] = _render_matriz(C, text_fn)
                    ctx["pasos"] = [
                        {"operacion": p.get("operacion"), "matriz": _render_matriz(p.get("matriz"), text_fn)}
                        for p in pasos
                    ]
                else:
                    C = op.multiplicar_matrices(A, B)
                    ctx["resultado"] = _render_matriz(C, text_fn)
                if A and B:
                    ctx["dims"] = {
                        "A": f"{len(A)}×{len(A[0])}",
                        "B": f"{len(B)}×{len(B[0])}",
                        "C": f"{len(C)}×{len(C[0])}"
                    }
            ctx["result_format"] = (fmt or 'frac')
            ctx["precision"] = int(prec)
        except Exception as e:
            ctx["error"] = str(e)
    return render(request, "algebra/multiplicacion.html", ctx)

def escalar(request: HttpRequest):
    """Multiplicación de escalar por matriz: c · A."""
    ctx = {}
    if request.method == "POST":
        try:
            fmt = request.POST.get("result_format")
            prec = request.POST.get("precision") or 6
            text_fn = _make_text_fn(fmt, prec)
            A = _parse_matriz_simple(request.POST.get("matrizA"))
            c_txt = (request.POST.get("escalar") or "0").strip()
            c = u.crear_fraccion_desde_cadena(c_txt)
            want_steps = bool(request.POST.get("show_steps"))
            C, pasos = op.multiplicar_escalar_matriz(c, A, registrar_pasos=want_steps, text_fn=text_fn)
            ctx["resultado"] = _render_matriz(C, text_fn)
            if want_steps and pasos:
                ctx["pasos"] = [
                    {"operacion": p.get("operacion"), "matriz": _render_matriz(p.get("matriz"), text_fn)}
                    for p in pasos
                ]
            if A:
                ctx["dims"] = {"A": f"{len(A)}×{len(A[0])}"}
            ctx["c"] = c_txt
            ctx["result_format"] = (fmt or 'frac')
            ctx["precision"] = int(prec)
        except Exception as e:
            ctx["error"] = str(e)
    return render(request, "algebra/escalar.html", ctx)

def gauss(request: HttpRequest):
    ctx = {}
    if request.method == "POST":
        try:
            fmt = request.POST.get("result_format")
            prec = request.POST.get("precision") or 6
            text_fn = _make_text_fn(fmt, prec)
            M = _parse_matriz_aumentada(request.POST.get("matrizAug"))
            want_steps = bool(request.POST.get("show_steps"))
            info = op.gauss_info(M, registrar_pasos=want_steps, text_fn=text_fn)
            R = info["matriz"]
            ctx["resultado"] = _render_matriz(R, text_fn)
            ctx["analisis"] = info.get("analisis")
            ctx["pivotes"] = info.get("pivotes")
            if want_steps and "pasos" in info:
                ctx["pasos"] = [
                    {"operacion": p.get("operacion"), "matriz": _render_matriz(p.get("matriz"), text_fn)}
                    for p in info["pasos"]
                ]
            if M:
                m = len(M); n = len(M[0]) - 1
                ctx["dims"] = {"A": f"{m}×{n}", "b": f"{m}×1"}
            ctx["result_format"] = (fmt or 'frac')
            ctx["precision"] = int(prec)
        except Exception as e:
            ctx["error"] = str(e)
    return render(request, "algebra/gauss.html", ctx)

def gauss_jordan(request: HttpRequest):
    ctx = {}
    if request.method == "POST":
        try:
            fmt = request.POST.get("result_format")
            prec = request.POST.get("precision") or 6
            text_fn = _make_text_fn(fmt, prec)
            M = _parse_matriz_aumentada(request.POST.get("matrizAug"))
            want_steps = bool(request.POST.get("show_steps"))
            info = op.gauss_jordan_info(M, registrar_pasos=want_steps, text_fn=text_fn)
            R = info["matriz"]
            ctx["resultado"] = _render_matriz(R, text_fn)
            ctx["analisis"] = info.get("analisis")
            ctx["pivotes"] = info.get("pivotes")
            if want_steps and "pasos" in info:
                ctx["pasos"] = [
                    {"operacion": p.get("operacion"), "matriz": _render_matriz(p.get("matriz"), text_fn)}
                    for p in info["pasos"]
                ]
            if M:
                m = len(M); n = len(M[0]) - 1
                ctx["dims"] = {"A": f"{m}×{n}", "b": f"{m}×1"}
            ctx["result_format"] = (fmt or 'frac')
            ctx["precision"] = int(prec)
        except Exception as e:
            ctx["error"] = str(e)
    return render(request, "algebra/gauss_jordan.html", ctx)

def homogeneo(request: HttpRequest):
    """Vista para resolver A x = 0 y analizar independencia lineal.
    Reutiliza Gauss-Jordan sobre (A|0)."""
    ctx = {}
    if request.method == "POST":
        try:
            fmt = request.POST.get("result_format")
            prec = request.POST.get("precision") or 6
            text_fn = _make_text_fn(fmt, prec)
            A = _parse_matriz_simple(request.POST.get("matrizA"))
            want_steps = bool(request.POST.get("show_steps"))
            info = op.gauss_jordan_homogeneo_info(A, registrar_pasos=want_steps, text_fn=text_fn)
            ctx["resultado"] = _render_matriz(info["matriz"], text_fn)
            ctx["analisis"] = info["analisis"]
            if want_steps and "pasos" in info:
                ctx["pasos"] = [
                    {"operacion": p.get("operacion"), "matriz": _render_matriz(p.get("matriz"), text_fn)}
                    for p in info["pasos"]
                ]
            if A:
                ctx["dims"] = {"A": f"{len(A)}×{len(A[0])}"}
            ctx["result_format"] = (fmt or 'frac')
            ctx["precision"] = int(prec)
        except Exception as e:
            ctx["error"] = str(e)
    return render(request, "algebra/homogeneo.html", ctx)

def transposicion(request: HttpRequest):
    """Vista para calcular la transpuesta A^T."""
    ctx = {}
    if request.method == "POST":
        try:
            fmt = request.POST.get("result_format")
            prec = request.POST.get("precision") or 6
            text_fn = _make_text_fn(fmt, prec)
            A = _parse_matriz_simple(request.POST.get("matrizA"))
            want_steps = bool(request.POST.get("show_steps"))
            if want_steps:
                AT, pasos = op.transponer_matriz(A, registrar_pasos=True, text_fn=text_fn)
                ctx["resultado"] = _render_matriz(AT, text_fn)
                ctx["pasos"] = [
                    {"operacion": p.get("operacion"), "matriz": _render_matriz(p.get("matriz"), text_fn)}
                    for p in pasos
                ]
            else:
                AT = op.transponer_matriz(A)
                ctx["resultado"] = _render_matriz(AT, text_fn)
            if A:
                ctx["dims"] = {"A": f"{len(A)}×{len(A[0])}", "AT": f"{len(AT)}×{len(AT[0])}"}
            ctx["result_format"] = (fmt or 'frac')
            ctx["precision"] = int(prec)
        except Exception as e:
            ctx["error"] = str(e)
    return render(request, "algebra/transposicion.html", ctx)

def inversa(request: HttpRequest):
    """Vista para calcular la inversa de A si existe."""
    ctx = {}
    if request.method == "POST":
        try:
            fmt = request.POST.get("result_format")
            prec = request.POST.get("precision") or 6
            text_fn = _make_text_fn(fmt, prec)
            A = _parse_matriz_simple(request.POST.get("matrizA"))
            # Validación básica: cuadrada
            if not A or len(A) == 0:
                raise ValueError("La matriz A no puede ser vacía.")
            if any(len(f) != len(A[0]) for f in A):
                raise ValueError("Todas las filas deben tener la misma cantidad de columnas.")
            if len(A) != len(A[0]):
                info = {"invertible": False, "razon": "A no es cuadrada"}
                ctx["no_invertible"] = "A no es cuadrada (no tiene inversa)."
            want_steps = bool(request.POST.get("show_steps"))
            if want_steps:
                info, pasos = op.inversa_matriz(A, registrar_pasos=True, text_fn=text_fn)
            else:
                info = op.inversa_matriz(A, registrar_pasos=False, text_fn=text_fn)
                pasos = None
            if info.get("invertible"):
                inv = info.get("inversa")
                ctx["resultado"] = _render_matriz(inv, text_fn)
                estado = "INVERTIBLE"
                singular = False
            else:
                ctx["no_invertible"] = info.get("razon", "No invertible")
                estado = "NO_INVERTIBLE"
                singular = True
            n = len(A); m = len(A[0])
            ctx["dims"] = {"A": f"{n}×{m}"}
            if info.get("invertible"):
                ctx["dims"]["Ainv"] = f"{n}×{m}"
            ctx["estado"] = estado
            ctx["singular"] = singular
            if pasos:
                ctx["pasos"] = [
                    {"operacion": p.get("operacion"), "matriz": _render_matriz(p.get("matriz"), text_fn)}
                    for p in pasos
                ]
            ctx["result_format"] = (fmt or 'frac')
            ctx["precision"] = int(prec)
        except Exception as e:
            ctx["error"] = str(e)
    return render(request, "algebra/inversa.html", ctx)

def determinante(request: HttpRequest):
    """Vista para calcular el determinante |A| de una matriz cuadrada."""
    ctx = {}
    if request.method == "POST":
        try:
            fmt = request.POST.get("result_format")
            prec = request.POST.get("precision") or 6
            text_fn = _make_text_fn(fmt, prec)
            A = _parse_matriz_simple(request.POST.get("matrizA"))
            if not A or len(A) == 0:
                raise ValueError("La matriz A no puede ser vacía.")
            if len(A) != len(A[0]):
                raise ValueError("A debe ser cuadrada para calcular |A|.")
            want_steps = bool(request.POST.get("show_steps"))
            if want_steps:
                det, pasos = op.determinante_matriz(A, registrar_pasos=True, text_fn=text_fn)
            else:
                det = op.determinante_matriz(A, registrar_pasos=False, text_fn=text_fn)
                pasos = None
            det_str = text_fn(det)
            ctx["det"] = det
            ctx["det_str"] = det_str
            ctx["es_cero"] = (det[0] == 0)
            ctx["result_format"] = (fmt or 'frac')
            ctx["precision"] = int(prec)
            ctx["dims"] = {"A": f"{len(A)}×{len(A[0])}"}
            if pasos:
                ctx["pasos"] = [
                    {"operacion": p.get("operacion"), "matriz": _render_matriz(p.get("matriz"), text_fn)}
                    for p in pasos
                ]
        except Exception as e:
            ctx["error"] = str(e)
    return render(request, "algebra/determinante.html", ctx)

def cramer(request: HttpRequest):
    """Vista para resolver Ax=b por la regla de Cramer."""
    ctx = {}
    if request.method == "POST":
        try:
            fmt = request.POST.get("result_format")
            prec = request.POST.get("precision") or 6
            text_fn = _make_text_fn(fmt, prec)
            A = _parse_matriz_simple(request.POST.get("matrizA"))
            b = _parse_matriz_simple(request.POST.get("vectorb"))
            if not A or not b:
                raise ValueError("Debes ingresar A y b.")
            if len(b[0]) != 1:
                raise ValueError("b debe ser un vector columna (n×1).")
            if len(A) != len(A[0]):
                raise ValueError("A debe ser cuadrada (n×n).")
            if len(b) != len(A):
                raise ValueError("El tamaño de b debe coincidir con n (filas de A).")
            want_steps = bool(request.POST.get("show_steps"))
            if want_steps:
                info, pasos = op.cramer_resolver(A, b, registrar_pasos=True, text_fn=text_fn)
            else:
                info = op.cramer_resolver(A, b, registrar_pasos=False, text_fn=text_fn)
                pasos = None
            ctx["detA"] = text_fn(info["detA"]) if info.get("detA") else None
            ctx["invertible"] = info.get("invertible", False)
            if not info.get("invertible", False):
                ctx["no_invertible"] = info.get("mensaje", "|A| = 0 ⇒ A no es invertible")
            else:
                # Render vector solución
                xs = info.get("x", [])
                # matriz  n×1 (para mostrar también como tabla si se desea)
                ctx["resultado"] = [[text_fn(xi)] for xi in xs]
                # listado etiquetado x1=..., x2=... (como en Gauss/Gauss-Jordan)
                vector_sol = []
                j = 0
                while j < len(xs):
                    vector_sol.append(f"x{j+1} = {text_fn(xs[j])}")
                    j += 1
                ctx["vector_solucion"] = vector_sol
            ctx["componentes"] = {k: text_fn(v) for k, v in info.get("componentes", {}).items()}
            ctx["dims"] = {"A": f"{len(A)}×{len(A[0])}", "b": f"{len(b)}×1"}
            if pasos:
                ctx["pasos"] = [
                    {"operacion": p.get("operacion"), "matriz": _render_matriz(p.get("matriz"), text_fn)}
                    for p in pasos
                ]
            ctx["result_format"] = (fmt or 'frac')
            ctx["precision"] = int(prec)
        except Exception as e:
            ctx["error"] = str(e)
    return render(request, "algebra/cramer.html", ctx)

def compuestas(request: HttpRequest):
    """Vista base para operaciones compuestas.
    De momento solo muestra el formulario de entrada; la lógica de composición se añadirá gradualmente.
    """
    ctx = {}
    if request.method == "POST":
        try:
            fmt = request.POST.get("result_format")
            prec = request.POST.get("precision") or 6
            text_fn = _make_text_fn(fmt, prec)

            src = (request.POST.get("source") or "A").strip().upper()
            show_steps = bool(request.POST.get("show_steps"))
            raw_seq = request.POST.get("sequence_json") or "[]"
            try:
                seq = json.loads(raw_seq)
            except Exception:
                raise ValueError("Secuencia inválida (JSON)")

            A = _parse_matriz_simple(request.POST.get("matrizA"))
            B = _parse_matriz_simple(request.POST.get("matrizB"))
            ctx["dims"] = {}
            if A: ctx["dims"]["A"] = f"{len(A)}×{len(A[0])}"
            if B: ctx["dims"]["B"] = f"{len(B)}×{len(B[0])}"

            # Selección de fuente inicial
            if src == "B":
                M = B
            else:
                M = A
            if not M:
                raise ValueError("La matriz fuente seleccionada está vacía.")

            pasos_viz = []
            # Aplicar secuencia básica
            for step in (seq or []):
                stype = (step.get("type") or "").lower()
                params = step.get("params") or {}
                if stype == "transpose":
                    if show_steps:
                        M, p = op.transponer_matriz(M, registrar_pasos=True, text_fn=text_fn)
                        pasos_viz.extend([{"operacion": s.get("operacion"), "matriz": _render_matriz(s.get("matriz"), text_fn)} for s in p])
                    else:
                        M = op.transponer_matriz(M)
                elif stype == "scale":
                    c_txt = (params.get("c") or "0").strip()
                    c = u.crear_fraccion_desde_cadena(c_txt)
                    if show_steps:
                        M, p = op.multiplicar_escalar_matriz(c, M, registrar_pasos=True, text_fn=text_fn)
                        pasos_viz.extend([{"operacion": s.get("operacion"), "matriz": _render_matriz(s.get("matriz"), text_fn)} for s in p])
                    else:
                        M = op.multiplicar_escalar_matriz(c, M)
                elif stype == "mulb":
                    if not B:
                        raise ValueError("No hay matriz B para multiplicar (M·B).")
                    if show_steps:
                        M, p = op.multiplicar_matrices(M, B, registrar_pasos=True, text_fn=text_fn)
                        pasos_viz.extend([{"operacion": s.get("operacion"), "matriz": _render_matriz(s.get("matriz"), text_fn)} for s in p])
                    else:
                        M = op.multiplicar_matrices(M, B)
                elif stype == "sumb":
                    if not B:
                        raise ValueError("No hay matriz B para sumar (M+B).")
                    # Suma directa; sin pasos detallados para no generar ruido redundante
                    M = op.sumar_matrices(M, B)
                elif stype == "sumbesc":
                    if not B:
                        raise ValueError("No hay matriz B para sumar (M + b·B).")
                    b_txt = (params.get("b") or "0").strip()
                    b = u.crear_fraccion_desde_cadena(b_txt)
                    MB = op.multiplicar_escalar_matriz(b, B)
                    M = op.sumar_matrices(M, MB)
                elif stype == "lincomb" or stype == "combinacion" or stype == "abcomb":
                    if not A or not B:
                        raise ValueError("Se requieren A y B para a·A + b·B.")
                    a_txt = (params.get("a") or "0").strip()
                    b_txt = (params.get("b") or "0").strip()
                    a = u.crear_fraccion_desde_cadena(a_txt)
                    b = u.crear_fraccion_desde_cadena(b_txt)
                    if show_steps:
                        MA, pA = op.multiplicar_escalar_matriz(a, A, registrar_pasos=True, text_fn=text_fn)
                        pasos_viz.extend([
                            {"operacion": s.get("operacion"), "matriz": _render_matriz(s.get("matriz"), text_fn)} for s in (pA or [])
                        ])
                        MB, pB = op.multiplicar_escalar_matriz(b, B, registrar_pasos=True, text_fn=text_fn)
                        pasos_viz.extend([
                            {"operacion": s.get("operacion"), "matriz": _render_matriz(s.get("matriz"), text_fn)} for s in (pB or [])
                        ])
                        Mtmp = op.sumar_matrices(MA, MB)
                        pasos_viz.append({
                            "operacion": f"Sumamos {text_fn(a)}·A + {text_fn(b)}·B",
                            "matriz": _render_matriz(Mtmp, text_fn)
                        })
                        M = Mtmp
                    else:
                        MA = op.multiplicar_escalar_matriz(a, A)
                        MB = op.multiplicar_escalar_matriz(b, B)
                        M = op.sumar_matrices(MA, MB)
                elif stype == "inverse":
                    info = op.inversa_matriz(M, registrar_pasos=show_steps, text_fn=text_fn)
                    if isinstance(info, tuple):
                        info, p = info
                        pasos_viz.extend([{"operacion": s.get("operacion"), "matriz": _render_matriz(s.get("matriz"), text_fn)} for s in p])
                    if not info.get("invertible"):
                        raise ValueError(info.get("razon", "La matriz no es invertible."))
                    M = info.get("inversa")
                else:
                    # Ignorar tipos desconocidos (por ahora)
                    continue

            # Render final
            ctx["resultado"] = _render_matriz(M, text_fn)
            ctx["dims"]["M"] = f"{len(M)}×{len(M[0])}" if (M and len(M)>0) else None
            if show_steps and pasos_viz:
                ctx["pasos"] = pasos_viz
            ctx["result_format"] = (fmt or 'frac')
            ctx["precision"] = int(prec)
        except Exception as e:
            ctx["error"] = str(e)
    return render(request, "algebra/compuestas.html", ctx)
