# Prompt de contexto para IA - Revista Rápida

Copia y pega esto al inicio de tu conversación con cualquier IA para darle contexto completo del proyecto.

---

## PROMPT:

Estoy trabajando en una aplicación llamada **Revista Rápida**. El repositorio está en: https://github.com/bangchancooper-cmd/revista-rapida

### Qué hace la app:
Transforma artículos de una revista farmacéutica en PDF (Xpert Pharma) en código HTML/CSS encapsulado listo para pegar en un widget HTML de WordPress/Elementor (versión gratuita). El objetivo es que el post en el blog se parezca lo más posible al diseño original del artículo en la revista PDF.

### Stack tecnológico:
- **Backend:** Python 3.12 + Flask
- **Procesamiento PDF:** PyMuPDF (fitz)
- **IA opcional:** OpenAI GPT-4o-mini (para análisis de estilos visuales)
- **Frontend:** HTML/CSS/JS vanilla (interfaz de la app)
- **Output:** HTML/CSS encapsulado con JavaScript (IntersectionObserver para animaciones)

### Arquitectura (3 módulos principales):

1. **`pdf_processor.py`** - Extrae artículos del PDF:
   - Detecta secciones de la revista (PORTADA, MARCA LÍDER, AULA MÉDICA, GALENOCOTIDIANO, etc.)
   - Extrae texto con metadatos de fuente (tamaño, color, bold, italic, posición)
   - Detecta títulos (texto más grande de la página)
   - Detecta autor (patrón "POR Nombre")
   - Detecta destacados/balazos (texto grande italic o en color diferente al cuerpo)
   - Extrae imágenes con su posición (left/right/center basado en coordenadas)
   - Detecta color de fondo de cada página (muestreando pixeles de esquinas)
   - Agrupa páginas consecutivas de la misma sección en un solo artículo
   - Filtra publicidad y páginas no editoriales
   - Genera thumbnails de cada artículo

2. **`html_generator.py`** - Genera HTML/CSS encapsulado:
   - CSS scoped con ID único (`#xp-XXXXXXXX`) para no afectar el sitio
   - Variables CSS para colores (--xp-bg, --xp-accent, --xp-text, etc.)
   - Tipografías: Times New Roman para títulos y balazos, Montserrat para body
   - Imágenes posicionadas con float (left/right) o full-width (center)
   - Destacados/balazos con borde izquierdo y comillas decorativas
   - Animaciones de scroll: fade-up (textos desde abajo), fade-left/fade-right (imágenes desde los lados)
   - IntersectionObserver para activar animaciones al hacer scroll
   - Responsive (mobile-first, imágenes full-width en móvil)
   - Dos modos de imagen: base64 embebido o placeholders URL
   - Si el fondo del PDF es blanco, crea un tinte suave basado en el color accent

3. **`ai_analyzer.py`** (opcional) - Mejora detección de estilos con OpenAI:
   - Analiza thumbnails con GPT-4o-mini Vision
   - Sugiere colores y layout
   - Tiene un mapeo fallback de secciones a colores si no hay API key

### Flujo de la app:
1. Usuario sube PDF → `POST /upload` → PDFProcessor extrae artículos → retorna lista con thumbnails
2. Usuario selecciona artículo → `POST /generate/{session_id}/{index}` → HTMLGenerator produce HTML
3. Usuario ve preview en iframe, ajusta colores si quiere, y copia el HTML
4. Usuario pega el HTML en widget HTML de Elementor en WordPress

### Convenciones de diseño del output HTML:
- Fondo: tinte suave derivado del color accent del artículo (o color del PDF si es oscuro)
- Título: Times New Roman, italic, color accent, responsive (clamp 24-36px)
- Cuerpo: Montserrat 15px, justify, line-height 1.8
- Subtítulos (h2): Montserrat bold 20px, color accent
- Balazos/destacados: Times New Roman italic 20px, borde izquierdo 4px color accent, fondo claro
- Imágenes: border-radius 8px, box-shadow, float left/right al 45% o full-width
- Animaciones: 0.8s ease, transition-delay escalonado (0.1s entre elementos)
- Todo responsive: en móvil las imágenes pasan a 100% width

### Opciones de personalización (via JSON en el POST /generate):
```json
{
  "animations": true,
  "primary_color": "#1a7ab5",
  "background_color": "#f3f6f9",
  "image_mode": "base64"  // o "url"
}
```

### La revista (contexto editorial):
- Revista bimestral de Xpert Pharma (industria farmacéutica en México)
- ~13-14 artículos por edición
- Cada sección tiene su propio esquema de colores y estilo visual
- Secciones: Portada, Marca Líder, Colaboración del Experto, Panorama Médico, Aula Médica, Más Allá del Fármaco, Galenocotidiano, De la Vid a la Copa, Numeralia, Agenda de Salud, Tecnopíldoras, Fuera del Consultorio, Al Pie de la Letra

### El sitio WordPress destino:
- URL: https://xpertpharma.com.mx
- Elementor versión gratuita
- Tipografías del sitio: Montserrat (body), Times New Roman (títulos de entrada y destacados)
- El HTML se pega en un widget HTML de Elementor dentro del post
- El CSS está encapsulado para no modificar nada del tema/sitio

---

Con este contexto puedes ayudarme a mejorar, debuggear o agregar funcionalidades a la app.
