"""
Script to create test groups and sample data for AI group management testing.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from database import get_db
from models.user import User, UserPreferences
from models.community import SharedWoundGroup, UserClusterProfile
from models.emotion import EmotionAnalysis
from services.ai_group_manager import ai_group_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_test_users_and_profiles():
    """Create test users with realistic emotional profiles."""
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Test user profiles with different emotional patterns
        test_profiles = [
            {
                "username": "sarah_healing",
                "email": "sarah@test.com",
                "full_name": "Sarah Johnson",
                "emotions": {"anxiety": 0.7, "sadness": 0.5, "hope": 0.3},
                "themes": ["anxiety", "work_stress", "self_esteem"],
                "stage": "processing",
                "intensity": 0.6,
                "variability": 0.4
            },
            {
                "username": "mike_recovery",
                "email": "mike@test.com", 
                "full_name": "Mike Chen",
                "emotions": {"anger": 0.6, "frustration": 0.5, "determination": 0.4},
                "themes": ["anger_management", "relationship", "communication"],
                "stage": "integration",
                "intensity": 0.7,
                "variability": 0.3
            },
            {
                "username": "emma_growth",
                "email": "emma@test.com",
                "full_name": "Emma Rodriguez", 
                "emotions": {"sadness": 0.8, "grief": 0.6, "acceptance": 0.2},
                "themes": ["grief", "loss", "family"],
                "stage": "early",
                "intensity": 0.8,
                "variability": 0.6
            },
            {
                "username": "alex_journey",
                "email": "alex@test.com",
                "full_name": "Alex Thompson",
                "emotions": {"anxiety": 0.6, "fear": 0.5, "courage": 0.3},
                "themes": ["anxiety", "social_anxiety", "self_worth"],
                "stage": "processing", 
                "intensity": 0.5,
                "variability": 0.4
            },
            {
                "username": "lisa_support",
                "email": "lisa@test.com",
                "full_name": "Lisa Park",
                "emotions": {"depression": 0.7, "loneliness": 0.6, "hope": 0.2},
                "themes": ["depression", "isolation", "self_care"],
                "stage": "early",
                "intensity": 0.7,
                "variability": 0.5
            },
            {
                "username": "david_progress",
                "email": "david@test.com",
                "full_name": "David Wilson",
                "emotions": {"stress": 0.5, "overwhelm": 0.4, "resilience": 0.4},
                "themes": ["work_stress", "burnout", "balance"],
                "stage": "integration",
                "intensity": 0.4,
                "variability": 0.3
            }
        ]
        
        created_users = []
        
        for profile_data in test_profiles:
            # Check if user already exists
            existing_user = db.query(User).filter(User.username == profile_data["username"]).first()
            if existing_user:
                logger.info(f"User {profile_data['username']} already exists, skipping...")
                created_users.append(existing_user)
                continue
                
            # Create user
            user = User(
                username=profile_data["username"],
                email=profile_data["email"],
                full_name=profile_data["full_name"],
                hashed_password="$2b$12$dummy_hash_for_testing",  # Dummy hash
                is_active=True
            )
            db.add(user)
            db.flush()  # Get the user ID
            
            # Create user preferences
            preferences = UserPreferences(
                user_id=user.id,
                preferred_name=user.full_name.split()[0],
                communication_style="supportive",
                crisis_contact_enabled=True
            )
            db.add(preferences)
            
            # Create some emotion analyses for the user
            base_date = datetime.utcnow() - timedelta(days=30)
            for i in range(10):  # Create 10 emotion analyses over 30 days
                analysis_date = base_date + timedelta(days=i * 3)
                
                emotion_analysis = EmotionAnalysis(
                    user_id=user.id,
                    conversation_id=None,  # Not tied to specific conversation
                    emotions=profile_data["emotions"],
                    dominant_emotion=max(profile_data["emotions"], key=profile_data["emotions"].get),
                    intensity=profile_data["intensity"] + (i * 0.01),  # Slight variation
                    context="test_data",
                    created_at=analysis_date
                )
                db.add(emotion_analysis)
            
            # Create cluster vector (simplified for testing)
            cluster_vector = []
            for emotion, intensity in profile_data["emotions"].items():
                cluster_vector.extend([intensity, intensity * 0.8, intensity * 1.2])
            
            # Pad or trim to consistent length
            while len(cluster_vector) < 15:
                cluster_vector.append(0.0)
            cluster_vector = cluster_vector[:15]
            
            # Create user cluster profile
            cluster_profile = UserClusterProfile(
                user_id=user.id,
                dominant_emotions=profile_data["emotions"],
                emotion_intensity=profile_data["intensity"],
                emotion_variability=profile_data["variability"],
                trauma_themes=profile_data["themes"],
                healing_stage=profile_data["stage"],
                coping_patterns=["journaling", "meditation", "talking"],
                communication_style="empathetic",
                support_preference="balanced",
                activity_level="medium",
                cluster_vector=cluster_vector,
                last_clustered_at=datetime.utcnow(),
                cluster_confidence=0.8
            )
            db.add(cluster_profile)
            
            created_users.append(user)
            logger.info(f"Created test user: {user.full_name}")
        
        db.commit()
        logger.info(f"Created {len(created_users)} test users with profiles")
        return created_users
        
    except Exception as e:
        logger.error(f"Error creating test users: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def create_manual_test_group():
    """Create a manual test group to demonstrate the system."""
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Check if test group already exists
        existing_group = db.query(SharedWoundGroup).filter(
            SharedWoundGroup.name == "Anxiety & Hope Circle"
        ).first()
        
        if existing_group:
            logger.info("Test group already exists")
            return existing_group
        
        # Create a test group
        test_group = SharedWoundGroup(
            name="Anxiety & Hope Circle",
            description="A supportive community for those processing anxiety and building hope. This group was created as a test to demonstrate AI-powered group management.",
            cluster_id="test_anxiety_hope_001",
            ai_generated=True,
            confidence_score=0.85,
            emotional_pattern={
                "anxiety": 0.65,
                "sadness": 0.4,
                "hope": 0.3,
                "fear": 0.5,
                "determination": 0.2
            },
            trauma_themes=["anxiety", "work_stress", "self_esteem", "social_anxiety"],
            healing_stage="processing",
            member_count=0,  # Will be updated by AI
            activity_score=0.0,
            cohesion_score=0.85,
            growth_potential=0.7,
            max_members=50,
            is_active=True,
            requires_approval=False,
            last_ai_review=datetime.utcnow(),
            next_ai_review=datetime.utcnow() + timedelta(days=7)
        )
        
        db.add(test_group)
        db.commit()
        db.refresh(test_group)
        
        logger.info(f"Created test group: {test_group.name} (ID: {test_group.id})")
        return test_group
        
    except Exception as e:
        logger.error(f"Error creating test group: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def run_ai_group_discovery():
    """Run AI group management to discover new groups from test users."""
    try:
        logger.info("Running AI group management to discover new groups...")
        
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Run the AI group management
            results = await ai_group_manager.run_ai_group_management(db)
            
            logger.info("AI Group Management Results:")
            logger.info(f"  - Groups created: {results['groups_created']}")
            logger.info(f"  - Groups updated: {results['groups_updated']}")
            logger.info(f"  - Groups merged: {results['groups_merged']}")
            logger.info(f"  - Groups split: {results['groups_split']}")
            logger.info(f"  - Groups archived: {results['groups_archived']}")
            logger.info(f"  - Users reassigned: {results['users_reassigned']}")
            
            return results
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error running AI group discovery: {e}")
        raise


async def main():
    """Main function to set up test data."""
    try:
        logger.info("=== Setting up AI Group Management Test Data ===")
        
        # Step 1: Create test users with emotional profiles
        logger.info("\n1. Creating test users with emotional profiles...")
        users = await create_test_users_and_profiles()
        
        # Step 2: Create a manual test group
        logger.info("\n2. Creating manual test group...")
        test_group = await create_manual_test_group()
        
        # Step 3: Run AI group discovery
        logger.info("\n3. Running AI group discovery...")
        results = await run_ai_group_discovery()
        
        logger.info("\n=== Test Setup Complete! ===")
        logger.info("\nYou can now:")
        logger.info("1. Visit http://localhost:8000/community/groups to see available groups")
        logger.info("2. Check http://localhost:8000/community/ai-management/status for AI status")
        logger.info("3. Run http://localhost:8000/community/ai-management/run to trigger AI management")
        logger.info("4. Use the test users to join groups and test the chat functionality")
        
        logger.info(f"\nTest users created:")
        for user in users:
            logger.info(f"  - {user.username} ({user.full_name})")
            
    except Exception as e:
        logger.error(f"Error in main setup: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
