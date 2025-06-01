"""
Quick script to create a single test group for immediate testing.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import get_db
from models.community import SharedWoundGroup, PeerCircle, CircleStatus

def create_quick_test_group():
    """Create a quick test group for immediate testing."""
    db_gen = get_db()
    db = next(db_gen)

    try:
        # Check if test group already exists
        existing_group = db.query(SharedWoundGroup).filter(
            SharedWoundGroup.name.like("%Test%")
        ).first()

        if existing_group:
            print(f"Test group already exists: {existing_group.name} (ID: {existing_group.id})")
            return existing_group

        # Create a test group
        test_group = SharedWoundGroup(
            name="Healing Hearts Test Circle",
            description="A test group for demonstrating AI-powered community management. This group brings together people dealing with anxiety, stress, and emotional healing.",
            cluster_id="test_healing_hearts_001",
            ai_generated=True,
            confidence_score=0.82,
            emotional_pattern={
                "anxiety": 0.6,
                "stress": 0.5,
                "sadness": 0.4,
                "hope": 0.3,
                "determination": 0.2
            },
            trauma_themes=["anxiety", "stress", "emotional_healing", "self_care"],
            healing_stage="processing",
            member_count=0,
            activity_score=0.0,
            cohesion_score=0.82,
            growth_potential=0.75,
            max_members=50,
            is_active=True,
            requires_approval=False,
            last_ai_review=datetime.utcnow(),
            next_ai_review=datetime.utcnow() + timedelta(days=7)
        )

        db.add(test_group)
        db.commit()
        db.refresh(test_group)

        # Create a test peer circle within the group
        test_circle = PeerCircle(
            shared_wound_group_id=test_group.id,
            name="Healing Hearts - Circle 1",
            description="A peer support circle for daily check-ins and mutual support",
            status=CircleStatus.ACTIVE,
            max_members=8,
            is_private=True,
            requires_invitation=False,
            facilitator_id=None,  # AI-managed
            last_activity_at=datetime.utcnow(),
            message_count=0
        )

        db.add(test_circle)
        db.commit()
        db.refresh(test_circle)

        print("✅ Test group created successfully!")
        print(f"   Group: {test_group.name} (ID: {test_group.id})")
        print(f"   Circle: {test_circle.name} (ID: {test_circle.id})")
        print(f"   Themes: {', '.join(test_group.trauma_themes)}")
        print(f"   Stage: {test_group.healing_stage}")
        print(f"   Confidence: {test_group.confidence_score:.2f}")
        print(f"   Growth Potential: {test_group.growth_potential:.2f}")

        return test_group

    except Exception as e:
        print(f"❌ Error creating test group: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_another_test_group():
    """Create a second test group with different characteristics."""
    db_gen = get_db()
    db = next(db_gen)

    try:
        # Check if this specific group already exists
        existing_group = db.query(SharedWoundGroup).filter(
            SharedWoundGroup.name == "Journey Recovery Circle"
        ).first()

        if existing_group:
            print(f"Second test group already exists: {existing_group.name} (ID: {existing_group.id})")
            return existing_group

        # Create a second test group with different emotional patterns
        test_group2 = SharedWoundGroup(
            name="Journey Recovery Circle",
            description="A supportive space for those working through trauma recovery and building resilience. This AI-managed group focuses on integration and growth.",
            cluster_id="test_journey_recovery_002",
            ai_generated=True,
            confidence_score=0.78,
            emotional_pattern={
                "anger": 0.5,
                "frustration": 0.4,
                "determination": 0.6,
                "hope": 0.5,
                "peace": 0.3
            },
            trauma_themes=["trauma_recovery", "anger_management", "resilience", "growth"],
            healing_stage="integration",
            member_count=0,
            activity_score=0.0,
            cohesion_score=0.78,
            growth_potential=0.85,
            max_members=50,
            is_active=True,
            requires_approval=False,
            last_ai_review=datetime.utcnow(),
            next_ai_review=datetime.utcnow() + timedelta(days=7)
        )

        db.add(test_group2)
        db.commit()
        db.refresh(test_group2)

        # Create a peer circle for this group too
        test_circle2 = PeerCircle(
            shared_wound_group_id=test_group2.id,
            name="Journey Recovery - Circle 1",
            description="A peer circle for sharing recovery experiences and building strength together",
            status=CircleStatus.ACTIVE,
            max_members=8,
            is_private=True,
            requires_invitation=False,
            facilitator_id=None,
            last_activity_at=datetime.utcnow(),
            message_count=0
        )

        db.add(test_circle2)
        db.commit()
        db.refresh(test_circle2)

        print("✅ Second test group created successfully!")
        print(f"   Group: {test_group2.name} (ID: {test_group2.id})")
        print(f"   Circle: {test_circle2.name} (ID: {test_circle2.id})")
        print(f"   Themes: {', '.join(test_group2.trauma_themes)}")
        print(f"   Stage: {test_group2.healing_stage}")
        print(f"   Confidence: {test_group2.confidence_score:.2f}")
        print(f"   Growth Potential: {test_group2.growth_potential:.2f}")

        return test_group2

    except Exception as e:
        print(f"❌ Error creating second test group: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def list_existing_groups():
    """List all existing groups."""
    db_gen = get_db()
    db = next(db_gen)

    try:
        groups = db.query(SharedWoundGroup).all()

        if not groups:
            print("No groups found in database.")
            return

        print(f"\n📋 Existing Groups ({len(groups)} total):")
        print("-" * 60)

        for group in groups:
            print(f"ID: {group.id}")
            print(f"Name: {group.name}")
            print(f"AI Generated: {group.ai_generated}")
            print(f"Active: {group.is_active}")
            print(f"Members: {group.member_count}")
            print(f"Confidence: {group.confidence_score:.2f}" if group.confidence_score else "N/A")
            print(f"Themes: {', '.join(group.trauma_themes) if group.trauma_themes else 'None'}")
            print("-" * 60)

    except Exception as e:
        print(f"❌ Error listing groups: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Creating test groups for AI Community Management...")
    print()

    # List existing groups first
    list_existing_groups()

    # Create test groups
    print("\n🔨 Creating new test groups...")
    group1 = create_quick_test_group()
    print()
    group2 = create_another_test_group()

    print("\n🎉 Test setup complete!")
    print("\n📖 Next steps:")
    print("1. Start your server: uvicorn main:app --reload")
    print("2. Visit: http://localhost:8000/community/groups")
    print("3. Check AI status: http://localhost:8000/community/ai-management/status")
    print("4. Run AI management: POST http://localhost:8000/community/ai-management/run")
    print("\n💡 You can now test joining groups and chatting in circles!")
