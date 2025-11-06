"""Métodos numéricos - implementaciones de algoritmos.

Por ahora incluye el Método de bisección con validaciones y un evaluador
seguro limitado a funciones del módulo math y operaciones básicas.
"""
from typing import Any, Dict, List
import math

class BisectionError(ValueError):
    pass

def _make_eval(func_txt: str):
    if not func_txt or not func_txt.strip():
        raise BisectionError("La expresión de la función está vacía.")
    # Precompile expression
    try:
        code = compile(func_txt, '<bisection>', 'eval')
    except Exception as e:
        raise BisectionError(f"Expresión inválida: {e}")

    safe_names = {k: getattr(math, k) for k in dir(math) if not k.startswith('__')}
    safe_names.update({'abs': abs, 'pow': pow})

    def f(x: float) -> float:
        try:
            local = {'x': x}
            return float(eval(code, {'__builtins__': None}, {**safe_names, **local}))
        except Exception as e:
            raise BisectionError(f"Error evaluando la función en x={x}: {e}")

    return f


def biseccion(func_txt: str, a: float, b: float, tol: float = 1e-6, maxit: int = 100) -> Dict[str, Any]:
    """Ejecuta el método de la bisección sobre f definida por func_txt en [a,b].

    Retorna un diccionario con claves:
      - iterations: lista de filas {n,a,fa,b,fb,c,fc,update}
      - converged (bool), iter_count (int), root (float), error_estimate (float), froot (float)

    Lanza BisectionError en caso de parámetros inválidos o errores al evaluar f.
    """
    # Validaciones básicas
    if tol <= 0:
        raise BisectionError("La tolerancia debe ser un número positivo.")
    if maxit <= 0:
        raise BisectionError("El número máximo de iteraciones debe ser mayor que 0.")
    if a >= b:
        raise BisectionError("Se requiere a < b como intervalo inicial.")

    f = _make_eval(func_txt)

    fa = f(a)
    fb = f(b)
    # Raíz exacta en extremos
    if fa == 0.0:
        return { 'iterations': [], 'converged': True, 'iter_count': 0, 'root': float(a), 'error_estimate': 0.0, 'froot': 0.0 }
    if fb == 0.0:
        return { 'iterations': [], 'converged': True, 'iter_count': 0, 'root': float(b), 'error_estimate': 0.0, 'froot': 0.0 }

    if fa * fb > 0:
        raise BisectionError("No hay cambio de signo en el intervalo [a,b]. f(a)·f(b) debe ser < 0.")

    iterations: List[Dict[str, Any]] = []
    curr_a = float(a)
    curr_b = float(b)
    converged = False
    c = None

    # Cap iterations to reasonable safety limit
    maxit = min(maxit, 10000)

    for n in range(1, maxit + 1):
        c = (curr_a + curr_b) / 2.0
        fa = f(curr_a)
        fb = f(curr_b)
        fc = f(c)

        if fc == 0.0:
            update = 'f(c) = 0'
            iterations.append({'n': n, 'a': curr_a, 'fa': fa, 'b': curr_b, 'fb': fb, 'c': c, 'fc': fc, 'update': update})
            converged = True
            break

        if fa * fc < 0:
            update = 'b = c'
            iterations.append({'n': n, 'a': curr_a, 'fa': fa, 'b': curr_b, 'fb': fb, 'c': c, 'fc': fc, 'update': update})
            curr_b = c
        else:
            update = 'a = c'
            iterations.append({'n': n, 'a': curr_a, 'fa': fa, 'b': curr_b, 'fb': fb, 'c': c, 'fc': fc, 'update': update})
            curr_a = c

        if abs(curr_b - curr_a) < tol:
            converged = True
            break

    if c is None:
        raise BisectionError('No se pudo calcular una aproximación.')

    final_root = float(c)
    final_interval = abs(curr_b - curr_a)
    return {
        'iterations': iterations,
        'converged': converged,
        'iter_count': iterations[-1]['n'] if iterations else 0,
        'root': final_root,
        'error_estimate': final_interval / 2.0,
        'froot': f(final_root)
    }
