#!/usr/bin/env python3
"""
Database Setup and Data Loading Script
Run this after process_askjan_data.py to load data into PostgreSQL
"""

import json
import os
import sys
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# DATABASE SCHEMA
# ============================================================================

SCHEMA_SQL = """
-- Drop existing tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS limitation_accommodations CASCADE;
DROP TABLE IF EXISTS disability_accommodations CASCADE;
DROP TABLE IF EXISTS barrier_accommodations CASCADE;
DROP TABLE IF EXISTS limitation_barriers CASCADE;
DROP TABLE IF EXISTS disability_limitations CASCADE;
DROP TABLE IF EXISTS accommodations CASCADE;
DROP TABLE IF EXISTS barriers CASCADE;
DROP TABLE IF EXISTS limitations CASCADE;
DROP TABLE IF EXISTS disabilities CASCADE;

-- Core Tables
CREATE TABLE disabilities (
    disability_id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    about_description TEXT,
    accommodating_employees_info TEXT,
    questions_to_consider TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE limitations (
    limitation_id SERIAL PRIMARY KEY,
    limitation_name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE barriers (
    barrier_id SERIAL PRIMARY KEY,
    barrier_name VARCHAR(255) UNIQUE NOT NULL,
    barrier_category VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accommodations (
    accommodation_id SERIAL PRIMARY KEY,
    accommodation_text TEXT UNIQUE NOT NULL,
    accommodation_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Junction Tables (Relationships)
CREATE TABLE disability_limitations (
    disability_id INTEGER REFERENCES disabilities(disability_id) ON DELETE CASCADE,
    limitation_id INTEGER REFERENCES limitations(limitation_id) ON DELETE CASCADE,
    PRIMARY KEY (disability_id, limitation_id)
);

CREATE TABLE limitation_barriers (
    limitation_id INTEGER REFERENCES limitations(limitation_id) ON DELETE CASCADE,
    barrier_id INTEGER REFERENCES barriers(barrier_id) ON DELETE CASCADE,
    PRIMARY KEY (limitation_id, barrier_id)
);

CREATE TABLE barrier_accommodations (
    barrier_id INTEGER REFERENCES barriers(barrier_id) ON DELETE CASCADE,
    accommodation_id INTEGER REFERENCES accommodations(accommodation_id) ON DELETE CASCADE,
    PRIMARY KEY (barrier_id, accommodation_id)
);

CREATE TABLE disability_accommodations (
    disability_id INTEGER REFERENCES disabilities(disability_id) ON DELETE CASCADE,
    accommodation_id INTEGER REFERENCES accommodations(accommodation_id) ON DELETE CASCADE,
    PRIMARY KEY (disability_id, accommodation_id)
);

CREATE TABLE limitation_accommodations (
    limitation_id INTEGER REFERENCES limitations(limitation_id) ON DELETE CASCADE,
    accommodation_id INTEGER REFERENCES accommodations(accommodation_id) ON DELETE CASCADE,
    PRIMARY KEY (limitation_id, accommodation_id)
);

-- Indexes for better search performance
CREATE INDEX idx_disability_name ON disabilities(name);
CREATE INDEX idx_limitation_name ON limitations(limitation_name);
CREATE INDEX idx_barrier_name ON barriers(barrier_name);
CREATE INDEX idx_accommodation_text ON accommodations(accommodation_text);

-- Full-text search indexes
CREATE INDEX idx_disability_name_fts ON disabilities USING gin(to_tsvector('english', name));
CREATE INDEX idx_disability_about_fts ON disabilities USING gin(to_tsvector('english', about_description));
CREATE INDEX idx_limitation_name_fts ON limitations USING gin(to_tsvector('english', limitation_name));
CREATE INDEX idx_barrier_name_fts ON barriers USING gin(to_tsvector('english', barrier_name));
CREATE INDEX idx_accommodation_text_fts ON accommodations USING gin(to_tsvector('english', accommodation_text));

-- Relationship indexes
CREATE INDEX idx_dl_disability ON disability_limitations(disability_id);
CREATE INDEX idx_dl_limitation ON disability_limitations(limitation_id);
CREATE INDEX idx_lb_limitation ON limitation_barriers(limitation_id);
CREATE INDEX idx_lb_barrier ON limitation_barriers(barrier_id);
CREATE INDEX idx_ba_barrier ON barrier_accommodations(barrier_id);
CREATE INDEX idx_ba_accommodation ON barrier_accommodations(accommodation_id);
CREATE INDEX idx_da_disability ON disability_accommodations(disability_id);
CREATE INDEX idx_da_accommodation ON disability_accommodations(accommodation_id);
CREATE INDEX idx_la_limitation ON limitation_accommodations(limitation_id);
CREATE INDEX idx_la_accommodation ON limitation_accommodations(accommodation_id);
"""

# ============================================================================
# DATABASE LOADER CLASS
# ============================================================================

class DatabaseLoader:
    """Handles database initialization and data loading"""
    
    def __init__(self):
        """Initialize database connection"""
        # Get database URL from environment or use default
        self.database_url = os.getenv('DATABASE_URL')
        
        if not self.database_url:
            # Build URL from individual components
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            database = os.getenv('DB_NAME', 'accommodations_db')
            user = os.getenv('DB_USER', 'postgres')
            password = os.getenv('DB_PASSWORD', 'password')
            
            self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        print(f"📡 Connecting to database...")
        
        try:
            self.conn = psycopg2.connect(self.database_url)
            self.cur = self.conn.cursor()
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            print("\nPlease ensure PostgreSQL is running and check your .env file:")
            print("  DATABASE_URL=postgresql://user:password@localhost:5432/accommodations_db")
            print("  or individual variables: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
            sys.exit(1)
    
    def create_schema(self):
        """Create database schema"""
        print("\n🏗️  Creating database schema...")
        try:
            self.cur.execute(SCHEMA_SQL)
            self.conn.commit()
            print("✅ Schema created successfully")
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Error creating schema: {e}")
            raise
    
    def load_data(self, data_dir: str = 'processed_data'):
        """Load all data from JSON files into database"""
        print(f"\n📥 Loading data from {data_dir}/...")
        
        try:
            # Load disabilities
            self._load_disabilities(f'{data_dir}/disabilities.json')
            
            # Load limitations
            self._load_limitations(f'{data_dir}/limitations.json')
            
            # Load barriers
            self._load_barriers(f'{data_dir}/barriers.json')
            
            # Load accommodations
            self._load_accommodations(f'{data_dir}/accommodations.json')
            
            # Load relationships
            self._load_relationships(f'{data_dir}/relationships')
            
            # Commit all changes
            self.conn.commit()
            print("\n✅ All data loaded successfully!")
            
            # Print statistics
            self._print_statistics()
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Error loading data: {e}")
            raise
    
    def _load_disabilities(self, file_path: str):
        """Load disabilities into database"""
        with open(file_path, 'r') as f:
            disabilities = json.load(f)
        
        query = """
            INSERT INTO disabilities 
            (disability_id, name, about_description, accommodating_employees_info, questions_to_consider)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (disability_id) DO UPDATE
            SET name = EXCLUDED.name,
                about_description = EXCLUDED.about_description,
                accommodating_employees_info = EXCLUDED.accommodating_employees_info,
                questions_to_consider = EXCLUDED.questions_to_consider,
                updated_at = CURRENT_TIMESTAMP
        """
        
        data = []
        for d in disabilities:
            data.append((
                d['disability_id'],
                d['name'],
                d.get('about_description', ''),
                d.get('accommodating_employees_info', ''),
                d.get('questions_to_consider', [])
            ))
        
        execute_batch(self.cur, query, data)
        print(f"  ✓ Loaded {len(disabilities)} disabilities")
    
    def _load_limitations(self, file_path: str):
        """Load limitations into database"""
        with open(file_path, 'r') as f:
            limitations = json.load(f)
        
        query = """
            INSERT INTO limitations (limitation_id, limitation_name, category, description)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (limitation_id) DO UPDATE
            SET limitation_name = EXCLUDED.limitation_name,
                category = EXCLUDED.category,
                description = EXCLUDED.description
        """
        
        data = []
        for l in limitations:
            data.append((
                l['limitation_id'],
                l['limitation_name'],
                l.get('category'),
                l.get('description', '')
            ))
        
        execute_batch(self.cur, query, data)
        print(f"  ✓ Loaded {len(limitations)} limitations")
    
    def _load_barriers(self, file_path: str):
        """Load barriers into database"""
        with open(file_path, 'r') as f:
            barriers = json.load(f)
        
        query = """
            INSERT INTO barriers (barrier_id, barrier_name, barrier_category, description)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (barrier_id) DO UPDATE
            SET barrier_name = EXCLUDED.barrier_name,
                barrier_category = EXCLUDED.barrier_category,
                description = EXCLUDED.description
        """
        
        data = []
        for b in barriers:
            data.append((
                b['barrier_id'],
                b['barrier_name'],
                b['barrier_category'],
                b.get('description', '')
            ))
        
        execute_batch(self.cur, query, data)
        print(f"  ✓ Loaded {len(barriers)} barriers")
    
    def _load_accommodations(self, file_path: str):
        """Load accommodations into database"""
        with open(file_path, 'r') as f:
            accommodations = json.load(f)
        
        query = """
            INSERT INTO accommodations (accommodation_id, accommodation_text, accommodation_type)
            VALUES (%s, %s, %s)
            ON CONFLICT (accommodation_id) DO UPDATE
            SET accommodation_text = EXCLUDED.accommodation_text,
                accommodation_type = EXCLUDED.accommodation_type
        """
        
        data = []
        for a in accommodations:
            data.append((
                a['accommodation_id'],
                a['accommodation_text'],
                a.get('accommodation_type', 'general')
            ))
        
        # Use smaller page size for accommodations as there might be many
        execute_batch(self.cur, query, data, page_size=100)
        print(f"  ✓ Loaded {len(accommodations)} accommodations")
    
    def _load_relationships(self, relationships_dir: str):
        """Load all relationship tables"""
        relationships = [
            ('disability_limitations', 'disability_id', 'limitation_id'),
            ('limitation_barriers', 'limitation_id', 'barrier_id'),
            ('barrier_accommodations', 'barrier_id', 'accommodation_id'),
            ('disability_accommodations', 'disability_id', 'accommodation_id'),
            ('limitation_accommodations', 'limitation_id', 'accommodation_id')
        ]
        
        print("  Loading relationships:")
        
        for table, col1, col2 in relationships:
            file_path = f'{relationships_dir}/{table}.json'
            
            if not os.path.exists(file_path):
                print(f"    ⚠ Skipping {table} (file not found)")
                continue
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if data:
                query = f"""
                    INSERT INTO {table} ({col1}, {col2})
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """
                
                batch_data = [(item[col1], item[col2]) for item in data]
                execute_batch(self.cur, query, batch_data)
                print(f"    ✓ {table}: {len(data)} relationships")
    
    def _print_statistics(self):
        """Print database statistics"""
        print("\n📊 Database Statistics:")
        
        tables = [
            'disabilities',
            'limitations',
            'barriers',
            'accommodations',
            'disability_limitations',
            'limitation_barriers',
            'barrier_accommodations',
            'disability_accommodations',
            'limitation_accommodations'
        ]
        
        for table in tables:
            self.cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cur.fetchone()[0]
            print(f"  • {table}: {count} records")
    
    def close(self):
        """Close database connection"""
        self.cur.close()
        self.conn.close()
        print("\n👋 Database connection closed")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    print("=" * 60)
    print("  AskJAN Database Loader")
    print("=" * 60)
    
    # Check if processed data exists
    if not os.path.exists('processed_data'):
        print("\n❌ Error: 'processed_data' folder not found")
        print("Please run 'python process_askjan_data.py' first to process the data")
        sys.exit(1)
    
    # Check for .env file
    if not os.path.exists('.env'):
        print("\n⚠️  Warning: No .env file found")
        print("Creating a default .env file...")
        
        with open('.env', 'w') as f:
            f.write("""# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=accommodations_db
DB_USER=postgres
DB_PASSWORD=password

# Or use a single DATABASE_URL
# DATABASE_URL=postgresql://user:password@localhost:5432/accommodations_db

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=False
""")
        print("✅ Created .env file - please update with your database credentials")
        print("Then run this script again")
        sys.exit(0)
    
    # Load the database
    loader = DatabaseLoader()
    
    try:
        # Ask user if they want to recreate schema
        response = input("\n⚠️  This will DROP and recreate all tables. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Operation cancelled")
            sys.exit(0)
        
        # Create schema
        loader.create_schema()
        
        # Load data
        loader.load_data()
        
        print("\n✅ SUCCESS! Database is ready for use.")
        print("\nNext step: Run 'python api/app.py' to start the API server")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        loader.close()

if __name__ == "__main__":
    main()
