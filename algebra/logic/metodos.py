"""Módulo de métodos numéricos (versión en español).

Descripción:
- Aquí se implementa el Método de la bisección. El código usa nombres y
  comentarios en español. Para evaluar expresiones ingresadas por el
  usuario se emplea un evaluador controlado (limitado) que sólo expone
  funciones del módulo math y un pequeño conjunto de funciones seguras.

Importaciones:
- math: proporciona funciones matemáticas (sin, cos, exp, log, etc.) y
  constantes (pi, e). Se usa para permitir que el usuario escriba
  expresiones usando esas funciones.

Nota de seguridad:
- El evaluador usa eval() en un entorno muy restringido. Para producción
  se recomienda reemplazarlo por un parser seguro (por ejemplo sympy).
"""
import math


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

    # Compilar la expresión una vez para mejorar rendimiento y detectar
    # errores de sintaxis tempranamente.
    try:
        codigo = compile(texto_funcion, '<biseccion>', 'eval')
    except Exception as e:
        raise ErrorBiseccion(f"Expresión inválida: {e}")

    # Exponer sólo las funciones y constantes del módulo math y un par de
    # funciones seguras adicionales.
    nombres_permitidos = {k: getattr(math, k) for k in dir(math) if not k.startswith('__')}
    nombres_permitidos.update({'abs': abs, 'pow': pow})

    def evaluar(x):
        """Evalúa la expresión compilada en el punto x y devuelve un float.

        Envuelve errores de evaluación en ErrorBiseccion para un manejo
        uniforme en la capa de vista.
        """
        try:
            contexto_local = {'x': x}
            # Evaluar con __builtins__ deshabilitado y sólo los nombres
            # permitidos en el globals/local.
            return float(eval(codigo, {'__builtins__': None}, {**nombres_permitidos, **contexto_local}))
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

    for n in range(1, maxit + 1):
        c = (a_actual + b_actual) / 2.0
        fa = evaluar(a_actual)
        fb = evaluar(b_actual)
        fc = evaluar(c)

        if fc == 0.0:
            actualizacion = 'f(c) = 0'
            iteraciones.append({'n': n, 'a': a_actual, 'fa': fa, 'b': b_actual, 'fb': fb, 'c': c, 'fc': fc, 'actualizacion': actualizacion})
            convergio = True
            break

        if fa * fc < 0:
            actualizacion = 'b = c'
            iteraciones.append({'n': n, 'a': a_actual, 'fa': fa, 'b': b_actual, 'fb': fb, 'c': c, 'fc': fc, 'actualizacion': actualizacion})
            b_actual = c
        else:
            actualizacion = 'a = c'
            iteraciones.append({'n': n, 'a': a_actual, 'fa': fa, 'b': b_actual, 'fb': fb, 'c': c, 'fc': fc, 'actualizacion': actualizacion})
            a_actual = c

        if abs(b_actual - a_actual) < tol:
            convergio = True
            break

    if c is None:
        raise ErrorBiseccion('No se pudo calcular una aproximación.')

    raiz_final = float(c)
    intervalo_final = abs(b_actual - a_actual)
    return {
        'iteraciones': iteraciones,
        'convergio': convergio,
        'conteo_iter': iteraciones[-1]['n'] if iteraciones else 0,
        'raiz': raiz_final,
        'estimacion_error': intervalo_final / 2.0,
        'f_en_raiz': evaluar(raiz_final)
    }
