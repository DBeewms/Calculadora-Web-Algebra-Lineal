import sys
import operaciones
import menu
import gui


def ejecutar():
    print("Seleccione operación:")
    print("  1) Eliminación de Gauss (forma escalonada)")
    print("  2) Gauss-Jordan (forma escalonada reducida por filas)")
    print("  3) Suma de matrices (A + B)")
    print("  4) Multiplicación de matrices (A · B)")
    opcion = input("Opción (1/2/3/4): ").strip()
    if opcion == "3":
        A = menu.leer_matriz_simple(nombre="A")
        B = menu.leer_matriz_simple(nombre="B")
        try:
            C = operaciones.sumar_matrices(A, B)
        except ValueError as ex:
            print("Error:", str(ex))
            return
        print("\nResultado de A + B:")
        menu.imprimir_matriz(C)
        return
    if opcion == "4":
        print("\nNota: Para multiplicar A (m×p) por B (p×n), las columnas de A deben coincidir con las filas de B.")
        A = menu.leer_matriz_simple(nombre="A")
        B = menu.leer_matriz_simple(nombre="B")
        try:
            C, pasos = operaciones.multiplicar_matrices(A, B)
        except ValueError as ex:
            print("Error:", str(ex))
            return
        print("\nResultado de A · B:")
        menu.imprimir_matriz(C)
        # Mostrar pasos como combinación lineal
        ver = input("Mostrar pasos del procedimiento? (s/n): ").strip().lower()
        if ver == "s":
            menu.mostrar_pasos(pasos)
        return
    # Caso sistemas lineales
    M = menu.leer_matriz_aumentada()
    if opcion == "1":
        R, pivotes, pasos = operaciones.eliminacion_gauss(M)
        respuesta = operaciones.analizar_solucion_gauss(R, pivotes)
    else:
        R, pivotes, pasos = operaciones.gauss_jordan(M)
        respuesta = operaciones.analizar_solucion(R, pivotes)
    ver = input("Mostrar pasos del procedimiento? (s/n): ").strip().lower()
    if ver == "s":
        menu.mostrar_pasos(pasos)
    menu.mostrar_resultado(R, respuesta)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() in {"cli", "-c", "--cli"}:
        ejecutar()
    else:
        gui.run_gui()
