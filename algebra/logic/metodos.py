"""Módulo de métodos numéricos

Descripción:
- Para evaluar expresiones ingresadas por el
  usuario se emplea un evaluador controlado que sólo expone
  funciones del módulo math y un pequeño conjunto de funciones seguras.

Importaciones:
- math: proporciona funciones matemáticas (sin, cos, exp, log, etc.) y
  constantes (pi, e). Se usa para permitir que el usuario escriba
  expresiones usando esas funciones.
"""
import math
from typing import Callable

class ErrorBiseccion(ValueError):
    """Excepción específica para errores durante el proceso de bisección."""
    pass

def _crear_evaluador(texto_funcion):
    """Construye y devuelve una función evaluadora f(x) a partir de la
    cadena `texto_funcion`.

    Lanza ErrorBiseccion si la expresión es inválida o falla la compilación.
    """
    if not texto_funcion or not texto_funcion.strip():
        raise ErrorBiseccion("La expresión de la función está vacía.")

    # Normalizaciones menores: muchos usuarios escriben '^' para potencia
    # (ej: x^2). En Python '^' es XOR, no potencia, por eso transformamos a
    # '**' antes de compilar. También permitimos que el usuario envíe una
    # ecuación del tipo "lhs = rhs" y la normalizamos a "(lhs) - (rhs)"
    # para obtener una expresión equivalente f(x) = lhs - rhs.
    texto_normalizado = texto_funcion.replace('^', '**')

    # Normalizaciones adicionales para aceptar entradas tipo LaTeX que
    # usan llaves y escapes: convertir '{' '}' a paréntesis y quitar '\\'.
    # Ej: e^{-x} -> e**(-x)
    try:
        texto_normalizado = texto_normalizado.replace('{', '(').replace('}', ')')
        texto_normalizado = texto_normalizado.replace('\\', '')
        # Normalizar signos unicode comunes
        texto_normalizado = texto_normalizado.replace('\u2212', '-')
        # MathLive/other frontends sometimes render Euler's constant as
        # 'exponentialE' or similar; normalizarlo a 'E' para que sympy lo
        # reconozca como la constante de Euler.
        texto_normalizado = texto_normalizado.replace('exponentialE', 'E')
    except Exception:
        # En caso de cualquier problema con replace, continuar sin bloquear.
        pass

    # Si el usuario envía una ecuación con '=' convertimos a una expresión
    # restando los dos lados. Esto evita errores de sintaxis (por ejemplo
    # '=' no es válido en modo eval) y hace al servidor robusto frente a
    # clientes que no normalicen correctamente antes de enviar.
    if '=' in texto_normalizado:
        try:
            left, right = texto_normalizado.split('=', 1)
            left = left.strip() or '0'
            right = right.strip() or '0'
            texto_normalizado = f"({left}) - ({right})"
        except Exception:
            # Si por alguna razón el split falla, dejamos la cadena original
            # y seguiremos con el intento de parseo/compilación que levantará
            # el ErrorBiseccion correspondiente.
            pass

    # Intentar usar sympy para parseo seguro y lambdify
    # Si sympy no está disponible, se usa la estrategia anterior dentro de un entorno restringido.
    try:
        import sympy as sp

        # Parsear la expresión con sympy
        try:
            x_sym = sp.symbols('x')
            # Aceptar alias comunes: 'ln' -> log y 'e' -> E (constante de Euler)
            sym_locals = {'ln': sp.log, 'e': sp.E}
            expresion = sp.sympify(texto_normalizado, locals=sym_locals, evaluate=True)
        except Exception as e:
            raise ErrorBiseccion(f"Expresión inválida (sympy): {e}")

        # Crear una función numérica eficiente usando lambdify. Usamos el módulo 'math'
        # para que devuelva valores numéricos con funciones estándar.
        try:
            f_lamb = sp.lambdify(x_sym, expresion, modules=["math"])
        except Exception:
            # En caso de que lambdify falle por alguna razón usamos una conversión a
            # objeto sympy que luego evaluaremos numéricamente.
            def f_lamb(x_val):
                try:
                    return float(expresion.evalf(subs={x_sym: x_val}))
                except Exception as e2:
                    raise ErrorBiseccion(f"Error evaluando la función (sympy) en x={x_val}: {e2}")

        # Guardar el texto original para mensajes de error más claros
        _orig_text = texto_funcion

        def _es_secuencial(v):
            # consideramos secuencial cualquier iterable con __len__ distinto de str/bytes
            return (hasattr(v, '__len__') and not isinstance(v, (str, bytes)))

        def evaluar(x):
            try:
                val = f_lamb(x)

                # Detectar valores inesperados (None o estructuras secuenciales)
                if val is None:
                    raise ErrorBiseccion(f"El evaluador devolvió None para x={x}. Expresión: {repr(_orig_text)}")
                if _es_secuencial(val):
                    raise ErrorBiseccion(f"La función evaluada devolvió un objeto secuencial en x={x} (esperado escalar). Expresión: {repr(_orig_text)}")

                # f_lamb puede devolver un int/float o un objeto sympy.
                # Intentar convertir a float de forma robusta.
                try:
                    return float(val)
                except TypeError:
                    # Si es un objeto sympy que no admite float() directamente,
                    # intentar evalf() y convertir.
                    try:
                        return float(val.evalf())
                    except Exception:
                        # Como último recurso evaluar la expresión sympy numéricamente
                        # usando expresion.evalf con subs.
                        try:
                            v2 = expresion.evalf(subs={x_sym: x})
                            if v2 is None:
                                raise ErrorBiseccion(f"La evaluación sympy devolvió None para x={x}. Expresión: {repr(_orig_text)}")
                            if _es_secuencial(v2):
                                raise ErrorBiseccion(f"La evaluación sympy devolvió un objeto secuencial en x={x}. Expresión: {repr(_orig_text)}")
                            return float(v2)
                        except ErrorBiseccion:
                            raise
                        except Exception as e3:
                            raise ErrorBiseccion(f"Error evaluando la función (sympy) en x={x}: {e3}")
            except ErrorBiseccion:
                # Re-lanzar nuestras propias excepciones sin envoltura extra
                raise
            except Exception as e:
                raise ErrorBiseccion(f"Error evaluando la función (sympy) en x={x}: {e}")

        return evaluar

    except ImportError:
        # Fallback: usar el evaluador basado en compile/eval en un entorno restringido.
        try:
            codigo = compile(texto_normalizado, '<biseccion>', 'eval')
        except Exception as e:
            raise ErrorBiseccion(f"Expresión inválida: {e}")

        # Exponer sólo las funciones y constantes del módulo math y un par de
        # funciones seguras adicionales.
        nombres_permitidos = {k: getattr(math, k) for k in dir(math) if not k.startswith('__')}
        nombres_permitidos.update({'abs': abs, 'pow': pow})

        def evaluar(x):
            try:
                contexto_local = {'x': x}
                # Evaluar con __builtins__ deshabilitado y sólo los nombres
                # permitidos en el globals/local.
                val = eval(codigo, {'__builtins__': None}, {**nombres_permitidos, **contexto_local})
                # Comprobaciones defensivas: None o secuenciales no están permitidos
                if val is None:
                    raise ErrorBiseccion(f"El evaluador devolvió None para x={x}. Expresión: {repr(texto_normalizado)}")
                if hasattr(val, '__len__') and not isinstance(val, (str, bytes)):
                    raise ErrorBiseccion(f"La evaluación devolvió un objeto secuencial en x={x} (esperado escalar). Expresión: {repr(texto_normalizado)}")
                return float(val)
            except ErrorBiseccion:
                raise
            except Exception as e:
                raise ErrorBiseccion(f"Error evaluando la función en x={x}: {e}")

        return evaluar


def biseccion(texto_funcion, a, b, tol=1e-6, maxit=100):
    """Ejecuta el método de la bisección en el intervalo [a, b].

    Parámetros:
    - texto_funcion: cadena con la expresión matemática en variable 'x'.
    - a, b: extremos del intervalo (números).
    - tol: tolerancia (positivo).
    - maxit: máximo de iteraciones.

    Retorna un diccionario con las siguientes claves (en español):
      - 'iteraciones': lista de diccionarios por iteración
      - 'convergio' (bool)
      - 'conteo_iter' (int)
      - 'raiz' (float)
      - 'estimacion_error' (float)
      - 'f_en_raiz' (float)

    Lanza ErrorBiseccion en caso de parámetros inválidos o errores de evaluación.
    """
    # Validaciones básicas
    if tol <= 0:
        raise ErrorBiseccion("La tolerancia debe ser un número positivo.")
    if maxit <= 0:
        raise ErrorBiseccion("El número máximo de iteraciones debe ser mayor que 0.")
    if a >= b:
        raise ErrorBiseccion("Se requiere a < b como intervalo inicial.")

    evaluar = _crear_evaluador(texto_funcion)

    fa = evaluar(a)
    fb = evaluar(b)

    # Si la función se anula exactamente en los extremos, devolvemos la raíz
    if fa == 0.0:
        return {'iteraciones': [], 'convergio': True, 'conteo_iter': 0, 'raiz': float(a), 'estimacion_error': 0.0, 'f_en_raiz': 0.0}
    if fb == 0.0:
        return {'iteraciones': [], 'convergio': True, 'conteo_iter': 0, 'raiz': float(b), 'estimacion_error': 0.0, 'f_en_raiz': 0.0}

    if fa * fb > 0:
        raise ErrorBiseccion("No hay cambio de signo en el intervalo [a,b]. f(a)·f(b) debe ser < 0.")

    iteraciones = []
    a_actual = float(a)
    b_actual = float(b)
    convergio = False
    c = None

    # Limitar el número máximo de iteraciones por seguridad
    maxit = min(maxit, 10000)

    # Evaluaciones iniciales
    fa = evaluar(a_actual)
    fb = evaluar(b_actual)

    for n in range(1, maxit + 1):
        # Punto medio
        c = (a_actual + b_actual) / 2.0
        fc = evaluar(c)

        # Registrar la iteración y decidir actualización
        if fc == 0.0 or abs(fc) < 1e-14:
            # Raíz exacta (o numéricamente cero)
            actualizacion = 'f(c) = 0'
            iteraciones.append({'i': n, 'a': a_actual, 'fa': fa, 'b': b_actual, 'fb': fb, 'c': c, 'fc': fc, 'actualizacion': actualizacion})
            convergio = True
            break

        # Si el signo de f(a) y f(c) es distinto, la raíz está en [a, c]
        if fa * fc < 0:
            actualizacion = 'b = c'
            iteraciones.append({'i': n, 'a': a_actual, 'fa': fa, 'b': b_actual, 'fb': fb, 'c': c, 'fc': fc, 'actualizacion': actualizacion})
            # acotamos el extremo derecho y actualizamos fb
            b_actual = c
            fb = fc
        else:
            actualizacion = 'a = c'
            iteraciones.append({'i': n, 'a': a_actual, 'fa': fa, 'b': b_actual, 'fb': fb, 'c': c, 'fc': fc, 'actualizacion': actualizacion})
            # acotamos el extremo izquierdo y actualizamos fa
            a_actual = c
            fa = fc

        # Criterio de parada: intervalo suficientemente pequeño o f(c) pequeño
        if abs(b_actual - a_actual) / 2.0 < tol or abs(fc) < tol:
            convergio = True
            break

    if c is None:
        raise ErrorBiseccion('No se pudo calcular una aproximación.')

    raiz_final = float(c)
    intervalo_final = abs(b_actual - a_actual)
    return {
        'iteraciones': iteraciones,
        'convergio': convergio,
        'conteo_iter': iteraciones[-1]['i'] if iteraciones else 0,
        'raiz': raiz_final,
        'estimacion_error': intervalo_final / 2.0,
        'f_en_raiz': evaluar(raiz_final)
    }
