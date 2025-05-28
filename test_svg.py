#!/usr/bin/env python3
"""
Simple test script for SVG generation.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.svg_generator import SVGGenerator
from models.recommendation import RecommendationType

def test_svg_generation():
    """Test SVG generation for different recommendation types."""
    
    svg_generator = SVGGenerator()
    
    test_cases = [
        {
            "type": RecommendationType.BREATHING_EXERCISE,
            "title": "4-7-8 Breathing for Emotional Balance",
            "description": "A calming breathing technique",
            "target_emotions": ["sadness"],
            "name": "breathing_478"
        },
        {
            "type": RecommendationType.MINDFULNESS_PRACTICE,
            "title": "Loving-Kindness Meditation",
            "description": "A meditation practice for self-compassion",
            "target_emotions": ["sadness"],
            "name": "mindfulness_loving_kindness"
        },
        {
            "type": RecommendationType.JOURNALING_PROMPT,
            "title": "Daily Reflection Journal",
            "description": "Write about your thoughts and feelings",
            "target_emotions": ["general"],
            "name": "journaling_reflection"
        },
        {
            "type": RecommendationType.COGNITIVE_REFRAMING,
            "title": "Anger Thought Challenge",
            "description": "Examine and reframe angry thoughts",
            "target_emotions": ["anger"],
            "name": "cognitive_anger"
        },
        {
            "type": RecommendationType.PHYSICAL_ACTIVITY,
            "title": "Energizing Movement",
            "description": "Physical activity to boost mood",
            "target_emotions": ["general"],
            "name": "physical_movement"
        },
        {
            "type": RecommendationType.RELAXATION_TECHNIQUE,
            "title": "Progressive Muscle Relaxation",
            "description": "Full-body relaxation technique",
            "target_emotions": ["stress"],
            "name": "relaxation_progressive"
        }
    ]
    
    print("Testing SVG generation for different recommendation types...")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            print(f"\n{i}. Testing {test_case['name']}:")
            print(f"   Type: {test_case['type'].value}")
            print(f"   Title: {test_case['title']}")
            
            # Generate SVG
            svg_data_url = svg_generator.generate_svg(test_case)
            
            # Check if it's a valid data URL
            if svg_data_url.startswith("data:image/svg+xml;base64,"):
                print(f"   ✓ SVG generated successfully")
                print(f"   ✓ Data URL length: {len(svg_data_url)} characters")
                
                # Optionally save to file for inspection
                import base64
                svg_content = base64.b64decode(svg_data_url.split(',')[1]).decode('utf-8')
                filename = f"test_output_{test_case['name']}.svg"
                with open(filename, 'w') as f:
                    f.write(svg_content)
                print(f"   ✓ Saved to {filename}")
                
            else:
                print(f"   ✗ Invalid data URL format")
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("SVG generation test completed!")

if __name__ == "__main__":
    test_svg_generation()
