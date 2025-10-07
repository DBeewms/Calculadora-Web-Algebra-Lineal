from django.shortcuts import render
from django.http import HttpRequest
from .logic import utilidades as u
from .logic import operaciones as op

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

def _render_matriz(M):
    return [[u.texto_fraccion(x) for x in fila] for fila in (M or [])]

def suma(request: HttpRequest):
    ctx = {}
    if request.method == "POST":
        try:
            A = _parse_matriz_simple(request.POST.get("matrizA"))
            B = _parse_matriz_simple(request.POST.get("matrizB"))
            C = op.sumar_matrices(A, B)
            ctx["resultado"] = _render_matriz(C)
            if A:
                ctx["dims"] = {"A": f"{len(A)}×{len(A[0])}", "B": f"{len(B)}×{len(B[0])}", "C": f"{len(C)}×{len(C[0])}"}
        except Exception as e:
            ctx["error"] = str(e)
    return render(request, "algebra/suma.html", ctx)

def multiplicacion(request: HttpRequest):
    ctx = {}
    if request.method == "POST":
        try:
            A = _parse_matriz_simple(request.POST.get("matrizA"))
            B = _parse_matriz_simple(request.POST.get("matrizB"))
            want_steps = bool(request.POST.get("show_steps"))
            if want_steps:
                C, pasos = op.multiplicar_matrices(A, B, registrar_pasos=True)
                ctx["resultado"] = _render_matriz(C)
                # Renderizar matrices de cada paso a texto fracción
                ctx["pasos"] = [
                    {"operacion": p.get("operacion"), "matriz": _render_matriz(p.get("matriz"))}
                    for p in pasos
                ]
            else:
                C = op.multiplicar_matrices(A, B)
                ctx["resultado"] = _render_matriz(C)
            if A and B:
                ctx["dims"] = {
                    "A": f"{len(A)}×{len(A[0])}",
                    "B": f"{len(B)}×{len(B[0])}",
                    "C": f"{len(C)}×{len(C[0])}"
                }
        except Exception as e:
            ctx["error"] = str(e)
    return render(request, "algebra/multiplicacion.html", ctx)

def gauss(request: HttpRequest):
    ctx = {}
    if request.method == "POST":
        try:
            M = _parse_matriz_aumentada(request.POST.get("matrizAug"))
            want_steps = bool(request.POST.get("show_steps"))
            info = op.gauss_info(M, registrar_pasos=want_steps)
            R = info["matriz"]
            ctx["resultado"] = _render_matriz(R)
            ctx["analisis"] = info.get("analisis")
            ctx["pivotes"] = info.get("pivotes")
            if want_steps and "pasos" in info:
                ctx["pasos"] = [
                    {"operacion": p.get("operacion"), "matriz": _render_matriz(p.get("matriz"))}
                    for p in info["pasos"]
                ]
            if M:
                m = len(M); n = len(M[0]) - 1
                ctx["dims"] = {"A": f"{m}×{n}", "b": f"{m}×1"}
        except Exception as e:
            ctx["error"] = str(e)
    return render(request, "algebra/gauss.html", ctx)

def gauss_jordan(request: HttpRequest):
    ctx = {}
    if request.method == "POST":
        try:
            M = _parse_matriz_aumentada(request.POST.get("matrizAug"))
            want_steps = bool(request.POST.get("show_steps"))
            info = op.gauss_jordan_info(M, registrar_pasos=want_steps)
            R = info["matriz"]
            ctx["resultado"] = _render_matriz(R)
            ctx["analisis"] = info.get("analisis")
            ctx["pivotes"] = info.get("pivotes")
            if want_steps and "pasos" in info:
                ctx["pasos"] = [
                    {"operacion": p.get("operacion"), "matriz": _render_matriz(p.get("matriz"))}
                    for p in info["pasos"]
                ]
            if M:
                m = len(M); n = len(M[0]) - 1
                ctx["dims"] = {"A": f"{m}×{n}", "b": f"{m}×1"}
        except Exception as e:
            ctx["error"] = str(e)
    return render(request, "algebra/gauss_jordan.html", ctx)
