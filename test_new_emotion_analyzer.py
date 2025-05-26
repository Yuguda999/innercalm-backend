"""
Test script for the new DistilRoBERTa-based emotion analyzer.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.emotion_analyzer import EmotionAnalyzer
import time

def test_emotion_analyzer():
    """Test the new emotion analyzer with various text samples."""
    print("🧠 Testing New DistilRoBERTa-based Emotion Analyzer")
    print("=" * 60)
    
    # Initialize the analyzer
    print("Loading emotion classifier...")
    start_time = time.time()
    try:
        analyzer = EmotionAnalyzer()
        load_time = time.time() - start_time
        print(f"✅ Model loaded successfully in {load_time:.2f} seconds")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return
    
    # Test cases with expected dominant emotions
    test_cases = [
        {
            "text": "I am so happy and excited about this amazing opportunity!",
            "expected": "joy",
            "description": "Happy/excited text"
        },
        {
            "text": "I feel really sad and depressed today. Everything seems hopeless.",
            "expected": "sadness", 
            "description": "Sad/depressed text"
        },
        {
            "text": "I'm so angry and frustrated with this situation! This is ridiculous!",
            "expected": "anger",
            "description": "Angry/frustrated text"
        },
        {
            "text": "I'm scared and anxious about what might happen. I'm really worried.",
            "expected": "fear",
            "description": "Fearful/anxious text"
        },
        {
            "text": "Wow, I never expected that to happen! What a surprise!",
            "expected": "surprise",
            "description": "Surprised text"
        },
        {
            "text": "That's absolutely disgusting and revolting. I can't stand it.",
            "expected": "disgust",
            "description": "Disgusted text"
        },
        {
            "text": "The weather is okay today. I went to the store.",
            "expected": "neutral",
            "description": "Neutral text"
        },
        {
            "text": "I keep having flashbacks and nightmares about the trauma I experienced.",
            "expected": "fear",  # Should also detect trauma theme
            "description": "Trauma-related text"
        }
    ]
    
    print(f"\n🧪 Testing {len(test_cases)} different emotion scenarios...")
    print("-" * 60)
    
    correct_predictions = 0
    total_time = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Text: \"{test_case['text']}\"")
        
        # Analyze emotion
        start_time = time.time()
        try:
            result = analyzer.analyze_emotion(test_case["text"], user_id=1)
            analysis_time = time.time() - start_time
            total_time += analysis_time
            
            # Find dominant emotion
            emotions = {
                "joy": result["joy"],
                "sadness": result["sadness"], 
                "anger": result["anger"],
                "fear": result["fear"],
                "surprise": result["surprise"],
                "disgust": result["disgust"]
            }
            
            # Get top emotion
            dominant_emotion = max(emotions, key=emotions.get)
            dominant_score = emotions[dominant_emotion]
            
            # Check if prediction is correct
            is_correct = dominant_emotion == test_case["expected"]
            if is_correct:
                correct_predictions += 1
                status = "✅ CORRECT"
            else:
                status = "❌ INCORRECT"
            
            print(f"Expected: {test_case['expected']}")
            print(f"Predicted: {dominant_emotion} (confidence: {dominant_score:.3f}) {status}")
            print(f"Sentiment: {result['sentiment_label']} (score: {result['sentiment_score']:.3f})")
            print(f"Analysis time: {analysis_time:.3f}s")
            
            # Show all emotion scores
            print("All emotions:", end=" ")
            for emotion, score in emotions.items():
                print(f"{emotion}: {score:.3f}", end=", ")
            print()
            
            # Show themes if detected
            if result.get("themes"):
                print(f"Themes: {result['themes']}")
            
            # Show keywords
            if result.get("keywords"):
                print(f"Keywords: {result['keywords'][:5]}")  # Show first 5 keywords
                
        except Exception as e:
            print(f"❌ Error analyzing text: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    accuracy = (correct_predictions / len(test_cases)) * 100
    avg_time = total_time / len(test_cases)
    
    print(f"Accuracy: {correct_predictions}/{len(test_cases)} ({accuracy:.1f}%)")
    print(f"Average analysis time: {avg_time:.3f} seconds")
    print(f"Total analysis time: {total_time:.3f} seconds")
    
    if accuracy >= 70:
        print("🎉 Great! The emotion analyzer is working well.")
    elif accuracy >= 50:
        print("⚠️  Decent performance, but could be improved.")
    else:
        print("❌ Poor performance, needs investigation.")
    
    print("\n🔬 Model Performance:")
    print(f"- Model: j-hartmann/emotion-english-distilroberta-base")
    print(f"- Size: ~65 MB")
    print(f"- Speed: {avg_time:.3f}s per analysis")
    print(f"- Emotions: 7 (anger, disgust, fear, joy, neutral, sadness, surprise)")

def test_edge_cases():
    """Test edge cases and special scenarios."""
    print("\n🔍 Testing Edge Cases")
    print("-" * 30)
    
    analyzer = EmotionAnalyzer()
    
    edge_cases = [
        "",  # Empty string
        "   ",  # Whitespace only
        "😀😢😡",  # Emojis only
        "a",  # Single character
        "This is a very long text that goes on and on and repeats itself multiple times to test how the model handles longer inputs with lots of repetition and redundancy." * 3,  # Very long text
        "I'm feeling happy but also sad at the same time, it's confusing.",  # Mixed emotions
    ]
    
    for i, text in enumerate(edge_cases, 1):
        print(f"\nEdge case {i}: {repr(text[:50])}")
        try:
            result = analyzer.analyze_emotion(text, user_id=1)
            print(f"✅ Handled successfully")
            print(f"Sentiment: {result['sentiment_label']} ({result['sentiment_score']:.3f})")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        test_emotion_analyzer()
        test_edge_cases()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
