from . import utilidades as u
from .utilidades import (
    texto_fraccion, copiar_matriz, es_cero, es_uno, negativo_fraccion,
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

def _gauss_jordan_detallado(M):
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
            registrar("F" + str(fila_pivote+1) + " → (1/" + texto_fraccion(piv) + ")·F" + str(fila_pivote+1))
        # Anular el resto de la columna
        r = 0
        while r < m:
            if r != fila_pivote and not es_cero(R[r][col]):
                factor = R[r][col]
                fila_sumar_multiplo(R, r, fila_pivote, negativo_fraccion(factor))
                registrar("F" + str(r+1) + " → F" + str(r+1) + " − (" + texto_fraccion(factor) + ")·F" + str(fila_pivote+1))
            r += 1
        fila_pivote += 1
        col += 1
    # Estado final
    registrar("Matriz en forma escalonada reducida por filas (final)")
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

def gauss_jordan(M, registrar_pasos=False):
    """Envuelve Gauss-Jordan devolviendo sólo lo necesario para la vista.

    - Si registrar_pasos es True: retorna (R, pasos)
    - En caso contrario: retorna sólo R
    """
    R, _pivotes, pasos = _gauss_jordan_detallado(M)
    return (R, pasos) if registrar_pasos else R

def eliminacion_gauss(M):
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
            registrar("F" + str(fila_pivote+1) + " → (1/" + texto_fraccion(piv) + ")·F" + str(fila_pivote+1))
        r = fila_pivote + 1
        while r < m:
            if not es_cero(R[r][col]):
                factor = R[r][col]
                fila_sumar_multiplo(R, r, fila_pivote, negativo_fraccion(factor))
                registrar("F" + str(r+1) + " → F" + str(r+1) + " − (" + texto_fraccion(factor) + ")·F" + str(fila_pivote+1))
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

def gauss(M, registrar_pasos=False):
    """Envuelve la eliminación de Gauss devolviendo formato amigable a las vistas.

    - Si registrar_pasos es True: retorna (R, pasos)
    - En caso contrario: retorna sólo R
    """
    R, _pivotes, pasos = eliminacion_gauss(M)
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

def construir_expresiones_parametricas_rref(R, pivotes):
    """Construye expresiones de variables dependientes (pivote) en función
    de variables libres para una matriz aumentada en forma escalonada reducida.

    Devuelve dict con:
      - expresiones: lista de strings 'x_i = ...'
      - libres: indices columnas libres
      - mapa_parametros: {columna_libre: nombre_parametro}
    """
    m = len(R)
    n = len(R[0]) - 1
    libres = _variables_libres(n, pivotes)
    # Usar directamente los nombres de las variables libres (x_j) en lugar de parámetros t
    expresiones = []
    # Para cada fila (en orden) asociada a pivote
    r = 0
    while r < len(pivotes) and r < m:
        pcol = pivotes[r]
        # b es término independiente
        b = R[r][n]
        partes = []
        if not es_cero(b):
            partes.append(texto_fraccion(b))
        # Para cada libre f aparece con signo negativo al trasladar al otro lado
        li = 0
        while li < len(libres):
            fcol = libres[li]
            coef = R[r][fcol]
            if not es_cero(coef):
                # x_p = b - coef * x_f  (mostramos directo x{fcol+1})
                # Simplificar coef = 1 o -1 en representación
                frac_txt = texto_fraccion(coef)
                if frac_txt == '1':
                    term = f"- x{fcol+1}"
                elif frac_txt == '-1':
                    term = f"+ x{fcol+1}"  # porque -(-1)*x => + x
                else:
                    term = f"- {frac_txt}·x{fcol+1}"
                partes.append(term)
            li += 1
        if not partes:
            rhs = "0"
        else:
            # Unir y limpiar dobles espacios
            rhs = " ".join(partes).replace("  ", " ")
            # Si comienza con '- ' dejarlo así, si contiene patrones '- -' simplificar se omite por simplicidad
        expresiones.append(f"x{pcol+1} = {rhs}")
        r += 1
    return {"expresiones": expresiones, "libres": libres}

def gauss_info(M, registrar_pasos=False):
    """Devuelve toda la información necesaria para la vista de Gauss:
    {
      'matriz': R (forma escalonada),
      'pivotes': [...],
      'pasos': [...]*opcional,
      'analisis': { tipo, vector_solucion, libres, ... }
    }
    """
    R, pivotes, pasos = eliminacion_gauss(M)
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
            vector_sol.append(f"x{j+1} = {texto_fraccion(base['solucion_particular'][j])}")
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
            vector_sol.append(f"x{j+1} = {texto_fraccion(base['solucion_particular'][j])}")
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
            analisis["detalle"] = f"Fila {fila_inc+1} indica 0 = {texto_fraccion(R[fila_inc][ncols])}"
    info = {"matriz": R, "pivotes": pivotes, "analisis": analisis}
    if registrar_pasos:
        info["pasos"] = pasos
    return info

def gauss_jordan_info(M, registrar_pasos=False):
    """Devuelve información extendida para la vista Gauss-Jordan, incluyendo
    expresiones paramétricas cuando hay variables libres."""
    R, pivotes, pasos = _gauss_jordan_detallado(M)
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
            vector_sol.append(f"x{j+1} = {texto_fraccion(base['solucion_particular'][j])}")
            j += 1
        analisis["vector_solucion"] = vector_sol
    elif base["solucion"] == "INFINITAS":
        datos_param = construir_expresiones_parametricas_rref(R, pivotes)
        libres = datos_param["libres"]
        analisis["libres"] = libres
        analisis["libres_nombres"] = [f"x{c+1}" for c in libres]
        analisis["expresiones"] = datos_param["expresiones"]
        analisis["libres_detalle"] = [f"x{c+1} libre" for c in libres]
        vector_sol = []
        j = 0
        while j < n:
            vector_sol.append(f"x{j+1} = {texto_fraccion(base['solucion_particular'][j])}")
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
            analisis["detalle"] = f"Fila {fila_inc+1} indica 0 = {texto_fraccion(R[fila_inc][ncols])}"
    info = {"matriz": R, "pivotes": pivotes, "analisis": analisis}
    if registrar_pasos:
        info["pasos"] = pasos
    return info

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

def multiplicar_matrices(A, B, registrar_pasos=False):
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
    # Paso inicial
    pasos.append({"operacion": "Inicializar C (m×n) con ceros", "matriz": copiar_matriz(C), "tipo": "simple"})

    # Hacemos la multiplicación por columnas: cada columna j de C es combinación
    # lineal de las columnas de A con coeficientes en la columna j de B.
    j = 0
    while j < n:
        pasos.append({"operacion": f"Calcular columna {j+1} de C como combinación lineal de columnas de A (usando la columna {j+1} de B)", "matriz": copiar_matriz(C), "tipo": "simple"})
        k = 0
        while k < p:
            coef = B[k][j]
            # Añadir coef * columna k de A a la columna j de C
            i = 0
            while i < m:
                termino = multiplicar_fracciones(coef, A[i][k])
                C[i][j] = sumar_fracciones(C[i][j], termino)
                i += 1
            pasos.append({"operacion": f"Agregar ({texto_fraccion(coef)})·columna A{ k+1 } a columna {j+1} de C", "matriz": copiar_matriz(C), "tipo": "simple"})
            k += 1
        # Resumen de la columna j
        partes = []
        k = 0
        while k < p:
            coef = B[k][j]
            if not u.es_cero(coef):
                partes.append(texto_fraccion(coef) + "·A[:," + str(k+1) + "]")
            k += 1
        suma_text = " + ".join(partes) if partes else "0"
        pasos.append({"operacion": f"Columna {j+1} terminada: C[:,{j+1}] = {suma_text}", "matriz": copiar_matriz(C), "tipo": "simple"})
        j += 1

    return (C, pasos) if registrar_pasos else C
