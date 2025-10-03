import tkinter as tk
from tkinter import ttk, messagebox
import operaciones
import utilidades as u

# Paleta definida en el requerimiento
COLOR_PRIMARIO_PRESSED = "#6A1B9A"
COLOR_PRIMARIO_BASE = "#7E57C2"
COLOR_PRIMARIO_HOVER = "#3949AB"
COLOR_ACTIVO = "#5C6BC0"
COLOR_SUAVE = "#7BBBC4"
COLOR_FONDO = "#FFFFFF"
COLOR_PANEL = "#F7F7FB"
COLOR_BORDES = "#E3E5F0"
COLOR_TEXTO = "#1F2233"
COLOR_TEXTO_SEC = "#5A6079"


def crear_estilo():
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    fuente_base = ("Segoe UI", 10)
    style.configure("TFrame", background=COLOR_PANEL)
    style.configure("TLabel", background=COLOR_PANEL, foreground=COLOR_TEXTO, font=fuente_base)
    style.configure("Secondary.TLabel", foreground=COLOR_TEXTO_SEC, background=COLOR_PANEL, font=("Segoe UI", 9))
    style.configure("Title.TLabel", font=("Segoe UI", 12, "bold"), foreground=COLOR_PRIMARIO_BASE, background=COLOR_PANEL)

    # Estilos tipo "card" (fondos blancos) para contenedores
    style.configure("Card.TFrame", background=COLOR_FONDO)
    style.configure("Card.TLabelframe", background=COLOR_FONDO, borderwidth=1, relief="solid")
    style.configure("Card.TLabelframe.Label", background=COLOR_FONDO, foreground=COLOR_TEXTO_SEC)

    style.configure("Primary.TButton",
                    background=COLOR_PRIMARIO_BASE,
                    foreground="#FFFFFF",
                    font=fuente_base,
                    padding=(12, 8),
                    borderwidth=0)
    style.map("Primary.TButton",
              background=[("active", COLOR_PRIMARIO_HOVER), ("pressed", COLOR_PRIMARIO_PRESSED)],
              relief=[("pressed", "sunken"), ("!pressed", "flat")])

    style.configure("TButton", padding=(10, 7), font=fuente_base)

    # Entry / Combobox
    style.configure("TEntry", fieldbackground=COLOR_FONDO, background=COLOR_FONDO, foreground=COLOR_TEXTO)
    style.configure("TCombobox", fieldbackground=COLOR_FONDO, background=COLOR_FONDO, foreground=COLOR_TEXTO)

    # Notebook
    style.configure("TNotebook", background=COLOR_PANEL, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(16, 8), font=fuente_base)
    style.map("TNotebook.Tab", background=[("selected", COLOR_FONDO)], foreground=[("selected", COLOR_PRIMARIO_BASE)])

    return style


def matriz_a_texto(M):
    """Devuelve representación alineada de la matriz aumentada usando utilidades."""
    if not M:
        return "[ ]"
    filas = len(M)
    cols_total = len(M[0])
    cols_A = cols_total - 1
    anchos = []
    for c in range(cols_total):
        max_len = 0
        for f in range(filas):
            t = u.texto_fraccion(M[f][c])
            if len(t) > max_len:
                max_len = len(t)
        anchos.append(max_len)
    lineas = []
    for f in range(filas):
        izquierda = []
        for c in range(cols_A):
            txt = u.texto_fraccion(M[f][c])
            izquierda.append(txt.rjust(anchos[c]))
        txt_b = u.texto_fraccion(M[f][cols_A]).rjust(anchos[cols_A])
        lineas.append("[ " + "  ".join(izquierda) + " | " + txt_b + " ]")
    return "\n".join(lineas)


class AlgebraLinealApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora Álgebra Lineal")
        self.configure(bg=COLOR_PANEL)
        self.minsize(980, 640)
        crear_estilo()
        self._construir_ui()

    # UI
    def _construir_ui(self):
        cont = ttk.Frame(self, padding=10)
        cont.pack(fill="both", expand=True)

        header = ttk.Frame(cont)
        header.pack(fill="x")
        ttk.Label(header, text="Resolución de Sistemas Lineales", style="Title.TLabel").pack(side="left")

        # Barra de controles (en un contenedor card para resaltar)
        barra = ttk.Frame(cont, style="Card.TFrame", padding=10)
        barra.pack(fill="x", pady=(10, 12))
        form = ttk.Frame(barra, style="Card.TFrame")
        form.pack(fill="x")

        # Método
        ttk.Label(form, text="Operación:").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        self.metodo_var = tk.StringVar(value="Gauss-Jordan (forma escalonada reducida por filas)")
        self.combo_metodo = ttk.Combobox(form, textvariable=self.metodo_var, state="readonly", width=42,
                                         values=[
                                             "Eliminación de Gauss (forma escalonada)",
                                             "Gauss-Jordan (forma escalonada reducida por filas)",
                                             "Suma de matrices (A + B)",
                                             "Multiplicación de matrices (A · B)"
                                         ])
        self.combo_metodo.grid(row=0, column=1, sticky="w", pady=2)
        self.combo_metodo.bind("<<ComboboxSelected>>", lambda e: self._cambio_metodo())

        # Dimensiones
        self.label_m = ttk.Label(form, text="Ecuaciones (m):")
        self.label_m.grid(row=1, column=0, sticky="w", padx=(0, 6), pady=2)
        self.m_var = tk.StringVar(value="3")
        self.e_m = ttk.Entry(form, width=8, textvariable=self.m_var)
        self.e_m.grid(row=1, column=1, sticky="w", pady=2)

        self.label_n = ttk.Label(form, text="Incógnitas (n):")
        self.label_n.grid(row=1, column=2, sticky="w", padx=(18, 6), pady=2)
        self.n_var = tk.StringVar(value="3")
        self.e_n = ttk.Entry(form, width=8, textvariable=self.n_var)
        self.e_n.grid(row=1, column=3, sticky="w", pady=2)

        # Dimensión intermedia p (solo multiplicación)
        self.label_p = ttk.Label(form, text="Columnas de A = Filas de B (p):")
        self.p_var = tk.StringVar(value="3")
        self.e_p = ttk.Entry(form, width=8, textvariable=self.p_var)
        # Se posiciona y muestra solo cuando aplica

        self.btn_generar = ttk.Button(form, text="Generar matriz", style="Primary.TButton", command=self.generar_matriz)
        self.btn_generar.grid(row=0, column=2, sticky="w", padx=(0, 6))

        self.btn_limpiar = ttk.Button(form, text="Limpiar", style="Primary.TButton", command=self.limpiar_matriz_valores)
        self.btn_limpiar.grid(row=0, column=3, sticky="w", padx=(0, 0))

        self.mostrar_pasos_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(form, text="Mostrar pasos", variable=self.mostrar_pasos_var).grid(row=0, column=4, padx=(25, 0))

        # Botón resolver integrado a la derecha
        self.btn_resolver = ttk.Button(form, text="Resolver", style="Primary.TButton", command=self.resolver)
        self.btn_resolver.grid(row=0, column=5, sticky="e")

        # Empujar 'Resolver' a la derecha
        form.columnconfigure(4, weight=0)
        form.columnconfigure(5, weight=1)

        # Separador visual entre controles y matrices
        ttk.Separator(cont, orient="horizontal").pack(fill="x", pady=(4, 10))

        # Hint de ayuda
        ttk.Label(cont, text="Formato: enteros, fracciones a/b o decimales.", style="Secondary.TLabel").pack(anchor="w", padx=2)

        # Contenedores de matrices (encima de las pestañas)
        self.contenedor_matriz_unica = ttk.LabelFrame(cont, text="Matriz aumentada [A|b]", padding=12, style="Card.TLabelframe")
        self.contenedor_matriz_unica.pack(fill="x", pady=(8, 6))
        self.matriz_frame = ttk.Frame(self.contenedor_matriz_unica)
        self.matriz_frame.pack(fill="x")

        self.contenedor_dos_matrices = ttk.Frame(cont, style="Card.TFrame")
        # LabelFrames para A y B
        self.frame_A_outer = ttk.LabelFrame(self.contenedor_dos_matrices, text="Matriz A", padding=12, style="Card.TLabelframe")
        self.frame_B_outer = ttk.LabelFrame(self.contenedor_dos_matrices, text="Matriz B", padding=12, style="Card.TLabelframe")
        self.frame_A_outer.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.frame_B_outer.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.matrizA_frame = ttk.Frame(self.frame_A_outer)
        self.matrizB_frame = ttk.Frame(self.frame_B_outer)
        self.matrizA_frame.pack(fill="x")
        self.matrizB_frame.pack(fill="x")

        # Separador entre matrices y resultados
        ttk.Separator(cont, orient="horizontal").pack(fill="x", pady=(10, 8))

        # Notebook resultados (debajo de las matrices), en contenedor "card"
        nb_frame = ttk.Frame(cont, style="Card.TFrame", padding=6)
        nb_frame.pack(fill="both", expand=True, pady=(0,0))
        notebook = ttk.Notebook(nb_frame)
        notebook.pack(fill="both", expand=True)
        self.tab_resultado = ttk.Frame(notebook)
        self.tab_pasos = ttk.Frame(notebook)
        notebook.add(self.tab_resultado, text="Resultado")
        notebook.add(self.tab_pasos, text="Pasos")

        # Resultado
        self.text_resultado = tk.Text(self.tab_resultado, wrap="word", height=18, font=("Consolas", 10), background=COLOR_FONDO, borderwidth=0, relief="flat")
        self.text_resultado.pack(fill="both", expand=True, padx=6, pady=6)
        try:
            self.text_resultado.configure(highlightthickness=1, highlightbackground=COLOR_BORDES)
        except Exception:
            pass

        # Pasos
        self.text_pasos = tk.Text(self.tab_pasos, wrap="none", font=("Consolas", 10), background=COLOR_FONDO, borderwidth=0, relief="flat")
        sx = ttk.Scrollbar(self.tab_pasos, orient="horizontal", command=self.text_pasos.xview)
        sy = ttk.Scrollbar(self.tab_pasos, orient="vertical", command=self.text_pasos.yview)
        self.text_pasos.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
        self.text_pasos.grid(row=0, column=0, sticky="nsew", padx=(6,0), pady=6)
        sy.grid(row=0, column=1, sticky="ns", pady=6)
        sx.grid(row=1, column=0, sticky="ew", padx=(6,0))
        self.tab_pasos.rowconfigure(0, weight=1)
        self.tab_pasos.columnconfigure(0, weight=1)
        try:
            self.text_pasos.configure(highlightthickness=1, highlightbackground=COLOR_BORDES)
        except Exception:
            pass

        # Inicial
        self.entries = []          # para [A|b]
        self.entries_A = []        # para suma: A
        self.entries_B = []        # para suma: B
        self.generar_matriz()

    # Lógica GUI

    def limpiar_matriz(self):
        for fila in self.entries:
            for e in fila:
                e.destroy()
        self.entries = []
        for fila in self.entries_A:
            for e in fila:
                e.destroy()
        self.entries_A = []
        for fila in self.entries_B:
            for e in fila:
                e.destroy()
        self.entries_B = []

    def limpiar_matriz_valores(self):
        if self.metodo_var.get().startswith("Suma"):
            for fila in self.entries_A:
                for e in fila:
                    e.delete(0, "end"); e.insert(0, "0")
            for fila in self.entries_B:
                for e in fila:
                    e.delete(0, "end"); e.insert(0, "0")
        else:
            for fila in self.entries:
                for e in fila:
                    e.delete(0, "end"); e.insert(0, "0")

    def _cambio_metodo(self):
        # Cambiar visibilidad de contenedores según operación
        if self.metodo_var.get().startswith("Suma"):
            # Mostrar dos matrices, ocultar aumentada
            self.contenedor_matriz_unica.pack_forget()
            self.contenedor_dos_matrices.pack(fill="x")
            self.label_m.configure(text="Filas (m):")
            self.label_n.configure(text="Columnas (n):")
            # ocultar p si estuviera
            self.label_p.grid_forget(); self.e_p.grid_forget()
        else:
            self.contenedor_dos_matrices.pack_forget()
            self.contenedor_matriz_unica.pack(fill="x")
            self.label_m.configure(text="Ecuaciones (m):")
            self.label_n.configure(text="Incógnitas (n):")
            # ocultar p si estuviera
            self.label_p.grid_forget(); self.e_p.grid_forget()
        # Multiplicación
        if self.metodo_var.get().startswith("Multiplicación"):
            self.contenedor_matriz_unica.pack_forget()
            self.contenedor_dos_matrices.pack(fill="x")
            self.label_m.configure(text="Filas de A (m):")
            self.label_n.configure(text="Columnas de B (n):")
            # mostrar p
            self.label_p.grid(row=2, column=0, sticky="w", padx=(0, 6), pady=2)
            self.e_p.grid(row=2, column=1, sticky="w", pady=2)
        # No generar matriz aquí para evitar bucles; el usuario puede presionar "Generar matriz".

    def generar_matriz(self):
        try:
            m = int(self.m_var.get())
            n = int(self.n_var.get())
            if m <= 0 or n <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "m y n deben ser enteros positivos.")
            return
        self.limpiar_matriz()
        if self.metodo_var.get().startswith("Suma"):
            # construir dos matrices m x n
            for i in range(m):
                fila_A = []
                fila_B = []
                for j in range(n):
                    eA = ttk.Entry(self.matrizA_frame, width=8, font=("Segoe UI", 10))
                    eA.grid(row=i, column=j, padx=6, pady=6)
                    eA.insert(0, "0")
                    fila_A.append(eA)
                    eB = ttk.Entry(self.matrizB_frame, width=8, font=("Segoe UI", 10))
                    eB.grid(row=i, column=j, padx=6, pady=6)
                    eB.insert(0, "0")
                    fila_B.append(eB)
                self.entries_A.append(fila_A)
                self.entries_B.append(fila_B)
            # asegurar visibilidad adecuada (no forzar regeneración recursiva)
            if not self.contenedor_dos_matrices.winfo_ismapped():
                self.contenedor_matriz_unica.pack_forget()
                self.contenedor_dos_matrices.pack(fill="x")
        elif self.metodo_var.get().startswith("Multiplicación"):
            # construir A (m×p) y B (p×n)
            try:
                p = int(self.p_var.get())
                if p <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "p debe ser un entero positivo.")
                return
            for i in range(m):
                fila_A = []
                for j in range(p):
                    eA = ttk.Entry(self.matrizA_frame, width=8, font=("Segoe UI", 10))
                    eA.grid(row=i, column=j, padx=6, pady=6)
                    eA.insert(0, "0")
                    fila_A.append(eA)
                self.entries_A.append(fila_A)
            for i in range(p):
                fila_B = []
                for j in range(n):
                    eB = ttk.Entry(self.matrizB_frame, width=8, font=("Segoe UI", 10))
                    eB.grid(row=i, column=j, padx=6, pady=6)
                    eB.insert(0, "0")
                    fila_B.append(eB)
                self.entries_B.append(fila_B)
            if not self.contenedor_dos_matrices.winfo_ismapped():
                self.contenedor_matriz_unica.pack_forget()
                self.contenedor_dos_matrices.pack(fill="x")
        else:
            for i in range(m):
                fila_entries = []
                for j in range(n + 1):
                    e = ttk.Entry(self.matriz_frame, width=8, font=("Segoe UI", 10))
                    e.grid(row=i, column=j, padx=6, pady=6)
                    e.insert(0, "0")
                    fila_entries.append(e)
                self.entries.append(fila_entries)

    def _leer_matriz_desde_entries(self):
        M = []
        for fila_entries in self.entries:
            fila = []
            for e in fila_entries:
                txt = e.get().strip()
                if txt == "":
                    txt = "0"
                try:
                    fr = u.crear_fraccion_desde_cadena(txt)
                except Exception:
                    raise ValueError(f"Valor inválido: '{txt}'")
                fila.append(fr)
            M.append(fila)
        return M

    def _leer_matriz_simple(self, entries_matriz):
        M = []
        for fila_entries in entries_matriz:
            fila = []
            for e in fila_entries:
                txt = e.get().strip() or "0"
                try:
                    fr = u.crear_fraccion_desde_cadena(txt)
                except Exception:
                    raise ValueError(f"Valor inválido: '{txt}'")
                fila.append(fr)
            M.append(fila)
        return M

    def resolver(self):
        try:
            if self.metodo_var.get().startswith("Suma"):
                A = self._leer_matriz_simple(self.entries_A)
                B = self._leer_matriz_simple(self.entries_B)
            elif self.metodo_var.get().startswith("Multiplicación"):
                A = self._leer_matriz_simple(self.entries_A)
                B = self._leer_matriz_simple(self.entries_B)
            else:
                M = self._leer_matriz_desde_entries()
        except ValueError as ex:
            messagebox.showerror("Error de datos", str(ex))
            return
        metodo_texto = self.metodo_var.get()
        if metodo_texto.startswith("Suma"):
            try:
                C = operaciones.sumar_matrices(A, B)
            except ValueError as ex:
                messagebox.showerror("Error", str(ex)); return
            # Mostrar en resultados
            self.text_resultado.delete("1.0", tk.END)
            self.text_resultado.insert(tk.END, "Resultado de A + B:\n")
            self.text_resultado.insert(tk.END, matriz_simple_a_texto(C) + "\n")
            # Pasos no aplican
            self.text_pasos.delete("1.0", tk.END)
            self.text_pasos.insert(tk.END, "Esta operación no genera pasos intermedios.\n")
            return
        if metodo_texto.startswith("Multiplicación"):
            try:
                C, pasos = operaciones.multiplicar_matrices(A, B)
            except ValueError as ex:
                messagebox.showerror("Error", str(ex)); return
            self.text_resultado.delete("1.0", tk.END)
            self.text_resultado.insert(tk.END, "Resultado de A · B:\n")
            self.text_resultado.insert(tk.END, matriz_simple_a_texto(C) + "\n")
            # Mostrar pasos generados por la multiplicación
            self.text_pasos.delete("1.0", tk.END)
            if not pasos:
                self.text_pasos.insert(tk.END, "(No hay pasos intermedios).\n")
            else:
                for idx, paso in enumerate(pasos, start=1):
                    op = paso.get('operacion', '')
                    self.text_pasos.insert(tk.END, f"{idx:02d}) {op}\n")
                    mat = paso.get('matriz', [])
                    # Matriz simple
                    self.text_pasos.insert(tk.END, matriz_simple_a_texto(mat) + "\n")
                    self.text_pasos.insert(tk.END, "-" * 42 + "\n")
            return
        usar_gauss = metodo_texto.startswith("Eliminación")
        if usar_gauss:
            R, pivotes, pasos = operaciones.eliminacion_gauss(M)
            info = operaciones.analizar_solucion_gauss(R, pivotes)
        else:
            R, pivotes, pasos = operaciones.gauss_jordan(M)
            info = operaciones.analizar_solucion(R, pivotes)
        self.mostrar_resultado(R, info)
        if self.mostrar_pasos_var.get():
            self.mostrar_pasos(pasos)
        else:
            self.text_pasos.delete("1.0", tk.END)
            self.text_pasos.insert(tk.END, "(Pasos ocultos)\n")

    # Resultados
    def mostrar_resultado(self, R, info):
        self.text_resultado.delete("1.0", tk.END)
        tipo = info.get("tipo_forma", "")
        solucion = info.get("solucion", "")
        pivotes = info.get("pivotes", [])
        self.text_resultado.insert(tk.END, f"Tipo de solución: {solucion}\n")
        if solucion == "INCONSISTENTE":
            self.text_resultado.insert(tk.END, "Sistema inconsistente.\n\n")
        else:
            if tipo == "ESCALONADA_REDUCIDA" and solucion != "UNICA":
                # Mostrar variables en función de las libres (Gauss-Jordan)
                m = len(R)
                n = len(R[0]) - 1
                es_pivote = [False] * n
                for c in pivotes:
                    if 0 <= c < n:
                        es_pivote[c] = True
                libres = [j for j in range(n) if not es_pivote[j]]
                if libres:
                    vars_libres = ", ".join(f"x{j+1}" for j in libres)
                    self.text_resultado.insert(tk.END, f"Variables libres: {vars_libres}\n")
                if pivotes:
                    self.text_resultado.insert(tk.END, "Variables dependientes en función de las libres:\n")
                r = 0
                while r < m and r < len(pivotes):
                    c = pivotes[r]
                    b = R[r][n]
                    partes = [u.texto_fraccion(b)]
                    j = 0
                    while j < n:
                        if not es_pivote[j]:
                            coef = R[r][j]
                            if not u.es_cero(coef):
                                neg = u.negativo_fraccion(coef)
                                signo = "-" if neg[0] < 0 else "+"
                                abs_val = [-neg[0], neg[1]] if neg[0] < 0 else [neg[0], neg[1]]
                                coef_txt = u.texto_fraccion(abs_val)
                                partes.append(f" {signo} {coef_txt}·x{j+1}")
                        j += 1
                    self.text_resultado.insert(tk.END, f"x{c+1} = " + "".join(partes) + "\n")
                    r += 1
                self.text_resultado.insert(tk.END, "\n")
            else:
                sp = info.get("solucion_particular", [])
                if sp:
                    self.text_resultado.insert(tk.END, "Variables (fracción = decimal):\n")
                    for i, fr in enumerate(sp, start=1):
                        self.text_resultado.insert(tk.END, f"x{i} = {u.texto_fraccion(fr)} = {u.texto_decimal(fr)}\n")
                    self.text_resultado.insert(tk.END, "\n")
                libres = info.get("libres", [])
                if libres:
                    vars_libres = ", ".join(f"x{c+1}" for c in libres)
                    self.text_resultado.insert(tk.END, f"Variables libres: {vars_libres}\n\n")
        etiqueta = "Forma escalonada reducida por filas" if tipo == "ESCALONADA_REDUCIDA" else "Forma escalonada"
        self.text_resultado.insert(tk.END, etiqueta + " final ([A|b]):\n")
        if tipo == "ESCALONADA_REDUCIDA":
            if pivotes:
                texto_pivotes = ", ".join(str(p+1) for p in pivotes)
                self.text_resultado.insert(tk.END, f"Columnas pivote: {texto_pivotes}.\n")
            else:
                self.text_resultado.insert(tk.END, "Columnas pivote: ninguna.\n")
        self.text_resultado.insert(tk.END, matriz_a_texto(R) + "\n")

    def mostrar_pasos(self, pasos):
        self.text_pasos.delete("1.0", tk.END)
        if not pasos:
            self.text_pasos.insert(tk.END, "No hubo operaciones (matriz ya estaba reducida).\n")
            return
        for idx, paso in enumerate(pasos, start=1):
            if isinstance(paso, dict):
                self.text_pasos.insert(tk.END, f"{idx:02d}) {paso.get('operacion','')}\n")
                self.text_pasos.insert(tk.END, matriz_a_texto(paso.get("matriz", [])) + "\n")
                self.text_pasos.insert(tk.END, "-" * 42 + "\n")
            else:
                self.text_pasos.insert(tk.END, f"{idx:02d}) {paso}\n")

def matriz_simple_a_texto(M):
    if not M:
        return "[ ]"
    filas = len(M)
    cols = len(M[0])
    anchos = [0] * cols
    i = 0
    while i < filas:
        j = 0
        while j < cols:
            txt = u.texto_fraccion(M[i][j])
            if len(txt) > anchos[j]:
                anchos[j] = len(txt)
            j += 1
        i += 1
    lineas = []
    i = 0
    while i < filas:
        partes = []
        j = 0
        while j < cols:
            txt = u.texto_fraccion(M[i][j])
            partes.append(txt.rjust(anchos[j]))
            j += 1
        lineas.append("[ " + "  ".join(partes) + " ]")
        i += 1
    return "\n".join(lineas)

def run_gui():
    app = AlgebraLinealApp()
    app.mainloop()

if __name__ == "__main__":
    run_gui()
