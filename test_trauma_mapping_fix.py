#!/usr/bin/env python3
"""
Test script to verify the trauma mapping service fixes.
"""
import sys
import os
import asyncio

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from database import engine, Base
from models.trauma_mapping import LifeEvent, EventType, EventCategory
from models.user import User
from services.trauma_mapping_service import TraumaMappingService
from datetime import datetime

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_trauma_mapping_service():
    """Test the trauma mapping service with the enum fixes."""
    print("🧪 Testing Trauma Mapping Service...")
    
    db = SessionLocal()
    try:
        # Check if we have any users
        user = db.query(User).first()
        if not user:
            print("❌ No users found in database. Please create a user first.")
            return False
        
        print(f"✅ Found user: {user.username}")
        
        # Check if we have any life events
        events = db.query(LifeEvent).filter(LifeEvent.user_id == user.id).all()
        print(f"✅ Found {len(events)} life events for user")
        
        if len(events) == 0:
            print("ℹ️ No life events found. Creating a test event...")
            # Create a test event
            test_event = LifeEvent(
                user_id=user.id,
                title="Test Event for Service",
                description="Testing the trauma mapping service",
                event_date=datetime.now(),
                event_type=EventType.NEUTRAL,
                category=EventCategory.OTHER,
                emotional_impact_score=0.0,
                trauma_severity=2.0,
                is_resolved=False
            )
            
            db.add(test_event)
            db.commit()
            db.refresh(test_event)
            print(f"✅ Created test event with ID: {test_event.id}")
        
        # Test the trauma mapping service
        service = TraumaMappingService()
        print("✅ Created TraumaMappingService instance")
        
        # Test the timeline analysis
        print("🔍 Testing timeline analysis...")
        try:
            result = await service.analyze_timeline_patterns(db, user.id)
            print("✅ Timeline analysis completed successfully!")
            print(f"   Total events: {result.get('total_events', 0)}")
            print(f"   Traumatic events: {result.get('traumatic_events_count', 0)}")
            print(f"   Positive events: {result.get('positive_events_count', 0)}")
            print(f"   Unresolved events: {result.get('unresolved_events_count', 0)}")
            print(f"   Patterns found: {len(result.get('patterns', []))}")
            print(f"   Recommendations: {len(result.get('recommendations', []))}")
            
            return True
            
        except Exception as e:
            print(f"❌ Timeline analysis failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        db.close()

def main():
    """Main test function."""
    print("🔧 Testing Trauma Mapping Service Fixes")
    print("=" * 50)
    
    # Run the async test
    success = asyncio.run(test_trauma_mapping_service())
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! Trauma mapping service is working correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
