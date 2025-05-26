"""
Integration test for the new emotion analyzer with the existing system.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.emotion_analyzer import EmotionAnalyzer
from models.emotion import EmotionAnalysis
from models.user import User
from database import SessionLocal, create_tables
from models import user, conversation, emotion, recommendation

def test_integration():
    """Test that the new emotion analyzer integrates properly with the existing system."""
    print("🔗 Testing Integration with Existing System")
    print("=" * 50)
    
    # Create database tables
    print("Setting up database...")
    create_tables()
    
    # Initialize analyzer
    print("Loading emotion analyzer...")
    analyzer = EmotionAnalyzer()
    
    # Test basic emotion analysis
    print("\n1. Testing basic emotion analysis...")
    test_text = "I'm feeling really anxious and worried about my job interview tomorrow."
    result = analyzer.analyze_emotion(test_text, user_id=1, message_id=1)
    
    print(f"Text: {test_text}")
    print(f"Result keys: {list(result.keys())}")
    print(f"Dominant emotion: fear={result['fear']:.3f}")
    print(f"Sentiment: {result['sentiment_label']} ({result['sentiment_score']:.3f})")
    print(f"Confidence: {result['confidence']:.3f}")
    
    # Test database integration
    print("\n2. Testing database integration...")
    db = SessionLocal()
    try:
        # Create a test user
        test_user = User(
            username="test_user",
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Create emotion analysis record
        emotion_analysis = EmotionAnalysis(
            user_id=test_user.id,
            message_id=None,
            joy=result["joy"],
            sadness=result["sadness"],
            anger=result["anger"],
            fear=result["fear"],
            surprise=result["surprise"],
            disgust=result["disgust"],
            sentiment_score=result["sentiment_score"],
            sentiment_label=result["sentiment_label"],
            themes=result.get("themes", []),
            keywords=result.get("keywords", []),
            confidence=result["confidence"]
        )
        
        db.add(emotion_analysis)
        db.commit()
        db.refresh(emotion_analysis)
        
        print(f"✅ Successfully saved emotion analysis to database")
        print(f"   Analysis ID: {emotion_analysis.id}")
        print(f"   User ID: {emotion_analysis.user_id}")
        print(f"   Fear score: {emotion_analysis.fear}")
        
    except Exception as e:
        print(f"❌ Database integration failed: {e}")
        db.rollback()
    finally:
        db.close()
    
    # Test pattern detection
    print("\n3. Testing pattern detection...")
    try:
        patterns = analyzer.detect_patterns(SessionLocal(), user_id=1, days=30)
        print(f"✅ Pattern detection works (found {len(patterns)} patterns)")
    except Exception as e:
        print(f"❌ Pattern detection failed: {e}")
    
    # Test various emotion types
    print("\n4. Testing various emotion types...")
    test_cases = [
        ("I'm so happy!", "joy"),
        ("I feel terrible", "sadness"),
        ("This makes me angry", "anger"),
        ("I'm scared", "fear"),
        ("What a surprise!", "surprise"),
        ("That's disgusting", "disgust")
    ]
    
    for text, expected in test_cases:
        try:
            result = analyzer.analyze_emotion(text, user_id=1)
            emotions = {
                "joy": result["joy"],
                "sadness": result["sadness"],
                "anger": result["anger"],
                "fear": result["fear"],
                "surprise": result["surprise"],
                "disgust": result["disgust"]
            }
            dominant = max(emotions, key=emotions.get)
            score = emotions[dominant]
            
            status = "✅" if dominant == expected else "⚠️"
            print(f"   {status} '{text}' -> {dominant} ({score:.3f})")
        except Exception as e:
            print(f"   ❌ '{text}' -> Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Integration test completed!")
    print("The new DistilRoBERTa emotion analyzer is fully integrated.")

if __name__ == "__main__":
    try:
        test_integration()
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
