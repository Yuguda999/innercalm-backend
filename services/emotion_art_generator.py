"""
Emotion art generator service for creating SVG emotion portraits.
"""
import random
import math
import base64
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import colorsys

from models.emotion_art import ArtStyle, ArtStatus
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class EmotionArtGenerator:
    """Service for generating SVG emotion portraits based on mood."""

    def __init__(self):
        self.openai_service = OpenAIService()

        # Color palettes for different emotions
        self.emotion_colors = {
            "joy": ["#FFD700", "#FFA500", "#FF6347", "#FF69B4", "#FFFF00"],
            "sadness": ["#4169E1", "#1E90FF", "#87CEEB", "#B0C4DE", "#708090"],
            "anger": ["#DC143C", "#B22222", "#8B0000", "#FF4500", "#FF6347"],
            "fear": ["#800080", "#4B0082", "#483D8B", "#6A5ACD", "#9370DB"],
            "surprise": ["#FF1493", "#FF69B4", "#DA70D6", "#BA55D3", "#9932CC"],
            "disgust": ["#556B2F", "#6B8E23", "#808000", "#9ACD32", "#ADFF2F"],
            "neutral": ["#696969", "#778899", "#A9A9A9", "#C0C0C0", "#D3D3D3"]
        }

        # Art style configurations
        self.style_configs = {
            ArtStyle.ABSTRACT: {
                "shapes": ["circle", "ellipse", "path", "polygon"],
                "complexity_multiplier": 1.0,
                "organic_factor": 0.8
            },
            ArtStyle.GEOMETRIC: {
                "shapes": ["rect", "polygon", "circle"],
                "complexity_multiplier": 0.7,
                "organic_factor": 0.2
            },
            ArtStyle.ORGANIC: {
                "shapes": ["path", "ellipse", "circle"],
                "complexity_multiplier": 1.2,
                "organic_factor": 1.0
            },
            ArtStyle.MINIMALIST: {
                "shapes": ["circle", "rect", "line"],
                "complexity_multiplier": 0.4,
                "organic_factor": 0.3
            },
            ArtStyle.EXPRESSIVE: {
                "shapes": ["path", "polygon", "ellipse", "circle"],
                "complexity_multiplier": 1.5,
                "organic_factor": 0.9
            }
        }

    async def generate_emotion_art(
        self,
        emotion_data: Dict[str, float],
        art_style: ArtStyle = ArtStyle.ABSTRACT,
        complexity_level: int = 3,
        color_preferences: Optional[List[str]] = None,
        canvas_size: Tuple[int, int] = (400, 400)
    ) -> Dict[str, Any]:
        """
        Generate SVG emotion art based on emotion data.

        Args:
            emotion_data: Dictionary of emotion scores
            art_style: Style of art to generate
            complexity_level: Complexity level (1-5)
            color_preferences: Optional color preferences
            canvas_size: Canvas dimensions

        Returns:
            Dictionary containing SVG content and metadata
        """
        try:
            # Determine dominant emotion and intensity
            dominant_emotion = max(emotion_data, key=emotion_data.get) if emotion_data else "neutral"
            emotional_intensity = max(emotion_data.values()) if emotion_data else 0.5

            # Generate color palette
            color_palette = self._generate_color_palette(
                dominant_emotion, emotional_intensity, color_preferences
            )

            # Generate SVG content
            svg_content = self._create_svg_art(
                emotion_data, dominant_emotion, emotional_intensity,
                art_style, complexity_level, color_palette, canvas_size
            )

            # Convert to data URL
            svg_data_url = self._svg_to_data_url(svg_content)

            # Generate unique seed for reproducibility
            generation_seed = self._generate_seed(emotion_data, art_style, complexity_level)

            return {
                "svg_content": svg_content,
                "svg_data_url": svg_data_url,
                "color_palette": color_palette,
                "dominant_emotion": dominant_emotion,
                "emotional_intensity": emotional_intensity,
                "generation_seed": generation_seed,
                "generation_parameters": {
                    "art_style": art_style.value,
                    "complexity_level": complexity_level,
                    "canvas_size": canvas_size,
                    "emotion_data": emotion_data
                },
                "status": ArtStatus.COMPLETED.value
            }

        except Exception as e:
            logger.error(f"Error generating emotion art: {e}")
            return {
                "status": ArtStatus.FAILED.value,
                "error": str(e)
            }

    def _generate_color_palette(
        self,
        dominant_emotion: str,
        intensity: float,
        preferences: Optional[List[str]] = None
    ) -> List[str]:
        """Generate a color palette based on emotion and intensity."""
        base_colors = self.emotion_colors.get(dominant_emotion, self.emotion_colors["neutral"])

        # Adjust colors based on intensity
        palette = []
        for color in base_colors[:4]:  # Use top 4 colors
            # Convert hex to RGB
            rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))

            # Adjust saturation and brightness based on intensity
            hsv = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)

            # Increase saturation and brightness for higher intensity
            new_saturation = min(1.0, hsv[1] + (intensity - 0.5) * 0.3)
            new_value = min(1.0, hsv[2] + (intensity - 0.5) * 0.2)

            new_rgb = colorsys.hsv_to_rgb(hsv[0], new_saturation, new_value)
            new_hex = "#{:02x}{:02x}{:02x}".format(
                int(new_rgb[0] * 255),
                int(new_rgb[1] * 255),
                int(new_rgb[2] * 255)
            )
            palette.append(new_hex)

        # Add complementary colors for contrast
        if len(palette) >= 2:
            # Generate complementary color
            main_rgb = tuple(int(palette[0][i:i+2], 16) for i in (1, 3, 5))
            main_hsv = colorsys.rgb_to_hsv(main_rgb[0]/255, main_rgb[1]/255, main_rgb[2]/255)

            # Complementary hue (opposite on color wheel)
            comp_hue = (main_hsv[0] + 0.5) % 1.0
            comp_rgb = colorsys.hsv_to_rgb(comp_hue, main_hsv[1] * 0.7, main_hsv[2] * 0.8)
            comp_hex = "#{:02x}{:02x}{:02x}".format(
                int(comp_rgb[0] * 255),
                int(comp_rgb[1] * 255),
                int(comp_rgb[2] * 255)
            )
            palette.append(comp_hex)

        return palette

    def _create_svg_art(
        self,
        emotion_data: Dict[str, float],
        dominant_emotion: str,
        intensity: float,
        art_style: ArtStyle,
        complexity_level: int,
        color_palette: List[str],
        canvas_size: Tuple[int, int]
    ) -> str:
        """Create the actual SVG art content."""
        width, height = canvas_size
        style_config = self.style_configs[art_style]

        # Calculate number of elements based on complexity
        base_elements = 5
        num_elements = int(base_elements * complexity_level * style_config["complexity_multiplier"])

        # Start SVG
        svg_parts = [
            f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
            self._create_background_gradient(color_palette, width, height),
        ]

        # Generate elements based on emotions
        for emotion, score in emotion_data.items():
            if score > 0.1:  # Only include emotions with significant scores
                elements = self._create_emotion_elements(
                    emotion, score, intensity, art_style, style_config,
                    color_palette, width, height, num_elements
                )
                svg_parts.extend(elements)

        # Add central focal point
        focal_point = self._create_focal_point(
            dominant_emotion, intensity, color_palette, width, height, art_style
        )
        svg_parts.append(focal_point)

        # Close SVG
        svg_parts.append('</svg>')

        return '\n'.join(svg_parts)

    def _create_background_gradient(self, colors: List[str], width: int, height: int) -> str:
        """Create a background gradient."""
        if len(colors) < 2:
            return f'<rect width="{width}" height="{height}" fill="{colors[0] if colors else "#f0f0f0"}"/>'

        gradient_id = "bgGradient"
        gradient = f'''
        <defs>
            <radialGradient id="{gradient_id}" cx="50%" cy="50%" r="70%">
                <stop offset="0%" stop-color="{colors[0]}" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="{colors[1]}" stop-opacity="0.1"/>
            </radialGradient>
        </defs>
        <rect width="{width}" height="{height}" fill="url(#{gradient_id})"/>
        '''
        return gradient

    def _create_emotion_elements(
        self,
        emotion: str,
        score: float,
        intensity: float,
        art_style: ArtStyle,
        style_config: Dict[str, Any],
        colors: List[str],
        width: int,
        height: int,
        max_elements: int
    ) -> List[str]:
        """Create SVG elements representing a specific emotion."""
        elements = []
        num_elements = max(1, int(score * max_elements * 0.3))

        emotion_colors = self.emotion_colors.get(emotion, colors)

        for i in range(num_elements):
            # Random position
            x = random.randint(int(width * 0.1), int(width * 0.9))
            y = random.randint(int(height * 0.1), int(height * 0.9))

            # Size based on emotion score and intensity
            base_size = 20 + (score * intensity * 50)
            size = base_size + random.uniform(-10, 10)

            # Choose shape based on emotion and style
            shape = self._choose_shape_for_emotion(emotion, art_style, style_config)
            color = random.choice(emotion_colors if emotion_colors else colors)

            # Create element
            element = self._create_shape_element(
                shape, x, y, size, color, score, style_config["organic_factor"]
            )
            elements.append(element)

        return elements

    def _choose_shape_for_emotion(
        self,
        emotion: str,
        art_style: ArtStyle,
        style_config: Dict[str, Any]
    ) -> str:
        """Choose appropriate shape for an emotion."""
        emotion_shapes = {
            "joy": ["circle", "star", "heart"],
            "sadness": ["teardrop", "ellipse", "wave"],
            "anger": ["triangle", "zigzag", "spike"],
            "fear": ["jagged", "spiral", "broken"],
            "surprise": ["burst", "star", "explosion"],
            "disgust": ["irregular", "blob", "twisted"],
            "neutral": ["circle", "rect", "ellipse"]
        }

        available_shapes = style_config["shapes"]
        emotion_preferred = emotion_shapes.get(emotion, ["circle"])

        # Find intersection of available and preferred shapes
        compatible_shapes = [s for s in emotion_preferred if s in available_shapes]

        if compatible_shapes:
            return random.choice(compatible_shapes)
        else:
            return random.choice(available_shapes)

    def _create_shape_element(
        self,
        shape: str,
        x: int,
        y: int,
        size: float,
        color: str,
        opacity_factor: float,
        organic_factor: float
    ) -> str:
        """Create an SVG element for a specific shape."""
        opacity = min(0.8, 0.3 + opacity_factor * 0.5)

        if shape == "circle":
            radius = size / 2
            return f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}" opacity="{opacity}"/>'

        elif shape == "ellipse":
            rx = size / 2 + random.uniform(-5, 5) * organic_factor
            ry = size / 3 + random.uniform(-3, 3) * organic_factor
            return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{color}" opacity="{opacity}"/>'

        elif shape == "rect":
            width = size + random.uniform(-10, 10) * organic_factor
            height = size * 0.7 + random.uniform(-5, 5) * organic_factor
            return f'<rect x="{x-width/2}" y="{y-height/2}" width="{width}" height="{height}" fill="{color}" opacity="{opacity}"/>'

        elif shape == "polygon":
            points = self._generate_polygon_points(x, y, size, 6, organic_factor)
            return f'<polygon points="{points}" fill="{color}" opacity="{opacity}"/>'

        elif shape == "path":
            path_data = self._generate_organic_path(x, y, size, organic_factor)
            return f'<path d="{path_data}" fill="{color}" opacity="{opacity}"/>'

        elif shape == "star":
            points = self._generate_star_points(x, y, size, 5)
            return f'<polygon points="{points}" fill="{color}" opacity="{opacity}"/>'

        elif shape == "heart":
            path_data = self._generate_heart_path(x, y, size)
            return f'<path d="{path_data}" fill="{color}" opacity="{opacity}"/>'

        elif shape == "teardrop":
            path_data = self._generate_teardrop_path(x, y, size)
            return f'<path d="{path_data}" fill="{color}" opacity="{opacity}"/>'

        else:
            # Default to circle
            radius = size / 2
            return f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}" opacity="{opacity}"/>'

    def _generate_polygon_points(
        self,
        cx: int,
        cy: int,
        size: float,
        sides: int,
        organic_factor: float
    ) -> str:
        """Generate points for a polygon."""
        points = []
        angle_step = 2 * math.pi / sides

        for i in range(sides):
            angle = i * angle_step
            radius = size / 2 + random.uniform(-5, 5) * organic_factor
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            points.append(f"{x},{y}")

        return " ".join(points)

    def _generate_star_points(self, cx: int, cy: int, size: float, points: int) -> str:
        """Generate points for a star shape."""
        outer_radius = size / 2
        inner_radius = outer_radius * 0.4
        angle_step = math.pi / points

        star_points = []
        for i in range(points * 2):
            angle = i * angle_step
            radius = outer_radius if i % 2 == 0 else inner_radius
            x = cx + radius * math.cos(angle - math.pi / 2)
            y = cy + radius * math.sin(angle - math.pi / 2)
            star_points.append(f"{x},{y}")

        return " ".join(star_points)

    def _generate_heart_path(self, cx: int, cy: int, size: float) -> str:
        """Generate path data for a heart shape."""
        scale = size / 40
        return f"M {cx} {cy + 5*scale} C {cx} {cy + 2*scale}, {cx - 10*scale} {cy - 5*scale}, {cx - 10*scale} {cy - 10*scale} C {cx - 10*scale} {cy - 15*scale}, {cx} {cy - 15*scale}, {cx} {cy - 10*scale} C {cx} {cy - 15*scale}, {cx + 10*scale} {cy - 15*scale}, {cx + 10*scale} {cy - 10*scale} C {cx + 10*scale} {cy - 5*scale}, {cx} {cy + 2*scale}, {cx} {cy + 5*scale} Z"

    def _generate_teardrop_path(self, cx: int, cy: int, size: float) -> str:
        """Generate path data for a teardrop shape."""
        radius = size / 2
        return f"M {cx} {cy - radius} C {cx + radius} {cy - radius}, {cx + radius} {cy + radius}, {cx} {cy + radius} C {cx - radius} {cy + radius}, {cx - radius} {cy - radius}, {cx} {cy - radius} Z"

    def _generate_organic_path(self, cx: int, cy: int, size: float, organic_factor: float) -> str:
        """Generate an organic, flowing path."""
        radius = size / 2
        num_points = 8
        angle_step = 2 * math.pi / num_points

        path_parts = []
        for i in range(num_points):
            angle = i * angle_step
            r = radius + random.uniform(-radius * 0.3, radius * 0.3) * organic_factor
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)

            if i == 0:
                path_parts.append(f"M {x} {y}")
            else:
                # Use quadratic curves for organic feel
                prev_angle = (i - 1) * angle_step
                prev_r = radius + random.uniform(-radius * 0.2, radius * 0.2) * organic_factor
                ctrl_x = cx + prev_r * 1.2 * math.cos(prev_angle + angle_step / 2)
                ctrl_y = cy + prev_r * 1.2 * math.sin(prev_angle + angle_step / 2)
                path_parts.append(f"Q {ctrl_x} {ctrl_y} {x} {y}")

        path_parts.append("Z")
        return " ".join(path_parts)

    def _create_focal_point(
        self,
        dominant_emotion: str,
        intensity: float,
        colors: List[str],
        width: int,
        height: int,
        art_style: ArtStyle
    ) -> str:
        """Create a central focal point for the artwork."""
        cx = width // 2
        cy = height // 2
        size = 30 + intensity * 40

        main_color = colors[0] if colors else "#888888"
        accent_color = colors[1] if len(colors) > 1 else main_color

        if art_style == ArtStyle.MINIMALIST:
            return f'<circle cx="{cx}" cy="{cy}" r="{size/2}" fill="{main_color}" opacity="0.6"/>'

        elif art_style == ArtStyle.GEOMETRIC:
            return f'<rect x="{cx-size/2}" y="{cy-size/2}" width="{size}" height="{size}" fill="{main_color}" opacity="0.7" transform="rotate(45 {cx} {cy})"/>'

        else:
            # Create a complex focal point with multiple layers
            gradient_id = "focalGradient"
            return f'''
            <defs>
                <radialGradient id="{gradient_id}" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stop-color="{accent_color}" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="{main_color}" stop-opacity="0.4"/>
                </radialGradient>
            </defs>
            <circle cx="{cx}" cy="{cy}" r="{size}" fill="url(#{gradient_id})"/>
            <circle cx="{cx}" cy="{cy}" r="{size*0.6}" fill="{main_color}" opacity="0.3"/>
            '''

    def _svg_to_data_url(self, svg_content: str) -> str:
        """Convert SVG content to data URL."""
        svg_bytes = svg_content.encode('utf-8')
        svg_b64 = base64.b64encode(svg_bytes).decode('utf-8')
        return f"data:image/svg+xml;base64,{svg_b64}"

    def _generate_seed(
        self,
        emotion_data: Dict[str, float],
        art_style: ArtStyle,
        complexity_level: int
    ) -> str:
        """Generate a unique seed for reproducible art generation."""
        emotion_str = "_".join([f"{k}:{v:.2f}" for k, v in sorted(emotion_data.items())])
        return f"{art_style.value}_{complexity_level}_{hash(emotion_str) % 10000}"

    async def customize_art(
        self,
        original_svg: str,
        customization_type: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Apply customizations to existing artwork."""
        try:
            if customization_type == "color":
                return self._customize_colors(original_svg, parameters)
            elif customization_type == "shape":
                return self._customize_shapes(original_svg, parameters)
            elif customization_type == "style":
                return self._customize_style(original_svg, parameters)
            elif customization_type == "composition":
                return self._customize_composition(original_svg, parameters)
            else:
                return original_svg

        except Exception as e:
            logger.error(f"Error customizing art: {e}")
            return original_svg

    def _customize_colors(self, svg: str, parameters: Dict[str, Any]) -> str:
        """Customize colors in the artwork."""
        new_colors = parameters.get("colors", [])
        if not new_colors:
            return svg

        # Simple color replacement (in a real implementation, this would be more sophisticated)
        customized_svg = svg
        for i, color in enumerate(new_colors):
            if i < len(new_colors):
                # Replace colors in the SVG (simplified approach)
                customized_svg = customized_svg.replace(f'fill="#{i:06x}"', f'fill="{color}"')

        return customized_svg

    def _customize_shapes(self, svg: str, parameters: Dict[str, Any]) -> str:
        """Customize shapes in the artwork."""
        # This would involve more complex SVG manipulation
        return svg

    def _customize_style(self, svg: str, parameters: Dict[str, Any]) -> str:
        """Customize the overall style of the artwork."""
        # This would involve style transformations
        return svg

    def _customize_composition(self, svg: str, parameters: Dict[str, Any]) -> str:
        """Customize the composition of the artwork."""
        # This would involve layout changes
        return svg
