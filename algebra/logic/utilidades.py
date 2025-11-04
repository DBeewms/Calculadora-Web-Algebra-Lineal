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
    """Convierte texto a fracción [n,d].

    Soporta:
    - enteros ("12"), decimales ("3.5"), fracciones simples ("3/4")
    - expresiones con +, -, *, ×, /, ÷, ^, paréntesis y raíz: sqrt( … ) o "√( … )"
      Ej.: "-3/4 + 2^3", "√(2)", "(1+1/2)/3"
    """
    texto = fraccion_texto.strip()

    # ¿Es una expresión más allá de los casos simples?
    has_ops = any(c in texto for c in ["+", "-", "*", "×", "/", "÷", "^", "(", ")", "√"]) or "sqrt" in texto
    if has_ops:
        return _evaluar_expresion_a_fraccion(texto)

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

def _es_decimal_finito(denominador):
    """Devuelve True si 1/denominador tiene expansión decimal finita (solo factores 2 y 5)."""
    if denominador == 0:
        return False
    d = denominador if denominador >= 0 else -denominador
    # eliminar factores 2 y 5
    while d % 2 == 0:
        d //= 2
    while d % 5 == 0:
        d //= 5
    return d == 1

def texto_numero(a, modo="frac", decimales=6):
    """Formatea una fracción [n,d] según el modo solicitado.

    - modo = 'frac'  => fracción exacta (usa texto_fraccion)
    - modo = 'dec'   => decimal con 'decimales' cifras
    - modo = 'auto'  => si el decimal es finito, mostrar decimal exacto; en otro caso fracción
    """
    if modo == "dec":
        return texto_decimal(a, decimales=decimales)
    if modo == "auto":
        # si el denominador produce decimal finito, mostramos decimal con los dígitos justos
        if _es_decimal_finito(a[1]):
            # usar muchos decimales y recortar ceros finales
            return texto_decimal(a, decimales=max(decimales, 12))
        return texto_fraccion(a)
    # por defecto: fracción exacta
    return texto_fraccion(a)

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

# =====================
#  Expresiones numéricas
# =====================

def _normalizar_entrada(expr: str) -> str:
    # Unificar símbolos unicode a ASCII y eliminar espacios
    e = expr.replace("×", "*").replace("÷", "/").replace("−", "-")
    e = e.replace("√", "sqrt")
    # permitir coma decimal? lo ignoramos, usamos '.'
    return "".join(ch for ch in e if ch not in [" ", "\t", "\n"])

def _es_numero_token(tok: str) -> bool:
    if not tok:
        return False
    if tok.count(".") > 1:
        return False
    # permite números como .5 -> 0.5
    if tok.startswith('.'):
        tok = '0' + tok
    return tok.replace('.', '', 1).isdigit()

def _tokenizar(expr: str):
    e = _normalizar_entrada(expr)
    tokens = []
    i = 0
    while i < len(e):
        ch = e[i]
        # función sqrt
        if e.startswith('sqrt', i):
            tokens.append('sqrt')
            i += 4
            continue
        if ch.isdigit() or ch == '.':
            j = i + 1
            while j < len(e) and (e[j].isdigit() or e[j] == '.'):
                j += 1
            tokens.append(e[i:j])
            i = j
            continue
        if ch in '+-*/^()':
            tokens.append(ch)
            i += 1
            continue
        # caracteres no ASCII que ya normalizamos: si quedara algo, error
        raise Exception(f"Carácter no soportado en la expresión: '{ch}'")
    return tokens

def _precedencia(op: str) -> int:
    if op == 'neg':
        # La negación unaria debe tener MENOR precedencia que la potencia
        # para que -3^2 se interprete como -(3^2)
        return 2
    if op == 'neg_hi':
        # Variante para exponentes: 2^-3 => 2^( -3 )
        return 5
    if op == 'sqrt':
        return 4
    if op == '^':
        return 3
    if op in ('*', '/'):
        return 2
    if op in ('+', '-'):
        return 1
    return 0

def _es_derecha_asociativo(op: str) -> bool:
    return op in ('^', 'neg')

def _a_rpn(tokens):
    salida = []
    pila = []
    prev = None
    for tok in tokens:
        if _es_numero_token(tok):
            salida.append(tok)
            prev = 'num'
            continue
        if tok == 'sqrt':
            pila.append('sqrt')
            prev = 'op'
            continue
        if tok in '+-*/^':
            # detectar unario: al inicio, tras '(', u operador
            if tok == '-' and (prev is None or prev in ('op', 'lp')):
                op = 'neg'
                # Si hay un '^' en la cima, queremos que la negación se aplique al exponente
                if pila and pila[-1] == '^':
                    op = 'neg_hi'
            else:
                op = tok
            while pila and pila[-1] not in ('(',) and (
                _precedencia(pila[-1]) > _precedencia(op) or (
                    _precedencia(pila[-1]) == _precedencia(op) and not _es_derecha_asociativo(op)
                )
            ):
                salida.append(pila.pop())
            pila.append(op)
            prev = 'op'
            continue
        if tok == '(':
            pila.append('(')
            prev = 'lp'
            continue
        if tok == ')':
            while pila and pila[-1] != '(':
                salida.append(pila.pop())
            if not pila:
                raise Exception('Paréntesis no balanceados')
            pila.pop()  # eliminar '('
            # si hay una función en la cima (sqrt), sacarla a salida
            if pila and pila[-1] == 'sqrt':
                salida.append(pila.pop())
            prev = 'rp'
            continue
        raise Exception(f"Token no soportado: {tok}")

    while pila:
        t = pila.pop()
        if t in ('(', ')'):
            raise Exception('Paréntesis no balanceados')
        salida.append(t)
    return salida

def _num_token_a_fraccion(tok: str):
    # normalizar .5 => 0.5
    if tok.startswith('.'):
        tok = '0' + tok
    if '.' in tok:
        return crear_fraccion_desde_decimal(tok)
    return crear_fraccion_desde_entero(tok)

def potencia_fraccion(a, e: int):
    if e == 0:
        return [1, 1]
    base_n, base_d = a[0], a[1]
    if e < 0:
        e = -e
        base_n, base_d = base_d, base_n
        if base_d == 0:
            raise Exception('División por cero en potencia negativa')
    # exponenciación entera
    n = 1
    d = 1
    i = 0
    while i < e:
        n *= base_n
        d *= base_d
        i += 1
    return simplificar_fraccion(n, d)

def _es_cuadrado_perfecto(n: int) -> bool:
    if n < 0:
        return False
    import math
    r = int(math.isqrt(n))
    return r * r == n

def sqrt_fraccion(a, precision_decimales: int = 10):
    """Devuelve la raíz cuadrada de la fracción. Si es exacta (ambos perfect squares), exacta; si no, aproxima.
    La aproximación se hace como fracción con denominador 10^precision_decimales.
    """
    if a[0] < 0:
        raise Exception('Raíz de número negativo no soportada')
    import math
    n, d = a[0], a[1]
    if _es_cuadrado_perfecto(n) and _es_cuadrado_perfecto(d):
        return simplificar_fraccion(int(math.isqrt(n)), int(math.isqrt(d)))
    # aproximación decimal
    val = math.sqrt(n / d)
    escala = 10 ** precision_decimales
    num = int(round(val * escala))
    return simplificar_fraccion(num, escala)

def _evaluar_rpn(rpn):
    pila = []
    for tok in rpn:
        if _es_numero_token(tok):
            pila.append(_num_token_a_fraccion(tok))
            continue
        if tok in ('+', '-', '*', '/', '^', 'sqrt', 'neg', 'neg_hi'):
            if tok == 'neg':
                if not pila:
                    raise Exception('Falta operando para negación')
                pila.append(negativo_fraccion(pila.pop()))
                continue
            if tok == 'neg_hi':
                if not pila:
                    raise Exception('Falta operando para negación')
                pila.append(negativo_fraccion(pila.pop()))
                continue
            if tok == 'sqrt':
                if not pila:
                    raise Exception('Falta operando para raíz')
                pila.append(sqrt_fraccion(pila.pop()))
                continue
            # binarios
            if len(pila) < 2:
                raise Exception('Faltan operandos')
            b = pila.pop()
            a = pila.pop()
            if tok == '+':
                pila.append(sumar_fracciones(a, b))
            elif tok == '-':
                pila.append(restar_fracciones(a, b))
            elif tok == '*':
                pila.append(multiplicar_fracciones(a, b))
            elif tok == '/':
                pila.append(dividir_fracciones(a, b))
            elif tok == '^':
                # exponente debe ser entero
                if b[1] != 1:
                    raise Exception('El exponente debe ser un entero')
                pila.append(potencia_fraccion(a, b[0]))
            continue
        else:
            raise Exception(f'Operador no soportado: {tok}')
    if len(pila) != 1:
        raise Exception('Expresión inválida')
    return pila[0]

def _evaluar_expresion_a_fraccion(expr: str):
    tokens = _tokenizar(expr)
    rpn = _a_rpn(tokens)
    return _evaluar_rpn(rpn)

# ======================================
#  Parseo de sistemas de ecuaciones lineales
# ======================================

def _normalizar_ecuacion(s: str) -> str:
    """Normaliza símbolos aritméticos pero preserva variables. Quita espacios.
    Permite ×, ÷, √ en los coeficientes.
    """
    if s is None:
        return ""
    # Reutiliza normalización pero sin eliminar letras
    e = s.replace("×", "*").replace("÷", "/").replace("−", "-")
    e = e.replace("√", "sqrt")
    # eliminar espacios
    return "".join(ch for ch in e if ch not in [" ", "\t", "\n", "\r"])

def _sumar_en_dic(dic, var, frac):
    """Acumula en dic[var] la fracción 'frac' (sumando)."""
    if var not in dic:
        dic[var] = frac
    else:
        dic[var] = sumar_fracciones(dic[var], frac)

def _parse_nombre_variable(s: str, i: int):
    """Devuelve (nombre, j) si en s[i:] hay una variable del tipo [a-zA-Z][a-zA-Z0-9_]*, o (None, i)."""
    if i < len(s) and s[i].isalpha():
        j = i + 1
        while j < len(s) and (s[j].isalnum() or s[j] == '_'):
            j += 1
        return s[i:j], j
    return None, i

def _parse_numeric_expr(s: str, i: int):
    """Intenta leer una expresión numérica (sin variables) desde s[i:].
    Acepta dígitos, '.', '+', '-', '*', '/', '^', '(', ')', y 'sqrt'.
    Se detiene antes de una variable o un '+'/'-' de nivel superior.
    Retorna (expr_str, j). expr_str puede ser "" si no hay nada que consumir.
    """
    start = i
    depth = 0
    while i < len(s):
        ch = s[i]
        if ch.isalpha():
            # inicio de variable o 'sqrt' pero si es 'sqrt' es parte numérica
            if s.startswith('sqrt', i):
                # consumir 'sqrt'
                i += 4
                continue
            break
        if depth == 0 and (ch == '+' or ch == '-'):
            break
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        i += 1
    expr = s[start:i]
    return expr, i

def _evaluar_coef(expr: str):
    expr = expr.strip()
    if not expr:
        return [1, 1]
    return _evaluar_expresion_a_fraccion(expr)

def _evaluar_num(expr: str):
    expr = expr.strip()
    if not expr:
        return [0, 1]
    return _evaluar_expresion_a_fraccion(expr)

def _parse_linear_side(s: str, side_sign: int):
    """Parsea un lado de la ecuación (sin el '=') y devuelve (coef_dict, const_frac) ya multiplicados por side_sign.
    coef_dict: { var -> [n,d] }
    const_frac: [n,d]
    """
    i = 0
    coeffs = {}
    const = [0, 1]
    current_sign = 1
    while i < len(s):
        ch = s[i]
        if ch == '+':
            current_sign = 1
            i += 1
            continue
        if ch == '-':
            current_sign = -1
            i += 1
            continue
        # Intentar leer una parte numérica
        num_expr, j = _parse_numeric_expr(s, i)
        # Permitir '*' explícito entre coef y var
        k = j
        if k < len(s) and s[k] == '*':
            k += 1
        # ¿Sigue una variable?
        var, end = _parse_nombre_variable(s, k)
        if var:
            coef = _evaluar_coef(num_expr)
            if current_sign * side_sign == -1:
                coef = negativo_fraccion(coef)
            _sumar_en_dic(coeffs, var, coef)
            i = end
            continue
        # No hay variable: es un término numérico solo
        val = _evaluar_num(num_expr)
        if current_sign * side_sign == -1:
            val = negativo_fraccion(val)
        const = sumar_fracciones(const, val)
        i = j
    return coeffs, const

def parsear_sistema_ecuaciones(texto: str):
    """Convierte un sistema ingresado como ecuaciones en A y b.

    Entrada: multilinea, cada línea con '='. Ej:
        x + 2y = 5
        3x - y = 4

    Soporta coeficientes como fracciones/decimales/expresiones con + - * / ^ sqrt() y paréntesis.
    Variables válidas: nombres que comienzan por letra, p.ej. x, y, z, x1, a2.

    Retorna (variables, A, b), donde A es lista de filas con fracciones [n,d] y b es lista de fracciones [n,d].
    """
    raw = (texto or "").strip()
    if not raw:
        raise ValueError("No se ingresaron ecuaciones.")
    lineas = []
    # Permitir separar por ';' además de nuevas líneas
    for ln in raw.replace(';', '\n').splitlines():
        t = ln.strip()
        if t:
            lineas.append(t)
    if not lineas:
        raise ValueError("No se encontraron ecuaciones válidas.")

    ecuaciones = []
    variables_set = set()
    for linea in lineas:
        if '=' not in linea:
            raise ValueError("Cada ecuación debe contener '='.")
        L, R = linea.split('=', 1)
        Ln = _normalizar_ecuacion(L)
        Rn = _normalizar_ecuacion(R)
        # Para recolectar variables, hacemos un escaneo simple
        for ch in Ln + Rn:
            # recolectar nombres completos
            pass
        # Parseo de lados
        cL, kL = _parse_linear_side(Ln, +1)
        cR, kR = _parse_linear_side(Rn, -1)
        # Unir coeficientes
        coeffs = {}
        for d in (cL, cR):
            for v, fr in d.items():
                variables_set.add(v)
                _sumar_en_dic(coeffs, v, fr)
        const = sumar_fracciones(kL, kR)  # kL - kR ya está incorporado en side_sign
        ecuaciones.append((coeffs, const))

    if not variables_set:
        raise ValueError("No se detectaron variables en las ecuaciones.")
    vars_orden = sorted(variables_set)

    # Construir A y b
    A = []
    b = []
    for coeffs, const in ecuaciones:
        fila = []
        for v in vars_orden:
            c = coeffs.get(v, [0, 1])
            fila.append(c)
        # Pasar constantes al lado derecho: sum_i a_i x_i = b  con  b = -const_total
        b_val = negativo_fraccion(const)
        A.append(fila)
        b.append(b_val)
    return vars_orden, A, b
