#!/usr/bin/env python3
"""
Script to help optimize InnerCalm server startup performance.
"""
import sys
import os
import time
import subprocess
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))


def test_model_loading_time():
    """Test how long it takes to load the emotion model."""
    print("🧪 Testing emotion model loading time...")
    
    try:
        from services.emotion_analyzer import EmotionAnalyzer
        
        start_time = time.time()
        analyzer = EmotionAnalyzer()
        # Trigger model loading
        _ = analyzer.classifier
        load_time = time.time() - start_time
        
        print(f"✅ Model loaded in {load_time:.2f} seconds")
        return load_time
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None


def update_env_file(preload: bool):
    """Update the .env.development file with the preload setting."""
    env_file = backend_dir / ".env.development"
    
    if not env_file.exists():
        print(f"❌ Environment file not found: {env_file}")
        return False
    
    try:
        # Read current content
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Update the PRELOAD_EMOTION_MODEL setting
        lines = content.split('\n')
        updated = False
        
        for i, line in enumerate(lines):
            if line.startswith('PRELOAD_EMOTION_MODEL='):
                lines[i] = f'PRELOAD_EMOTION_MODEL={str(preload).lower()}'
                updated = True
                break
        
        if not updated:
            # Add the setting if it doesn't exist
            lines.append(f'PRELOAD_EMOTION_MODEL={str(preload).lower()}')
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Updated PRELOAD_EMOTION_MODEL={str(preload).lower()} in {env_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating environment file: {e}")
        return False


def main():
    """Main optimization script."""
    print("🚀 InnerCalm Server Startup Optimization")
    print("=" * 50)
    
    print("\nThis script will help you optimize your server startup time.")
    print("There are two options:")
    print("  1. Fast startup, slower first chat (default)")
    print("  2. Slower startup, fast first chat (preload model)")
    
    # Test model loading time
    print("\n" + "=" * 50)
    load_time = test_model_loading_time()
    
    if load_time is None:
        print("❌ Could not test model loading. Please check your setup.")
        return
    
    print("\n" + "=" * 50)
    print("📊 Performance Analysis:")
    
    if load_time < 5:
        print(f"✅ Fast model loading ({load_time:.2f}s)")
        print("   Recommendation: Keep default (no preload)")
        print("   Your system loads the model quickly, so preloading isn't necessary.")
        recommended_preload = False
        
    elif load_time < 15:
        print(f"⚠️  Moderate model loading ({load_time:.2f}s)")
        print("   Recommendation: Consider preloading for better user experience")
        print("   Users will wait ~{:.1f}s for their first chat message.".format(load_time))
        recommended_preload = True
        
    else:
        print(f"🐌 Slow model loading ({load_time:.2f}s)")
        print("   Recommendation: Enable preloading")
        print("   Users would wait too long for their first chat message.")
        recommended_preload = True
    
    # Ask user for preference
    print("\n" + "=" * 50)
    print("Configuration Options:")
    print("  1. Fast startup (default) - Model loads on first chat")
    print("  2. Preload model - Model loads during server startup")
    
    while True:
        choice = input(f"\nChoose option (1-2) [recommended: {'2' if recommended_preload else '1'}]: ").strip()
        
        if choice == '' and recommended_preload:
            choice = '2'
        elif choice == '':
            choice = '1'
            
        if choice in ['1', '2']:
            break
        print("Please enter 1 or 2")
    
    preload = choice == '2'
    
    # Update environment file
    print(f"\n🔧 Configuring PRELOAD_EMOTION_MODEL={str(preload).lower()}...")
    
    if update_env_file(preload):
        print("\n✅ Configuration updated successfully!")
        
        if preload:
            print("\n📝 Next steps:")
            print("  1. Restart your server with: ./scripts/dev.sh")
            print("  2. The model will load during startup (may take 10-30s)")
            print("  3. First chat will be fast!")
        else:
            print("\n📝 Next steps:")
            print("  1. Restart your server with: ./scripts/dev.sh")
            print("  2. Server will start quickly")
            print(f"  3. First chat will take ~{load_time:.1f}s to load the model")
    else:
        print("\n❌ Failed to update configuration")


if __name__ == "__main__":
    main()
