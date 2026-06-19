"""
REVISTA RÁPIDA - PDF to WordPress/Elementor HTML Generator
Transforma artículos de revista PDF en código HTML/CSS encapsulado
listo para pegar en Elementor.
"""

import os
import json
import base64
import uuid
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv

from pdf_processor import PDFProcessor
from html_generator import HTMLGenerator
from ai_analyzer import AIAnalyzer

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
app.config['OUTPUT_FOLDER'] = Path(__file__).parent / 'output'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

# Crear directorios necesarios
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
app.config['OUTPUT_FOLDER'].mkdir(exist_ok=True)


@app.route('/')
def index():
    """Página principal con la interfaz de carga."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_pdf():
    """Procesa el PDF subido y extrae artículos."""
    if 'pdf' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo PDF'}), 400

    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó archivo'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'El archivo debe ser un PDF'}), 400

    # Guardar PDF
    session_id = str(uuid.uuid4())[:8]
    pdf_path = app.config['UPLOAD_FOLDER'] / f"{session_id}_{file.filename}"
    file.save(pdf_path)

    # Procesar PDF
    processor = PDFProcessor(str(pdf_path))
    try:
        articles = processor.extract_articles()
    except Exception as e:
        return jsonify({'error': f'Error procesando PDF: {str(e)}'}), 500

    # Guardar datos de sesión
    session_dir = app.config['OUTPUT_FOLDER'] / session_id
    session_dir.mkdir(exist_ok=True)

    session_data = {
        'session_id': session_id,
        'pdf_filename': file.filename,
        'articles': articles
    }

    with open(session_dir / 'session.json', 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

    return jsonify({
        'session_id': session_id,
        'total_articles': len(articles),
        'articles': [
            {
                'index': i,
                'title': a.get('title', f'Artículo {i+1}'),
                'section': a.get('section', 'Sin sección'),
                'pages': a.get('pages', []),
                'thumbnail': a.get('thumbnail', '')
            }
            for i, a in enumerate(articles)
        ]
    })


@app.route('/generate/<session_id>/<int:article_index>', methods=['POST'])
def generate_html(session_id, article_index):
    """Genera HTML/CSS para un artículo específico."""
    session_dir = app.config['OUTPUT_FOLDER'] / session_id
    session_file = session_dir / 'session.json'

    if not session_file.exists():
        return jsonify({'error': 'Sesión no encontrada'}), 404

    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)

    articles = session_data['articles']
    if article_index >= len(articles):
        return jsonify({'error': 'Artículo no encontrado'}), 404

    article = articles[article_index]

    # Obtener opciones de personalización del request
    options = request.get_json() or {}

    # Usar IA para analizar estilo si hay API key disponible
    ai_analysis = None
    if os.getenv('OPENAI_API_KEY'):
        analyzer = AIAnalyzer()
        ai_analysis = analyzer.analyze_article_style(article)

    # Generar HTML
    generator = HTMLGenerator()
    html_output = generator.generate(article, options, ai_analysis)

    # Guardar output
    output_file = session_dir / f"article_{article_index}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_output)

    # También guardar imágenes como archivos independientes
    images_dir = session_dir / 'images'
    images_dir.mkdir(exist_ok=True)
    image_filenames = []
    for i, img in enumerate(article.get('images', [])):
        if img.get('data'):
            ext = img.get('ext', 'png')
            filename = f"article_{article_index}_img_{i}.{ext}"
            img_path = images_dir / filename
            with open(img_path, 'wb') as imgf:
                imgf.write(base64.b64decode(img['data']))
            image_filenames.append(filename)

    return jsonify({
        'html': html_output,
        'article_title': article.get('title', f'Artículo {article_index + 1}'),
        'images': image_filenames,
        'stats': {
            'text_blocks': len(article.get('text_blocks', [])),
            'images': len(article.get('images', [])),
            'highlights': len(article.get('highlights', [])),
            'background_color': article.get('primary_background', '#ffffff')
        }
    })


@app.route('/preview/<session_id>/<int:article_index>')
def preview_article(session_id, article_index):
    """Muestra preview del artículo generado."""
    session_dir = app.config['OUTPUT_FOLDER'] / session_id
    output_file = session_dir / f"article_{article_index}.html"

    if not output_file.exists():
        return "Artículo no generado aún", 404

    with open(output_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    return render_template('preview.html', html_content=html_content)


@app.route('/images/<session_id>/<filename>')
def serve_image(session_id, filename):
    """Sirve imágenes extraídas del PDF."""
    session_dir = app.config['OUTPUT_FOLDER'] / session_id / 'images'
    return send_from_directory(session_dir, filename)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  REVISTA RÁPIDA - PDF to WordPress/Elementor")
    print("  Abre tu navegador en: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)
