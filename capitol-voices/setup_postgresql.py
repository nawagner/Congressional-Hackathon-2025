#!/usr/bin/env python3
"""
PostgreSQL Setup for CapitolVoices
Sets up PostgreSQL database and user for Congressional hearing data
"""

import os
import sys
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configuration
DB_NAME = "capitol_voices"
DB_USER = "capitol_voices"
DB_PASSWORD = "capitol_voices_password"
DB_HOST = "localhost"
DB_PORT = "5432"

def check_postgresql_installed():
    """Check if PostgreSQL is installed and running"""
    try:
        # Try to connect to default postgres database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database="postgres",
            user="postgres"
        )
        conn.close()
        print("✅ PostgreSQL is installed and running")
        return True
    except psycopg2.OperationalError as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("\nTo install PostgreSQL:")
        print("  macOS: brew install postgresql")
        print("  Ubuntu: sudo apt-get install postgresql postgresql-contrib")
        print("  Windows: Download from https://www.postgresql.org/download/")
        return False

def create_database_and_user():
    """Create database and user for CapitolVoices"""
    try:
        # Connect to postgres database as superuser
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database="postgres",
            user="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Create user
        try:
            cur.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}';")
            print(f"✅ Created user: {DB_USER}")
        except psycopg2.errors.DuplicateObject:
            print(f"ℹ️  User {DB_USER} already exists")
        
        # Create database
        try:
            cur.execute(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER};")
            print(f"✅ Created database: {DB_NAME}")
        except psycopg2.errors.DuplicateDatabase:
            print(f"ℹ️  Database {DB_NAME} already exists")
        
        # Grant privileges
        cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};")
        print(f"✅ Granted privileges to {DB_USER}")
        
        cur.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database setup failed: {e}")
        return False

def test_connection():
    """Test connection with the new user and database"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"✅ Connection successful!")
        print(f"   PostgreSQL version: {version}")
        cur.close()
        conn.close()
        return True
    except psycopg2.Error as e:
        print(f"❌ Connection test failed: {e}")
        return False

def create_env_file():
    """Create .env file with PostgreSQL configuration"""
    env_content = f"""# CapitolVoices PostgreSQL Configuration
STORAGE_ENGINE=postgresql
POSTGRESQL_CONNECTION_STRING=postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}
POSTGRESQL_SCHEMA=capitol_voices

# HuggingFace token for PyAnnote (required)
HF_TOKEN=your_huggingface_token_here

# Other settings
LOG_LEVEL=INFO
CHUNK_SECONDS=600
MAX_WORKERS=2
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ Created .env file with PostgreSQL configuration")
    print("   Please update HF_TOKEN with your HuggingFace token")

def install_dependencies():
    """Install required Python packages"""
    packages = [
        "psycopg2-binary",
        "sqlalchemy",
        "alembic"
    ]
    
    print("📦 Installing PostgreSQL dependencies...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")

def main():
    """Main setup function"""
    print("🏛️  CapitolVoices PostgreSQL Setup")
    print("=" * 50)
    
    # Check if PostgreSQL is installed
    if not check_postgresql_installed():
        print("\n❌ Please install and start PostgreSQL first")
        return False
    
    # Install Python dependencies
    install_dependencies()
    
    # Create database and user
    if not create_database_and_user():
        print("\n❌ Database setup failed")
        return False
    
    # Test connection
    if not test_connection():
        print("\n❌ Connection test failed")
        return False
    
    # Create .env file
    create_env_file()
    
    print("\n🎉 PostgreSQL setup complete!")
    print("\nNext steps:")
    print("1. Update .env file with your HuggingFace token")
    print("2. Run: python demo_congressional_setup.py")
    print("3. Launch: streamlit run ui/app.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
