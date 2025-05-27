#!/usr/bin/env python3
"""
Environment switching utility for InnerCalm backend.
"""
import os
import sys
import shutil
import argparse
from pathlib import Path


def switch_environment(env: str):
    """Switch to the specified environment."""
    
    # Validate environment
    valid_envs = ["development", "production", "testing"]
    if env not in valid_envs:
        print(f"❌ Invalid environment: {env}")
        print(f"Valid environments: {', '.join(valid_envs)}")
        return False
    
    # Get paths
    backend_dir = Path(__file__).parent.parent
    env_file_local = backend_dir / f".env.{env}.local"
    env_file = backend_dir / f".env.{env}"
    target_file = backend_dir / ".env"
    
    # Prefer .local file if it exists, otherwise use template
    if env_file_local.exists():
        source_file = env_file_local
        print(f"📁 Using local environment file: {source_file.name}")
    elif env_file.exists():
        source_file = env_file
        print(f"📁 Using template environment file: {source_file.name}")
        print(f"💡 Tip: Create {env_file_local.name} with actual credentials for local development")
    else:
        print(f"❌ Environment file not found: {env_file} or {env_file_local}")
        return False
    
    try:
        # Backup current .env if it exists
        if target_file.exists():
            backup_file = backend_dir / ".env.backup"
            shutil.copy2(target_file, backup_file)
            print(f"📁 Backed up current .env to .env.backup")
        
        # Copy environment file to .env
        shutil.copy2(source_file, target_file)
        print(f"✅ Switched to {env} environment")
        print(f"📄 Copied {source_file.name} → .env")
        
        # Set environment variable
        os.environ["ENVIRONMENT"] = env
        
        # Display current configuration
        print(f"\n📊 Current Configuration:")
        print(f"   Environment: {env}")
        
        # Read and display key settings
        with open(target_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    if 'DATABASE_URL' in line:
                        db_url = line.split('=', 1)[1].strip('"')
                        if 'sqlite' in db_url:
                            if ':memory:' in db_url:
                                print(f"   Database: In-memory SQLite (testing)")
                            else:
                                print(f"   Database: SQLite ({db_url.split('/')[-1]})")
                        elif 'postgresql' in db_url:
                            if 'your_postgresql' in db_url:
                                print(f"   Database: PostgreSQL (template - needs real URL)")
                            else:
                                print(f"   Database: PostgreSQL (production)")
                    elif 'DEBUG' in line:
                        debug = line.split('=', 1)[1].strip()
                        print(f"   Debug Mode: {debug}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error switching environment: {e}")
        return False


def show_current_environment():
    """Show the current environment configuration."""
    backend_dir = Path(__file__).parent.parent
    env_file = backend_dir / ".env"
    
    if not env_file.exists():
        print("❌ No .env file found")
        print("💡 Run: python3 scripts/switch_env.py switch development")
        return
    
    print("📊 Current Environment Configuration:")
    print("=" * 40)
    
    try:
        with open(env_file, 'r') as f:
            lines = f.readlines()
            
        current_env = "unknown"
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if 'ENVIRONMENT=' in line:
                    current_env = line.split('=', 1)[1].strip('"')
                    break
        
        print(f"Environment: {current_env}")
        print("-" * 40)
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"')
                    
                    # Mask sensitive values
                    if 'API_KEY' in key or 'SECRET' in key:
                        if len(value) > 10 and 'your_' not in value and 'test-' not in value:
                            value = value[:10] + "..." + value[-4:]
                    elif 'DATABASE_URL' in key:
                        if 'postgresql' in value:
                            if 'your_postgresql' in value:
                                value = "PostgreSQL (template - needs real URL)"
                            else:
                                value = "PostgreSQL (production database)"
                        elif 'sqlite' in value and ':memory:' not in value:
                            value = f"SQLite ({value.split('/')[-1]})"
                        elif ':memory:' in value:
                            value = "In-memory SQLite (testing)"
                    
                    print(f"{key}: {value}")
                
    except Exception as e:
        print(f"❌ Error reading environment: {e}")


def list_available_environments():
    """List all available environment files."""
    backend_dir = Path(__file__).parent.parent
    env_files = list(backend_dir.glob(".env.*"))
    
    print("📁 Available Environments:")
    print("=" * 30)
    
    environments = []
    for env_file in sorted(env_files):
        if env_file.name.startswith('.env.') and not env_file.name.endswith('.backup'):
            env_name = env_file.name.replace('.env.', '')
            if env_name not in ['local']:
                environments.append(env_name)
                print(f"  • {env_name}")
                
                # Show brief description
                try:
                    with open(env_file, 'r') as f:
                        first_line = f.readline().strip()
                        if first_line.startswith('#'):
                            description = first_line[1:].strip()
                            print(f"    {description}")
                except:
                    pass
                print()
    
    if not environments:
        print("  No environment files found!")
        print("  Expected files: .env.development, .env.production, .env.testing")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Switch between development, production, and testing environments"
    )
    parser.add_argument(
        "action",
        choices=["switch", "current", "list"],
        help="Action to perform"
    )
    parser.add_argument(
        "environment",
        nargs="?",
        choices=["development", "production", "testing"],
        help="Environment to switch to (required for 'switch' action)"
    )
    
    args = parser.parse_args()
    
    if args.action == "switch":
        if not args.environment:
            print("❌ Environment required for switch action")
            print("Usage: python3 scripts/switch_env.py switch <environment>")
            print("Available environments: development, production, testing")
            sys.exit(1)
        
        success = switch_environment(args.environment)
        sys.exit(0 if success else 1)
        
    elif args.action == "current":
        show_current_environment()
        
    elif args.action == "list":
        list_available_environments()


if __name__ == "__main__":
    main()
