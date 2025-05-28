"""
Script to generate SVG illustrations for existing recommendations.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import get_db
from models.recommendation import Recommendation
from services.svg_generator import SVGGenerator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_svgs_for_existing_recommendations():
    """Generate SVG illustrations for all existing recommendations that don't have them."""
    
    # Initialize SVG generator
    svg_generator = SVGGenerator()
    
    # Get database session
    db: Session = next(get_db())
    
    try:
        # Get all recommendations without SVG illustrations
        recommendations = db.query(Recommendation).filter(
            Recommendation.image_url.is_(None)
        ).all()
        
        logger.info(f"Found {len(recommendations)} recommendations without SVG illustrations")
        
        updated_count = 0
        
        for rec in recommendations:
            try:
                # Prepare recommendation data for SVG generation
                recommendation_data = {
                    "type": rec.type,
                    "title": rec.title,
                    "description": rec.description,
                    "instructions": rec.instructions,
                    "target_emotions": rec.target_emotions,
                    "difficulty_level": rec.difficulty_level,
                    "estimated_duration": rec.estimated_duration
                }
                
                # Generate SVG
                svg_data_url = svg_generator.generate_svg(recommendation_data)
                
                # Update recommendation with SVG data
                rec.image_url = svg_data_url
                rec.illustration_prompt = f"SVG illustration for {rec.title} - {rec.type.value}"
                
                updated_count += 1
                logger.info(f"Generated SVG for recommendation {rec.id}: {rec.title}")
                
            except Exception as e:
                logger.error(f"Failed to generate SVG for recommendation {rec.id}: {e}")
                continue
        
        # Commit all changes
        db.commit()
        logger.info(f"Successfully updated {updated_count} recommendations with SVG illustrations")
        
    except Exception as e:
        logger.error(f"Error generating SVGs: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    generate_svgs_for_existing_recommendations()
