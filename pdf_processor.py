"""
Módulo para procesar PDFs y extraer artículos con su contenido,
imágenes y metadatos de estilo.
"""

import base64
import re
from pathlib import Path

import fitz  # PyMuPDF


class PDFProcessor:
    """Extrae artículos de una revista en PDF."""

    # Secciones conocidas de Xpert Pharma
    KNOWN_SECTIONS = [
        'PORTADA', 'MARCA LÍDER', 'COLABORACIÓN DEL EXPERTO',
        'PANORAMA MÉDICO', 'AULA MÉDICA', 'MÁS ALLÁ DEL FÁRMACO',
        'GALENOCOTIDIANO', 'DE LA VID A LA COPA', 'NUMERALIA',
        'AGENDA DE SALUD', 'TECNOPÍLDORAS', 'FUERA DEL CONSULTORIO',
        'AL PIE DE LA LETRA', 'VISIÓN DEL ESPECIALISTA'
    ]

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.output_dir = Path(pdf_path).parent

    def extract_articles(self) -> list:
        """Extrae todos los artículos del PDF."""
        # Primera pasada: analizar todas las páginas
        all_pages_data = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            page_data = self._analyze_page(page, page_num)
            page_data['page_num'] = page_num
            all_pages_data.append(page_data)

        # Segunda pasada: agrupar páginas en artículos usando lógica mejorada
        articles = []
        current_article = None

        for page_data in all_pages_data:
            page_num = page_data['page_num']
            
            # Determinar si inicia un artículo nuevo
            starts_new = False
            
            if page_data['is_new_article']:
                # Si tiene sección diferente a la actual, es nuevo artículo
                if current_article is None:
                    starts_new = True
                elif page_data.get('section') and page_data['section'] != current_article.get('section', ''):
                    starts_new = True
                elif page_data.get('section') == current_article.get('section', ''):
                    # Misma sección - verificar si es la misma historia o una nueva
                    # Si la página anterior era de esta sección Y hubo un título nuevo largo
                    new_title = page_data.get('title', '')
                    current_title = current_article.get('title', '')
                    if new_title and current_title and new_title[:20] != current_title[:20]:
                        # Título diferente dentro de la misma sección = posible artículo nuevo
                        # Pero solo si no es una continuación (verificar si página consecutiva)
                        last_page = current_article['pages'][-1] if current_article['pages'] else 0
                        if (page_num + 1) - last_page > 1:
                            starts_new = True
                        # Si es consecutiva, probablemente es continuación del mismo artículo
                    elif not current_title and new_title:
                        starts_new = True
                else:
                    starts_new = True
            
            # Páginas sin sección que no son continuación
            if not page_data['is_new_article'] and current_article is None:
                starts_new = True

            if starts_new:
                if current_article and (current_article.get('text_blocks') or current_article.get('images')):
                    articles.append(self._finalize_article(current_article))
                
                current_article = {
                    'section': page_data.get('section', ''),
                    'title': page_data.get('title', ''),
                    'subtitle': page_data.get('subtitle', ''),
                    'author': page_data.get('author', ''),
                    'pages': [page_num + 1],
                    'text_blocks': page_data.get('text_blocks', []),
                    'images': page_data.get('images', []),
                    'colors': page_data.get('colors', {}),
                    'highlights': page_data.get('highlights', []),
                    'page_backgrounds': [page_data.get('background_color', '#ffffff')]
                }
            elif current_article:
                # Continuar artículo actual
                current_article['pages'].append(page_num + 1)
                current_article['text_blocks'].extend(page_data.get('text_blocks', []))
                current_article['images'].extend(page_data.get('images', []))
                current_article['highlights'].extend(page_data.get('highlights', []))
                if page_data.get('colors'):
                    for key, val in page_data['colors'].items():
                        if key in current_article['colors'] and isinstance(val, list):
                            current_article['colors'][key].extend(val)
                        else:
                            current_article['colors'][key] = val
                current_article['page_backgrounds'].append(
                    page_data.get('background_color', '#ffffff')
                )
                # Actualizar título si el actual está vacío o incompleto
                if not current_article['title'] and page_data.get('title'):
                    current_article['title'] = page_data['title']
                if not current_article['author'] and page_data.get('author'):
                    current_article['author'] = page_data['author']

        # Último artículo
        if current_article and (current_article.get('text_blocks') or current_article.get('images')):
            articles.append(self._finalize_article(current_article))

        self.doc.close()
        
        # Post-procesamiento: fusionar artículos de la misma sección que están consecutivos
        articles = self._merge_consecutive_articles(articles)
        
        # Filtrar publicidad y páginas de contenido editorial corto
        articles = self._filter_articles(articles)
        
        return articles

    def _merge_consecutive_articles(self, articles: list) -> list:
        """Fusiona artículos consecutivos que pertenecen a la misma sección."""
        if not articles:
            return articles
        
        merged = [articles[0]]
        
        for article in articles[1:]:
            prev = merged[-1]
            
            # Fusionar si:
            # 1. Misma sección
            # 2. Páginas consecutivas (diferencia <= 1)
            # 3. Uno de los dos no tiene título largo
            same_section = (prev.get('section') and 
                          prev.get('section') == article.get('section'))
            
            pages_consecutive = False
            if prev.get('pages') and article.get('pages'):
                pages_consecutive = article['pages'][0] - prev['pages'][-1] <= 1
            
            short_title = len(article.get('title', '')) < 15
            
            if same_section and pages_consecutive and short_title:
                # Fusionar
                prev['pages'].extend(article['pages'])
                prev['text_blocks'].extend(article.get('text_blocks', []))
                prev['images'].extend(article.get('images', []))
                prev['highlights'].extend(article.get('highlights', []))
                prev['page_backgrounds'].extend(article.get('page_backgrounds', []))
                if not prev.get('title') and article.get('title'):
                    prev['title'] = article['title']
            else:
                merged.append(article)
        
        return merged

    def _filter_articles(self, articles: list) -> list:
        """Filtra publicidad y páginas no editoriales."""
        filtered = []
        
        # Palabras clave de publicidad
        ad_keywords = [
            'anúnciate', 'anunciate', 'publicidad', 'contrata',
            'lleva tu empresa', 'protegemos el futuro',
            'innovación y compromiso'  # Portada de la revista
        ]
        
        # Palabras de páginas no editoriales
        non_editorial = ['e d i t o r i a l', 'editorial', 'contenido', 'índice']
        
        for article in articles:
            title_lower = article.get('title', '').lower()
            
            # Filtrar si tiene muy poco texto (probable publicidad o portada de revista)
            total_text = ' '.join(b.get('text', '') for b in article.get('text_blocks', []))
            if len(total_text) < 100 and not article.get('section'):
                continue
            
            # Filtrar publicidad obvia
            is_ad = any(kw in title_lower for kw in ad_keywords)
            if is_ad:
                continue
            
            # Filtrar editorial e índice
            is_non_editorial = any(kw in title_lower for kw in non_editorial)
            if is_non_editorial and len(total_text) < 500:
                continue
            
            # Filtrar páginas que son solo tabla de contenido (muchos números cortos)
            # Pero solo si no tiene sección conocida
            if re.match(r'^[\d\s\-]+$', article.get('title', '').strip()) and not article.get('section'):
                continue
            
            # Filtrar páginas que solo tienen números y son tabla de contenido
            # (una página con sección pero título tipo "10 13 15 7 12" es tabla de contenido)
            if article.get('pages') and len(article['pages']) == 1:
                title_clean = article.get('title', '').strip()
                if re.match(r'^[\d\s\-]+$', title_clean) and len(total_text) < 300:
                    continue
            
            # Limpiar título: si es un solo caracter, nombre de sección, o muy corto
            title = article.get('title', '').strip()
            section = article.get('section', '')
            
            # Limpiar basura del título (URLs, números de página)
            title = re.sub(r'www\.\w+\.\w+\.\w+', '', title)
            title = re.sub(r'\b\d{1,2}\b\s*$', '', title)  # Números de página al final
            title = re.sub(r'^\d{1,2}\s+', '', title)  # Números de página al inicio
            title = title.strip()
            article['title'] = title
            
            # Si el título es igual al nombre de la sección, buscar uno mejor
            if (len(title) <= 2 or 
                title.upper() == section.upper() or
                title.upper().startswith(section.upper())):
                # Buscar el primer heading real en text_blocks
                for block in article.get('text_blocks', []):
                    if block.get('is_heading') and len(block.get('text', '')) > 10:
                        candidate = block['text'][:120]
                        # Limpiar candidate
                        candidate = re.sub(r'www\.\w+\.\w+\.\w+', '', candidate).strip()
                        if candidate.upper() != section.upper() and len(candidate) > 5:
                            article['title'] = candidate
                            break
                # Si aún no hay título, usar los primeros caracteres del texto
                if (article['title'].upper() == section.upper() or 
                    len(article['title']) <= 2):
                    for block in article.get('text_blocks', []):
                        text = block.get('text', '').strip()
                        if len(text) > 20 and not text.startswith('www'):
                            article['title'] = text[:80]
                            break
            
            filtered.append(article)
        
        return filtered

    def _analyze_page(self, page, page_num: int) -> dict:
        """Analiza una página completa del PDF."""
        result = {
            'is_new_article': False,
            'section': '',
            'title': '',
            'subtitle': '',
            'author': '',
            'text_blocks': [],
            'images': [],
            'colors': {},
            'highlights': [],
            'background_color': '#ffffff'
        }

        # Extraer colores de fondo
        result['background_color'] = self._get_background_color(page)
        
        # Extraer bloques de texto con formato
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        
        all_text_spans = []
        
        for block in blocks:
            if block['type'] == 0:  # Texto
                for line in block.get('lines', []):
                    for span in line.get('spans', []):
                        span_data = {
                            'text': span['text'].strip(),
                            'font': span['font'],
                            'size': span['size'],
                            'color': self._color_to_hex(span['color']),
                            'bold': 'Bold' in span['font'] or 'bold' in span['font'].lower(),
                            'italic': 'Italic' in span['font'] or 'italic' in span['font'].lower(),
                            'bbox': span['bbox'],
                            'origin': span.get('origin', (0, 0))
                        }
                        if span_data['text']:
                            all_text_spans.append(span_data)

        # Detectar sección
        for span in all_text_spans[:10]:  # Solo primeros spans
            text_upper = span['text'].upper().strip('»« ')
            for section in self.KNOWN_SECTIONS:
                if section in text_upper:
                    result['section'] = section
                    result['is_new_article'] = True
                    break
            if result['section']:
                break

        # Detectar título (texto más grande de la página)
        if all_text_spans:
            max_size = max(s['size'] for s in all_text_spans)
            title_spans = [s for s in all_text_spans if s['size'] >= max_size * 0.9 and s['size'] > 14]
            if title_spans:
                result['title'] = ' '.join(s['text'] for s in title_spans[:5])
                if len(result['title']) > 10:
                    result['is_new_article'] = True

        # Detectar autor (patrones como "POR Nombre" o "Por: Nombre")
        for span in all_text_spans[:15]:
            if re.match(r'^POR\s+', span['text'], re.IGNORECASE):
                result['author'] = span['text']
                break

        # Clasificar texto en bloques
        body_spans = []
        for span in all_text_spans:
            # Detectar destacados/balazos (texto grande italic o en color diferente)
            is_highlight = (
                (span['size'] > 13 and span['italic']) or
                (span['size'] > 14 and span['color'] != '#000000' and 
                 span['color'] != result['background_color'])
            )
            
            if is_highlight and len(span['text']) > 20:
                result['highlights'].append({
                    'text': span['text'],
                    'color': span['color'],
                    'font': span['font'],
                    'size': span['size']
                })
            else:
                body_spans.append(span)

        # Agrupar spans en párrafos
        result['text_blocks'] = self._group_into_paragraphs(body_spans)
        
        # Recopilar colores usados
        colors_found = set()
        for span in all_text_spans:
            if span['color'] != '#000000':
                colors_found.add(span['color'])
        result['colors'] = {
            'accent_colors': list(colors_found),
            'background': result['background_color']
        }

        # Extraer imágenes
        result['images'] = self._extract_images(page, page_num)

        return result

    def _get_background_color(self, page) -> str:
        """Detecta el color de fondo predominante de una página."""
        # Renderizar un pequeño sample de la página para detectar fondo
        pix = page.get_pixmap(matrix=fitz.Matrix(0.1, 0.1))
        
        # Muestrear esquinas
        samples = []
        w, h = pix.width, pix.height
        positions = [(0, 0), (w-1, 0), (0, h-1), (w-1, h-1), (w//2, 0)]
        
        for x, y in positions:
            if 0 <= x < w and 0 <= y < h:
                pixel = pix.pixel(x, y)
                samples.append(pixel[:3])
        
        if samples:
            # Color más frecuente de las muestras
            from collections import Counter
            most_common = Counter(samples).most_common(1)[0][0]
            r, g, b = most_common
            return f'#{r:02x}{g:02x}{b:02x}'
        
        return '#ffffff'

    def _color_to_hex(self, color_int: int) -> str:
        """Convierte un entero de color a formato hexadecimal."""
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        return f'#{r:02x}{g:02x}{b:02x}'

    def _group_into_paragraphs(self, spans: list) -> list:
        """Agrupa spans consecutivos en párrafos."""
        if not spans:
            return []

        paragraphs = []
        current_para = {
            'text': '',
            'font_size': spans[0]['size'],
            'is_heading': False,
            'color': spans[0]['color']
        }

        prev_y = spans[0]['bbox'][1] if spans else 0

        for span in spans:
            y_pos = span['bbox'][1]
            size_diff = abs(span['size'] - current_para['font_size'])
            y_gap = abs(y_pos - prev_y)

            # Nuevo párrafo si hay cambio significativo de posición o tamaño
            if y_gap > span['size'] * 1.8 or size_diff > 2:
                if current_para['text'].strip():
                    current_para['text'] = current_para['text'].strip()
                    current_para['is_heading'] = current_para['font_size'] > 12
                    paragraphs.append(current_para)
                current_para = {
                    'text': '',
                    'font_size': span['size'],
                    'is_heading': False,
                    'color': span['color']
                }

            current_para['text'] += span['text'] + ' '
            prev_y = span['bbox'][3]  # Bottom of bbox

        # Último párrafo
        if current_para['text'].strip():
            current_para['text'] = current_para['text'].strip()
            current_para['is_heading'] = current_para['font_size'] > 12
            paragraphs.append(current_para)

        return paragraphs

    def _extract_images(self, page, page_num: int) -> list:
        """Extrae imágenes de la página."""
        images = []
        image_list = page.get_images(full=True)

        for img_idx, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = self.doc.extract_image(xref)
                
                if base_image:
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Filtrar imágenes muy pequeñas (logos de pie de página, etc.)
                    if len(image_bytes) < 5000:
                        continue
                    
                    # Convertir a base64 para incluir en el HTML
                    img_b64 = base64.b64encode(image_bytes).decode('utf-8')
                    
                    # Obtener posición de la imagen en la página
                    img_rects = page.get_image_rects(xref)
                    position = 'center'
                    if img_rects:
                        rect = img_rects[0]
                        page_width = page.rect.width
                        img_center_x = (rect.x0 + rect.x1) / 2
                        if img_center_x < page_width * 0.35:
                            position = 'left'
                        elif img_center_x > page_width * 0.65:
                            position = 'right'
                        else:
                            position = 'center'

                    images.append({
                        'data': img_b64,
                        'ext': image_ext,
                        'position': position,
                        'page': page_num + 1,
                        'width': base_image.get('width', 0),
                        'height': base_image.get('height', 0)
                    })
            except Exception:
                continue

        return images

    def _finalize_article(self, article: dict) -> dict:
        """Finaliza y limpia un artículo extraído."""
        # Generar thumbnail de la primera página
        if article['pages']:
            first_page = article['pages'][0] - 1
            page = self.doc[first_page]
            pix = page.get_pixmap(matrix=fitz.Matrix(0.3, 0.3))
            thumb_bytes = pix.tobytes("png")
            article['thumbnail'] = base64.b64encode(thumb_bytes).decode('utf-8')

        # Determinar color principal
        bg_colors = article.get('page_backgrounds', ['#ffffff'])
        # Usar el color de fondo más frecuente (que no sea blanco puro)
        non_white = [c for c in bg_colors if c != '#ffffff' and c != '#fefefe']
        article['primary_background'] = non_white[0] if non_white else '#ffffff'

        # Limpiar highlights duplicados
        seen_texts = set()
        unique_highlights = []
        for h in article.get('highlights', []):
            text_key = h['text'][:50]
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_highlights.append(h)
        article['highlights'] = unique_highlights

        return article
