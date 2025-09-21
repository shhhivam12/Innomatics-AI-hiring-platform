#!/usr/bin/env python3
"""
Hiring Portal Setup Script
This script helps set up the hiring portal with all necessary configurations.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10 or higher is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install Python dependencies"""
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    return True

def create_env_file():
    """Create .env file from template"""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ env.example file not found")
        return False
    
    # Copy template
    with open(env_example, 'r') as f:
        content = f.read()
    
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ Created .env file from template")
    print("⚠️  Please edit .env file with your actual configuration values")
    return True

def validate_env_file():
    """Validate .env file configuration"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY', 
        'SUPABASE_SERVICE_ROLE_KEY',
        'GROQ_API_KEY',
        'GEMINI_API_KEY',
        'LLM_PROVIDER',
        'SMTP_HOST',
        'SMTP_PORT',
        'SMTP_USER',
        'SMTP_PASS'
    ]
    
    missing_vars = []
    with open(env_file, 'r') as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=" not in content or f"{var}=your-" in content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Please configure these environment variables in .env:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ .env file configuration looks good")
    return True

def test_imports():
    """Test if all required packages can be imported"""
    required_packages = [
        'flask',
        'supabase',
        'groq',
        'google.generativeai',
        'sentence_transformers',
        'pdfplumber',
        'docx',
        'psycopg2',
        'sqlalchemy',
        'smtplib',
        'dotenv'
    ]
    
    failed_imports = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            failed_imports.append(package)
    
    if failed_imports:
        print(f"❌ Failed to import these packages: {', '.join(failed_imports)}")
        return False
    
    print("✅ All required packages imported successfully")
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        'static/uploads',
        'logs',
        'temp'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created necessary directories")
    return True

def main():
    """Main setup function"""
    print("🚀 Hiring Portal Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("❌ Setup failed at .env file creation")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("❌ Setup failed at directory creation")
        sys.exit(1)
    
    # Test imports
    if not test_imports():
        print("❌ Setup failed at import testing")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your actual configuration values")
    print("2. Set up your Supabase database using database_schema.sql")
    print("3. Run: python app.py")
    print("\nFor detailed setup instructions, see README.md")

if __name__ == "__main__":
    main()
