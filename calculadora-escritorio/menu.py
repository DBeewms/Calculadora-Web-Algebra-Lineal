import operaciones
import utilidades as u

def leer_matriz_aumentada():
    m = int(input("Número de ecuaciones m = ").strip())
    n = int(input("Número de incógnitas n = ").strip())
    matriz = []
    i = 0
    while i < m:
        linea = input("Ingrese fila " + str(i+1) + " (valores separados por espacios, incluida b): ").strip().split()
        if len(linea) != n + 1:
            print("Cantidad incorrecta de valores. Deben ser", n+1)
            continue
        fila = []
        j = 0
        while j < len(linea):
            fr = u.crear_fraccion_desde_cadena(linea[j])
            fila.append(fr)
            j = j + 1
        matriz.append(fila)
        i = i + 1
    return matriz

def leer_matriz_simple(nombre="A"):
    print(f"\nIngrese dimensiones de la matriz {nombre}:")
    m = int(input("Filas (m) = ").strip())
    n = int(input("Columnas (n) = ").strip())
    print(f"\nIntroduzca la matriz {nombre} fila por fila (valores separados por espacios):")
    matriz = []
    i = 0
    while i < m:
        linea = input(f"Fila {i+1} de {nombre}: ").strip().split()
        if len(linea) != n:
            print("Cantidad incorrecta de valores. Deben ser", n)
            continue
        fila = []
        j = 0
        while j < len(linea):
            fr = u.crear_fraccion_desde_cadena(linea[j])
            fila.append(fr)
            j = j + 1
        matriz.append(fila)
        i = i + 1
    return matriz

def imprimir_matriz(M):
    if len(M) == 0:
        print("[]")
        return
    filas = len(M)
    columnas = len(M[0])
    anchos = []
    j = 0
    while j < columnas:
        maximo = 0
        i = 0
        while i < filas:
            texto = u.texto_fraccion(M[i][j])
            largo = len(texto)
            if largo > maximo:
                maximo = largo
            i = i + 1
        anchos.append(maximo)
        j = j + 1
    i = 0
    while i < filas:
        partes = []
        j = 0
        while j < columnas:
            txt = u.texto_fraccion(M[i][j])
            espacios = anchos[j] - len(txt)
            pad = " " * espacios
            partes.append(pad + txt)
            j = j + 1
        print("[ " + "  ".join(partes) + " ]")
        i = i + 1

def imprimir_matriz_aumentada(M):
    if len(M) == 0:
        print("[]")
        return
    filas = len(M)
    columnas_totales = len(M[0])
    columnas_A = columnas_totales - 1
    anchos = []
    j = 0
    while j < columnas_totales:
        maximo = 0
        i = 0
        while i < filas:
            texto = u.texto_fraccion(M[i][j])
            largo = len(texto)
            if largo > maximo:
                maximo = largo
            i = i + 1
        anchos.append(maximo)
        j = j + 1
    i = 0
    while i < filas:
        izquierda = ""
        j = 0
        while j < columnas_A:
            if j > 0:
                izquierda = izquierda + "  "
            txt = u.texto_fraccion(M[i][j])
            espacios = anchos[j] - len(txt)
            k = 0
            while k < espacios:
                izquierda = izquierda + " "
                k = k + 1
            izquierda = izquierda + txt
            j = j + 1
        txt_b = u.texto_fraccion(M[i][columnas_A])
        espacios_b = anchos[columnas_A] - len(txt_b)
        pad = ""
        k = 0
        while k < espacios_b:
            pad = pad + " "
            k = k + 1
        print("[ " + izquierda + " | " + pad + txt_b + " ]")
        i = i + 1

def mostrar_pasos(pasos):
    if not pasos:
        print("No se realizaron operaciones (la matriz ya estaba en forma escalonada reducida por filas o vacía).")
        return
    i = 0
    while i < len(pasos):
        paso = pasos[i]
        if isinstance(paso, dict):
            print(f"{i+1:02d}) {paso.get('operacion','')}")
            tipo = paso.get('tipo', 'aumentada')
            mat = paso.get('matriz', [])
            if tipo == 'simple':
                imprimir_matriz(mat)
            else:
                imprimir_matriz_aumentada(mat)
            if i < len(pasos) - 1:
                print("-" * 40)
        else:
            print(f"{i+1:02d}) {paso}")
        i += 1

def mostrar_resultado(R, info):
    solucion = info["solucion"]
    tipo = info.get("tipo_forma", "ESCALONADA_REDUCIDA")
    etiqueta = "Matriz en forma escalonada reducida por filas ([A|b]):" if tipo == "ESCALONADA_REDUCIDA" else "Matriz en forma escalonada ([A|b]):"
    pivotes = info.get("pivotes", [])
    if solucion == "INCONSISTENTE":
        print("Solución:", solucion)
        print(etiqueta)
        if tipo == "ESCALONADA_REDUCIDA":
            print("Columnas pivote:", ", ".join(str(p+1) for p in pivotes))
        imprimir_matriz_aumentada(R)
        return
    if solucion == "UNICA":
        print("Solución:", solucion)
        valores = info.get("solucion_particular", [])
        i = 0
        while i < len(valores):
            frac = u.texto_fraccion(valores[i])
            dec = u.texto_decimal(valores[i])
            print("x" + str(i+1) + " = " + frac + " = " + dec)
            i = i + 1
        print(etiqueta)
        if tipo == "ESCALONADA_REDUCIDA":
            print("Columnas pivote:", ", ".join(str(p+1) for p in pivotes))
        imprimir_matriz_aumentada(R)
        return
    if solucion == "INFINITAS":
        print("Solución:", solucion)
        # Si es Gauss-Jordan, expresar cada variable en función de las libres
        if tipo == "ESCALONADA_REDUCIDA":
            m = len(R)
            n = len(R[0]) - 1
            # Determinar columnas libres
            es_pivote = [False] * n
            for c in pivotes:
                if 0 <= c < n:
                    es_pivote[c] = True
            libres = [j for j in range(n) if not es_pivote[j]]
            # Mostrar variables libres
            if libres:
                print("Variables libres:", ", ".join(f"x{j+1}" for j in libres))
            # Expresar variables pivote
            if pivotes:
                print("Variables dependientes en función de las libres:")
            r = 0
            while r < m and r < len(pivotes):
                c = pivotes[r]
                # x_c = b - sum(coef_j * x_j libres)
                b = R[r][n]
                # Construir expresión
                partes = [u.texto_fraccion(b)]
                j = 0
                while j < n:
                    if not es_pivote[j]:
                        coef = R[r][j]
                        if not u.es_cero(coef):
                            # term = -coef * t_k
                            neg = u.negativo_fraccion(coef)
                            # signo y valor absoluto
                            signo = "-" if neg[0] < 0 else "+"
                            abs_val = [-neg[0], neg[1]] if neg[0] < 0 else [neg[0], neg[1]]
                            coef_txt = u.texto_fraccion(abs_val)
                            partes.append(f" {signo} {coef_txt}·x{j+1}")
                    j += 1
                print(f"x{c+1} = " + "".join(partes))
                r += 1
            # Si no hay pivotes, todas son libres: ya se imprimieron
        print(etiqueta)
        if tipo == "ESCALONADA_REDUCIDA":
            print("Columnas pivote:", ", ".join(str(p+1) for p in pivotes))
        imprimir_matriz_aumentada(R)
