def mcd(a, b):
    a = a if a >= 0 else -a
    b = b if b >= 0 else -b
    while b != 0:
        resto = a % b
        a = b
        b = resto
    return a

def simplificar_fraccion(numerador, denominador):
    if denominador == 0:
        raise Exception("Denominador cero.")
    if denominador < 0:
        numerador = -numerador
        denominador = -denominador
    divisor = mcd(numerador, denominador)
    num_s = numerador // divisor
    den_s = denominador // divisor
    return [num_s, den_s]

def crear_fraccion_desde_entero(texto):
    numero = int(texto)
    return [numero, 1]

def crear_fraccion_desde_decimal(texto):
    negativo = False
    cadena = texto
    if cadena[0] == "-":
        negativo = True
        cadena = cadena[1:]
    partes = cadena.split(".")
    if len(partes) == 1:
        entero = int(partes[0])
        if negativo:
            entero = -entero
        return [entero, 1]
    parte_entera = partes[0]
    parte_decimal = partes[1]
    if parte_entera == "":
        parte_entera = "0"
    decimales = 0
    indice = 0
    while indice < len(parte_decimal):
        if parte_decimal[indice].isdigit():
            decimales = decimales + 1
        indice = indice + 1
    base = 1
    j = 0
    while j < decimales:
        base = base * 10
        j = j + 1
    numero_sin_punto = int(parte_entera + parte_decimal)
    if negativo:
        numero_sin_punto = -numero_sin_punto
    return simplificar_fraccion(numero_sin_punto, base)

def crear_fraccion_desde_cadena(fraccion_texto):
    texto = fraccion_texto.strip()
    if "/" in texto:
        partes = texto.split("/")
        numerador = int(partes[0].strip())
        denominador = int(partes[1].strip())
        return simplificar_fraccion(numerador, denominador)
    if "." in texto:
        return crear_fraccion_desde_decimal(texto)
    return crear_fraccion_desde_entero(texto)

def sumar_fracciones(a, b):
    a_n = a[0]
    a_d = a[1]
    b_n = b[0]
    b_d = b[1]
    numerador = a_n * b_d + b_n * a_d
    denominador = a_d * b_d
    return simplificar_fraccion(numerador, denominador)

def restar_fracciones(a, b):
    a_n = a[0]
    a_d = a[1]
    b_n = b[0]
    b_d = b[1]
    numerador = a_n * b_d - b_n * a_d
    denominador = a_d * b_d
    return simplificar_fraccion(numerador, denominador)

def multiplicar_fracciones(a, b):
    a_n = a[0]
    a_d = a[1]
    b_n = b[0]
    b_d = b[1]
    numerador = a_n * b_n
    denominador = a_d * b_d
    return simplificar_fraccion(numerador, denominador)

def dividir_fracciones(a, b):
    if b[0] == 0:
        raise Exception("División por cero.")
    a_n = a[0]
    a_d = a[1]
    b_n = b[0]
    b_d = b[1]
    numerador = a_n * b_d
    denominador = a_d * b_n
    return simplificar_fraccion(numerador, denominador)

def negativo_fraccion(a):
    return [-a[0], a[1]]

def es_cero(a):
    return a[0] == 0

def es_uno(a):
    return a[0] == a[1]

def texto_fraccion(a):
    if a[1] == 1:
        return str(a[0])
    else:
        return str(a[0]) + "/" + str(a[1])

def texto_decimal(a, decimales=6):
    """Convierte una fracción a decimal con precisión dada. Se recorta el cero final y el punto si quedan innecesarios."""
    if a[1] == 0:
        return "∞"
    valor = a[0] / a[1]
    formato = ("{:." + str(decimales) + "f}").format(valor)
    # quitar ceros a la derecha y posible punto final
    formato = formato.rstrip('0').rstrip('.') if '.' in formato else formato
    return formato

def copiar_matriz(M):
    R = []
    filas = len(M)
    if filas == 0:
        return R
    columnas = len(M[0])
    i = 0
    while i < filas:
        fila = []
        j = 0
        while j < columnas:
            par = M[i][j]
            fila.append([par[0], par[1]])
            j = j + 1
        R.append(fila)
        i = i + 1
    return R
