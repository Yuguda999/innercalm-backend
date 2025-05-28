"""
SVG illustration generator for recommendations.
Creates specific SVG illustrations based on recommendation content.
"""
import hashlib
import base64
from typing import Dict, Optional
from models.recommendation import RecommendationType


class SVGGenerator:
    """Generate SVG illustrations for recommendations."""

    def __init__(self):
        self.svg_templates = {
            RecommendationType.BREATHING_EXERCISE: self._breathing_svg_templates,
            RecommendationType.MINDFULNESS_PRACTICE: self._mindfulness_svg_templates,
            RecommendationType.JOURNALING_PROMPT: self._journaling_svg_templates,
            RecommendationType.COGNITIVE_REFRAMING: self._cognitive_svg_templates,
            RecommendationType.PHYSICAL_ACTIVITY: self._physical_svg_templates,
            RecommendationType.RELAXATION_TECHNIQUE: self._relaxation_svg_templates,
        }

    def generate_svg(self, recommendation_data: Dict) -> str:
        """
        Generate an SVG illustration for a recommendation.

        Args:
            recommendation_data: Dictionary containing recommendation details

        Returns:
            SVG string as data URL
        """
        rec_type = recommendation_data.get("type")
        title = recommendation_data.get("title", "")
        target_emotions = recommendation_data.get("target_emotions", [])

        # Get appropriate SVG template
        template_func = self.svg_templates.get(rec_type, self._default_svg_template)
        svg_content = template_func(title, target_emotions)

        # Convert to data URL
        svg_bytes = svg_content.encode('utf-8')
        svg_b64 = base64.b64encode(svg_bytes).decode('utf-8')
        return f"data:image/svg+xml;base64,{svg_b64}"

    def _breathing_svg_templates(self, title: str, emotions: list) -> str:
        """Generate SVG for breathing exercises."""
        # Different breathing patterns based on title
        if "4-7-8" in title:
            return self._create_478_breathing_svg()
        elif "grounding" in title.lower():
            return self._create_grounding_breathing_svg()
        else:
            return self._create_general_breathing_svg()

    def _create_478_breathing_svg(self) -> str:
        """Create 4-7-8 breathing pattern SVG."""
        return '''
        <svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="breathGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:1" />
                </linearGradient>
                <filter id="glow">
                    <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                    <feMerge>
                        <feMergeNode in="coloredBlur"/>
                        <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                </filter>
            </defs>

            <!-- Background -->
            <rect width="400" height="300" fill="#f8fafc"/>

            <!-- Central breathing circle -->
            <circle cx="200" cy="150" r="80" fill="url(#breathGradient)" opacity="0.3" filter="url(#glow)">
                <animate attributeName="r" values="60;100;60" dur="12s" repeatCount="indefinite"/>
                <animate attributeName="opacity" values="0.2;0.6;0.2" dur="12s" repeatCount="indefinite"/>
            </circle>

            <!-- Breathing pattern indicators -->
            <g transform="translate(200,150)">
                <!-- Inhale arc (4 counts) -->
                <path d="M -120,-120 A 120,120 0 0,1 120,-120" stroke="#3b82f6" stroke-width="4" fill="none" opacity="0.7"/>
                <text x="0" y="-140" text-anchor="middle" font-family="Arial" font-size="14" fill="#3b82f6">Inhale 4</text>

                <!-- Hold arc (7 counts) -->
                <path d="M 120,-120 A 120,120 0 0,1 120,120" stroke="#8b5cf6" stroke-width="4" fill="none" opacity="0.7"/>
                <text x="140" y="0" text-anchor="middle" font-family="Arial" font-size="14" fill="#8b5cf6">Hold 7</text>

                <!-- Exhale arc (8 counts) -->
                <path d="M 120,120 A 120,120 0 0,1 -120,120" stroke="#06b6d4" stroke-width="4" fill="none" opacity="0.7"/>
                <text x="0" y="155" text-anchor="middle" font-family="Arial" font-size="14" fill="#06b6d4">Exhale 8</text>
            </g>

            <!-- Floating particles for calm effect -->
            <circle cx="100" cy="80" r="3" fill="#3b82f6" opacity="0.4">
                <animate attributeName="cy" values="80;60;80" dur="4s" repeatCount="indefinite"/>
            </circle>
            <circle cx="320" cy="220" r="2" fill="#8b5cf6" opacity="0.4">
                <animate attributeName="cy" values="220;200;220" dur="6s" repeatCount="indefinite"/>
            </circle>
            <circle cx="80" cy="250" r="2.5" fill="#06b6d4" opacity="0.4">
                <animate attributeName="cy" values="250;230;250" dur="5s" repeatCount="indefinite"/>
            </circle>
        </svg>
        '''

    def _create_grounding_breathing_svg(self) -> str:
        """Create grounding breathing SVG."""
        return '''
        <svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <radialGradient id="groundGradient" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" style="stop-color:#10b981;stop-opacity:0.8" />
                    <stop offset="100%" style="stop-color:#059669;stop-opacity:0.3" />
                </radialGradient>
            </defs>

            <!-- Background -->
            <rect width="400" height="300" fill="#f0f9ff"/>

            <!-- Ground/Earth base -->
            <ellipse cx="200" cy="280" rx="180" ry="20" fill="#059669" opacity="0.3"/>

            <!-- Tree trunk (grounding symbol) -->
            <rect x="190" y="200" width="20" height="80" fill="#92400e" rx="10"/>

            <!-- Tree canopy with breathing animation -->
            <circle cx="200" cy="180" r="60" fill="url(#groundGradient)">
                <animate attributeName="r" values="55;65;55" dur="8s" repeatCount="indefinite"/>
            </circle>

            <!-- Roots (grounding) -->
            <g stroke="#059669" stroke-width="3" fill="none" opacity="0.6">
                <path d="M 190,280 Q 150,290 120,300"/>
                <path d="M 200,280 Q 200,295 200,310"/>
                <path d="M 210,280 Q 250,290 280,300"/>
            </g>

            <!-- Breathing rhythm indicators -->
            <g transform="translate(200,150)">
                <circle r="20" fill="none" stroke="#10b981" stroke-width="2" opacity="0.8">
                    <animate attributeName="r" values="15;30;15" dur="8s" repeatCount="indefinite"/>
                    <animate attributeName="opacity" values="0.8;0.3;0.8" dur="8s" repeatCount="indefinite"/>
                </circle>
            </g>

            <!-- Hand placement indicators -->
            <g transform="translate(120,120)">
                <ellipse rx="25" ry="35" fill="#3b82f6" opacity="0.2"/>
                <text x="0" y="50" text-anchor="middle" font-family="Arial" font-size="12" fill="#3b82f6">Chest</text>
            </g>
            <g transform="translate(280,180)">
                <ellipse rx="25" ry="35" fill="#8b5cf6" opacity="0.2"/>
                <text x="0" y="50" text-anchor="middle" font-family="Arial" font-size="12" fill="#8b5cf6">Belly</text>
            </g>
        </svg>
        '''

    def _create_general_breathing_svg(self) -> str:
        """Create general breathing SVG."""
        return '''
        <svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="breathFlow" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#06b6d4;stop-opacity:1" />
                    <stop offset="50%" style="stop-color:#3b82f6;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:1" />
                </linearGradient>
            </defs>

            <!-- Background -->
            <rect width="400" height="300" fill="#fefefe"/>

            <!-- Breathing waves -->
            <g opacity="0.6">
                <path d="M 50,150 Q 100,100 150,150 T 250,150 T 350,150" stroke="url(#breathFlow)" stroke-width="3" fill="none">
                    <animate attributeName="d" values="M 50,150 Q 100,100 150,150 T 250,150 T 350,150;M 50,150 Q 100,200 150,150 T 250,150 T 350,150;M 50,150 Q 100,100 150,150 T 250,150 T 350,150" dur="6s" repeatCount="indefinite"/>
                </path>
                <path d="M 50,170 Q 100,120 150,170 T 250,170 T 350,170" stroke="url(#breathFlow)" stroke-width="2" fill="none" opacity="0.5">
                    <animate attributeName="d" values="M 50,170 Q 100,120 150,170 T 250,170 T 350,170;M 50,170 Q 100,220 150,170 T 250,170 T 350,170;M 50,170 Q 100,120 150,170 T 250,170 T 350,170" dur="6s" repeatCount="indefinite" begin="1s"/>
                </path>
            </g>

            <!-- Central focus point -->
            <circle cx="200" cy="150" r="40" fill="url(#breathFlow)" opacity="0.3">
                <animate attributeName="r" values="30;50;30" dur="6s" repeatCount="indefinite"/>
            </circle>

            <!-- Breathing text -->
            <text x="200" y="150" text-anchor="middle" font-family="Arial" font-size="16" fill="#1f2937" font-weight="bold">Breathe</text>
        </svg>
        '''

    def _mindfulness_svg_templates(self, title: str, emotions: list) -> str:
        """Generate SVG for mindfulness practices."""
        if "loving-kindness" in title.lower():
            return self._create_loving_kindness_svg()
        else:
            return self._create_general_mindfulness_svg()

    def _create_loving_kindness_svg(self) -> str:
        """Create loving-kindness meditation SVG."""
        return '''
        <svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <radialGradient id="heartGradient" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" style="stop-color:#f472b6;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#ec4899;stop-opacity:0.6" />
                </radialGradient>
            </defs>

            <!-- Background -->
            <rect width="400" height="300" fill="#fdf2f8"/>

            <!-- Central heart -->
            <g transform="translate(200,150)">
                <path d="M 0,-20 C -20,-40 -50,-40 -50,-10 C -50,20 0,50 0,50 C 0,50 50,20 50,-10 C 50,-40 20,-40 0,-20 Z" fill="url(#heartGradient)">
                    <animate attributeName="transform" values="scale(1);scale(1.1);scale(1)" dur="4s" repeatCount="indefinite"/>
                </path>
            </g>

            <!-- Radiating love circles -->
            <circle cx="200" cy="150" r="80" fill="none" stroke="#f472b6" stroke-width="2" opacity="0.4">
                <animate attributeName="r" values="60;120;60" dur="8s" repeatCount="indefinite"/>
                <animate attributeName="opacity" values="0.6;0.1;0.6" dur="8s" repeatCount="indefinite"/>
            </circle>
            <circle cx="200" cy="150" r="100" fill="none" stroke="#ec4899" stroke-width="1" opacity="0.3">
                <animate attributeName="r" values="80;140;80" dur="10s" repeatCount="indefinite"/>
                <animate attributeName="opacity" values="0.5;0.1;0.5" dur="10s" repeatCount="indefinite"/>
            </circle>

            <!-- Floating hearts -->
            <g opacity="0.6">
                <path d="M 100,80 C 95,75 85,75 85,85 C 85,95 100,110 100,110 C 100,110 115,95 115,85 C 115,75 105,75 100,80 Z" fill="#f472b6">
                    <animate attributeName="transform" values="translate(0,0);translate(0,-20);translate(0,0)" dur="6s" repeatCount="indefinite"/>
                </path>
                <path d="M 320,220 C 315,215 305,215 305,225 C 305,235 320,250 320,250 C 320,250 335,235 335,225 C 335,215 325,215 320,220 Z" fill="#ec4899">
                    <animate attributeName="transform" values="translate(0,0);translate(0,-15);translate(0,0)" dur="8s" repeatCount="indefinite"/>
                </path>
            </g>

            <!-- Compassion text -->
            <text x="200" y="250" text-anchor="middle" font-family="Arial" font-size="14" fill="#be185d" font-style="italic">May I be kind to myself</text>
        </svg>
        '''

    def _create_general_mindfulness_svg(self) -> str:
        """Create general mindfulness SVG."""
        return '''
        <svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="mindfulGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#10b981;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#059669;stop-opacity:0.7" />
                </linearGradient>
            </defs>

            <!-- Background -->
            <rect width="400" height="300" fill="#f0fdf4"/>

            <!-- Meditation figure -->
            <g transform="translate(200,180)">
                <!-- Body -->
                <ellipse cx="0" cy="0" rx="30" ry="40" fill="url(#mindfulGradient)" opacity="0.8"/>
                <!-- Head -->
                <circle cx="0" cy="-60" r="25" fill="url(#mindfulGradient)" opacity="0.9"/>
                <!-- Arms in meditation pose -->
                <ellipse cx="-35" cy="-10" rx="15" ry="8" fill="url(#mindfulGradient)" opacity="0.7" transform="rotate(-30)"/>
                <ellipse cx="35" cy="-10" rx="15" ry="8" fill="url(#mindfulGradient)" opacity="0.7" transform="rotate(30)"/>
            </g>

            <!-- Mindfulness aura -->
            <circle cx="200" cy="150" r="100" fill="none" stroke="#10b981" stroke-width="1" opacity="0.3">
                <animate attributeName="r" values="80;120;80" dur="12s" repeatCount="indefinite"/>
                <animate attributeName="opacity" values="0.5;0.1;0.5" dur="12s" repeatCount="indefinite"/>
            </circle>

            <!-- Present moment indicators -->
            <g opacity="0.6">
                <circle cx="150" cy="100" r="4" fill="#10b981">
                    <animate attributeName="opacity" values="0.3;1;0.3" dur="3s" repeatCount="indefinite"/>
                </circle>
                <circle cx="250" cy="120" r="3" fill="#059669">
                    <animate attributeName="opacity" values="0.3;1;0.3" dur="4s" repeatCount="indefinite"/>
                </circle>
                <circle cx="180" cy="80" r="2" fill="#10b981">
                    <animate attributeName="opacity" values="0.3;1;0.3" dur="5s" repeatCount="indefinite"/>
                </circle>
            </g>
        </svg>
        '''

    def _journaling_svg_templates(self, title: str, emotions: list) -> str:
        """Generate SVG for journaling prompts."""
        return '''
        <svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="paperGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#fbbf24;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#f59e0b;stop-opacity:0.8" />
                </linearGradient>
            </defs>

            <!-- Background -->
            <rect width="400" height="300" fill="#fffbeb"/>

            <!-- Journal/notebook -->
            <g transform="translate(200,150)">
                <!-- Notebook cover -->
                <rect x="-80" y="-100" width="160" height="200" fill="url(#paperGradient)" rx="8"/>
                <!-- Spiral binding -->
                <g stroke="#d97706" stroke-width="2" fill="none">
                    <circle cx="-60" cy="-80" r="3"/>
                    <circle cx="-60" cy="-40" r="3"/>
                    <circle cx="-60" cy="0" r="3"/>
                    <circle cx="-60" cy="40" r="3"/>
                    <circle cx="-60" cy="80" r="3"/>
                </g>
                <!-- Pages -->
                <rect x="-70" y="-90" width="140" height="180" fill="#fefefe" rx="4"/>
                <!-- Writing lines -->
                <g stroke="#e5e7eb" stroke-width="1">
                    <line x1="-60" y1="-70" x2="60" y2="-70"/>
                    <line x1="-60" y1="-50" x2="60" y2="-50"/>
                    <line x1="-60" y1="-30" x2="60" y2="-30"/>
                    <line x1="-60" y1="-10" x2="60" y2="-10"/>
                    <line x1="-60" y1="10" x2="60" y2="10"/>
                </g>
            </g>

            <!-- Pen -->
            <g transform="translate(280,120) rotate(45)">
                <rect x="-2" y="-30" width="4" height="60" fill="#1f2937"/>
                <polygon points="-2,-30 2,-30 0,-40" fill="#374151"/>
            </g>

            <!-- Thought bubbles -->
            <circle cx="120" cy="80" r="8" fill="#fbbf24" opacity="0.4">
                <animate attributeName="r" values="6;10;6" dur="4s" repeatCount="indefinite"/>
            </circle>
            <circle cx="320" cy="220" r="6" fill="#f59e0b" opacity="0.4">
                <animate attributeName="r" values="4;8;4" dur="6s" repeatCount="indefinite"/>
            </circle>
        </svg>
        '''

    def _cognitive_svg_templates(self, title: str, emotions: list) -> str:
        """Generate SVG for cognitive reframing exercises."""
        return '''
        <svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="brainGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#8b5cf6;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#7c3aed;stop-opacity:0.8" />
                </linearGradient>
            </defs>

            <!-- Background -->
            <rect width="400" height="300" fill="#faf5ff"/>

            <!-- Brain outline -->
            <g transform="translate(200,150)">
                <path d="M -60,-40 Q -80,-60 -60,-80 Q -20,-90 20,-80 Q 60,-60 60,-40 Q 80,-20 60,0 Q 40,20 20,40 Q -20,50 -60,40 Q -80,20 -60,0 Q -80,-20 -60,-40 Z" fill="url(#brainGradient)" opacity="0.7"/>

                <!-- Neural pathways -->
                <g stroke="#8b5cf6" stroke-width="2" fill="none" opacity="0.6">
                    <path d="M -40,-20 Q -20,-10 0,0 Q 20,10 40,20">
                        <animate attributeName="stroke-dasharray" values="0,100;50,50;100,0;0,100" dur="4s" repeatCount="indefinite"/>
                    </path>
                    <path d="M -30,10 Q 0,20 30,10">
                        <animate attributeName="stroke-dasharray" values="0,60;30,30;60,0;0,60" dur="3s" repeatCount="indefinite"/>
                    </path>
                </g>

                <!-- Thought transformation -->
                <circle cx="-30" cy="-10" r="8" fill="#ef4444" opacity="0.6">
                    <animate attributeName="fill" values="#ef4444;#10b981;#ef4444" dur="6s" repeatCount="indefinite"/>
                </circle>
                <circle cx="30" cy="10" r="8" fill="#10b981" opacity="0.6">
                    <animate attributeName="r" values="6;10;6" dur="4s" repeatCount="indefinite"/>
                </circle>
            </g>

            <!-- Reframing arrows -->
            <g stroke="#7c3aed" stroke-width="3" fill="none" marker-end="url(#arrowhead)">
                <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                        <polygon points="0 0, 10 3.5, 0 7" fill="#7c3aed"/>
                    </marker>
                </defs>
                <path d="M 100,100 Q 150,80 200,100">
                    <animate attributeName="stroke-dasharray" values="0,100;100,0" dur="3s" repeatCount="indefinite"/>
                </path>
            </g>

            <!-- Labels -->
            <text x="100" y="120" text-anchor="middle" font-family="Arial" font-size="12" fill="#7c3aed">Negative</text>
            <text x="300" y="120" text-anchor="middle" font-family="Arial" font-size="12" fill="#10b981">Balanced</text>
        </svg>
        '''

    def _physical_svg_templates(self, title: str, emotions: list) -> str:
        """Generate SVG for physical activities."""
        return '''
        <svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="energyGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#f97316;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#ea580c;stop-opacity:0.8" />
                </linearGradient>
            </defs>

            <!-- Background -->
            <rect width="400" height="300" fill="#fff7ed"/>

            <!-- Active figure -->
            <g transform="translate(200,180)">
                <!-- Body -->
                <ellipse cx="0" cy="0" rx="25" ry="35" fill="url(#energyGradient)" opacity="0.8"/>
                <!-- Head -->
                <circle cx="0" cy="-50" r="20" fill="url(#energyGradient)" opacity="0.9"/>
                <!-- Arms in motion -->
                <ellipse cx="-30" cy="-15" rx="12" ry="6" fill="url(#energyGradient)" opacity="0.7" transform="rotate(-45)">
                    <animateTransform attributeName="transform" values="rotate(-45);rotate(-30);rotate(-45)" dur="2s" repeatCount="indefinite"/>
                </ellipse>
                <ellipse cx="30" cy="-15" rx="12" ry="6" fill="url(#energyGradient)" opacity="0.7" transform="rotate(45)">
                    <animateTransform attributeName="transform" values="rotate(45);rotate(30);rotate(45)" dur="2s" repeatCount="indefinite"/>
                </ellipse>
                <!-- Legs -->
                <ellipse cx="-15" cy="25" rx="8" ry="20" fill="url(#energyGradient)" opacity="0.7"/>
                <ellipse cx="15" cy="25" rx="8" ry="20" fill="url(#energyGradient)" opacity="0.7"/>
            </g>

            <!-- Energy lines -->
            <g stroke="#f97316" stroke-width="2" fill="none" opacity="0.6">
                <path d="M 150,100 Q 200,80 250,100">
                    <animate attributeName="stroke-dasharray" values="0,100;100,0" dur="2s" repeatCount="indefinite"/>
                </path>
                <path d="M 160,200 Q 200,180 240,200">
                    <animate attributeName="stroke-dasharray" values="0,80;80,0" dur="1.5s" repeatCount="indefinite"/>
                </path>
            </g>

            <!-- Movement indicators -->
            <g opacity="0.5">
                <circle cx="120" cy="120" r="3" fill="#f97316">
                    <animate attributeName="cx" values="120;280;120" dur="3s" repeatCount="indefinite"/>
                </circle>
                <circle cx="280" cy="160" r="2" fill="#ea580c">
                    <animate attributeName="cx" values="280;120;280" dur="4s" repeatCount="indefinite"/>
                </circle>
            </g>
        </svg>
        '''

    def _relaxation_svg_templates(self, title: str, emotions: list) -> str:
        """Generate SVG for relaxation techniques."""
        if "progressive" in title.lower():
            return self._create_progressive_relaxation_svg()
        else:
            return self._create_general_relaxation_svg()

    def _create_progressive_relaxation_svg(self) -> str:
        """Create progressive muscle relaxation SVG."""
        return '''
        <svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="relaxGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#06b6d4;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#0891b2;stop-opacity:0.7" />
                </linearGradient>
            </defs>

            <!-- Background -->
            <rect width="400" height="300" fill="#f0f9ff"/>

            <!-- Relaxed figure lying down -->
            <g transform="translate(200,150)">
                <!-- Body -->
                <ellipse cx="0" cy="0" rx="60" ry="25" fill="url(#relaxGradient)" opacity="0.8"/>
                <!-- Head -->
                <circle cx="-70" cy="0" r="18" fill="url(#relaxGradient)" opacity="0.9"/>
                <!-- Arms relaxed -->
                <ellipse cx="-20" cy="-30" rx="30" ry="8" fill="url(#relaxGradient)" opacity="0.7"/>
                <ellipse cx="-20" cy="30" rx="30" ry="8" fill="url(#relaxGradient)" opacity="0.7"/>
                <!-- Legs -->
                <ellipse cx="40" cy="-15" rx="25" ry="10" fill="url(#relaxGradient)" opacity="0.7"/>
                <ellipse cx="40" cy="15" rx="25" ry="10" fill="url(#relaxGradient)" opacity="0.7"/>
            </g>

            <!-- Relaxation waves -->
            <g opacity="0.4">
                <path d="M 50,100 Q 100,80 150,100 T 250,100 T 350,100" stroke="#06b6d4" stroke-width="2" fill="none">
                    <animate attributeName="d" values="M 50,100 Q 100,80 150,100 T 250,100 T 350,100;M 50,100 Q 100,120 150,100 T 250,100 T 350,100;M 50,100 Q 100,80 150,100 T 250,100 T 350,100" dur="8s" repeatCount="indefinite"/>
                </path>
                <path d="M 50,200 Q 100,180 150,200 T 250,200 T 350,200" stroke="#0891b2" stroke-width="2" fill="none">
                    <animate attributeName="d" values="M 50,200 Q 100,180 150,200 T 250,200 T 350,200;M 50,200 Q 100,220 150,200 T 250,200 T 350,200;M 50,200 Q 100,180 150,200 T 250,200 T 350,200" dur="10s" repeatCount="indefinite"/>
                </path>
            </g>

            <!-- Muscle group indicators -->
            <g opacity="0.6">
                <circle cx="130" cy="150" r="4" fill="#06b6d4">
                    <animate attributeName="opacity" values="0.3;1;0.3" dur="3s" repeatCount="indefinite"/>
                </circle>
                <circle cx="200" cy="130" r="3" fill="#0891b2">
                    <animate attributeName="opacity" values="0.3;1;0.3" dur="4s" repeatCount="indefinite" begin="1s"/>
                </circle>
                <circle cx="240" cy="165" r="3" fill="#06b6d4">
                    <animate attributeName="opacity" values="0.3;1;0.3" dur="5s" repeatCount="indefinite" begin="2s"/>
                </circle>
            </g>
        </svg>
        '''

    def _create_general_relaxation_svg(self) -> str:
        """Create general relaxation SVG."""
        return '''
        <svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <radialGradient id="calmGradient" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" style="stop-color:#a78bfa;stop-opacity:0.8" />
                    <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:0.4" />
                </radialGradient>
            </defs>

            <!-- Background -->
            <rect width="400" height="300" fill="#faf5ff"/>

            <!-- Peaceful scene -->
            <g transform="translate(200,150)">
                <!-- Central calm circle -->
                <circle cx="0" cy="0" r="60" fill="url(#calmGradient)">
                    <animate attributeName="r" values="50;70;50" dur="12s" repeatCount="indefinite"/>
                    <animate attributeName="opacity" values="0.6;0.3;0.6" dur="12s" repeatCount="indefinite"/>
                </circle>

                <!-- Inner peace symbol -->
                <circle cx="0" cy="0" r="20" fill="none" stroke="#8b5cf6" stroke-width="2" opacity="0.7">
                    <animate attributeName="r" values="15;25;15" dur="8s" repeatCount="indefinite"/>
                </circle>
            </g>

            <!-- Floating calm elements -->
            <g opacity="0.5">
                <circle cx="100" cy="80" r="2" fill="#a78bfa">
                    <animate attributeName="cy" values="80;60;80" dur="6s" repeatCount="indefinite"/>
                </circle>
                <circle cx="320" cy="220" r="1.5" fill="#8b5cf6">
                    <animate attributeName="cy" values="220;200;220" dur="8s" repeatCount="indefinite"/>
                </circle>
                <circle cx="80" cy="250" r="2.5" fill="#a78bfa">
                    <animate attributeName="cy" values="250;230;250" dur="7s" repeatCount="indefinite"/>
                </circle>
            </g>

            <!-- Zen text -->
            <text x="200" y="250" text-anchor="middle" font-family="Arial" font-size="14" fill="#8b5cf6" font-style="italic">Release and let go</text>
        </svg>
        '''

    def _default_svg_template(self, title: str, emotions: list) -> str:
        """Default SVG template for unknown recommendation types."""
        return '''
        <svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="defaultGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#6366f1;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#4f46e5;stop-opacity:0.8" />
                </linearGradient>
            </defs>

            <!-- Background -->
            <rect width="400" height="300" fill="#f8fafc"/>

            <!-- Central wellness symbol -->
            <g transform="translate(200,150)">
                <circle cx="0" cy="0" r="50" fill="url(#defaultGradient)" opacity="0.6">
                    <animate attributeName="r" values="40;60;40" dur="6s" repeatCount="indefinite"/>
                </circle>

                <!-- Wellness cross -->
                <g stroke="#6366f1" stroke-width="4" opacity="0.8">
                    <line x1="-30" y1="0" x2="30" y2="0"/>
                    <line x1="0" y1="-30" x2="0" y2="30"/>
                </g>
            </g>

            <!-- Healing particles -->
            <g opacity="0.4">
                <circle cx="120" cy="100" r="3" fill="#6366f1">
                    <animate attributeName="opacity" values="0.2;0.8;0.2" dur="3s" repeatCount="indefinite"/>
                </circle>
                <circle cx="280" cy="200" r="2" fill="#4f46e5">
                    <animate attributeName="opacity" values="0.2;0.8;0.2" dur="4s" repeatCount="indefinite"/>
                </circle>
            </g>
        </svg>
        '''
