#!/usr/bin/env python3
"""
Test script to verify the enum fix for trauma mapping.
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from database import engine, Base
from models.trauma_mapping import LifeEvent, EventType, EventCategory
from models.user import User
from datetime import datetime

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_enum_values():
    """Test that enum values work correctly."""
    print("🧪 Testing enum values...")
    
    # Test EventType enum
    print(f"EventType.POSITIVE.value = {EventType.POSITIVE.value}")
    print(f"EventType.NEGATIVE.value = {EventType.NEGATIVE.value}")
    print(f"EventType.NEUTRAL.value = {EventType.NEUTRAL.value}")
    print(f"EventType.TRAUMATIC.value = {EventType.TRAUMATIC.value}")
    print(f"EventType.MILESTONE.value = {EventType.MILESTONE.value}")
    
    # Test EventCategory enum
    print(f"EventCategory.FAMILY.value = {EventCategory.FAMILY.value}")
    print(f"EventCategory.RELATIONSHIPS.value = {EventCategory.RELATIONSHIPS.value}")
    print(f"EventCategory.OTHER.value = {EventCategory.OTHER.value}")

def test_database_operations():
    """Test database operations with the fixed enums."""
    print("\n🗄️ Testing database operations...")
    
    db = SessionLocal()
    try:
        # Check if we have any users
        user = db.query(User).first()
        if not user:
            print("❌ No users found in database. Please create a user first.")
            return False
        
        print(f"✅ Found user: {user.username}")
        
        # Try to create a new life event with uppercase enum values
        test_event = LifeEvent(
            user_id=user.id,
            title="Test Event - Enum Fix",
            description="Testing the enum fix",
            event_date=datetime.now(),
            event_type=EventType.POSITIVE,
            category=EventCategory.OTHER,
            emotional_impact_score=5.0,
            trauma_severity=0.0,
            is_resolved=False
        )
        
        db.add(test_event)
        db.commit()
        db.refresh(test_event)
        
        print(f"✅ Created test event with ID: {test_event.id}")
        print(f"   Event type: {test_event.event_type}")
        print(f"   Category: {test_event.category}")
        
        # Try to retrieve existing life events
        events = db.query(LifeEvent).filter(LifeEvent.user_id == user.id).all()
        print(f"✅ Found {len(events)} life events for user")
        
        for event in events[:3]:  # Show first 3 events
            print(f"   - {event.title}: {event.event_type.value} / {event.category.value}")
        
        # Clean up test event
        db.delete(test_event)
        db.commit()
        print("✅ Cleaned up test event")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Main test function."""
    print("🔧 Testing Enum Fix for Trauma Mapping")
    print("=" * 50)
    
    # Test enum values
    test_enum_values()
    
    # Test database operations
    success = test_database_operations()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! Enum fix is working correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
