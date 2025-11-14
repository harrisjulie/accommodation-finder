#!/usr/bin/env python3
"""
All-in-One Setup Script for Accommodations Finder
Run this single script to process data, setup database, and start the API
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def run_command(cmd, description):
    """Run a shell command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True
        else:
            print(f"❌ {description} - Failed")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def check_prerequisites():
    """Check if all prerequisites are installed"""
    print_header("Checking Prerequisites")
    
    # Check Python
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        print(f"✅ Python {python_version.major}.{python_version.minor} installed")
    else:
        print(f"❌ Python 3.8+ required (found {python_version.major}.{python_version.minor})")
        return False
    
    # Check for input file
    input_files = list(Path('.').glob('*.txt')) + list(Path('.').glob('*.docx'))
    if not input_files:
        print("❌ No input file found (looking for .txt or .docx file)")
        print("   Please add your disability database file to this directory")
        return False
    
    print(f"✅ Found input file: {input_files[0]}")
    
    return True, input_files[0] if input_files else None

def setup_virtual_environment():
    """Create and activate virtual environment"""
    print_header("Setting Up Virtual Environment")
    
    if not os.path.exists('venv'):
        if not run_command('python -m venv venv', 'Creating virtual environment'):
            return False
    else:
        print("✅ Virtual environment already exists")
    
    # Install requirements
    pip_cmd = 'venv\\Scripts\\pip' if os.name == 'nt' else 'venv/bin/pip'
    
    # Create requirements.txt if it doesn't exist
    if not os.path.exists('requirements.txt'):
        print("📝 Creating requirements.txt...")
        with open('requirements.txt', 'w') as f:
            f.write("""psycopg2-binary==2.9.9
python-dotenv==1.0.0
flask==3.0.0
flask-cors==4.0.0
pandas==2.1.3
gunicorn==21.2.0
""")
    
    if not run_command(f'{pip_cmd} install -r requirements.txt', 'Installing dependencies'):
        return False
    
    return True

def create_env_file():
    """Create .env file if it doesn't exist"""
    print_header("Setting Up Environment Configuration")
    
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return True
    
    print("📝 Creating .env file with default configuration...")
    
    env_content = """# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=accommodations_db
DB_USER=postgres
DB_PASSWORD=password

# Or use a single DATABASE_URL (for cloud databases)
# DATABASE_URL=postgresql://user:password@localhost:5432/accommodations_db

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=False
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file")
    print("⚠️  Please update the database credentials if needed")
    
    return True

def check_postgresql():
    """Check if PostgreSQL is available"""
    print_header("Checking PostgreSQL")
    
    # Try to import psycopg2
    try:
        import psycopg2
        print("✅ psycopg2 installed")
    except ImportError:
        print("❌ psycopg2 not installed - installing now...")
        pip_cmd = 'venv\\Scripts\\pip' if os.name == 'nt' else 'venv/bin/pip'
        run_command(f'{pip_cmd} install psycopg2-binary', 'Installing psycopg2')
    
    # Try to connect to PostgreSQL
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        import psycopg2
        
        # Get connection details
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', 'password')
        
        # Try to connect
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        conn.close()
        print("✅ PostgreSQL connection successful")
        
        # Try to create database if it doesn't exist
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'accommodations_db'")
        exists = cur.fetchone()
        
        if not exists:
            cur.execute("CREATE DATABASE accommodations_db")
            print("✅ Created database 'accommodations_db'")
        else:
            print("✅ Database 'accommodations_db' exists")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"⚠️  PostgreSQL connection failed: {e}")
        print("\n📋 PostgreSQL Setup Options:")
        print("1. Install PostgreSQL locally:")
        print("   - Mac: brew install postgresql")
        print("   - Linux: sudo apt-get install postgresql")
        print("   - Windows: Download from postgresql.org")
        print("\n2. Use Docker:")
        print("   docker run -d --name postgres-accommodations \\")
        print("     -e POSTGRES_PASSWORD=password \\")
        print("     -e POSTGRES_DB=accommodations_db \\")
        print("     -p 5432:5432 postgres:15")
        print("\n3. Use a cloud database (update .env with connection string)")
        
        response = input("\nContinue anyway? (y/n): ")
        return response.lower() == 'y'

def process_data(input_file):
    """Process the disability data"""
    print_header("Processing Disability Data")
    
    python_cmd = 'venv\\Scripts\\python' if os.name == 'nt' else 'venv/bin/python'
    
    # Check if processing script exists
    if not os.path.exists('process_askjan_data.py'):
        print("❌ process_askjan_data.py not found")
        print("   Please ensure all script files are in the current directory")
        return False
    
    # Run the processing script
    cmd = f'{python_cmd} process_askjan_data.py "{input_file}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Data processing complete")
        print(result.stdout)
        
        # Check if processed_data directory was created
        if os.path.exists('processed_data'):
            # Count processed items
            try:
                with open('processed_data/disabilities.json', 'r') as f:
                    disabilities = json.load(f)
                    print(f"📊 Processed {len(disabilities)} disabilities")
            except:
                pass
        
        return True
    else:
        print("❌ Data processing failed")
        print(result.stderr)
        return False

def load_database():
    """Load data into PostgreSQL"""
    print_header("Loading Data into Database")
    
    python_cmd = 'venv\\Scripts\\python' if os.name == 'nt' else 'venv/bin/python'
    
    # Check if loader script exists
    if not os.path.exists('load_to_database.py'):
        print("❌ load_to_database.py not found")
        return False
    
    # Check if processed data exists
    if not os.path.exists('processed_data'):
        print("❌ processed_data directory not found")
        print("   Please run data processing first")
        return False
    
    print("⚠️  This will DROP and recreate all database tables")
    print("   This is normal for initial setup")
    
    # Run the loader script with automatic 'yes' response
    cmd = f'echo yes | {python_cmd} load_to_database.py'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if "SUCCESS" in result.stdout or result.returncode == 0:
        print("✅ Database loaded successfully")
        print(result.stdout)
        return True
    else:
        print("❌ Database loading failed")
        print(result.stderr)
        return False

def start_api():
    """Start the Flask API server"""
    print_header("Starting API Server")
    
    python_cmd = 'venv\\Scripts\\python' if os.name == 'nt' else 'venv/bin/python'
    
    # Check if API script exists
    if not os.path.exists('app.py'):
        print("❌ app.py not found")
        return False
    
    print("🚀 Starting Flask API server...")
    print("   API will be available at http://localhost:5000")
    print("   Press Ctrl+C to stop the server")
    print("\n" + "=" * 60)
    
    # Start the API server
    try:
        subprocess.run(f'{python_cmd} app.py', shell=True)
    except KeyboardInterrupt:
        print("\n\n👋 API server stopped")
        return True

def main():
    """Main execution"""
    print_header("ACCOMMODATIONS FINDER - AUTOMATED SETUP")
    
    # Step 1: Check prerequisites
    prereq_result = check_prerequisites()
    if not prereq_result[0]:
        print("\n❌ Prerequisites check failed")
        sys.exit(1)
    
    input_file = prereq_result[1]
    
    # Step 2: Setup virtual environment
    if not setup_virtual_environment():
        print("\n❌ Virtual environment setup failed")
        sys.exit(1)
    
    # Step 3: Create .env file
    if not create_env_file():
        print("\n❌ Environment configuration failed")
        sys.exit(1)
    
    # Step 4: Check PostgreSQL
    if not check_postgresql():
        print("\n⚠️  Continuing without database")
        print("   You can still process the data but won't be able to run the API")
    
    # Step 5: Process data
    if not process_data(input_file):
        print("\n❌ Data processing failed")
        print("   Please check the input file format")
        sys.exit(1)
    
    # Step 6: Load database
    db_loaded = load_database()
    if not db_loaded:
        print("\n⚠️  Database not loaded - API will not work")
        print("   Fix PostgreSQL connection and run: python load_to_database.py")
    
    # Step 7: Summary
    print_header("SETUP COMPLETE")
    
    if db_loaded:
        print("✅ Everything is ready!")
        print("\n📋 Next steps:")
        print("1. Start the API: python app.py")
        print("2. Test the API: curl http://localhost:5000/api/stats")
        print("3. Deploy to cloud: Follow README.md instructions")
        
        print("\n🎯 Quick test URLs:")
        print("   http://localhost:5000/")
        print("   http://localhost:5000/api/disabilities")
        print("   http://localhost:5000/api/search?q=fatigue&type=limitation")
        
        response = input("\n🚀 Start the API server now? (y/n): ")
        if response.lower() == 'y':
            start_api()
    else:
        print("⚠️  Setup partially complete")
        print("   Data has been processed but database is not configured")
        print("   Please setup PostgreSQL and run: python load_to_database.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
