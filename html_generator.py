"""
Generador de HTML/CSS encapsulado para WordPress/Elementor.
Produce código que emula el diseño de la revista con animaciones elegantes.
"""

import hashlib
import re


class HTMLGenerator:
    """Genera HTML/CSS encapsulado listo para Elementor."""

    def generate(self, article: dict, options: dict = None, ai_analysis: dict = None) -> str:
        """Genera el HTML completo encapsulado para un artículo."""
        options = options or {}
        
        # Determinar estilos basados en el artículo
        styles = self._compute_styles(article, options, ai_analysis)
        
        # Generar un ID único para encapsular
        scope_id = f"xp-{hashlib.md5(article.get('title', '').encode()).hexdigest()[:8]}"
        
        # Modo de imágenes: 'base64' (default) o 'url'
        image_mode = options.get('image_mode', 'base64')
        
        # Construir HTML
        html_parts = []
        html_parts.append(self._generate_css(scope_id, styles, article))
        html_parts.append(f'<div id="{scope_id}" class="xp-article-container">')
        
        # Header del artículo
        html_parts.append(self._generate_header(article, styles))
        
        # Cuerpo del artículo con imágenes intercaladas
        html_parts.append(self._generate_body(article, styles, image_mode))
        
        # Footer de sección
        html_parts.append(self._generate_footer(article, styles))
        
        html_parts.append('</div>')
        
        # Script de animaciones
        if styles['animation_enabled']:
            html_parts.append(self._generate_animations_script(scope_id))
        
        return '\n'.join(html_parts)

    def _compute_styles(self, article: dict, options: dict, ai_analysis: dict = None) -> dict:
        """Calcula los estilos basados en el análisis del artículo."""
        # Color de fondo principal
        bg_color = article.get('primary_background', '#ffffff')
        
        # Colores de acento
        accent_colors = []
        if article.get('colors', {}).get('accent_colors'):
            accent_colors = [c for c in article['colors']['accent_colors'] 
                          if c != '#000000' and c != '#ffffff' and c != bg_color]
        
        # Color principal de acento (el más usado que no sea negro ni blanco)
        primary_accent = accent_colors[0] if accent_colors else '#1a7ab5'
        
        # Si hay análisis de IA, usar sus sugerencias
        if ai_analysis:
            if ai_analysis.get('primary_color'):
                primary_accent = ai_analysis['primary_color']
            if ai_analysis.get('background_color'):
                bg_color = ai_analysis['background_color']

        # Opciones del usuario override
        if options.get('primary_color'):
            primary_accent = options['primary_color']
        if options.get('background_color'):
            bg_color = options['background_color']

        # Determinar si el fondo es oscuro para ajustar texto
        text_color = '#333333'
        if self._is_dark_color(bg_color):
            text_color = '#f0f0f0'

        # Si el fondo es blanco pero la revista usa un color claro, aplicar un tinte
        if bg_color in ('#ffffff', '#fefefe', '#fdfdfd'):
            # Crear un tinte suave basado en el color accent
            bg_color = self._create_tint(primary_accent, 0.95)

        return {
            'background_color': bg_color,
            'primary_accent': primary_accent,
            'secondary_accent': accent_colors[1] if len(accent_colors) > 1 else self._lighten_color(primary_accent, 0.7),
            'text_color': text_color,
            'heading_color': primary_accent if not self._is_dark_color(bg_color) else '#ffffff',
            'highlight_bg': self._lighten_color(primary_accent, 0.85),
            'highlight_border': primary_accent,
            'animation_enabled': options.get('animations', True)
        }

    def _generate_css(self, scope_id: str, styles: dict, article: dict) -> str:
        """Genera el CSS encapsulado."""
        return f'''<style>
#{scope_id} {{
    --xp-bg: {styles['background_color']};
    --xp-accent: {styles['primary_accent']};
    --xp-accent-light: {styles['secondary_accent']};
    --xp-text: {styles['text_color']};
    --xp-heading: {styles['heading_color']};
    --xp-highlight-bg: {styles['highlight_bg']};
    --xp-highlight-border: {styles['highlight_border']};
}}

#{scope_id}.xp-article-container {{
    font-family: 'Montserrat', sans-serif;
    background-color: var(--xp-bg);
    color: var(--xp-text);
    padding: 40px 20px;
    max-width: 900px;
    margin: 0 auto;
    line-height: 1.7;
    overflow: hidden;
}}

#{scope_id} .xp-section-tag {{
    font-family: 'Montserrat', sans-serif;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--xp-accent);
    margin-bottom: 10px;
    padding-left: 15px;
    border-left: 3px solid var(--xp-accent);
}}

#{scope_id} .xp-article-header {{
    margin-bottom: 40px;
    padding-bottom: 30px;
    border-bottom: 1px solid rgba(0,0,0,0.08);
}}

#{scope_id} .xp-article-title {{
    font-family: 'Times New Roman', Georgia, serif;
    font-size: clamp(24px, 4vw, 36px);
    font-weight: 700;
    font-style: italic;
    color: var(--xp-heading);
    line-height: 1.3;
    margin: 15px 0;
}}

#{scope_id} .xp-article-author {{
    font-family: 'Montserrat', sans-serif;
    font-size: 13px;
    font-weight: 500;
    color: var(--xp-text);
    opacity: 0.7;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

#{scope_id} .xp-body-text {{
    font-family: 'Montserrat', sans-serif;
    font-size: 15px;
    line-height: 1.8;
    margin-bottom: 20px;
    text-align: justify;
}}

#{scope_id} .xp-subheading {{
    font-family: 'Montserrat', sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: var(--xp-heading);
    margin: 35px 0 15px;
    line-height: 1.3;
}}

#{scope_id} .xp-highlight {{
    font-family: 'Times New Roman', Georgia, serif;
    font-size: 20px;
    font-style: italic;
    line-height: 1.5;
    color: var(--xp-accent);
    padding: 25px 30px;
    margin: 35px 0;
    border-left: 4px solid var(--xp-highlight-border);
    background: var(--xp-highlight-bg);
    border-radius: 0 8px 8px 0;
    position: relative;
}}

#{scope_id} .xp-highlight::before {{
    content: '\\201C';
    font-size: 60px;
    position: absolute;
    top: -10px;
    left: 10px;
    color: var(--xp-accent);
    opacity: 0.3;
    font-family: Georgia, serif;
}}

#{scope_id} .xp-image-container {{
    margin: 30px 0;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}}

#{scope_id} .xp-image-container.xp-img-left {{
    float: left;
    width: 45%;
    margin-right: 30px;
    margin-bottom: 15px;
}}

#{scope_id} .xp-image-container.xp-img-right {{
    float: right;
    width: 45%;
    margin-left: 30px;
    margin-bottom: 15px;
}}

#{scope_id} .xp-image-container.xp-img-center {{
    width: 100%;
    clear: both;
}}

#{scope_id} .xp-image-container img {{
    width: 100%;
    height: auto;
    display: block;
}}

#{scope_id} .xp-clearfix {{
    clear: both;
}}

#{scope_id} .xp-article-footer {{
    margin-top: 40px;
    padding-top: 20px;
    border-top: 2px solid var(--xp-accent);
    text-align: center;
    font-size: 12px;
    color: var(--xp-text);
    opacity: 0.6;
}}

/* Animaciones */
#{scope_id} .xp-fade-up {{
    opacity: 0;
    transform: translateY(30px);
    transition: opacity 0.8s ease, transform 0.8s ease;
}}

#{scope_id} .xp-fade-up.xp-visible {{
    opacity: 1;
    transform: translateY(0);
}}

#{scope_id} .xp-fade-left {{
    opacity: 0;
    transform: translateX(-40px);
    transition: opacity 0.8s ease, transform 0.8s ease;
}}

#{scope_id} .xp-fade-left.xp-visible {{
    opacity: 1;
    transform: translateX(0);
}}

#{scope_id} .xp-fade-right {{
    opacity: 0;
    transform: translateX(40px);
    transition: opacity 0.8s ease, transform 0.8s ease;
}}

#{scope_id} .xp-fade-right.xp-visible {{
    opacity: 1;
    transform: translateX(0);
}}

/* Responsive */
@media (max-width: 768px) {{
    #{scope_id}.xp-article-container {{
        padding: 25px 15px;
    }}
    
    #{scope_id} .xp-image-container.xp-img-left,
    #{scope_id} .xp-image-container.xp-img-right {{
        float: none;
        width: 100%;
        margin: 20px 0;
    }}
    
    #{scope_id} .xp-article-title {{
        font-size: 22px;
    }}
    
    #{scope_id} .xp-highlight {{
        font-size: 17px;
        padding: 20px;
    }}
}}
</style>'''

    def _generate_header(self, article: dict, styles: dict) -> str:
        """Genera el header del artículo."""
        parts = []
        parts.append('  <div class="xp-article-header xp-fade-up">')
        
        # Sección/categoría
        if article.get('section'):
            parts.append(f'    <div class="xp-section-tag">{article["section"]}</div>')
        
        # Título
        if article.get('title'):
            title = self._clean_text(article['title'])
            parts.append(f'    <h1 class="xp-article-title">{title}</h1>')
        
        # Subtítulo
        if article.get('subtitle'):
            parts.append(f'    <p class="xp-article-subtitle">{article["subtitle"]}</p>')
        
        # Autor
        if article.get('author'):
            parts.append(f'    <p class="xp-article-author">{article["author"]}</p>')
        
        parts.append('  </div>')
        return '\n'.join(parts)

    def _generate_body(self, article: dict, styles: dict, image_mode: str = 'base64') -> str:
        """Genera el cuerpo del artículo con texto, imágenes y destacados intercalados."""
        parts = []
        parts.append('  <div class="xp-article-body">')
        
        text_blocks = article.get('text_blocks', [])
        images = article.get('images', [])
        highlights = article.get('highlights', [])
        
        # Distribuir imágenes y destacados entre los bloques de texto
        img_interval = max(1, len(text_blocks) // (len(images) + 1)) if images else 999
        highlight_interval = max(1, len(text_blocks) // (len(highlights) + 1)) if highlights else 999
        
        img_idx = 0
        highlight_idx = 0
        animation_counter = 0
        
        for i, block in enumerate(text_blocks):
            # Insertar imagen si corresponde
            if images and img_idx < len(images) and i > 0 and i % img_interval == 0:
                img = images[img_idx]
                anim_class = 'xp-fade-left' if img['position'] == 'left' else 'xp-fade-right'
                if img['position'] == 'center':
                    anim_class = 'xp-fade-up'
                
                img_src = self._get_image_src(img, img_idx, image_mode)
                
                parts.append(f'    <div class="xp-image-container xp-img-{img["position"]} {anim_class}" style="transition-delay: {animation_counter * 0.1}s">')
                parts.append(f'      <img src="{img_src}" alt="{self._clean_text(article.get("title", "Imagen del artículo"))}" loading="lazy">')
                parts.append('    </div>')
                img_idx += 1
                animation_counter += 1
            
            # Insertar destacado/balazo si corresponde
            if highlights and highlight_idx < len(highlights) and i > 0 and i % highlight_interval == 0:
                h = highlights[highlight_idx]
                parts.append(f'    <blockquote class="xp-highlight xp-fade-up" style="transition-delay: {animation_counter * 0.1}s">')
                parts.append(f'      {self._clean_text(h["text"])}')
                parts.append('    </blockquote>')
                highlight_idx += 1
                animation_counter += 1
            
            # Bloque de texto
            text = self._clean_text(block.get('text', ''))
            if not text:
                continue
                
            if block.get('is_heading'):
                parts.append(f'    <h2 class="xp-subheading xp-fade-up" style="transition-delay: {animation_counter * 0.1}s">{text}</h2>')
            else:
                parts.append(f'    <p class="xp-body-text xp-fade-up" style="transition-delay: {animation_counter * 0.1}s">{text}</p>')
            
            animation_counter += 1
        
        # Imágenes restantes
        while img_idx < len(images):
            img = images[img_idx]
            anim_class = 'xp-fade-left' if img['position'] == 'left' else 'xp-fade-right'
            img_src = self._get_image_src(img, img_idx, image_mode)
            parts.append(f'    <div class="xp-image-container xp-img-{img["position"]} {anim_class}" style="transition-delay: {animation_counter * 0.1}s">')
            parts.append(f'      <img src="{img_src}" alt="{self._clean_text(article.get("title", "Imagen"))}" loading="lazy">')
            parts.append('    </div>')
            img_idx += 1
            animation_counter += 1
        
        # Destacados restantes
        while highlight_idx < len(highlights):
            h = highlights[highlight_idx]
            parts.append(f'    <blockquote class="xp-highlight xp-fade-up" style="transition-delay: {animation_counter * 0.1}s">')
            parts.append(f'      {self._clean_text(h["text"])}')
            parts.append('    </blockquote>')
            highlight_idx += 1
            animation_counter += 1
        
        parts.append('    <div class="xp-clearfix"></div>')
        parts.append('  </div>')
        return '\n'.join(parts)

    def _get_image_src(self, img: dict, index: int, mode: str) -> str:
        """Retorna el src de la imagen según el modo."""
        if mode == 'url':
            # Placeholder URL para que el usuario reemplace con la URL de WordPress
            return f'#IMAGEN_{index + 1}_URL_AQUI'
        else:
            # Base64 embebido
            return f"data:image/{img.get('ext', 'png')};base64,{img.get('data', '')}"

    def _generate_footer(self, article: dict, styles: dict) -> str:
        """Genera el footer del artículo."""
        section = article.get('section', '')
        return f'''  <div class="xp-article-footer xp-fade-up">
    <span>Xpert Pharma | Innovación y Salud | {section}</span>
  </div>'''

    def _generate_animations_script(self, scope_id: str) -> str:
        """Genera el JavaScript para las animaciones de scroll."""
        return f'''<script>
(function() {{
    const container = document.getElementById('{scope_id}');
    if (!container) return;
    
    const observer = new IntersectionObserver((entries) => {{
        entries.forEach(entry => {{
            if (entry.isIntersecting) {{
                entry.target.classList.add('xp-visible');
            }}
        }});
    }}, {{
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    }});
    
    container.querySelectorAll('.xp-fade-up, .xp-fade-left, .xp-fade-right').forEach(el => {{
        observer.observe(el);
    }});
}})();
</script>'''

    def _clean_text(self, text: str) -> str:
        """Limpia texto extraído del PDF."""
        # Remover saltos de línea innecesarios
        text = re.sub(r'\s+', ' ', text)
        # Remover caracteres especiales problemáticos
        text = text.replace('\x00', '')
        # Trim
        return text.strip()

    def _is_dark_color(self, hex_color: str) -> bool:
        """Determina si un color es oscuro."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            return False
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance < 0.5

    def _lighten_color(self, hex_color: str, factor: float = 0.9) -> str:
        """Aclara un color hex."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            return '#f5f5f5'
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return f'#{r:02x}{g:02x}{b:02x}'

    def _create_tint(self, hex_color: str, lightness: float = 0.95) -> str:
        """Crea un tinte muy claro de un color (para fondos)."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            return '#f8f9fa'
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        # Mezclar con blanco al porcentaje indicado
        r = int(255 * lightness + r * (1 - lightness))
        g = int(255 * lightness + g * (1 - lightness))
        b = int(255 * lightness + b * (1 - lightness))
        return f'#{min(r,255):02x}{min(g,255):02x}{min(b,255):02x}'
