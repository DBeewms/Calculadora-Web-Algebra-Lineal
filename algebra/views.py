from django.shortcuts import render
from django.http import HttpRequest
from .logic import utilidades as u
from .logic import operaciones as op
from .logic.metodos import biseccion as biseccion_algo, regula_falsi as regula_falsi_algo, newton_raphson as newton_raphson_algo, secante as secante_algo, ErrorBiseccion, _crear_evaluador
from sympy import sympify, symbols, limit as sympy_limit, oo, sin, cos, tan, asin, acos, atan, exp, log, sqrt, Abs
import json
import logging

logger = logging.getLogger(__name__)

def friendly_error(exc: Exception) -> str:
    """Devuelve un mensaje comprensible para el usuario final sin detalles internos.

    Las excepciones específicas mantienen su mensaje si ya es claro (ValueError con texto en español).
    """
    # Si ya es un ValueError con mensaje explícito lo devolvemos tal cual
    if isinstance(exc, ValueError):
        msg = str(exc).strip()
        if msg:
            return msg
    txt = str(exc).lower()
    # División por cero
    if isinstance(exc, ZeroDivisionError) or 'division by zero' in txt or 'divide by zero' in txt:
        return 'Se produjo una división por cero durante el cálculo. Revisa si la expresión tiene denominadores que se anulan.'
    # Dominio matemático
    if 'math domain error' in txt or 'domain error' in txt or 'sqrt' in txt and ('- ' in txt or 'negativo' in txt):
        return 'La función intentó evaluar una operación fuera de su dominio (por ejemplo raíz de número negativo o log de valor no permitido). Ajusta la función o el intervalo.'
    # Overflow
    if isinstance(exc, OverflowError) or 'overflow' in txt:
        return 'El cálculo produjo números demasiado grandes para manejar. Prueba con otro intervalo o modifica la función.'
    # Sintaxis / nombre desconocido
    if isinstance(exc, SyntaxError) or 'syntax' in txt:
        return 'La expresión de la función tiene un formato inválido. Revisa paréntesis y operadores.'
    if isinstance(exc, NameError) or 'is not defined' in txt or 'name' in txt and 'not defined' in txt:
        return 'La función contiene símbolos desconocidos. Usa solo x y funciones estándar (sin, cos, exp, log, etc.).'
    if isinstance(exc, TypeError):
        return 'La expresión o los parámetros tienen tipos incompatibles. Revisa la escritura de la función y los valores ingresados.'
    # Fallback genérico
    return 'No fue posible completar el cálculo. Verifica los valores ingresados o ajusta la función.'

def index(request: HttpRequest):
    # Definición estructurada de operaciones con matrices para la cuadrícula
    operations_matrices = [
        {
            "name": "suma",
            "title": "Suma de matrices",
            "desc": "Suma dos matrices del mismo tamaño mostrando cada operación paso a paso.",
            "icon": "plus",
            "style": "suma",
        },
        {
            "name": "multiplicacion",
            "title": "Multiplicación",
            "desc": "Multiplica matrices compatibles mostrando cómo se forma cada entrada.",
            "icon": "times",
            "style": "mul",
        },
        {
            "name": "escalar",
            "title": "Escalar",
            "desc": "Multiplica cada elemento por un número conservando signos y formato.",
            "icon": "scalar",
            "style": "mul",
        },
        {
            "name": "transposicion",
            "title": "Transpuesta",
            "desc": "Intercambia filas y columnas resaltando patrones y simetrías.",
            "icon": "transpose",
            "style": "mul",
        },
        {
            "name": "determinante",
            "title": "Determinante",
            "desc": "Calcula el determinante e interpreta invertibilidad y escala.",
            "icon": "det",
            "style": "mul",
        },
        {
            "name": "inversa",
            "title": "Inversa",
            "desc": "Obtiene la inversa si existe usando operaciones y pivotes.",
            "icon": "inv",
            "style": "mul",
        },
    ]
    # Se usan directamente en una sola cuadrícula 3×2 (orden preservado)
    ctx = {"operations_matrices": operations_matrices}
    return render(request, "algebra/index.html", ctx)

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
            logger.exception("Error en vista suma")
            ctx["error"] = friendly_error(e)
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
            logger.exception("Error en vista multiplicacion")
            ctx["error"] = friendly_error(e)
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
            logger.exception("Error en vista escalar")
            ctx["error"] = friendly_error(e)
    return render(request, "algebra/escalar.html", ctx)

def gauss(request: HttpRequest):
    ctx = {}
    if request.method == "POST":
        try:
            fmt = request.POST.get("result_format")
            prec = request.POST.get("precision") or 6
            text_fn = _make_text_fn(fmt, prec)
            eqs_txt = (request.POST.get("equations") or "").strip()
            if eqs_txt:
                vars_ord, A, b = u.parsear_sistema_ecuaciones(eqs_txt)
                # Enforce counts from UI when provided
                try:
                    exp_rows = int(request.POST.get("rows") or 0)
                except Exception:
                    exp_rows = 0
                try:
                    exp_cols = int(request.POST.get("cols") or 0)
                except Exception:
                    exp_cols = 0
                if exp_rows and len(A) != exp_rows:
                    raise ValueError(f"Se esperaban {exp_rows} ecuaciones, pero ingresaste {len(A)}.")
                if exp_cols and len(vars_ord) != exp_cols:
                    raise ValueError(f"Se esperaban {exp_cols} variables distintas, pero se detectaron {len(vars_ord)}: {', '.join(vars_ord)}.")
                M = [row + [b[i]] for i, row in enumerate(A)]
                ctx["vars"] = vars_ord
                # Prefill matrices inputs on response so A|b refleje las ecuaciones ingresadas
                try:
                    preA = [[u.texto_fraccion(x) for x in fila] for fila in A]
                    preb = [u.texto_fraccion(x) for x in b]
                    ctx["prefill"] = json.dumps({"A": preA, "b": preb})
                except Exception:
                    pass
            else:
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
            logger.exception("Error en vista gauss")
            ctx["error"] = friendly_error(e)
    return render(request, "algebra/gauss.html", ctx)

def gauss_jordan(request: HttpRequest):
    ctx = {}
    if request.method == "POST":
        try:
            fmt = request.POST.get("result_format")
            prec = request.POST.get("precision") or 6
            text_fn = _make_text_fn(fmt, prec)
            eqs_txt = (request.POST.get("equations") or "").strip()
            if eqs_txt:
                vars_ord, A, b = u.parsear_sistema_ecuaciones(eqs_txt)
                # Enforce counts from UI when provided
                try:
                    exp_rows = int(request.POST.get("rows") or 0)
                except Exception:
                    exp_rows = 0
                try:
                    exp_cols = int(request.POST.get("cols") or 0)
                except Exception:
                    exp_cols = 0
                if exp_rows and len(A) != exp_rows:
                    raise ValueError(f"Se esperaban {exp_rows} ecuaciones, pero ingresaste {len(A)}.")
                if exp_cols and len(vars_ord) != exp_cols:
                    raise ValueError(f"Se esperaban {exp_cols} variables distintas, pero se detectaron {len(vars_ord)}: {', '.join(vars_ord)}.")
                M = [row + [b[i]] for i, row in enumerate(A)]
                ctx["vars"] = vars_ord
                # Prefill matrices inputs on response so A|b refleje las ecuaciones ingresadas
                try:
                    preA = [[u.texto_fraccion(x) for x in fila] for fila in A]
                    preb = [u.texto_fraccion(x) for x in b]
                    ctx["prefill"] = json.dumps({"A": preA, "b": preb})
                except Exception:
                    pass
            else:
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
            logger.exception("Error en vista gauss_jordan")
            ctx["error"] = friendly_error(e)
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
            eqs_txt = (request.POST.get("equations") or "").strip()
            if eqs_txt:
                vars_ord, A, b = u.parsear_sistema_ecuaciones(eqs_txt)
                # Enforce counts from UI when provided
                try:
                    exp_rows = int(request.POST.get("rows") or 0)
                except Exception:
                    exp_rows = 0
                try:
                    exp_cols = int(request.POST.get("cols") or 0)
                except Exception:
                    exp_cols = 0
                if exp_rows and len(A) != exp_rows:
                    raise ValueError(f"Se esperaban {exp_rows} ecuaciones, pero ingresaste {len(A)}.")
                if exp_cols and len(vars_ord) != exp_cols:
                    raise ValueError(f"Se esperaban {exp_cols} variables distintas, pero se detectaron {len(vars_ord)}: {', '.join(vars_ord)}.")
                # Validar que b es todo cero para sistema homogéneo
                if any(not u.es_cero(x) for x in b):
                    raise ValueError("Para el sistema homogéneo Ax = 0, los términos independientes deben ser 0. Si tu sistema es Ax = b con b ≠ 0, usa Gauss o Gauss-Jordan.")
                # Prefill matrices inputs on response so A refleje las ecuaciones ingresadas
                try:
                    preA = [[u.texto_fraccion(x) for x in fila] for fila in A]
                    ctx["prefill"] = json.dumps({"A": preA})
                except Exception:
                    pass
            else:
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
            logger.exception("Error en vista homogeneo")
            ctx["error"] = friendly_error(e)
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
            logger.exception("Error en vista transposicion")
            ctx["error"] = friendly_error(e)
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
            logger.exception("Error en vista inversa")
            ctx["error"] = friendly_error(e)
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
            logger.exception("Error en vista determinante")
            ctx["error"] = friendly_error(e)
    return render(request, "algebra/determinante.html", ctx)

def cramer(request: HttpRequest):
    """Vista para resolver Ax=b por la regla de Cramer."""
    ctx = {}
    if request.method == "POST":
        try:
            fmt = request.POST.get("result_format")
            prec = request.POST.get("precision") or 6
            text_fn = _make_text_fn(fmt, prec)
            eqs_txt = (request.POST.get("equations") or "").strip()
            if eqs_txt:
                vars_ord, A, b_vec = u.parsear_sistema_ecuaciones(eqs_txt)
                # Validaciones: cuadrada y consistente con UI
                n_rows = len(A)
                n_cols = len(vars_ord)
                if n_rows != n_cols:
                    raise ValueError("Para Cramer, A debe ser cuadrada (n×n). Ajusta las ecuaciones y variables para que n ecuaciones involucren n variables.")
                try:
                    exp_rows = int(request.POST.get("rows") or 0)
                except Exception:
                    exp_rows = 0
                try:
                    exp_cols = int(request.POST.get("cols") or 0)
                except Exception:
                    exp_cols = 0
                if exp_rows and n_rows != exp_rows:
                    raise ValueError(f"Se esperaban {exp_rows} ecuaciones, pero ingresaste {n_rows}.")
                if exp_cols and n_cols != exp_cols:
                    raise ValueError(f"Se esperaban {exp_cols} variables distintas, pero se detectaron {n_cols}: {', '.join(vars_ord)}.")
                # b como matriz n×1
                b = [[b_vec[i]] for i in range(len(b_vec))]
                # Prefill A y b para que el cliente refleje lo ingresado
                try:
                  preA = [[u.texto_fraccion(x) for x in fila] for fila in A]
                  preb = [u.texto_fraccion(x[0]) for x in b]
                  ctx["prefill"] = json.dumps({"A": preA, "b": preb})
                except Exception:
                  pass
            else:
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
            logger.exception("Error en vista cramer")
            ctx["error"] = friendly_error(e)
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
                elif stype == "transposeother":
                    # Operar sobre la matriz que NO es la fuente actual
                    if src == "A":
                        if not B:
                            raise ValueError("No hay matriz B para transponer.")
                        Bt = op.transponer_matriz(B)
                        B = Bt
                        pasos_viz.append({"operacion": "B ← Bᵀ", "matriz": _render_matriz(M, text_fn)})
                    else:
                        if not A:
                            raise ValueError("No hay matriz A para transponer.")
                        At = op.transponer_matriz(A)
                        A = At
                        pasos_viz.append({"operacion": "A ← Aᵀ", "matriz": _render_matriz(M, text_fn)})
                elif stype == "inverseother":
                    # Invertir la matriz que NO es la fuente actual (debe ser cuadrada e invertible)
                    if src == "A":
                        if not B:
                            raise ValueError("No hay matriz B para invertir.")
                        infoB = op.inversa_matriz(B, registrar_pasos=False, text_fn=text_fn)
                        if not infoB.get("invertible"):
                            raise ValueError(infoB.get("razon", "B no es invertible."))
                        B = infoB.get("inversa")
                        pasos_viz.append({"operacion": "B ← B^{-1}", "matriz": _render_matriz(M, text_fn)})
                    else:
                        if not A:
                            raise ValueError("No hay matriz A para invertir.")
                        infoA = op.inversa_matriz(A, registrar_pasos=False, text_fn=text_fn)
                        if not infoA.get("invertible"):
                            raise ValueError(infoA.get("razon", "A no es invertible."))
                        A = infoA.get("inversa")
                        pasos_viz.append({"operacion": "A ← A^{-1}", "matriz": _render_matriz(M, text_fn)})
                elif stype == "sumi":
                    # Sumar con Identidad: requiere matriz cuadrada
                    if not M or len(M) == 0:
                        raise ValueError("La matriz fuente está vacía.")
                    n_rows = len(M); n_cols = len(M[0])
                    if n_rows != n_cols:
                        raise ValueError("Para sumar con I, la matriz debe ser cuadrada (n×n).")
                    # Construir I y sumar
                    I = []
                    i = 0
                    while i < n_rows:
                        fila = []
                        j = 0
                        while j < n_cols:
                            fila.append([1,1] if i == j else [0,1])
                            j += 1
                        I.append(fila)
                        i += 1
                    M = op.sumar_matrices(M, I)
                    if show_steps:
                        pasos_viz.append({
                            "operacion": "Sumamos la identidad: M ← M + I",
                            "matriz": _render_matriz(M, text_fn)
                        })
                elif stype == "checkli":
                    # Verificar independencia lineal de columnas de M usando sistema homogéneo M x = 0
                    if not M or len(M) == 0:
                        raise ValueError("La matriz fuente está vacía.")
                    try:
                        infoLI = op.gauss_jordan_homogeneo_info(M, registrar_pasos=False, text_fn=text_fn)
                        anal = infoLI.get("analisis", {})
                        esLI = bool(anal.get("independencia", False))
                        detalle = "Vectores columna LI (independientes)" if esLI else "Vectores columna LD (dependientes)"
                        pasos_viz.append({
                            "operacion": f"Verificación de independencia lineal: {detalle}",
                            "matriz": _render_matriz(infoLI.get("matriz"), text_fn)
                        })
                    except Exception as _e:
                        raise ValueError("No se pudo verificar independencia lineal para la matriz dada.")
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
            logger.exception("Error en vista compuestas")
            ctx["error"] = friendly_error(e)
    return render(request, "algebra/compuestas.html", ctx)


def metodos_index(request: HttpRequest):
    """Página índice del módulo Métodos numéricos (entrada al submódulos)."""
    return render(request, "algebra/metodos_index.html")


def metodos_cerrados(request: HttpRequest):
    """Página para la subclase 'Métodos cerrados' (lista de métodos)."""
    ctx = {
        "subclass": "Métodos cerrados",
        "methods": [
            {"name": "Método de bisección", "url_name": "biseccion", "slug": "biseccion"},
            {"name": "Regla Falsa (Regula Falsi)", "url_name": "regula_falsi", "slug": "regula_falsi"}
        ]
    }
    return render(request, "algebra/metodos_cerrados.html", ctx)


def metodos_abiertos(request: HttpRequest):
    """Página para la subclase 'Métodos abiertos' (lista de métodos)."""
    ctx = {
        "subclass": "Métodos abiertos",
        "methods": [
            {"name": "Newton–Raphson", "url_name": "newton_raphson", "slug": "newton_raphson"},
            {"name": "Método de la secante", "url_name": "secante", "slug": "secante"},
        ]
    }
    return render(request, "algebra/metodos_abiertos.html", ctx)


def limite(request: HttpRequest):
    """Calcular límite usando sympy.limit.

    El formulario envía una expresión ya normalizada en `expr` (cliente intenta
    convertir LaTeX mediante `latexToFunction` y `toJSExpr`). Si no está,
    intentamos sympify del texto recibido.
    """
    ctx = {}
    resultado = None
    expr_used = None
    point_used = None
    direction_used = None
    if request.method == 'POST':
        try:
            raw = (request.POST.get('expr') or request.POST.get('latex') or '').strip()
            # Variable fija: 'x'
            varname = 'x'
            point = (request.POST.get('point') or '0').strip()
            direction = (request.POST.get('direction') or 'both')
            show_steps = bool(request.POST.get('show_steps'))

            expr_used = raw
            point_used = point
            direction_used = direction

            # map point to sympy symbol/value
            if point.lower() in ('oo', 'infty', 'infinito', 'inf', '∞'):
                a = oo
            elif point.lower() in ('-oo', '-infty', '-inf'):
                a = -oo
            else:
                # try numeric
                try:
                    a = sympify(point)
                except Exception:
                    a = sympify('0')

            # Prepare locals allowing common math functions
            local_dict = {
                'sin': sin, 'cos': cos, 'tan': tan,
                'asin': asin, 'acos': acos, 'atan': atan,
                'exp': exp, 'log': log, 'sqrt': sqrt,
                'abs': Abs, 'pi': sympify('pi'), 'e': sympify('E')
            }

            if not raw:
                raise ValueError('Debes introducir una expresión.')

            # Sympify expression
            try:
                expr_sym = sympify(raw, locals=local_dict)
            except Exception:
                # try raw latex-ish fallback: remove LaTeX backslashes and try
                fallback = raw.replace('\\', '').replace('^', '**')
                expr_sym = sympify(fallback, locals=local_dict)

            x = symbols(varname)

            pasos = []
            if show_steps:
                # Paso 1: expresión sympify
                try:
                    pasos.append({"operacion": "Expr. simbólica", "detalle": str(expr_sym)})
                except Exception:
                    pass
                # Paso 2: intento de simplificar
                try:
                    simp = expr_sym.simplify()
                    pasos.append({"operacion": "Simplificación", "detalle": str(simp)})
                except Exception:
                    simp = expr_sym
                # Paso 3: factorización (si aplica)
                try:
                    fact = expr_sym.factor()
                    if str(fact) != str(expr_sym):
                        pasos.append({"operacion": "Factorización", "detalle": str(fact)})
                except Exception:
                    pass
                # Paso 4: serie (si es punto finito y no infinito)
                try:
                    if a not in (oo, -oo):
                        ser = expr_sym.series(x, a, 3)
                        pasos.append({"operacion": "Expansión en serie (orden 3)", "detalle": str(ser)})
                except Exception:
                    pass

            if direction in ('+', '-'):
                res = sympy_limit(expr_sym, x, a, dir=direction)
            else:
                res = sympy_limit(expr_sym, x, a)

            resultado = str(res)
            ctx['resultado'] = resultado
            ctx['expr_used'] = expr_used
            ctx['point_used'] = point_used
            ctx['direction_used'] = direction_used
            if show_steps and pasos:
                ctx['pasos'] = pasos
        except Exception as e:
            logger.exception('Error en vista limite')
            ctx['error'] = friendly_error(e)
    return render(request, 'algebra/limite.html', ctx)


def derivadas(request: HttpRequest):
    """Calcular la derivada simbólica respecto a x. Opcionalmente evaluar en un punto.

    El formulario envía `expr` (cliente intenta normalizar LaTeX). Si se solicita
    mostrar pasos, se construye una lista básica de transformaciones.
    """
    ctx = {}
    if request.method == 'POST':
        try:
            raw = (request.POST.get('expr') or request.POST.get('latex') or '').strip()
            point = (request.POST.get('point') or '').strip()
            show_steps = bool(request.POST.get('show_steps'))

            if not raw:
                raise ValueError('Debes introducir una expresión.')

            # mismos locales que en limite
            local_dict = {
                'sin': sin, 'cos': cos, 'tan': tan,
                'asin': asin, 'acos': acos, 'atan': atan,
                'exp': exp, 'log': log, 'sqrt': sqrt,
                'abs': Abs, 'pi': sympify('pi'), 'e': sympify('E')
            }

            try:
                expr_sym = sympify(raw, locals=local_dict)
            except Exception:
                fallback = raw.replace('\\', '').replace('^', '**')
                expr_sym = sympify(fallback, locals=local_dict)

            x = symbols('x')
            pasos = []
            if show_steps:
                try:
                    pasos.append({'operacion': 'Expresión simbólica', 'detalle': str(expr_sym)})
                except Exception:
                    pass

            # derivada simbólica
            deriv = expr_sym.diff(x)

            if show_steps:
                try:
                    pasos.append({'operacion': 'Derivada simbólica', 'detalle': str(deriv)})
                except Exception:
                    pass
                try:
                    simp = deriv.simplify()
                    if str(simp) != str(deriv):
                        pasos.append({'operacion': 'Simplificación', 'detalle': str(simp)})
                    deriv = simp
                except Exception:
                    pass

            ctx['derivada'] = str(deriv)
            ctx['expr_used'] = raw

            # si se pide evaluar en un punto
            if point:
                try:
                    if point.lower() in ('oo', 'infty', 'infinito', 'inf', '∞'):
                        val = oo
                    elif point.lower() in ('-oo', '-infty', '-inf'):
                        val = -oo
                    else:
                        val = sympify(point)
                    # evitar sustituir infinito en la evaluación directa
                    if val in (oo, -oo):
                        eval_result = deriv.limit(x, val)
                    else:
                        eval_result = deriv.subs(x, val)
                    ctx['eval_point'] = point
                    ctx['eval_result'] = str(eval_result)
                    if show_steps:
                        pasos.append({'operacion': f'Evaluación en x={point}', 'detalle': str(eval_result)})
                except Exception:
                    ctx['eval_point'] = point
                    ctx['eval_result'] = 'No se pudo evaluar en el punto dado.'

            if show_steps and pasos:
                ctx['pasos'] = pasos

        except Exception as e:
            logger.exception('Error en vista derivadas')
            ctx['error'] = friendly_error(e)

    return render(request, 'algebra/derivadas.html', ctx)


def biseccion(request: HttpRequest):
    """Página para el Método de bisección.

    Soporta GET (muestra formulario) y POST (ejecuta algoritmo y muestra tabla de iteraciones).
    """
    ctx = {"title": "Método de bisección"}
    if request.method == 'POST':
        func_txt = (request.POST.get('function') or '').strip()
        a_txt = (request.POST.get('a') or '').strip()
        b_txt = (request.POST.get('b') or '').strip()
        tol_txt = (request.POST.get('tol') or '').strip()
        maxit_txt = (request.POST.get('maxit') or '').strip()

        # Helper to ensure numeric parsing accepts simple fractions like '1/2'
        from fractions import Fraction
        def _replace_vulgar_fraction_chars(s: str) -> str:
            # Map common single-character unicode vulgar fractions to 'a/b'
            vf_map = {
                '\u00BC': '1/4', '\u00BD': '1/2', '\u00BE': '3/4',
                '\u2150': '1/7', '\u2151': '1/9', '\u2152': '1/10',
                '\u2153': '1/3', '\u2154': '2/3', '\u2155': '1/5', '\u2156': '2/5', '\u2157': '3/5', '\u2158': '4/5',
                '\u2159': '1/6', '\u215A': '5/6', '\u215B': '1/8', '\u215C': '3/8', '\u215D': '5/8', '\u215E': '7/8'
            }
            out = []
            for ch in s:
                if ch in vf_map:
                    out.append(vf_map[ch])
                else:
                    out.append(ch)
            return ''.join(out)

        def parse_number(txt, default=None):
            if txt is None or str(txt).strip() == '':
                return default
            s = str(txt).strip()
            # Normalize common unicode characters that break parsing
            s = s.replace('\u2212', '-')  # minus sign
            s = s.replace('\u2060', '')   # word joiner
            s = s.replace('\u2009', '')   # thin space
            s = s.replace('\u00A0', '')   # non-breaking space
            # Replace single-char vulgar fractions like '½' -> '1/2'
            s = _replace_vulgar_fraction_chars(s)
            # Try straightforward float conversion first (handles '0.5', '1e-4')
            try:
                return float(s)
            except Exception:
                try:
                    # Accept forms like '1/2'
                    return float(Fraction(s))
                except Exception:
                    # As last resort, try evaluating simple numeric expression safely
                    try:
                        # allow scientific notation and basic arithmetic; convert ^ to **
                        s2 = s.replace('^', '**')
                        return float(eval(s2, {'__builtins__': None}, {}))
                    except Exception:
                        raise

        # Parse numeric inputs with validations
        try:
            a = parse_number(a_txt)
            b = parse_number(b_txt)
            if a is None or b is None:
                raise ValueError('a o b vacío')
        except Exception:
            ctx['error'] = 'Parámetros numéricos inválidos: a y b deben ser números (aceptamos 0.5 o 1/2).'
            # preserve user inputs so template shows them
            ctx['function'] = func_txt
            ctx['a_input'] = a_txt
            ctx['b_input'] = b_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/biseccion.html', ctx)

        try:
            tol = parse_number(tol_txt, default=1e-6)
            if tol is None or tol <= 0:
                raise ValueError()
        except Exception:
            ctx['error'] = 'Tolerancia inválida; debe ser un número positivo.'
            ctx['function'] = func_txt
            ctx['a_input'] = a_txt
            ctx['b_input'] = b_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/biseccion.html', ctx)

        try:
            maxit = int(maxit_txt) if maxit_txt != '' else 100
            if maxit <= 0:
                raise ValueError()
        except Exception:
            ctx['error'] = 'Max iteraciones inválido; debe ser entero y mayor que 0.'
            ctx['function'] = func_txt
            ctx['a_input'] = a_txt
            ctx['b_input'] = b_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/biseccion.html', ctx)

        # Ejecutar el algoritmo extraído y manejar errores específicos
        try:
            resultado = biseccion_algo(func_txt, a, b, tol=tol, maxit=maxit)
        except ErrorBiseccion as be:
            ctx['error'] = str(be)
            # preserve inputs
            ctx['function'] = func_txt
            ctx['a_input'] = a_txt
            ctx['b_input'] = b_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/biseccion.html', ctx)
        except Exception as e:
            logger.exception("Error inesperado en método biseccion")
            ctx['error'] = friendly_error(e)
            ctx['function'] = func_txt
            ctx['a_input'] = a_txt
            ctx['b_input'] = b_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/biseccion.html', ctx)

        # Formatear los números a cadenas usando punto decimal (.) y
        # reordenar columnas tal como se solicita. Esto evita el uso de
        # filtros de plantilla que podrían aplicar coma según la localización.
        raw_iters = resultado.get('iteraciones', [])
        iteraciones_formateadas = []
        for it in raw_iters:
            # asegurar que las claves numéricas existen y convertir a float
            a_val = float(it.get('a', 0))
            b_val = float(it.get('b', 0))
            c_val = float(it.get('c', 0))
            fa_val = float(it.get('fa', 0))
            fb_val = float(it.get('fb', 0))
            fc_val = float(it.get('fc', 0))
            iteraciones_formateadas.append({
                'i': it.get('i', 0),
                'a': format(a_val, '.6f'),
                'b': format(b_val, '.6f'),
                'c': format(c_val, '.6f'),
                'fa': format(fa_val, '.6f'),
                'fb': format(fb_val, '.6f'),
                'fc': format(fc_val, '.6f'),
                'actualizacion': it.get('actualizacion', '')
            })

        ctx['iteraciones'] = iteraciones_formateadas
        # Si no hay iteraciones detalladas pero el método indica convergencia
        # (por ejemplo raíz exacta en extremo), construir una fila mínima para
        # que la UI muestre la tabla en lugar de solo el resumen/gráfica.
        if not iteraciones_formateadas and resultado.get('convergio'):
            try:
                a_val = float(a)
                b_val = float(b)
                raiz_val = resultado.get('raiz')
                c_val = float(raiz_val) if raiz_val is not None else (a_val + b_val) / 2.0
                f = _crear_evaluador(func_txt)
                fa_val = float(f(a_val)) if a_val is not None else 0.0
                fb_val = float(f(b_val)) if b_val is not None else 0.0
                fc_val = float(f(c_val)) if c_val is not None else 0.0
                ctx['iteraciones'] = [{
                    'i': 0,
                    'a': format(a_val, '.6f'),
                    'b': format(b_val, '.6f'),
                    'c': format(c_val, '.6f'),
                    'fa': format(fa_val, '.6f'),
                    'fb': format(fb_val, '.6f'),
                    'fc': format(fc_val, '.6f'),
                    'actualizacion': 'resultado directo'
                }]
            except Exception:
                # no bloquear la vista por un fallo al intentar construir la fila
                pass
        ctx['convergio'] = resultado.get('convergio', False)
        ctx['conteo_iter'] = resultado.get('conteo_iter', 0)
        # Resumen también formateado con punto decimal
        raiz_val = resultado.get('raiz')
        estim_err_val = resultado.get('estimacion_error')
        f_en_raiz_val = resultado.get('f_en_raiz')
        ctx['raiz'] = format(float(raiz_val), '.8f') if raiz_val is not None else ''
        ctx['estimacion_error'] = format(float(estim_err_val), '.8f') if estim_err_val is not None else ''
        ctx['f_en_raiz'] = format(float(f_en_raiz_val), '.10f') if f_en_raiz_val is not None else ''
        ctx['function'] = func_txt
        ctx['a_input'] = a_txt
        ctx['b_input'] = b_txt
        ctx['tol_input'] = tol_txt
        ctx['maxit_input'] = maxit_txt

        # Generar datos para la gráfica con Plotly: muestreamos f(x) en una ventana amplia
        try:
            f = _crear_evaluador(func_txt)
            N = 401
            xs = []
            ys = []
            # Definir una ventana de muestreo más amplia que [a,b] e incluyendo x=0
            aa = float(min(a, b))
            bb = float(max(a, b))
            span = bb - aa
            if span <= 0:
                span = 2.0
                aa -= 1.0
                bb += 1.0
            center = (aa + bb) / 2.0
            scale = 2.5  # factor para ampliar la ventana respecto al intervalo
            x1 = center - span * scale
            x2 = center + span * scale
            # Asegurar que 0 esté dentro de la ventana para ver el eje Y
            x1 = min(x1, 0.0)
            x2 = max(x2, 0.0)
            for i in range(N):
                t = i / (N - 1)
                x = x1 + (x2 - x1) * t
                try:
                    y = float(f(x))
                except Exception:
                    y = None  # Plotly corta la línea si hay None
                xs.append(x)
                ys.append(y)
            fa = None
            fb = None
            try: fa = float(f(float(a)))
            except Exception: fa = None
            try: fb = float(f(float(b)))
            except Exception: fb = None
            import json as _json
            ctx['plot'] = _json.dumps({
                'xs': xs,
                'ys': ys,
                'a': float(a),
                'b': float(b),
                'fa': fa,
                'fb': fb
            })
        except Exception:
            # Si algo falla en la generación de la gráfica, ignoramos silenciosamente para no romper la vista
            pass

        return render(request, 'algebra/biseccion.html', ctx)

    # GET
    return render(request, 'algebra/biseccion.html', ctx)


def regula_falsi(request: HttpRequest):
    """Vista para el método de Regla Falsa. Reutiliza la plantilla de bisección
    porque la interfaz y los parámetros son equivalentes.
    """
    ctx = {"title": "Método de Regla Falsa (Regula Falsi)"}
    if request.method == 'POST':
        # Reuse the same parsing/validation logic as biseccion to avoid duplication
        func_txt = (request.POST.get('function') or '').strip()
        a_txt = (request.POST.get('a') or '').strip()
        b_txt = (request.POST.get('b') or '').strip()
        tol_txt = (request.POST.get('tol') or '').strip()
        maxit_txt = (request.POST.get('maxit') or '').strip()

        from fractions import Fraction
        def _replace_vulgar_fraction_chars(s: str) -> str:
            vf_map = {
                '\u00BC': '1/4', '\u00BD': '1/2', '\u00BE': '3/4',
                '\u2150': '1/7', '\u2151': '1/9', '\u2152': '1/10',
                '\u2153': '1/3', '\u2154': '2/3', '\u2155': '1/5', '\u2156': '2/5', '\u2157': '3/5', '\u2158': '4/5',
                '\u2159': '1/6', '\u215A': '5/6', '\u215B': '1/8', '\u215C': '3/8', '\u215D': '5/8', '\u215E': '7/8'
            }
            out = []
            for ch in s:
                if ch in vf_map:
                    out.append(vf_map[ch])
                else:
                    out.append(ch)
            return ''.join(out)

        def parse_number(txt, default=None):
            if txt is None or str(txt).strip() == '':
                return default
            s = str(txt).strip()
            s = s.replace('\u2212', '-')
            s = s.replace('\u2060', '')
            s = s.replace('\u2009', '')
            s = s.replace('\u00A0', '')
            s = _replace_vulgar_fraction_chars(s)
            try:
                return float(s)
            except Exception:
                try:
                    return float(Fraction(s))
                except Exception:
                    try:
                        s2 = s.replace('^', '**')
                        return float(eval(s2, {'__builtins__': None}, {}))
                    except Exception:
                        raise

        try:
            a = parse_number(a_txt)
            b = parse_number(b_txt)
            if a is None or b is None:
                raise ValueError('a o b vacío')
        except Exception:
            ctx['error'] = 'Parámetros numéricos inválidos: a y b deben ser números (aceptamos 0.5 o 1/2).'
            ctx['function'] = func_txt
            ctx['a_input'] = a_txt
            ctx['b_input'] = b_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/biseccion.html', ctx)

        try:
            tol = parse_number(tol_txt, default=1e-6)
            if tol is None or tol <= 0:
                raise ValueError()
        except Exception:
            ctx['error'] = 'Tolerancia inválida; debe ser un número positivo.'
            ctx['function'] = func_txt
            ctx['a_input'] = a_txt
            ctx['b_input'] = b_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/biseccion.html', ctx)

        try:
            maxit = int(maxit_txt) if maxit_txt != '' else 100
            if maxit <= 0:
                raise ValueError()
        except Exception:
            ctx['error'] = 'Max iteraciones inválido; debe ser entero y mayor que 0.'
            ctx['function'] = func_txt
            ctx['a_input'] = a_txt
            ctx['b_input'] = b_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/biseccion.html', ctx)

        try:
            resultado = regula_falsi_algo(func_txt, a, b, tol=tol, maxit=maxit)
        except ErrorBiseccion as be:
            ctx['error'] = str(be)
            ctx['function'] = func_txt
            ctx['a_input'] = a_txt
            ctx['b_input'] = b_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/biseccion.html', ctx)
        except Exception as e:
            logger.exception("Error inesperado en método regula_falsi")
            ctx['error'] = friendly_error(e)
            ctx['function'] = func_txt
            ctx['a_input'] = a_txt
            ctx['b_input'] = b_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/biseccion.html', ctx)

        # Reuse the same post-processing as the bisection view to format results & plot
        raw_iters = resultado.get('iteraciones', [])
        iteraciones_formateadas = []
        for it in raw_iters:
            a_val = float(it.get('a', 0))
            b_val = float(it.get('b', 0))
            c_val = float(it.get('c', 0))
            fa_val = float(it.get('fa', 0))
            fb_val = float(it.get('fb', 0))
            fc_val = float(it.get('fc', 0))
            iteraciones_formateadas.append({
                'i': it.get('i', 0),
                'a': format(a_val, '.6f'),
                'b': format(b_val, '.6f'),
                'c': format(c_val, '.6f'),
                'fa': format(fa_val, '.6f'),
                'fb': format(fb_val, '.6f'),
                'fc': format(fc_val, '.6f'),
                'actualizacion': it.get('actualizacion', '')
            })

        ctx['iteraciones'] = iteraciones_formateadas
        if not iteraciones_formateadas and resultado.get('convergio'):
            try:
                a_val = float(a)
                b_val = float(b)
                raiz_val = resultado.get('raiz')
                c_val = float(raiz_val) if raiz_val is not None else (a_val + b_val) / 2.0
                f = _crear_evaluador(func_txt)
                fa_val = float(f(a_val)) if a_val is not None else 0.0
                fb_val = float(f(b_val)) if b_val is not None else 0.0
                fc_val = float(f(c_val)) if c_val is not None else 0.0
                ctx['iteraciones'] = [{
                    'i': 0,
                    'a': format(a_val, '.6f'),
                    'b': format(b_val, '.6f'),
                    'c': format(c_val, '.6f'),
                    'fa': format(fa_val, '.6f'),
                    'fb': format(fb_val, '.6f'),
                    'fc': format(fc_val, '.6f'),
                    'actualizacion': 'resultado directo'
                }]
            except Exception:
                pass

        ctx['convergio'] = resultado.get('convergio', False)
        ctx['conteo_iter'] = resultado.get('conteo_iter', 0)
        raiz_val = resultado.get('raiz')
        estim_err_val = resultado.get('estimacion_error')
        f_en_raiz_val = resultado.get('f_en_raiz')
        ctx['raiz'] = format(float(raiz_val), '.8f') if raiz_val is not None else ''
        ctx['estimacion_error'] = format(float(estim_err_val), '.8f') if estim_err_val is not None else ''
        ctx['f_en_raiz'] = format(float(f_en_raiz_val), '.10f') if f_en_raiz_val is not None else ''
        ctx['function'] = func_txt
        ctx['a_input'] = a_txt
        ctx['b_input'] = b_txt
        ctx['tol_input'] = tol_txt
        ctx['maxit_input'] = maxit_txt

        try:
            f = _crear_evaluador(func_txt)
            N = 401
            xs = []
            ys = []
            aa = float(min(a, b))
            bb = float(max(a, b))
            span = bb - aa
            if span <= 0:
                span = 2.0
                aa -= 1.0
                bb += 1.0
            center = (aa + bb) / 2.0
            scale = 2.5
            x1 = center - span * scale
            x2 = center + span * scale
            x1 = min(x1, 0.0)
            x2 = max(x2, 0.0)
            for i in range(N):
                t = i / (N - 1)
                x = x1 + (x2 - x1) * t
                try:
                    y = float(f(x))
                except Exception:
                    y = None
                xs.append(x)
                ys.append(y)
            fa = None
            fb = None
            try: fa = float(f(float(a)))
            except Exception: fa = None
            try: fb = float(f(float(b)))
            except Exception: fb = None
            import json as _json
            ctx['plot'] = _json.dumps({
                'xs': xs,
                'ys': ys,
                'a': float(a),
                'b': float(b),
                'fa': fa,
                'fb': fb
            })
        except Exception:
            pass

        return render(request, 'algebra/biseccion.html', ctx)

    # GET
    return render(request, 'algebra/biseccion.html', ctx)


def newton_raphson(request: HttpRequest):
    """Vista para el método de Newton–Raphson (método abierto)."""
    ctx = {"title": "Método de Newton–Raphson"}
    if request.method == 'POST':
        func_txt = (request.POST.get('function') or '').strip()
        x0_txt = (request.POST.get('x0') or '').strip()
        tol_txt = (request.POST.get('tol') or '').strip()
        maxit_txt = (request.POST.get('maxit') or '').strip()

        from fractions import Fraction
        def _replace_vulgar_fraction_chars(s: str) -> str:
            vf_map = {
                '\u00BC': '1/4', '\u00BD': '1/2', '\u00BE': '3/4',
                '\u2150': '1/7', '\u2151': '1/9', '\u2152': '1/10',
                '\u2153': '1/3', '\u2154': '2/3', '\u2155': '1/5', '\u2156': '2/5', '\u2157': '3/5', '\u2158': '4/5',
                '\u2159': '1/6', '\u215A': '5/6', '\u215B': '1/8', '\u215C': '3/8', '\u215D': '5/8', '\u215E': '7/8'
            }
            return ''.join(vf_map.get(ch, ch) for ch in s)

        def parse_number(txt, default=None):
            if txt is None or str(txt).strip() == '':
                return default
            s = str(txt).strip()
            s = s.replace('\u2212', '-')
            s = s.replace('\u2060', '')
            s = s.replace('\u2009', '')
            s = s.replace('\u00A0', '')
            s = _replace_vulgar_fraction_chars(s)
            try:
                return float(s)
            except Exception:
                try:
                    return float(Fraction(s))
                except Exception:
                    try:
                        s2 = s.replace('^', '**')
                        return float(eval(s2, {'__builtins__': None}, {}))
                    except Exception:
                        raise

        try:
            x0 = parse_number(x0_txt)
            if x0 is None:
                raise ValueError('x0 vacío')
        except Exception:
            ctx['error'] = 'Parámetros numéricos inválidos: x0 debe ser un número (aceptamos 0.5 o 1/2).'
            ctx['function'] = func_txt
            ctx['x0_input'] = x0_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/newton_raphson.html', ctx)

        try:
            tol = parse_number(tol_txt, default=1e-6)
            if tol is None or tol <= 0:
                raise ValueError()
        except Exception:
            ctx['error'] = 'Tolerancia inválida; debe ser un número positivo.'
            ctx['function'] = func_txt
            ctx['x0_input'] = x0_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/newton_raphson.html', ctx)

        try:
            maxit = int(maxit_txt) if maxit_txt != '' else 100
            if maxit <= 0:
                raise ValueError()
        except Exception:
            ctx['error'] = 'Max iteraciones inválido; debe ser entero y mayor que 0.'
            ctx['function'] = func_txt
            ctx['x0_input'] = x0_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/newton_raphson.html', ctx)

        try:
            resultado = newton_raphson_algo(func_txt, x0, tol=tol, maxit=maxit)
        except ErrorBiseccion as be:
            ctx['error'] = str(be)
            ctx['function'] = func_txt
            ctx['x0_input'] = x0_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/newton_raphson.html', ctx)
        except Exception as e:
            logger.exception("Error inesperado en método newton_raphson")
            ctx['error'] = friendly_error(e)
            ctx['function'] = func_txt
            ctx['x0_input'] = x0_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/newton_raphson.html', ctx)

        # Formatear iteraciones
        raw_iters = resultado.get('iteraciones', [])
        it_out = []
        for it in raw_iters:
            def _fmt(v, nd='8'):
                try:
                    return format(float(v), f'.{nd}f')
                except Exception:
                    return ''
            it_out.append({
                'i': it.get('i', 0),
                'x': _fmt(it.get('x', 0.0), '8'),
                'x_next': _fmt(it.get('x_next', 0.0), '8') if it.get('x_next') is not None else '',
                'fx': _fmt(it.get('fx', 0.0), '8'),
                'dfx': _fmt(it.get('dfx', 0.0), '8'),
                'err': _fmt(it.get('err', None), '8') if it.get('err') is not None else ''
            })
        ctx['iteraciones'] = it_out

        ctx['convergio'] = resultado.get('convergio', False)
        ctx['conteo_iter'] = resultado.get('conteo_iter', 0)
        raiz_val = resultado.get('raiz')
        err_val = resultado.get('estimacion_error')
        f_en_raiz_val = resultado.get('f_en_raiz')
        ctx['raiz'] = format(float(raiz_val), '.8f') if raiz_val is not None else ''
        ctx['estimacion_error'] = format(float(err_val), '.8f') if err_val is not None else ''
        ctx['f_en_raiz'] = format(float(f_en_raiz_val), '.10f') if f_en_raiz_val is not None else ''
        # Mostrar advertencias (por ejemplo, f'(x)≈0) como mensaje informativo
        try:
            warns = resultado.get('warnings') or []
            if isinstance(warns, list) and len(warns) > 0:
                ctx['message'] = ' '.join(str(w) for w in warns)
        except Exception:
            pass
        ctx['function'] = func_txt
        ctx['x0_input'] = x0_txt
        ctx['tol_input'] = tol_txt
        ctx['maxit_input'] = maxit_txt

        # Gráfica alrededor de x0 y la raíz estimada
        try:
            f = _crear_evaluador(func_txt)
            N = 401
            xs = []
            ys = []
            # Ventana centrada en x0 y raíz, algo amplia
            try:
                xr = float(raiz_val)
            except Exception:
                xr = float(x0)
            center = (float(x0) + xr) / 2.0
            span = abs(xr - float(x0))
            if span <= 0:
                span = 2.0
            scale = 2.5
            x1 = center - span * scale
            x2 = center + span * scale
            x1 = min(x1, 0.0)
            x2 = max(x2, 0.0)
            for i in range(N):
                t = i / (N - 1)
                x = x1 + (x2 - x1) * t
                try:
                    y = float(f(x))
                except Exception:
                    y = None
                xs.append(x)
                ys.append(y)
            import json as _json
            ctx['plot'] = _json.dumps({'xs': xs, 'ys': ys, 'x0': float(x0), 'xr': float(raiz_val) if raiz_val is not None else None})
        except Exception:
            pass

        return render(request, 'algebra/newton_raphson.html', ctx)

    return render(request, 'algebra/newton_raphson.html', ctx)


def secante(request: HttpRequest):
    """Vista para el método de la secante (métodos abiertos)."""
    ctx = {"title": "Método de la secante"}
    if request.method == 'POST':
        func_txt = (request.POST.get('function') or '').strip()
        x0_txt = (request.POST.get('x0') or '').strip()
        x1_txt = (request.POST.get('x1') or '').strip()
        tol_txt = (request.POST.get('tol') or '').strip()
        maxit_txt = (request.POST.get('maxit') or '').strip()

        from fractions import Fraction
        def _replace_vulgar_fraction_chars(s: str) -> str:
            vf_map = {
                '\u00BC': '1/4', '\u00BD': '1/2', '\u00BE': '3/4',
                '\u2150': '1/7', '\u2151': '1/9', '\u2152': '1/10',
                '\u2153': '1/3', '\u2154': '2/3', '\u2155': '1/5', '\u2156': '2/5', '\u2157': '3/5', '\u2158': '4/5',
                '\u2159': '1/6', '\u215A': '5/6', '\u215B': '1/8', '\u215C': '3/8', '\u215D': '5/8', '\u215E': '7/8'
            }
            return ''.join(vf_map.get(ch, ch) for ch in s)

        def parse_number(txt, default=None):
            if txt is None or str(txt).strip() == '':
                return default
            s = str(txt).strip()
            s = s.replace('\u2212', '-')
            s = s.replace('\u2060', '')
            s = s.replace('\u2009', '')
            s = s.replace('\u00A0', '')
            s = _replace_vulgar_fraction_chars(s)
            try:
                return float(s)
            except Exception:
                try:
                    return float(Fraction(s))
                except Exception:
                    try:
                        s2 = s.replace('^', '**')
                        return float(eval(s2, {'__builtins__': None}, {}))
                    except Exception:
                        raise

        # Parse inputs
        try:
            x0 = parse_number(x0_txt)
            x1 = parse_number(x1_txt)
            if x0 is None or x1 is None:
                raise ValueError('x0/x1 vacíos')
        except Exception:
            ctx['error'] = 'Parámetros numéricos inválidos: x0 y x1 deben ser números (aceptamos 0.5 o 1/2).'
            ctx['function'] = func_txt
            ctx['x0_input'] = x0_txt
            ctx['x1_input'] = x1_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/secante.html', ctx)

        try:
            tol = parse_number(tol_txt, default=1e-6)
            if tol is None or tol <= 0:
                raise ValueError()
        except Exception:
            ctx['error'] = 'Tolerancia inválida; debe ser un número positivo.'
            ctx['function'] = func_txt
            ctx['x0_input'] = x0_txt
            ctx['x1_input'] = x1_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/secante.html', ctx)

        try:
            maxit = int(maxit_txt) if maxit_txt != '' else 100
            if maxit <= 0:
                raise ValueError()
        except Exception:
            ctx['error'] = 'Max iteraciones inválido; debe ser entero y mayor que 0.'
            ctx['function'] = func_txt
            ctx['x0_input'] = x0_txt
            ctx['x1_input'] = x1_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/secante.html', ctx)

        # Ejecutar algoritmo
        try:
            resultado = secante_algo(func_txt, x0, x1, tol=tol, maxit=maxit)
        except ErrorBiseccion as be:
            ctx['error'] = str(be)
            ctx['function'] = func_txt
            ctx['x0_input'] = x0_txt
            ctx['x1_input'] = x1_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/secante.html', ctx)
        except Exception as e:
            logger.exception("Error inesperado en método secante")
            ctx['error'] = friendly_error(e)
            ctx['function'] = func_txt
            ctx['x0_input'] = x0_txt
            ctx['x1_input'] = x1_txt
            ctx['tol_input'] = tol_txt
            ctx['maxit_input'] = maxit_txt
            return render(request, 'algebra/secante.html', ctx)

        # Formatear iteraciones
        it_out = []
        for it in (resultado.get('iteraciones') or []):
            def _fmt(v, nd='8'):
                try:
                    return format(float(v), f'.{nd}f')
                except Exception:
                    return ''
            it_out.append({
                'i': it.get('i', 0),
                'x_prev': _fmt(it.get('x_prev', 0.0), '8'),
                'x': _fmt(it.get('x', 0.0), '8'),
                'x_next': _fmt(it.get('x_next', 0.0), '8') if it.get('x_next') is not None else '',
                'f_prev': _fmt(it.get('f_prev', 0.0), '8'),
                'f': _fmt(it.get('f', 0.0), '8'),
                'err': _fmt(it.get('err', None), '8') if it.get('err') is not None else ''
            })
        ctx['iteraciones'] = it_out

        ctx['convergio'] = resultado.get('convergio', False)
        ctx['conteo_iter'] = resultado.get('conteo_iter', 0)
        raiz_val = resultado.get('raiz')
        err_val = resultado.get('estimacion_error')
        f_en_raiz_val = resultado.get('f_en_raiz')
        ctx['raiz'] = format(float(raiz_val), '.8f') if raiz_val is not None else ''
        ctx['estimacion_error'] = format(float(err_val), '.8f') if err_val is not None else ''
        ctx['f_en_raiz'] = format(float(f_en_raiz_val), '.10f') if f_en_raiz_val is not None else ''
        try:
            warns = resultado.get('warnings') or []
            if isinstance(warns, list) and len(warns) > 0:
                ctx['message'] = ' '.join(str(w) for w in warns)
        except Exception:
            pass
        ctx['function'] = func_txt
        ctx['x0_input'] = x0_txt
        ctx['x1_input'] = x1_txt
        ctx['tol_input'] = tol_txt
        ctx['maxit_input'] = maxit_txt

        # Gráfica con los dos puntos iniciales y la función alrededor
        try:
            f = _crear_evaluador(func_txt)
            N = 401
            xs = []
            ys = []
            aa = float(min(x0, x1))
            bb = float(max(x0, x1))
            span = bb - aa
            if span <= 0:
                span = 2.0
                aa -= 1.0
                bb += 1.0
            center = (aa + bb) / 2.0
            scale = 2.5
            x1s = center - span * scale
            x2s = center + span * scale
            x1s = min(x1s, 0.0)
            x2s = max(x2s, 0.0)
            for i in range(N):
                t = i / (N - 1)
                xv = x1s + (x2s - x1s) * t
                try:
                    yv = float(f(xv))
                except Exception:
                    yv = None
                xs.append(xv)
                ys.append(yv)
            f0 = None; f1 = None
            try: f0 = float(f(float(x0)))
            except Exception: f0 = None
            try: f1 = float(f(float(x1)))
            except Exception: f1 = None
            import json as _json
            ctx['plot'] = _json.dumps({
                'xs': xs, 'ys': ys, 'x0': float(x0), 'x1': float(x1), 'f0': f0, 'f1': f1
            })
        except Exception:
            pass

        return render(request, 'algebra/secante.html', ctx)

    return render(request, 'algebra/secante.html', ctx)
