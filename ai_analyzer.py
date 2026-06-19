"""
Módulo de análisis con IA (OpenAI) para mejorar la detección de estilos
y la generación de HTML cuando está disponible.
Este módulo es OPCIONAL - la app funciona sin API key.
"""

import os
import base64
import json

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class AIAnalyzer:
    """Usa OpenAI para analizar el estilo visual de artículos."""

    def __init__(self):
        self.client = None
        if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            self.client = OpenAI()

    def is_available(self) -> bool:
        """Verifica si el analizador de IA está disponible."""
        return self.client is not None

    def analyze_article_style(self, article: dict) -> dict:
        """
        Analiza el estilo visual de un artículo usando GPT-4 Vision.
        Retorna sugerencias de colores y layout.
        """
        if not self.is_available():
            return {}

        # Si hay thumbnail, usarlo para análisis visual
        thumbnail = article.get('thumbnail', '')
        if not thumbnail:
            return self._analyze_from_text(article)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un experto en diseño editorial y web. 
                        Analiza la imagen de esta página de revista y extrae:
                        1. Color de fondo principal (hex)
                        2. Color de acento principal (hex) 
                        3. Si el layout es de 1 o 2 columnas
                        4. Posición de las imágenes (left, right, center)
                        5. Si hay elementos decorativos especiales
                        Responde SOLO en JSON."""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Analiza el estilo visual de esta página de revista. Sección: {article.get('section', 'N/A')}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{thumbnail}",
                                    "detail": "low"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.3
            )

            result_text = response.choices[0].message.content
            # Limpiar posible markdown
            result_text = result_text.strip()
            if result_text.startswith('```'):
                result_text = result_text.split('\n', 1)[1]
                result_text = result_text.rsplit('```', 1)[0]

            result = json.loads(result_text)
            
            return {
                'primary_color': result.get('color_acento', result.get('primary_accent', '')),
                'background_color': result.get('color_fondo', result.get('background_color', '')),
                'layout': result.get('layout', 'single'),
                'image_position': result.get('posicion_imagenes', 'center'),
                'decorative_elements': result.get('elementos_decorativos', [])
            }

        except Exception as e:
            print(f"[AI Analyzer] Error: {e}")
            return {}

    def _analyze_from_text(self, article: dict) -> dict:
        """Análisis basado solo en texto cuando no hay thumbnail."""
        if not self.is_available():
            return {}

        colors = article.get('colors', {})
        section = article.get('section', '')

        # Mapeo de secciones a colores conocidos de Xpert Pharma
        section_colors = {
            'PORTADA': {'primary_color': '#1a7ab5', 'background_color': '#e8f4f8'},
            'MARCA LÍDER': {'primary_color': '#2c3e50', 'background_color': '#ffffff'},
            'COLABORACIÓN DEL EXPERTO': {'primary_color': '#27ae60', 'background_color': '#f8fdf8'},
            'PANORAMA MÉDICO': {'primary_color': '#8e44ad', 'background_color': '#faf5fd'},
            'AULA MÉDICA': {'primary_color': '#e74c3c', 'background_color': '#fdf5f5'},
            'GALENOCOTIDIANO': {'primary_color': '#f39c12', 'background_color': '#fef9f0'},
            'DE LA VID A LA COPA': {'primary_color': '#722f37', 'background_color': '#fdf5f6'},
            'NUMERALIA': {'primary_color': '#16a085', 'background_color': '#f0faf8'},
            'AGENDA DE SALUD': {'primary_color': '#2980b9', 'background_color': '#f5f9fd'},
            'TECNOPÍLDORAS': {'primary_color': '#1abc9c', 'background_color': '#f0fdfa'},
            'FUERA DEL CONSULTORIO': {'primary_color': '#e67e22', 'background_color': '#fef6f0'},
            'AL PIE DE LA LETRA': {'primary_color': '#34495e', 'background_color': '#f8f9fa'},
        }

        return section_colors.get(section, {})

    def enhance_html(self, html: str, article: dict) -> str:
        """
        Usa IA para mejorar el HTML generado (opcional, para refinamiento).
        """
        if not self.is_available():
            return html
        
        # Por ahora retorna el HTML sin modificar
        # Se puede expandir para pedir mejoras específicas a GPT
        return html
