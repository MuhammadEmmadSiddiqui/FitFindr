"""
Setup script for FitFindr
Run this to initialize the project
"""
import os
import sys
from pathlib import Path


def create_directories():
    """Create necessary directories"""
    dirs = [
        'data/uploads',
        'logs',
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")


def create_env_file():
    """Create .env file from template if it doesn't exist"""
    if Path('.env').exists():
        print("✓ .env file already exists")
        return
    
    if Path('.env.example').exists():
        import shutil
        shutil.copy('.env.example', '.env')
        print("✓ Created .env file from template")
        print("⚠️  IMPORTANT: Edit .env and add your GROQ_API_KEYS")
    else:
        print("✗ .env.example not found")


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python 3.10+ required. You have {version.major}.{version.minor}")
        return False


def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling dependencies...")
    os.system(f"{sys.executable} -m pip install --upgrade pip")
    os.system(f"{sys.executable} -m pip install -r requirements.txt")
    print("✓ Dependencies installed")


def initialize_database():
    """Initialize database"""
    print("\nInitializing database...")
    try:
        from src.database import init_db
        init_db()
        print("✓ Database initialized")
    except Exception as e:
        print(f"⚠️  Database initialization: {str(e)}")


def main():
    """Main setup function"""
    print("=" * 50)
    print("FitFindr Setup")
    print("=" * 50)
    print()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    print("\nCreating directories...")
    create_directories()
    
    # Create .env file
    print("\nSetting up environment...")
    create_env_file()
    
    # Ask about dependencies
    print("\n" + "=" * 50)
    response = input("Install Python dependencies? (y/n): ").lower()
    if response == 'y':
        install_dependencies()
    
    # Initialize database
    print("\n" + "=" * 50)
    response = input("Initialize database? (y/n): ").lower()
    if response == 'y':
        initialize_database()
    
    # Final instructions
    print("\n" + "=" * 50)
    print("Setup Complete! 🎉")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Edit .env and add your GROQ_API_KEYS")
    print("2. Run: streamlit run streamlit_app.py")
    print("   OR")
    print("   Run: docker-compose up -d")
    print("\nFor more details, see QUICKSTART.md")
    print("=" * 50)


if __name__ == "__main__":
    main()
