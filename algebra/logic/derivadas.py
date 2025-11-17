"""Herramientas para derivar funciones ingresadas por el usuario.

Este módulo usa sympy para:
- Normalizar texto de funciones (alias comunes, '^' -> '**', etc.)
- Parsear de forma robusta expresiones f(x)
- Calcular derivadas de orden n simbólicamente
- Exponer evaluadores numéricos de f(x) y f^{(n)}(x) vía math

API principal
------------
- derivar_funcion(texto_funcion: str, orden: int = 1, simplificar: bool = True) -> dict
    Calcula la derivada de orden `orden` de la expresión dada. Retorna:
      {
        'original': {'expr': expr, 'texto': str(expr), 'latex': latex(expr), 'evaluador': callable},
        'derivada': {'expr': d, 'texto': str(d), 'latex': latex(d), 'evaluador': callable},
        'orden': orden
      }

- derivar_n(texto_funcion: str, n: int) -> dict
    Atajo para derivar_funcion(texto_funcion, orden=n)

- crear_evaluador(texto_funcion: str) -> Callable[[float], float]
    Retorna un evaluador numérico para f(x) (sin derivar).

Notas
-----
- Acepta alias: ln->log, sen->sin, tg->tan, ctg->cot, lg->log10, e->E, pi->pi
- Si el usuario introduce una ecuación lhs = rhs, se normaliza como (lhs)-(rhs)
- Requiere sympy instalado (está listado en requirements.txt)
"""
from __future__ import annotations

import math
from typing import Callable, Dict, Any

class ErrorDerivada(ValueError):
    """Excepción para errores de parseo/derivación/evaluación."""
    pass

# ------------------- Normalización de texto -------------------

def _normalizar_texto_funcion(s: str) -> str:
    if s is None:
        return ''
    txt = str(s)
    txt = txt.replace('^', '**')
    # Curly a paréntesis y quitar backslashes (ej: LaTeX)
    txt = txt.replace('{', '(').replace('}', ')')
    txt = txt.replace('\\', '')
    # Signos unicode comunes
    txt = txt.replace('\u2212', '-')  # minus sign
    # MathLive: constante de Euler
    txt = txt.replace('exponentialE', 'E')
    # Aliases en español y comunes
    # ecuaciones: a=b -> (a)-(b)
    if '=' in txt:
        try:
            left, right = txt.split('=', 1)
            left = (left or '0').strip()
            right = (right or '0').strip()
            txt = f'({left})-({right})'
        except Exception:
            # dejar como está; sympy fallará luego con mensaje claro
            pass
    return txt

# ------------------- Parseo y SymPy -------------------

def _parse_sympy_expr(texto: str):
    try:
        import sympy as sp
    except Exception as e:
        raise ErrorDerivada(f"Sympy no disponible para derivar: {e}")

    # Normalizar y mapear alias a funciones/constantes de sympy
    t = _normalizar_texto_funcion(texto)
    x = sp.symbols('x')
    sym_locals = {
        # alias funciones
        'ln': sp.log,
        'sen': sp.sin,   # español -> sin
        'tg': sp.tan,    # español -> tan
        'ctg': sp.cot,   # español -> cot
        'sqrt': sp.sqrt,
        'abs': sp.Abs,
        'exp': sp.exp,
        # logaritmos base 10 y 2 (SymPy no siempre expone sp.log10/sp.log2 según versión)
        'lg': (lambda z: sp.log(z, 10)),
        'log10': (lambda z: sp.log(z, 10)),
        'log2': (lambda z: sp.log(z, 2)),
        # alias constantes
        'e': sp.E,
        'E': sp.E,
        'pi': sp.pi,
    }

    try:
        expr = sp.sympify(t, locals=sym_locals, evaluate=True)
    except Exception as e:
        raise ErrorDerivada(f"Expresión inválida: {e}")

    # Reescritura para potencias racionales con denominador impar como raíces reales con signo.
    # x**(p/q), q impar -> (sign(x) * Abs(x)**(1/q))**p
    # Esto permite evaluar en bases negativas manteniendo resultados reales para q impar
    def _rewrite_real_rational_powers(e):
        def cond(node):
            return isinstance(node, sp.Pow) and isinstance(node.exp, sp.Rational)
        def repl(node):
            p = int(node.exp.p)
            q = int(node.exp.q)
            if q % 2 == 1:
                inner = sp.sign(node.base) * sp.Abs(node.base)**sp.Rational(1, q)
                return inner if p == 1 else inner**p
            return node
        return e.replace(cond, repl)

    try:
        expr = _rewrite_real_rational_powers(expr)
    except Exception:
        # Si la reescritura falla, continuar con la expresión original
        pass

    # Asegurar que la variable independiente 'x' aparezca o que sea una constante
    # Si no hay x, sympy trata expr como constante; permitimos derivadas (dan 0)
    return x, expr

# ------------------- API pública -------------------

def crear_evaluador(texto_funcion: str) -> Callable[[float], float]:
    """Devuelve un evaluador numérico para f(x). Usa math como backend."""
    try:
        import sympy as sp
    except Exception as e:
        raise ErrorDerivada(f"Sympy no disponible: {e}")
    x, expr = _parse_sympy_expr(texto_funcion)
    try:
        fnum = sp.lambdify(x, expr, modules=['math'])
    except Exception:
        def fnum(_x):
            try:
                return float(expr.evalf(subs={x: _x}))
            except Exception as e2:
                raise ErrorDerivada(f"Error evaluando f(x) en x={_x}: {e2}")
    def evaluar(val: float) -> float:
        try:
            v = fnum(val)
            if v is None:
                raise ErrorDerivada(f"Evaluación devolvió None en x={val}")
            if hasattr(v, '__len__') and not isinstance(v, (str, bytes)):
                raise ErrorDerivada(f"Evaluación devolvió objeto no escalar en x={val}")
            return float(v)
        except ErrorDerivada:
            raise
        except Exception as e:
            raise ErrorDerivada(f"Error evaluando f(x) en x={val}: {e}")
    return evaluar


def derivar_funcion(texto_funcion: str, orden: int = 1, simplificar: bool = True) -> Dict[str, Any]:
    """Calcula la derivada de orden `orden` de la función ingresada.

    Retorna un diccionario con:
      - 'original': { 'expr', 'texto', 'latex', 'evaluador' }
      - 'derivada': { 'expr', 'texto', 'latex', 'evaluador' }
      - 'orden': int
    """
    if orden is None or orden < 0:
        raise ErrorDerivada("El orden de la derivada debe ser un entero no negativo.")

    try:
        import sympy as sp
    except Exception as e:
        raise ErrorDerivada(f"Sympy no disponible: {e}")

    x, expr = _parse_sympy_expr(texto_funcion)

    # Derivar n veces
    try:
        d = sp.diff(expr, x, orden)
    except Exception as e:
        raise ErrorDerivada(f"No se pudo derivar la expresión: {e}")

    if simplificar:
        try:
            d = sp.simplify(d)
        except Exception:
            # Si falla, continuar con d sin simplificar
            pass

    # Representaciones de texto y LaTeX
    try:
        texto_expr = sp.sstr(expr)
    except Exception:
        texto_expr = str(expr)
    try:
        texto_der = sp.sstr(d)
    except Exception:
        texto_der = str(d)

    try:
        latex_expr = sp.latex(expr)
    except Exception:
        latex_expr = str(expr)
    try:
        latex_der = sp.latex(d)
    except Exception:
        latex_der = str(d)

    # Evaluadores numéricos
    try:
        f_eval = sp.lambdify(
            x,
            expr,
            modules=[
                {
                    'sign': (lambda v: (-1 if v < 0 else (1 if v > 0 else 0))),
                    'Abs': abs,
                },
                'math'
            ]
        )
    except Exception:
        def f_eval(_x):
            return float(expr.evalf(subs={x: _x}))

    try:
        df_eval = sp.lambdify(
            x,
            d,
            modules=[
                {
                    'sign': (lambda v: (-1 if v < 0 else (1 if v > 0 else 0))),
                    'Abs': abs,
                },
                'math'
            ]
        )
    except Exception:
        def df_eval(_x):
            return float(d.evalf(subs={x: _x}))

    def _wrap(fn, label):
        def inner(val: float) -> float:
            try:
                v = fn(val)
                if v is None:
                    raise ErrorDerivada(f"{label} devolvió None en x={val}")
                if hasattr(v, '__len__') and not isinstance(v, (str, bytes)):
                    raise ErrorDerivada(f"{label} devolvió objeto no escalar en x={val}")
                return float(v)
            except ErrorDerivada:
                raise
            except Exception as e:
                raise ErrorDerivada(f"Error evaluando {label} en x={val}: {e}")
        return inner

    return {
        'orden': int(orden),
        'original': {
            'expr': expr,
            'texto': texto_expr,
            'latex': latex_expr,
            'evaluador': _wrap(f_eval, 'f(x)')
        },
        'derivada': {
            'expr': d,
            'texto': texto_der,
            'latex': latex_der,
            'evaluador': _wrap(df_eval, "f'(x)")
        }
    }


def derivar_n(texto_funcion: str, n: int) -> Dict[str, Any]:
    """Atajo para derivar la n-ésima derivada."""
    return derivar_funcion(texto_funcion, orden=int(n), simplificar=True)
