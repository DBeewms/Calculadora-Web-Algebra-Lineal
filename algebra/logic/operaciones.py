from . import utilidades as u
from .utilidades import (
    texto_fraccion, texto_numero, copiar_matriz, es_cero, es_uno, negativo_fraccion,
    dividir_fracciones, sumar_fracciones, restar_fracciones,
    multiplicar_fracciones, simplificar_fraccion,
)

def copiar_matriz(M):
    return u.copiar_matriz(M)

def fila_intercambiar(M, i, j):
    temp = M[i]
    M[i] = M[j]
    M[j] = temp

def fila_escalar(M, i, c):
    columnas = len(M[i])
    j = 0
    while j < columnas:
        M[i][j] = multiplicar_fracciones(M[i][j], c)
        j = j + 1

def fila_sumar_multiplo(M, i, j, c):
    columnas = len(M[i])
    k = 0
    while k < columnas:
        termino = multiplicar_fracciones(c, M[j][k])
        M[i][k] = sumar_fracciones(M[i][k], termino)
        k = k + 1

def _gauss_jordan_detallado(M, text_fn=texto_fraccion):
    """Aplica Gauss-Jordan (forma escalonada reducida) y devuelve
    (R, pivotes, pasos) con todo el detalle."""
    R = copiar_matriz(M)
    m = len(R)
    n = len(R[0]) - 1
    pasos = []  # historial

    def registrar(operacion):
        pasos.append({"operacion": operacion, "matriz": copiar_matriz(R)})
    fila_pivote = 0
    col = 0
    # Recorre columnas buscando pivotes y los normaliza
    while col < n and fila_pivote < m:
        # Buscar fila con entrada no cero en la columna actual
        r = fila_pivote
        pivote_en = -1
        while r < m:
            if not es_cero(R[r][col]):
                pivote_en = r
                break
            r += 1
        if pivote_en == -1:
            col += 1
            continue
        if pivote_en != fila_pivote:
            fila_intercambiar(R, fila_pivote, pivote_en)
            registrar("Intercambiar F" + str(fila_pivote+1) + " ↔ F" + str(pivote_en+1))
        piv = R[fila_pivote][col]
        if not es_uno(piv):
            inv = dividir_fracciones([1,1], piv)
            fila_escalar(R, fila_pivote, inv)
            registrar("F" + str(fila_pivote+1) + " → (1/" + text_fn(piv) + ")·F" + str(fila_pivote+1))
        # Anular el resto de la columna
        r = 0
        while r < m:
            if r != fila_pivote and not es_cero(R[r][col]):
                factor = R[r][col]
                fila_sumar_multiplo(R, r, fila_pivote, negativo_fraccion(factor))
                registrar("F" + str(r+1) + " → F" + str(r+1) + " − (" + text_fn(factor) + ")·F" + str(fila_pivote+1))
            r += 1
        fila_pivote += 1
        col += 1
    # Estado final
    registrar("Matriz en forma escalonada reducida por filas")
    # Identificar columnas pivote
    pivotes = []
    r = 0
    c = 0
    while c < n and r < m:
        if es_uno(R[r][c]):
            limpio = True
            rr = 0
            while rr < m:
                if rr != r and not es_cero(R[rr][c]):
                    limpio = False
                    break
                rr += 1
            if limpio:
                pivotes.append(c)
                r += 1
        c += 1
    return [R, pivotes, pasos]

def gauss_jordan(M, registrar_pasos=False, text_fn=texto_fraccion):
    """Envuelve Gauss-Jordan devolviendo sólo lo necesario para la vista.

    - Si registrar_pasos es True: retorna (R, pasos)
    - En caso contrario: retorna sólo R
    """
    R, _pivotes, pasos = _gauss_jordan_detallado(M, text_fn=text_fn)
    return (R, pasos) if registrar_pasos else R

def eliminacion_gauss(M, text_fn=texto_fraccion):
    # Eliminación de Gauss para forma escalonada superior
    R = copiar_matriz(M)
    m = len(R)
    n = len(R[0]) - 1
    pasos = []

    def registrar(op):
        pasos.append({"operacion": op, "matriz": copiar_matriz(R)})

    fila_pivote = 0
    col = 0
    while col < n and fila_pivote < m:
        r = fila_pivote
        pivote_en = -1
        while r < m:
            if not es_cero(R[r][col]):
                pivote_en = r
                break
            r += 1
        if pivote_en == -1:
            col += 1
            continue
        if pivote_en != fila_pivote:
            fila_intercambiar(R, fila_pivote, pivote_en)
            registrar("Intercambiar F" + str(fila_pivote+1) + " ↔ F" + str(pivote_en+1))
        piv = R[fila_pivote][col]
        if not es_uno(piv):
            inv = dividir_fracciones([1,1], piv)
            fila_escalar(R, fila_pivote, inv)
            registrar("F" + str(fila_pivote+1) + " → (1/" + text_fn(piv) + ")·F" + str(fila_pivote+1))
        r = fila_pivote + 1
        while r < m:
            if not es_cero(R[r][col]):
                factor = R[r][col]
                fila_sumar_multiplo(R, r, fila_pivote, negativo_fraccion(factor))
                registrar("F" + str(r+1) + " → F" + str(r+1) + " − (" + text_fn(factor) + ")·F" + str(fila_pivote+1))
            r += 1
        fila_pivote += 1
        col += 1
    registrar("Matriz en forma escalonada")
    # Detecta columnas pivote
    pivotes = []
    r = 0
    c = 0
    while c < n and r < m:
        if not es_cero(R[r][c]):
            # asegurar que es primer no cero
            k = 0
            es_primero = True
            while k < c:
                if not es_cero(R[r][k]):
                    es_primero = False
                    break
                k += 1
            if es_primero:
                pivotes.append(c)
                r += 1
        c += 1
    return [R, pivotes, pasos]

def gauss(M, registrar_pasos=False, text_fn=texto_fraccion):
    """
    Si registrar_pasos es True: retorna (R, pasos)
    En caso contrario, retorna sólo R
    """
    R, _pivotes, pasos = eliminacion_gauss(M, text_fn=text_fn)
    return (R, pasos) if registrar_pasos else R

def analizar_solucion_gauss(R, pivotes):
    # Resuelve sistema a partir de forma escalonada y analiza con eliminación gaussiana
    m = len(R)
    n = len(R[0]) - 1
    i = 0
    while i < m:
        todos_ceros = True
        j = 0
        while j < n:
            if not es_cero(R[i][j]):
                todos_ceros = False
                break
            j += 1
        if todos_ceros and not es_cero(R[i][n]):
            return {"solucion": "INCONSISTENTE", "tipo_forma": "ESCALONADA"}
        i += 1
    solucion_particular = []
    j = 0
    while j < n:
        solucion_particular.append([0,1])
        j += 1
    libres = []
    c = 0
    while c < n:
        es_libre = True
        k = 0
        while k < len(pivotes):
            if pivotes[k] == c:
                es_libre = False
                break
            k += 1
        if es_libre:
            libres.append(c)
        c += 1
    fila = m - 1
    while fila >= 0:
        # encontrar pivote
        piv_col = -1
        col = 0
        while col < n:
            if not es_cero(R[fila][col]):
                piv_col = col
                break
            col += 1
        if piv_col != -1:
            suma = [0,1]
            j = piv_col + 1
            while j < n:
                if not es_cero(R[fila][j]):
                    suma = sumar_fracciones(suma, multiplicar_fracciones(R[fila][j], solucion_particular[j]))
                j += 1
            rhs = R[fila][n]
            resto = restar_fracciones(rhs, suma)
            piv = R[fila][piv_col]
            if not es_uno(piv):
                valor = dividir_fracciones(resto, piv)
            else:
                valor = resto
            solucion_particular[piv_col] = valor
        fila -= 1
    if len(pivotes) == n:
        return {"solucion": "UNICA", "solucion_particular": solucion_particular, "tipo_forma": "ESCALONADA"}
    return {"solucion": "INFINITAS", "solucion_particular": solucion_particular, "libres": libres, "tipo_forma": "ESCALONADA"}

def analizar_solucion(R, pivotes):
    # Analiza solución con Gauss-Jordan
    m = len(R)
    n = len(R[0]) - 1
    i = 0
    while i < m:
        todos_ceros = True
        j = 0
        while j < n:
            if not es_cero(R[i][j]):
                todos_ceros = False
                break
            j = j + 1
        if todos_ceros and not es_cero(R[i][n]):
            return {"solucion": "INCONSISTENTE", "tipo_forma": "ESCALONADA_REDUCIDA", "pivotes": pivotes}
        i = i + 1

    solucion_particular = []
    j = 0
    while j < n:
        solucion_particular.append([0,1])
        j = j + 1

    r = 0
    k = 0
    while k < len(pivotes):
        columna_pivote = pivotes[k]
        solucion_particular[columna_pivote] = R[r][n]
        r = r + 1
        k = k + 1

    libres = []
    c = 0
    while c < n:
        es_libre = True
        q = 0
        while q < len(pivotes):
            if c == pivotes[q]:
                es_libre = False
                break
            q = q + 1
        if es_libre:
            libres.append(c)
        c = c + 1

    # Determinar si el sistema es homogéneo
    es_homogeneo = all(es_cero(R[i][n]) for i in range(m))
    tipo_sistema = "HOMOGENEO" if es_homogeneo else "NO_HOMOGENEO"

    # Agregar información sobre soluciones triviales y no triviales
    teoria = (
        "CONJUNTOS SOLUCIÓN DE SISTEMAS LINEALES\n\n"
        "Se dice que un sistema de ecuaciones lineales es homogéneo si se puede escribir en la forma Ax = 0, "
        "donde A es una matriz de m × n, y 0 es el vector cero en Rⁿ.\n\n"
        "Tal sistema Ax = 0 siempre tiene al menos una solución x = 0 (el vector cero en n). "
        "Esta solución cero generalmente se conoce como solución trivial. Una solución no trivial es un vector x "
        "diferente de cero que satisfaga Ax = 0.\n\n"
        "La ecuación homogénea Ax = 0 tiene una solución no trivial si y solo si la ecuación tiene al menos una variable libre.\n"
    )

    resultado = {
        "solucion": "UNICA" if len(pivotes) == n else "INFINITAS",
        "solucion_particular": solucion_particular,
        "libres": libres,
        "tipo_forma": "ESCALONADA_REDUCIDA",
        "pivotes": pivotes,
        "tipo_sistema": tipo_sistema,
        "teoria": teoria
    }

    return resultado

# ================== Funciones de alto nivel para vistas ==================

def _variables_libres(n, pivotes):
    libres = []
    c = 0
    while c < n:
        es_libre = True
        k = 0
        while k < len(pivotes):
            if pivotes[k] == c:
                es_libre = False
                break
            k += 1
        if es_libre:
            libres.append(c)
        c += 1
    return libres

def construir_expresiones_parametricas(R, pivotes, text_fn=texto_fraccion):
    """Construye expresiones de variables dependientes (variables con pivote)
    en función de las variables libres, asumiendo que 'R' es una matriz
    aumentada ya en forma escalonada reducida por filas

    Notas de formato:
        - Cada fila asociada a un pivote corresponde a una ecuación del tipo
                  x_pivote = (término independiente) - (coeficientes * variables libres)
        - Si no hay término independiente ni coeficientes se coloca 0.
        - Coeficientes 1 y -1 se simplifican para mejorar legibilidad.

    Devuelve dict con:
        - 'expresiones': lista de cadenas 'x_i = ...'
        - 'libres': índices (0‑based) de las columnas libres.
    """
    m = len(R)
    n = len(R[0]) - 1
    libres = _variables_libres(n, pivotes)
    expresiones = []
    r = 0
    while r < len(pivotes) and r < m:
        pcol = pivotes[r]
        b = R[r][n]
        partes = []
        if not es_cero(b):
            partes.append(text_fn(b))
        li = 0
        while li < len(libres):
            fcol = libres[li]
            coef = R[r][fcol]
            if not es_cero(coef):
                frac_txt = text_fn(coef)
                if frac_txt == '1':
                    term = f"- x{fcol+1}"
                elif frac_txt == '-1':
                    term = f"+ x{fcol+1}"
                else:
                    term = f"- {frac_txt}·x{fcol+1}"
                partes.append(term)
            li += 1
        rhs = "0" if not partes else " ".join(partes).replace("  ", " ")
        expresiones.append(f"x{pcol+1} = {rhs}")
        r += 1
    return {"expresiones": expresiones, "libres": libres}

def gauss_info(M, registrar_pasos=False, text_fn=texto_fraccion):
    """Devuelve toda la información necesaria para la vista de Gauss:
    {
      'matriz': R (forma escalonada),
      'pivotes': [...],
      'pasos': [...]*opcional,
      'analisis': { tipo, vector_solucion, libres, ... }
    }
    """
    R, pivotes, pasos = eliminacion_gauss(M, text_fn=text_fn)
    base = analizar_solucion_gauss(R, pivotes)
    analisis = {"solucion": base["solucion"], "tipo_forma": base.get("tipo_forma", "ESCALONADA"), "pivotes": pivotes}
    analisis["pivotes_nombres"] = [f"x{p+1}" for p in pivotes]
    analisis["pivotes_nums"] = [p+1 for p in pivotes]
    n = len(R[0]) - 1
    if base["solucion"] == "UNICA":
        # Vector solución única
        vector_sol = []
        j = 0
        while j < n:
            vector_sol.append(f"x{j+1} = {text_fn(base['solucion_particular'][j])}")
            j += 1
        analisis["vector_solucion"] = vector_sol
    elif base["solucion"] == "INFINITAS":
        libres = base.get("libres", _variables_libres(n, pivotes))
        analisis["libres"] = libres
        analisis["libres_nombres"] = [f"x{c+1}" for c in libres]
        analisis["libres_detalle"] = [f"x{c+1} libre" for c in libres]
        vector_sol = []
        j = 0
        while j < n:
            vector_sol.append(f"x{j+1} = {text_fn(base['solucion_particular'][j])}")
            j += 1
        analisis["vector_solucion"] = vector_sol
    else:  # INCONSISTENTE
        # Identificar fila inconsistente para mensaje (opcional)
        m = len(R)
        ncols = len(R[0]) - 1
        fila_inc = -1
        i = 0
        while i < m:
            todos_ceros = True
            j = 0
            while j < ncols:
                if not es_cero(R[i][j]):
                    todos_ceros = False
                    break
                j += 1
            if todos_ceros and not es_cero(R[i][ncols]):
                fila_inc = i
                break
            i += 1
        if fila_inc != -1:
            analisis["detalle"] = f"Fila {fila_inc+1} indica 0 = {text_fn(R[fila_inc][ncols])}"
    info = {"matriz": R, "pivotes": pivotes, "analisis": analisis}
    if registrar_pasos:
        info["pasos"] = pasos
    return info

def gauss_jordan_info(M, registrar_pasos=False, text_fn=texto_fraccion):
    """Devuelve información extendida para la vista Gauss-Jordan, incluyendo
    expresiones paramétricas cuando hay variables libres."""
    R, pivotes, pasos = _gauss_jordan_detallado(M, text_fn=text_fn)
    base = analizar_solucion(R, pivotes)
    analisis = {
        "solucion": base["solucion"],
        "tipo_forma": base.get("tipo_forma", "ESCALONADA_REDUCIDA"),
        "pivotes": pivotes,
    }
    analisis["pivotes_nombres"] = [f"x{p+1}" for p in pivotes]
    analisis["pivotes_nums"] = [p+1 for p in pivotes]
    n = len(R[0]) - 1
    if base["solucion"] == "UNICA":
        vector_sol = []
        j = 0
        while j < n:
            vector_sol.append(f"x{j+1} = {text_fn(base['solucion_particular'][j])}")
            j += 1
        analisis["vector_solucion"] = vector_sol
    elif base["solucion"] == "INFINITAS":
        datos_param = construir_expresiones_parametricas(R, pivotes, text_fn=text_fn)
        libres = datos_param["libres"]
        analisis["libres"] = libres
        analisis["libres_nombres"] = [f"x{c+1}" for c in libres]
        analisis["expresiones"] = datos_param["expresiones"]
        analisis["libres_detalle"] = [f"x{c+1} libre" for c in libres]
        vector_sol = []
        j = 0
        while j < n:
            vector_sol.append(f"x{j+1} = {text_fn(base['solucion_particular'][j])}")
            j += 1
        analisis["vector_solucion"] = vector_sol
    else:  # INCONSISTENTE
        # Detectar fila inconsistente
        m = len(R)
        ncols = len(R[0]) - 1
        fila_inc = -1
        i = 0
        while i < m:
            todos_ceros = True
            j = 0
            while j < ncols:
                if not es_cero(R[i][j]):
                    todos_ceros = False
                    break
                j += 1
            if todos_ceros and not es_cero(R[i][ncols]):
                fila_inc = i
                break
            i += 1
        if fila_inc != -1:
            analisis["detalle"] = f"Fila {fila_inc+1} indica 0 = {text_fn(R[fila_inc][ncols])}"
    info = {"matriz": R, "pivotes": pivotes, "analisis": analisis}
    if registrar_pasos:
        info["pasos"] = pasos
    return info

def gauss_jordan_homogeneo_info(A, registrar_pasos=False, text_fn=texto_fraccion):
    """Analiza el sistema homogéneo A x = 0.
    Estrategia general:
        1. Formamos la matriz aumentada (A | 0) añadiendo una sola columna de ceros.
        2. Reutilizamos la misma rutina de análisis para sistemas generales (gauss_jordan_info).
             - Esa rutina clasifica como 'UNICA' (equivalente a solo trivial) o 'INFINITAS'.
             - En un sistema homogéneo nunca aparece el caso inconsistente.
        3. Traducimos:
                 'UNICA'     -> solucion = 'TRIVIAL'    (solo vector cero)  -> independencia lineal True
                 'INFINITAS' -> solucion = 'NO_TRIVIAL' (existen libres)    -> independencia lineal False
        4. Si hay variables libres, reconstruimos las expresiones de las variables con pivote
           en función de las libres para mostrarlas como dependencias.
    """
    if A is None or len(A) == 0:
        raise ValueError("La matriz A no puede ser vacía.")
    # Construimos matriz aumentada (A|0)
    M = []
    i = 0
    while i < len(A):
        fila = list(A[i]) + [[0,1]]  # término independiente cero
        M.append(fila)
        i += 1
    info = gauss_jordan_info(M, registrar_pasos=registrar_pasos, text_fn=text_fn)
    R = info["matriz"]
    anal_base = info["analisis"]
    pivotes = anal_base.get("pivotes", [])
    n = len(R[0]) - 1
    # En un sistema homogéneo no existe el caso inconsistente
    libres = []
    if anal_base["solucion"] == "UNICA":
        solucion_tipo = "TRIVIAL"
        independencia = True
    else:
        # Caso 'INFINITAS' del analizador general => hay variables libres => solución no trivial
        solucion_tipo = "NO_TRIVIAL"
        datos_param = construir_expresiones_parametricas(R, pivotes, text_fn=text_fn)
        libres = datos_param["libres"]
        independencia = False
    analisis = {
        "solucion": solucion_tipo,
        "independencia": independencia,  # True => LI, False => LD
        "pivotes": pivotes,
        "pivotes_nums": [p+1 for p in pivotes],
        "pivotes_nombres": [f"x{p+1}" for p in pivotes],
    }
    # Si existen variables libres, agregamos detalles de su lista y expresiones de dependencia
    if libres:
        analisis["libres"] = libres
        analisis["libres_nombres"] = [f"x{c+1}" for c in libres]
        analisis["expresiones"] = datos_param["expresiones"]
    # Vector solución trivial siempre x = 0; si no trivial también mostramos particular cero
    vector_sol = []
    j = 0
    while j < n:
        vector_sol.append(f"x{j+1} = 0")
        j += 1
    analisis["vector_trivial"] = vector_sol
    out = {"matriz": R, "analisis": analisis}
    if registrar_pasos and "pasos" in info:
        out["pasos"] = info["pasos"]
    return out

# ----------------------- Operaciones con matrices -----------------------

def _validar_dimensiones_iguales(A, B):
    if A is None or B is None or len(A) == 0 or len(B) == 0:
        raise ValueError("Las matrices no pueden ser vacías.")
    mA = len(A)
    nA = len(A[0])
    mB = len(B)
    nB = len(B[0])
    if mA != mB or nA != nB:
        raise ValueError("Para sumar, ambas matrices deben tener las mismas dimensiones.")

def sumar_matrices(A, B):
    """Suma dos matrices A y B (sin columna aumentada), elemento a elemento.
    Devuelve la matriz resultado C. Usa aritmética de fracciones del módulo utilidades.
    """
    _validar_dimensiones_iguales(A, B)
    m = len(A)
    n = len(A[0])
    C = []
    i = 0
    while i < m:
        fila = []
        j = 0
        while j < n:
            fila.append(sumar_fracciones(A[i][j], B[i][j]))
            j += 1
        C.append(fila)
        i += 1
    return C

def _validar_dimensiones_multiplicacion(A, B):
    if A is None or B is None or len(A) == 0 or len(B) == 0:
        raise ValueError("Las matrices no pueden ser vacías.")
    m = len(A)
    pA = len(A[0])
    pB = len(B)
    if pA != pB:
        raise ValueError("Para multiplicar, el número de columnas de A debe ser igual al número de filas de B.")

def multiplicar_matrices(A, B, registrar_pasos=False, text_fn=texto_fraccion):
    """Multiplica A (m×p) por B (p×n) devolviendo C (m×n).

    - Siempre calcula pasos del procedimiento (combinación lineal de columnas).
    - Si registrar_pasos es True: retorna (C, pasos).
    - Si es False (por defecto): retorna sólo C (compat con vistas Django).
    """
    _validar_dimensiones_multiplicacion(A, B)
    m = len(A)
    p = len(A[0])
    n = len(B[0])
    # Validar que B tenga n columnas en todas sus filas
    i = 0
    while i < len(B):
        if len(B[i]) != n:
            raise ValueError("La matriz B tiene filas con distinta cantidad de columnas.")
        i += 1
    # Inicializar C con ceros (fracción [0,1])
    C = []
    i = 0
    while i < m:
        filaC = []
        j = 0
        while j < n:
            filaC.append([0, 1])
            j += 1
        C.append(filaC)
        i += 1

    pasos = []
    # Paso inicial amigable
    pasos.append({
        "operacion": "Paso 1: Empezamos con una matriz resultado C llena de ceros",
        "matriz": copiar_matriz(C),
        "tipo": "simple"
    })

    # Explicación general (solo una vez)
    pasos.append({
        "operacion": "Idea: cada columna de C se obtiene combinando (sumando) columnas de A usando como pesos los números de la columna correspondiente de B",
        "matriz": copiar_matriz(C),
        "tipo": "simple"
    })

    j = 0
    while j < n:
        pasos.append({
            "operacion": f"Columna {j+1}: usamos los valores de la columna {j+1} de B como 'pesos'",
            "matriz": copiar_matriz(C),
            "tipo": "simple"
        })
        k = 0
        paso_col_idx = 1
        while k < p:
            coef = B[k][j]
            if not u.es_cero(coef):
                # Aplicamos coef * columna k de A
                i = 0
                while i < m:
                    termino = multiplicar_fracciones(coef, A[i][k])
                    C[i][j] = sumar_fracciones(C[i][j], termino)
                    i += 1
                pasos.append({
                    "operacion": f"Columna {j+1} (paso {paso_col_idx}): añadimos {text_fn(coef)} × (columna A{ k+1 })",
                    "matriz": copiar_matriz(C),
                    "tipo": "simple"
                })
                paso_col_idx += 1
            k += 1
        # Resumen sencillo de la columna
        partes = []
        k = 0
        while k < p:
            coef = B[k][j]
            if not u.es_cero(coef):
                partes.append(text_fn(coef) + "·A" + str(k+1))
            k += 1
        resumen = " + ".join(partes) if partes else "0"
        pasos.append({
            "operacion": f"Columna {j+1} terminada: combinación = {resumen}",
            "matriz": copiar_matriz(C),
            "tipo": "simple"
        })
        j += 1

    return (C, pasos) if registrar_pasos else C

def multiplicar_escalar_matriz(c, A, registrar_pasos=False, text_fn=texto_fraccion):
    """Devuelve c·A, escalando cada entrada de A por el escalar c (fracción [n,d])."""
    if A is None or len(A) == 0:
        raise ValueError("La matriz A no puede ser vacía.")
    m = len(A); n = len(A[0])
    # Validar rectangularidad
    i = 0
    while i < m:
        if len(A[i]) != n:
            raise ValueError("La matriz A no es rectangular.")
        i += 1
    C = []
    i = 0
    while i < m:
        fila = []
        j = 0
        while j < n:
            fila.append(multiplicar_fracciones(c, A[i][j]))
            j += 1
        C.append(fila)
        i += 1
    pasos = []
    if registrar_pasos:
        pasos.append({
            "operacion": f"Escalamos cada entrada por {text_fn(c)}",
            "matriz": copiar_matriz(C),
            "tipo": "simple"
        })
    return (C, pasos) if registrar_pasos else (C, None)

def multiplicar_matriz_vector_simbolico(A, v_simbolico, registrar_pasos=False, text_fn=texto_fraccion):
    """Multiplica A (m×n) por un vector simbólico v=[s1,..,sn]^T, devolviendo un vector columna de strings.

    Cada entrada es una combinación lineal: sum_k A[i][k] * v[k]. Se formatea como "a·x + b·y + ..." omitiendo términos con coef=0 y simplificando coef 1/-1.
    """
    if A is None or len(A) == 0:
        raise ValueError("La matriz A no puede ser vacía.")
    m = len(A); n = len(A[0])
    if len(v_simbolico) != n:
        raise ValueError("El vector simbólico debe tener tantas entradas como columnas de A.")
    # Validar que A sea rectangular
    i = 0
    while i < m:
        if len(A[i]) != n:
            raise ValueError("La matriz A no es rectangular.")
        i += 1
    # Construir expresiones por fila
    C = []  # m x 1 de strings
    pasos = []
    i = 0
    while i < m:
        partes = []
        k = 0
        while k < n:
            coef = A[i][k]
            if not es_cero(coef):
                coef_txt = text_fn(coef)
                var = v_simbolico[k]
                if coef_txt == '1':
                    term = var
                elif coef_txt == '-1':
                    term = f"- {var}"
                else:
                    term = f"{coef_txt}·{var}"
                partes.append(term)
            k += 1
        expr = " + ".join(partes) if partes else "0"
        # Normaliza signos como "+ - x" -> "- x"
        expr = expr.replace("+ - ", "- ")
        C.append([expr])
        if registrar_pasos:
            pasos.append({
                "operacion": f"Fila {i+1}: combinación de columnas con variables simbólicas",
                "matriz": copiar_matriz([[expr]]),
                "tipo": "simple"
            })
        i += 1
    return (C, pasos) if registrar_pasos else (C, None)

# ----------------------- Transposición -----------------------

def transponer_matriz(A, registrar_pasos=False, text_fn=texto_fraccion):
    """Devuelve la transpuesta A^T intercambiando filas por columnas.

    - A es m×n y A^T será n×m.
    - Si registrar_pasos es True, incluye un paso informativo con el resultado.
    """
    if A is None or len(A) == 0:
        raise ValueError("La matriz A no puede ser vacía.")
    m = len(A)
    n = len(A[0])
    # Validar rectangularidad
    i = 0
    while i < m:
        if len(A[i]) != n:
            raise ValueError("Todas las filas de A deben tener la misma cantidad de columnas.")
        i += 1
    # Crear A^T (n x m)
    AT = []
    j = 0
    while j < n:
        fila = []
        i = 0
        while i < m:
            fila.append([A[i][j][0], A[i][j][1]])
            i += 1
        AT.append(fila)
        j += 1
    if registrar_pasos:
        pasos = [{
            "operacion": f"Transpuesta: A^T es de tamaño {n}×{m} (columnas por filas)",
            "matriz": copiar_matriz(AT),
            "tipo": "simple"
        }]
        return AT, pasos
    return AT

# ----------------------- Inversa -----------------------

def _identidad(n):
    I = []
    i = 0
    while i < n:
        fila = []
        j = 0
        while j < n:
            fila.append([1,1] if i == j else [0,1])
            j += 1
        I.append(fila)
        i += 1
    return I

def inversa_matriz(A, registrar_pasos=False, text_fn=texto_fraccion):
    """Calcula la inversa de A si existe.

    Devuelve:
      - Si registrar_pasos: (info, pasos)
      - Si no: info

    info = {
      'invertible': bool,
      'inversa': matriz | None,
      'metodo': '2x2' | 'gauss' | '1x1',
      'razon': str opcional (cuando no es invertible)
    }
    """
    if A is None or len(A) == 0:
        raise ValueError("La matriz A no puede ser vacía.")
    n = len(A)
    # Validar cuadrada
    i = 0
    while i < n:
        if len(A[i]) != len(A[0]):
            raise ValueError("A debe ser rectangular.")
        i += 1
    m = len(A[0])
    if n != m:
        return ({"invertible": False, "inversa": None, "metodo": "gauss", "razon": "A no es cuadrada."}, []) if registrar_pasos else {"invertible": False, "inversa": None, "metodo": "gauss", "razon": "A no es cuadrada."}

    pasos = []

    # Caso 1x1
    if n == 1:
        a11 = A[0][0]
        if es_cero(a11):
            info = {"invertible": False, "inversa": None, "metodo": "1x1", "razon": "a11 = 0"}
            return (info, pasos) if registrar_pasos else info
        inv = [[dividir_fracciones([1,1], a11)]]
        if registrar_pasos:
            pasos.append({"operacion": f"Inversa de 1×1: A^{-1} = 1/a11", "matriz": copiar_matriz(inv), "tipo": "simple"})
        info = {"invertible": True, "inversa": inv, "metodo": "1x1"}
        return (info, pasos) if registrar_pasos else info

    # Caso 2x2 fórmula
    if n == 2:
        a = A[0][0]; b = A[0][1]; c = A[1][0]; d = A[1][1]
        ad = multiplicar_fracciones(a, d)
        bc = multiplicar_fracciones(b, c)
        det = restar_fracciones(ad, bc)
        if es_cero(det):
            info = {"invertible": False, "inversa": None, "metodo": "2x2", "razon": "ad − bc = 0"}
            if registrar_pasos:
                pasos.append({
                    "operacion": f"Paso 1: ad = {text_fn(ad)}, bc = {text_fn(bc)}",
                    "matriz": copiar_matriz(A),
                    "tipo": "simple"
                })
                pasos.append({
                    "operacion": f"Paso 2: Determinante det = ad − bc = {text_fn(ad)} − {text_fn(bc)} = 0 ⇒ A no es invertible",
                    "matriz": copiar_matriz(A),
                    "tipo": "simple"
                })
            return (info, pasos) if registrar_pasos else info
        inv_det = [det[1], det[0]]
        ATmp = [
            [ d, negativo_fraccion(b) ],
            [ negativo_fraccion(c), a ]
        ]
        inv = []
        i = 0
        while i < 2:
            fila = []
            j = 0
            while j < 2:
                fila.append(multiplicar_fracciones(ATmp[i][j], inv_det))
                j += 1
            inv.append(fila)
            i += 1
        if registrar_pasos:
            pasos.append({
                "operacion": f"Paso 1: ad = {text_fn(ad)}, bc = {text_fn(bc)}",
                "matriz": copiar_matriz(A),
                "tipo": "simple"
            })
            pasos.append({
                "operacion": f"Paso 2: Determinante det = ad − bc = {text_fn(ad)} − {text_fn(bc)} = {text_fn(det)} ≠ 0",
                "matriz": copiar_matriz(A),
                "tipo": "simple"
            })
            pasos.append({
                "operacion": "Paso 3: Matriz adjunta Adj(A) = [ d  −b ; −c  a ]",
                "matriz": copiar_matriz(ATmp),
                "tipo": "simple"
            })
            pasos.append({
                "operacion": f"Paso 4: A^{-1} = (1/{text_fn(det)}) · Adj(A)",
                "matriz": copiar_matriz(inv),
                "tipo": "simple"
            })
        info = {"invertible": True, "inversa": inv, "metodo": "2x2"}
        return (info, pasos) if registrar_pasos else info

    # Caso n≥3: Gauss-Jordan sobre [A | I]
    # Construir matriz aumentada con I a la derecha
    ancho = n * 2 # duplica el tamaño de la matriz
    M = []
    i = 0
    while i < n:
        fila = []
        j = 0
        while j < n:
            fila.append([A[i][j][0], A[i][j][1]])
            j += 1
        # añadir identidad
        j = 0
        while j < n:
            fila.append([1,1] if i == j else [0,1])
            j += 1
        M.append(fila)
        i += 1
    if registrar_pasos:
        pasos.append({"operacion": "Formamos [A | I]", "matriz": copiar_matriz(M), "tipo": "simple"})

    # Gauss-Jordan sobre primeras n columnas
    fila_piv = 0
    col = 0
    while col < n and fila_piv < n:
        # buscar pivote
        r = fila_piv
        piv_row = -1
        while r < n:
            if not es_cero(M[r][col]):
                piv_row = r; break
            r += 1
        if piv_row == -1:
            info = {"invertible": False, "inversa": None, "metodo": "gauss", "razon": f"Columna {col+1} sin pivote"}
            return (info, pasos) if registrar_pasos else info
        if piv_row != fila_piv:
            fila_intercambiar(M, fila_piv, piv_row)
            if registrar_pasos:
                pasos.append({"operacion": f"Intercambiamos filas {fila_piv+1} y {piv_row+1}", "matriz": copiar_matriz(M), "tipo": "fila"})
        piv = M[fila_piv][col]
        if not es_uno(piv):
            c = [piv[1], piv[0]]  # multiplicar por 1/piv
            fila_escalar(M, fila_piv, c)
            if registrar_pasos:
                pasos.append({"operacion": f"Escalamos fila {fila_piv+1} para hacer pivote = 1", "matriz": copiar_matriz(M), "tipo": "fila"})
        # eliminar en otras filas
        r = 0
        while r < n:
            if r != fila_piv and not es_cero(M[r][col]):
                factor = negativo_fraccion(M[r][col])
                fila_sumar_multiplo(M, r, fila_piv, factor)
                if registrar_pasos:
                    pasos.append({"operacion": f"Anulamos entrada ({r+1},{col+1}) con la fila {fila_piv+1}", "matriz": copiar_matriz(M), "tipo": "fila"})
            r += 1
        fila_piv += 1
        col += 1

    # extra: verificar que el bloque izquierdo es I
    i = 0
    while i < n:
        j = 0
        while j < n:
            if i == j and not es_uno(M[i][j]):
                info = {"invertible": False, "inversa": None, "metodo": "gauss", "razon": "El bloque izquierdo no es identidad"}
                return (info, pasos) if registrar_pasos else info
            if i != j and not es_cero(M[i][j]):
                info = {"invertible": False, "inversa": None, "metodo": "gauss", "razon": "No se logró identidad en A"}
                return (info, pasos) if registrar_pasos else info
            j += 1
        i += 1
    # extraer derecha como inversa
    inv = []
    i = 0
    while i < n:
        fila = []
        j = n
        while j < ancho:
            fila.append([M[i][j][0], M[i][j][1]])
            j += 1
        inv.append(fila)
        i += 1
    if registrar_pasos:
        pasos.append({"operacion": "Extraemos la derecha: A^{-1}", "matriz": copiar_matriz(inv), "tipo": "simple"})
    info = {"invertible": True, "inversa": inv, "metodo": "gauss"}
    return (info, pasos) if registrar_pasos else info
