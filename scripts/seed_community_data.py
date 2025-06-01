"""
Seed script for community data - shared wound groups and reflection chains.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models.community import (
    SharedWoundGroup, PeerCircle, ReflectionChain, ReflectionEntry,
    CircleStatus, MembershipStatus
)
from models.user import User


def create_shared_wound_groups(db: Session):
    """Create sample shared wound groups."""
    groups = [
        {
            "name": "Childhood Trauma Survivors",
            "description": "A supportive community for those healing from childhood experiences of neglect, abuse, or dysfunction.",
            "emotional_pattern": {
                "sadness": 0.4,
                "fear": 0.3,
                "anger": 0.2,
                "joy": 0.05,
                "surprise": 0.03,
                "disgust": 0.02
            },
            "trauma_themes": ["childhood_abuse", "neglect", "family_dysfunction", "abandonment"],
            "healing_stage": "processing",
            "max_members": 50,
            "is_active": True,
            "requires_approval": True
        },
        {
            "name": "Grief and Loss Support",
            "description": "For those navigating the complex journey of grief, whether from death, divorce, or other significant losses.",
            "emotional_pattern": {
                "sadness": 0.5,
                "anger": 0.15,
                "fear": 0.15,
                "joy": 0.1,
                "surprise": 0.05,
                "disgust": 0.05
            },
            "trauma_themes": ["death_of_loved_one", "divorce", "job_loss", "relationship_ending"],
            "healing_stage": "early",
            "max_members": 40,
            "is_active": True,
            "requires_approval": True
        },
        {
            "name": "Anxiety and Depression Warriors",
            "description": "A space for those battling anxiety, depression, and related mental health challenges.",
            "emotional_pattern": {
                "fear": 0.35,
                "sadness": 0.35,
                "anger": 0.1,
                "joy": 0.1,
                "surprise": 0.05,
                "disgust": 0.05
            },
            "trauma_themes": ["anxiety_disorders", "depression", "panic_attacks", "social_anxiety"],
            "healing_stage": "processing",
            "max_members": 60,
            "is_active": True,
            "requires_approval": False
        },
        {
            "name": "Relationship Trauma Recovery",
            "description": "Healing from toxic relationships, emotional abuse, and learning to build healthy connections.",
            "emotional_pattern": {
                "anger": 0.3,
                "sadness": 0.25,
                "fear": 0.25,
                "joy": 0.1,
                "surprise": 0.05,
                "disgust": 0.05
            },
            "trauma_themes": ["emotional_abuse", "toxic_relationships", "betrayal", "codependency"],
            "healing_stage": "integration",
            "max_members": 35,
            "is_active": True,
            "requires_approval": True
        },
        {
            "name": "Self-Compassion Builders",
            "description": "For those working on developing self-love, self-acceptance, and breaking patterns of self-criticism.",
            "emotional_pattern": {
                "sadness": 0.25,
                "anger": 0.2,
                "fear": 0.2,
                "joy": 0.25,
                "surprise": 0.05,
                "disgust": 0.05
            },
            "trauma_themes": ["self_criticism", "perfectionism", "low_self_esteem", "shame"],
            "healing_stage": "growth",
            "max_members": 45,
            "is_active": True,
            "requires_approval": False
        }
    ]
    
    created_groups = []
    for group_data in groups:
        group = SharedWoundGroup(**group_data)
        db.add(group)
        created_groups.append(group)
    
    db.commit()
    
    # Refresh to get IDs
    for group in created_groups:
        db.refresh(group)
    
    print(f"Created {len(created_groups)} shared wound groups")
    return created_groups


def create_peer_circles(db: Session, groups: list):
    """Create sample peer circles for each group."""
    circles = []
    
    for group in groups:
        # Create 2-3 circles per group
        circle_names = [
            f"{group.name} - Circle A",
            f"{group.name} - Circle B"
        ]
        
        if group.max_members > 40:
            circle_names.append(f"{group.name} - Circle C")
        
        for circle_name in circle_names:
            circle = PeerCircle(
                shared_wound_group_id=group.id,
                name=circle_name,
                description=f"A supportive peer circle within the {group.name} community.",
                status=CircleStatus.ACTIVE,
                max_members=8,
                is_private=True,
                requires_invitation=group.requires_approval,
                last_activity_at=datetime.utcnow() - timedelta(hours=2),
                message_count=0
            )
            db.add(circle)
            circles.append(circle)
    
    db.commit()
    
    # Refresh to get IDs
    for circle in circles:
        db.refresh(circle)
    
    print(f"Created {len(circles)} peer circles")
    return circles


def create_reflection_chains(db: Session):
    """Create sample reflection chains."""
    chains = [
        {
            "title": "Healing from Childhood Trauma",
            "description": "Share your wisdom and insights about healing from childhood experiences.",
            "healing_module": "Inner Child Work",
            "difficulty_level": "intermediate",
            "is_active": True,
            "max_entries": 100
        },
        {
            "title": "Building Self-Compassion",
            "description": "Reflections on developing kindness toward yourself and breaking self-critical patterns.",
            "healing_module": "Self-Compassion",
            "difficulty_level": "beginner",
            "is_active": True,
            "max_entries": 75
        },
        {
            "title": "Navigating Grief and Loss",
            "description": "Supporting others through the journey of grief with your experiences and insights.",
            "healing_module": "Grief Processing",
            "difficulty_level": "intermediate",
            "is_active": True,
            "max_entries": 80
        },
        {
            "title": "Overcoming Anxiety",
            "description": "Practical tips and encouragement for managing anxiety and fear.",
            "healing_module": "Anxiety Management",
            "difficulty_level": "beginner",
            "is_active": True,
            "max_entries": 90
        },
        {
            "title": "Healthy Relationships",
            "description": "Wisdom about building and maintaining healthy, supportive relationships.",
            "healing_module": "Relationship Skills",
            "difficulty_level": "advanced",
            "is_active": True,
            "max_entries": 60
        }
    ]
    
    created_chains = []
    for chain_data in chains:
        chain = ReflectionChain(**chain_data)
        db.add(chain)
        created_chains.append(chain)
    
    db.commit()
    
    # Refresh to get IDs
    for chain in created_chains:
        db.refresh(chain)
    
    print(f"Created {len(created_chains)} reflection chains")
    return created_chains


def create_sample_reflections(db: Session, chains: list):
    """Create sample reflection entries."""
    # Get the first user to attribute reflections to
    user = db.query(User).first()
    if not user:
        print("No users found. Please create a user first.")
        return
    
    sample_reflections = [
        {
            "chain_title": "Healing from Childhood Trauma",
            "entries": [
                {
                    "content": "One thing that really helped me was learning that my inner child deserves love and protection. I started talking to that younger version of myself with the kindness I never received. It felt awkward at first, but now it's become a source of comfort and healing.",
                    "reflection_type": "insight",
                    "target_stage": "processing"
                },
                {
                    "content": "To anyone just starting this journey: be patient with yourself. Healing isn't linear, and some days will be harder than others. That's okay. You're not broken, you're healing. Every small step counts, even when it doesn't feel like it.",
                    "reflection_type": "encouragement",
                    "target_stage": "early"
                }
            ]
        },
        {
            "chain_title": "Building Self-Compassion",
            "entries": [
                {
                    "content": "I used to think self-compassion was selfish or weak. But I learned it's actually the foundation for genuine strength. When I treat myself with kindness, I have more energy to help others and face life's challenges.",
                    "reflection_type": "insight",
                    "target_stage": "integration"
                },
                {
                    "content": "A simple practice that changed everything for me: when I notice self-critical thoughts, I pause and ask 'What would I say to a good friend in this situation?' Then I try to offer myself that same kindness.",
                    "reflection_type": "tip",
                    "target_stage": "early"
                }
            ]
        },
        {
            "chain_title": "Overcoming Anxiety",
            "entries": [
                {
                    "content": "Breathing exercises saved my life during panic attacks. The 4-7-8 technique: breathe in for 4, hold for 7, exhale for 8. It activates your parasympathetic nervous system and brings you back to the present moment.",
                    "reflection_type": "tip",
                    "target_stage": "early"
                }
            ]
        }
    ]
    
    created_entries = []
    for reflection_data in sample_reflections:
        # Find the matching chain
        chain = next((c for c in chains if c.title == reflection_data["chain_title"]), None)
        if not chain:
            continue
        
        for entry_data in reflection_data["entries"]:
            entry = ReflectionEntry(
                chain_id=chain.id,
                user_id=user.id,
                content=entry_data["content"],
                reflection_type=entry_data["reflection_type"],
                target_stage=entry_data.get("target_stage"),
                helpful_count=0,
                view_count=0
            )
            db.add(entry)
            created_entries.append(entry)
    
    db.commit()
    print(f"Created {len(created_entries)} sample reflection entries")


def main():
    """Main function to seed community data."""
    print("Starting community data seeding...")
    
    db = SessionLocal()
    try:
        # Create shared wound groups
        groups = create_shared_wound_groups(db)
        
        # Create peer circles
        circles = create_peer_circles(db, groups)
        
        # Create reflection chains
        chains = create_reflection_chains(db)
        
        # Create sample reflections
        create_sample_reflections(db, chains)
        
        print("Community data seeding completed successfully!")
        
    except Exception as e:
        print(f"Error seeding community data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
