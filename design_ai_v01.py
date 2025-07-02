##############################################################################
#
#####  Design AI  #####
#
# App desarrollada durante el AI Summit 2025 del Tecnológico de Monterrey
#    Asistente de diseño para estudiantes. Brinda retroalimentación
#     rápida y promueve el pensamiento divergente entre cada etapa
#     del proceso de diseño.
#
# Equipo integrado por profesores de los departamentos de Diseño de la
#  Escuela de Arquitectura, Arte y Diseño
#
#    Christiam Mendoza - christiam@tec.mx
#    Claudia Susana Lopez - lopezclau@tec.mx
#    Rocío Elizabeth Cortez Márquez - rocio.cortez@tec.mx
#    Nayra Mendoza Enríquez - nayra@tec.mx
#    Inés Alvarez Icaza Longoria - i.alvarezicaza@tec.mx
#    Alejandro Martínez - amb@tec.mx
#    Monica del Carmen Vazquez Garza - vazquez@tec.mx
#    Elva Yadira Ornelas Sánchez - yadira.ornelas@tec.mx
#    Juan Carlos Márquez Cañizares - jcmarquez@tec.mx
#    Griselda Esthela Oyervides Ramírez - gris.oyervides@tec.mx
#    Martha Elena Núñez López - martha.nunez@tec.mx
#
# This program is free software: you can redistribute it and/or modify it under the terms
#   of the GNU General Public License as published by the Free Software Foundation, either
#   version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#   without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#   See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program.
#   If not, see <https://www.gnu.org/licenses/>. 
#
#
##############################################################################

import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from PIL import Image, ImageTk
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar la API Key desde un archivo .env (recomendado)
load_dotenv()

def call_gemini_vision_api(api_key, prompt, image_path):
    """
    Función para comunicarse con el modelo de visión de Gemini.
    Devuelve la respuesta de texto del modelo.
    """
    try:
        genai.configure(api_key=api_key)
        img = Image.open(image_path)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([prompt, img])
        return response.text
    except FileNotFoundError:
        return f"Error: No se pudo encontrar el archivo de imagen en la ruta: {image_path}"
    except Exception as e:
        return f"Error al contactar la API de Gemini: {str(e)}"

class DesignApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Reflexión de Diseño")
        self.root.geometry("1000x800") # Ancho aumentado para la nueva columna

        # --- INICIO: REESTRUCTURACIÓN DEL LAYOUT PRINCIPAL CON GRID ---
        # Configurar la ventana principal para usar grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1) # La columna de contenido se expande
        self.root.grid_columnconfigure(1, weight=0) # La columna de previsualización no

        # --- Columna 0: Contenido con Scroll ---
        # Crear un frame contenedor principal para el canvas y la scrollbar
        scroll_container = ttk.Frame(root)
        scroll_container.grid(row=0, column=0, sticky="nsew")
        scroll_container.grid_rowconfigure(0, weight=1)
        scroll_container.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(scroll_container)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=self.canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        # --- Columna 1: Previsualización de Imágenes (Estática) ---
        preview_frame = ttk.LabelFrame(root, text="Previsualización", padding="10")
        preview_frame.grid(row=0, column=1, sticky="ns", padx=10, pady=10)
        self.create_preview_widgets(preview_frame)
        # --- FIN: REESTRUCTURACIÓN DEL LAYOUT ---

        # Estilo para los widgets
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure("TLabel", font=("Helvetica", 10))
        style.configure("TButton", font=("Helvetica", 10))
        style.configure("TLabelframe.Label", font=("Helvetica", 11, "bold"))

        # --- Variables de control ---
        self.sketch_path = tk.StringVar()
        self.sketch_mejora_path = tk.StringVar()
        self.api_key = tk.StringVar(value=os.getenv("GOOGLE_API_KEY", ""))

        # --- Widgets agregados al "scrollable_frame" ---
        form_frame = ttk.LabelFrame(self.scrollable_frame, text="1. Información del Proyecto", padding="10")
        form_frame.grid(row=0, column=0, sticky="ew", pady=10, padx=10)
        form_frame.columnconfigure(1, weight=1)
        self.create_form_widgets(form_frame)

        self.output_frame = ttk.LabelFrame(self.scrollable_frame, text="2. Sugerencias de Mejora", padding="10")
        self.create_suggestions_widgets(self.output_frame)

        self.validation_frame = ttk.LabelFrame(self.scrollable_frame, text="3. Resultados de Validación", padding="10")
        self.create_validation_widgets(self.validation_frame)

        self.define_text_tags()

    def create_preview_widgets(self, parent):
        """Crea los labels que mostrarán las imágenes de previsualización."""
        # Label para el sketch inicial
        ttk.Label(parent, text="Sketch Inicial:").pack(pady=(0, 5))
        self.preview_label1 = ttk.Label(parent, text="No cargado", relief="solid", padding=5)
        self.preview_label1.pack(pady=5)

        # Label para el sketch mejorado
        ttk.Label(parent, text="Sketch Mejorado:").pack(pady=(20, 5))
        self.preview_label2 = ttk.Label(parent, text="No cargado", relief="solid", padding=5)
        self.preview_label2.pack(pady=5)

    def _update_image_preview(self, label_widget, image_path):
        """Función auxiliar para abrir, redimensionar y mostrar una imagen en un label."""
        try:
            # Abrir la imagen con Pillow
            img = Image.open(image_path)
            # Redimensionar manteniendo el aspect ratio para que quepa en 250x250
            img.thumbnail((250, 250))
            # Convertir a un formato que Tkinter pueda usar
            photo = ImageTk.PhotoImage(img)
            # Actualizar el widget Label
            label_widget.config(image=photo, text="") # Limpiar texto placeholder
            # **Importante**: Mantener una referencia a la imagen para evitar que sea eliminada por el recolector de basura
            label_widget.image = photo
        except Exception as e:
            messagebox.showerror("Error de Imagen", f"No se pudo cargar la previsualización: {e}")

    def load_sketch(self):
        """Carga el sketch inicial y actualiza su previsualización."""
        filepath = filedialog.askopenfilename(title="Seleccionar Sketch Inicial", filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if filepath:
            self.sketch_path.set(os.path.basename(filepath))
            self._full_sketch_path = filepath
            # Actualizar la previsualización
            self._update_image_preview(self.preview_label1, self._full_sketch_path)

    def load_sketch_mejora(self):
        """Carga el sketch mejorado y actualiza su previsualización."""
        filepath = filedialog.askopenfilename(title="Seleccionar Sketch Mejorado", filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if filepath:
            self.sketch_mejora_path.set(os.path.basename(filepath))
            self._full_sketch_mejora_path = filepath
            # Actualizar la previsualización
            self._update_image_preview(self.preview_label2, self._full_sketch_mejora_path)

    # ... (El resto de los métodos como define_text_tags, create_form_widgets, etc., permanecen sin cambios)
    def define_text_tags(self):
        self.sugerencias_text.tag_configure("heading", font=("Helvetica", 12, "bold"), spacing1=5, spacing3=5)
        self.sugerencias_text.tag_configure("bold", font=("Helvetica", 10, "bold"))
        self.sugerencias_text.tag_configure("list_item", lmargin1=10, lmargin2=25, spacing1=2)
        self.resultados_text.tag_configure("heading", font=("Helvetica", 12, "bold"), spacing3=10)
        self.resultados_text.tag_configure("sub_heading", font=("Helvetica", 11, "bold"), spacing1=8, spacing3=5)
        self.resultados_text.tag_configure("criterion", font=("Helvetica", 10, "bold"))
        self.resultados_text.tag_configure("score", font=("Helvetica", 10))
        self.resultados_text.tag_configure("comment", font=("Helvetica", 10, "italic"), lmargin1=10, lmargin2=10)

    def create_form_widgets(self, parent):
        ttk.Label(parent, text="Gemini API Key:").grid(row=0, column=0, sticky="w", pady=2)
        self.api_key_entry = ttk.Entry(parent, textvariable=self.api_key, width=50, show="*")
        self.api_key_entry.grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(parent, text="Sketch (imagen):").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Button(parent, text="Cargar Sketch...", command=self.load_sketch).grid(row=1, column=1, sticky="w", pady=2)
        self.sketch_path_label = ttk.Label(parent, textvariable=self.sketch_path, wraplength=400)
        self.sketch_path_label.grid(row=2, column=1, sticky="w", pady=2)
        fields = ["Descripción del Sketch:", "¿Qué estás proponiendo?", "¿A quién está dirigido?", "¿Para qué sirve?", "¿Dónde se usará?"]
        self.entries = {}
        for i, field in enumerate(fields):
            ttk.Label(parent, text=field).grid(row=i+3, column=0, sticky="w", pady=2)
            if field == "Descripción del Sketch:":
                entry = tk.Text(parent, height=3, width=50, font=("Helvetica", 10))
            else:
                entry = ttk.Entry(parent, width=50, font=("Helvetica", 10))
            entry.grid(row=i+3, column=1, sticky="ew", pady=2)
            self.entries[field] = entry
        self.activar_btn = ttk.Button(parent, text="Activar Divergencia", command=self.run_divergence)
        self.activar_btn.grid(row=len(fields)+3, column=0, columnspan=2, pady=10)

    def create_suggestions_widgets(self, parent):
        self.sugerencias_text = tk.Text(parent, height=12, width=80, wrap="word", state="disabled", relief="sunken", borderwidth=1, font=("Helvetica", 10))
        self.sugerencias_text.pack(fill="x", expand=True, pady=5)
        upload_frame = ttk.Frame(parent)
        upload_frame.pack(fill="x", expand=True, pady=5)
        ttk.Label(upload_frame, text="Sketch Mejorado:").pack(side="left", padx=(0, 5))
        ttk.Button(upload_frame, text="Cargar Sketch Mejorado...", command=self.load_sketch_mejora).pack(side="left")
        self.sketch_mejora_path_label = ttk.Label(upload_frame, textvariable=self.sketch_mejora_path, wraplength=300)
        self.sketch_mejora_path_label.pack(side="left", padx=5)
        self.validar_btn = ttk.Button(parent, text="Validar Mejoras", command=self.run_validation)
        self.validar_btn.pack(pady=10)

    def create_validation_widgets(self, parent):
        self.resultados_text = tk.Text(parent, height=10, width=80, wrap="word", state="disabled", relief="sunken", borderwidth=1, font=("Helvetica", 10))
        self.resultados_text.pack(fill="x", expand=True, pady=5)

    def run_divergence(self):
        self.activar_btn.config(state="disabled", text="Analizando...")
        thread = threading.Thread(target=self._divergence_thread)
        thread.start()

    def _divergence_thread(self):
        api_key = self.api_key.get()
        if not api_key or not self.sketch_path.get():
            messagebox.showerror("Error", "La API Key y el Sketch inicial son obligatorios.")
            self.root.after(0, self.reset_activar_btn)
            return
        form_data = {k: (v.get("1.0", tk.END).strip() if isinstance(v, tk.Text) else v.get().strip()) for k, v in self.entries.items()}
        prompt = f"""
        Eres un experto en diseño de productos. Analiza el siguiente boceto y la descripción del proyecto. 
        Proporciona sugerencias de mejora concretas y accionables basadas en los siguientes CINCO criterios:
        1. **Estética**: ¿Cómo se ve? ¿Es atractivo?
        2. **Ergonomía**: ¿Es fácil y cómodo de usar?
        3. **Impacto Ambiental**: ¿Qué materiales se podrían usar? ¿Es sostenible?
        4. **Integración de Tecnología**: ¿Cómo se integra la tecnología? ¿Es innovadora? ¿Aporta valor?
        5. **Usabilidad**: ¿Qué tan intuitivo es el diseño para el usuario final? ¿Cumple su función de manera eficiente?
        Información del proyecto:
        - Descripción: {form_data['Descripción del Sketch:']}
        - ¿Qué estás proponiendo?: {form_data['¿Qué estás proponiendo?']}
        - ¿A quién está dirigido?: {form_data['¿A quién está dirigido?']}
        - ¿Para qué sirve?: {form_data['¿Para qué sirve?']}
        - ¿Dónde se usará?: {form_data['¿Dónde se usará?']}
        Organiza tu respuesta con encabezados en negrita para cada criterio y usa viñetas para las sugerencias.
        """
        sugerencias = call_gemini_vision_api(api_key, prompt, self._full_sketch_path)
        self.root.after(0, self.update_suggestions_ui, sugerencias)

    def update_suggestions_ui(self, sugerencias):
        self.output_frame.grid(row=1, column=0, sticky="ew", pady=10, padx=10)
        self.sugerencias_text.config(state="normal")
        self.sugerencias_text.delete("1.0", tk.END)
        for line in sugerencias.split('\n'):
            line = line.strip()
            if not line: continue
            if line.startswith('**') and line.endswith('**'):
                self.sugerencias_text.insert(tk.END, f"\n{line.strip('*')}\n", "heading")
            elif line.startswith('* ') or line.startswith('- '):
                self.sugerencias_text.insert(tk.END, f"• {line[2:]}\n", "list_item")
            else:
                self.sugerencias_text.insert(tk.END, f"{line}\n")
        self.sugerencias_text.config(state="disabled")
        self.reset_activar_btn()

    def reset_activar_btn(self):
        self.activar_btn.config(state="normal", text="Activar Divergencia")

    def run_validation(self):
        self.validar_btn.config(state="disabled", text="Validando...")
        thread = threading.Thread(target=self._validation_thread)
        thread.start()

    def _validation_thread(self):
        api_key = self.api_key.get()
        if not self.sketch_mejora_path.get():
            messagebox.showerror("Error", "Debes cargar un Sketch Mejorado para validar.")
            self.root.after(0, self.reset_validar_btn)
            return
        form_data = {k: (v.get("1.0", tk.END).strip() if isinstance(v, tk.Text) else v.get().strip()) for k, v in self.entries.items()}
        prompt = f"""
        Eres un experto en diseño de productos. Evalúa este NUEVO boceto mejorado.
        Información original del proyecto (para contexto):
        - Descripción: {form_data['Descripción del Sketch:']}
        - ¿Qué estás proponiendo?: {form_data['¿Qué estás proponiendo?']}
        - ¿A quién está dirigido?: {form_data['¿A quién está dirigido?']}
        - ¿Para qué sirve?: {form_data['¿Para qué sirve?']}
        - ¿Dónde se usará?: {form_data['¿Dónde se usará?']}
        Responde ÚNICAMENTE con un objeto JSON válido que contenga:
        1. Un objeto anidado "calificaciones" con una puntuación del 1 al 5 para cada uno de los siguientes criterios: "Estética", "Ergonomía", "Impacto Ambiental", "Integración de Tecnología", "Usabilidad".
        2. Una cadena de texto "comentario_general" con una breve conclusión o justificación de las calificaciones.
        El formato debe ser exactamente el siguiente:
        {{
          "calificaciones": {{
            "Estética": <puntuación 1-5>,
            "Ergonomía": <puntuación 1-5>,
            "Impacto Ambiental": <puntuación 1-5>,
            "Integración de Tecnología": <puntuación 1-5>,
            "Usabilidad": <puntuación 1-5>
          }},
          "comentario_general": "<Tu comentario aquí>"
        }}
        """
        resultados = call_gemini_vision_api(api_key, prompt, self._full_sketch_mejora_path)
        self.root.after(0, self.update_validation_ui, resultados)

    def update_validation_ui(self, resultados):
        self.validation_frame.grid(row=2, column=0, sticky="ew", pady=10, padx=10)
        self.resultados_text.config(state="normal")
        self.resultados_text.delete("1.0", tk.END)
        try:
            clean_json_str = resultados.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json_str)
            self.resultados_text.insert(tk.END, "Evaluación Final\n", "heading")
            if 'calificaciones' in data and isinstance(data['calificaciones'], dict):
                self.resultados_text.insert(tk.END, "Calificaciones por Criterio\n", "sub_heading")
                for key, value in data['calificaciones'].items():
                    self.resultados_text.insert(tk.END, f"{key}: ", "criterion")
                    self.resultados_text.insert(tk.END, f"{value} / 5\n", "score")
            if 'comentario_general' in data:
                self.resultados_text.insert(tk.END, "\nComentario General\n", "sub_heading")
                self.resultados_text.insert(tk.END, data['comentario_general'], "comment")
        except (json.JSONDecodeError, TypeError, KeyError):
            self.resultados_text.insert(tk.END, "Respuesta no procesable:\n", "heading")
            self.resultados_text.insert(tk.END, resultados)
        self.resultados_text.config(state="disabled")
        self.reset_validar_btn()

    def reset_validar_btn(self):
        self.validar_btn.config(state="normal", text="Validar Mejoras")

if __name__ == "__main__":
    root = tk.Tk()
    app = DesignApp(root)
    root.mainloop()
