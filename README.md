# 📰 Revista Rápida

**PDF de revista → HTML/CSS listo para WordPress/Elementor**

Transforma automáticamente los artículos de la revista Xpert Pharma (PDF) en código HTML/CSS encapsulado que emula el diseño original, con animaciones elegantes, listo para pegar en un widget HTML de Elementor.

## Características

- 📄 Extracción automática de artículos del PDF (texto, imágenes, colores, destacados)
- 🎨 Detección de colores del diseño original (fondos, acentos)
- ✍️ Tipografías: Montserrat (body), Times New Roman (títulos y balazos)
- 🎬 Animaciones de scroll: fade-in desde abajo (textos), fade lateral (imágenes)
- 🖼️ Imágenes posicionadas (izquierda/derecha/centro) como en la revista
- 💬 Destacados/Balazos con estilo editorial
- 📱 Diseño responsive (adaptable a móviles)
- 🔒 CSS encapsulado (no afecta el resto del sitio)
- 🎛️ Panel de personalización de colores
- 📋 Copiado directo del HTML para Elementor

## Requisitos

- Python 3.10+
- pip (gestor de paquetes de Python)

## Instalación

```bash
cd app
pip install -r requirements.txt
```

## Uso

### Opción 1: Doble clic en run.bat (Windows)

### Opción 2: Desde terminal
```bash
cd app
python app.py
```

Luego abre **http://localhost:5000** en tu navegador.

## Flujo de trabajo

1. **Sube el PDF** - Arrastra o selecciona el archivo PDF de la revista
2. **Selecciona un artículo** - En la barra lateral aparecen todos los artículos detectados con su thumbnail
3. **Preview** - El artículo se renderiza con el estilo de la revista
4. **Ajusta colores** (opcional) - Click en "🎨 Opciones" para cambiar colores de acento/fondo
5. **Copia el HTML** - Click en "📋 Copiar HTML" y pégalo en un widget HTML de Elementor

## Modos de imagen

- **Embebidas (base64)**: Las imágenes van incluidas directamente en el HTML. El código es más pesado pero no necesita subir imágenes por separado.
- **Placeholders URL**: Las imágenes se reemplazan por marcadores `#IMAGEN_1_URL_AQUI`. Sube las imágenes al Media Library de WordPress y reemplaza los placeholders con las URLs.

## Uso con OpenAI (Opcional)

Si agregas tu API key de OpenAI, la app puede usar GPT-4o-mini para analizar mejor los estilos visuales de cada artículo.

1. Copia `.env.example` como `.env`
2. Agrega tu API key: `OPENAI_API_KEY=sk-tu-key`

La app funciona perfectamente sin esta configuración.

## En Elementor

1. En el editor de Elementor, agrega un widget **HTML**
2. Pega el código copiado de Revista Rápida
3. El artículo se mostrará con el estilo de la revista
4. Las animaciones se activan automáticamente al hacer scroll

## Estructura

```
app/
├── app.py              # Servidor Flask principal
├── pdf_processor.py    # Extracción de artículos del PDF
├── html_generator.py   # Generación de HTML/CSS encapsulado
├── ai_analyzer.py      # Análisis con IA (opcional)
├── requirements.txt    # Dependencias
├── run.bat            # Lanzador Windows
├── .env.example       # Ejemplo de configuración
├── templates/
│   ├── index.html     # Interfaz principal
│   └── preview.html   # Preview standalone
├── uploads/           # PDFs subidos (temporal)
└── output/            # HTML generado y sesiones
```
