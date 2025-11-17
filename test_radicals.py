"""Quick verification of nth-root and nested radical expressions using _crear_evaluador.
Run: python test_radicals.py
"""
from algebra.logic.metodos import _crear_evaluador, ErrorBiseccion

# Expressions emulating frontend normalization (LaTeX \sqrt[n]{x} -> (x)^(1/(n)))
expressions = {
    "cube_root": "(x)^(1/(3))",
    "fifth_root_poly": "(x**2+1)^(1/(5))",
    "cube_root_squared": "((x)^(1/(3)))**2",  # (x^(1/3))^2
    "nested_roots": "(((x)^(1/(3)))**(1/(4)))**(1/(5))",  # successive roots
    "fraction_of_roots": "((x)^(1/(3)))/((x**2+1)^(1/(5)))",
    "root_power_chain": "((x**2+3*x+1)^(1/(3)))**(5)",  # (cube root)^5
    "root_in_exponent": "(x)^( (x)^(1/(3)) )",  # x^(x^(1/3)) stress test
}

sample_x = [0.125, 1.0, 8.0, 10.0]

print("Radical / nested power evaluation tests:\n")
for name, expr in expressions.items():
    try:
        f = _crear_evaluador(expr)
    except ErrorBiseccion as e:
        print(f"[INIT FAIL] {name}: {e}")
        continue
    rows = []
    for xv in sample_x:
        try:
            val = f(xv)
            rows.append((xv, val))
        except ErrorBiseccion as e:
            rows.append((xv, f"Error: {e}"))
        except Exception as e:
            rows.append((xv, f"Exception: {e}"))
    print(f"{name}: {expr}")
    for xv, out in rows:
        print(f"  x={xv:<6} -> {out}")
    print()

print("Done.")
