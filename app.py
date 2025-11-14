#!/usr/bin/env python3
"""
Flask API for Accommodations Finder
Provides RESTful endpoints for searching accommodations by disability, limitation, or barrier
"""

import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# ============================================================================
# FLASK APP INITIALIZATION
# ============================================================================

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # Build URL from components
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    database = os.getenv('DB_NAME', 'accommodations_db')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', 'password')
    DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{database}"

# ============================================================================
# DATABASE CONNECTION HELPER
# ============================================================================

def get_db_connection():
    """Create a database connection with RealDictCursor for JSON-friendly output"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/')
def home():
    """Home route with API information"""
    return jsonify({
        'name': 'Accommodations Finder API',
        'version': '1.0',
        'endpoints': {
            '/api/search': 'Search accommodations (GET)',
            '/api/disabilities': 'List all disabilities (GET)',
            '/api/disabilities/<id>': 'Get specific disability (GET)',
            '/api/limitations': 'List all limitations (GET)',
            '/api/barriers': 'List all barriers (GET)',
            '/api/accommodations/<id>/related': 'Get related accommodations (GET)',
            '/api/stats': 'Get database statistics (GET)',
            '/health': 'Health check (GET)'
        },
        'documentation': 'Use /api/search?q=<query>&type=<disability|limitation|barrier|accommodation>'
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/search', methods=['GET'])
def search():
    """
    Main search endpoint
    Query params:
    - q: search query (required)
    - type: search type (disability, limitation, barrier, accommodation)
    - filter: accommodation type filter (equipment, schedule, environment, policy, assistance, general)
    - limit: max results (default 50)
    """
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'accommodation').lower()
    filter_type = request.args.get('filter')
    limit = int(request.args.get('limit', 50))
    
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        results = []
        
        if search_type == 'disability':
            results = search_by_disability(cur, query, limit)
        elif search_type == 'limitation':
            results = search_by_limitation(cur, query, limit)
        elif search_type == 'barrier':
            results = search_by_barrier(cur, query, limit)
        else:  # accommodation or general search
            results = search_accommodations(cur, query, filter_type, limit)
        
        cur.close()
        conn.close()
        
        return jsonify({
            'query': query,
            'type': search_type,
            'filter': filter_type,
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/disabilities', methods=['GET'])
def list_disabilities():
    """List all disabilities"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT disability_id, name
            FROM disabilities
            ORDER BY name
        """)
        
        disabilities = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({
            'count': len(disabilities),
            'disabilities': disabilities
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/disabilities/<int:disability_id>', methods=['GET'])
def get_disability(disability_id):
    """Get specific disability with all its accommodations"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get disability info
        cur.execute("""
            SELECT * FROM disabilities WHERE disability_id = %s
        """, (disability_id,))
        
        disability = cur.fetchone()
        
        if not disability:
            return jsonify({'error': 'Disability not found'}), 404
        
        # Get accommodations
        cur.execute("""
            SELECT DISTINCT
                a.accommodation_id,
                a.accommodation_text,
                a.accommodation_type
            FROM disability_accommodations da
            JOIN accommodations a ON da.accommodation_id = a.accommodation_id
            WHERE da.disability_id = %s
            ORDER BY a.accommodation_type, a.accommodation_text
        """, (disability_id,))
        
        accommodations = cur.fetchall()
        
        # Get limitations
        cur.execute("""
            SELECT l.limitation_id, l.limitation_name, l.category
            FROM disability_limitations dl
            JOIN limitations l ON dl.limitation_id = l.limitation_id
            WHERE dl.disability_id = %s
            ORDER BY l.category, l.limitation_name
        """, (disability_id,))
        
        limitations = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({
            'disability': disability,
            'accommodations': accommodations,
            'limitations': limitations
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/limitations', methods=['GET'])
def list_limitations():
    """List all limitations grouped by category"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT limitation_id, limitation_name, category
            FROM limitations
            ORDER BY category, limitation_name
        """)
        
        limitations = cur.fetchall()
        
        # Group by category
        grouped = {}
        for lim in limitations:
            category = lim['category'] or 'other'
            if category not in grouped:
                grouped[category] = []
            grouped[category].append({
                'id': lim['limitation_id'],
                'name': lim['limitation_name']
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            'count': len(limitations),
            'limitations': grouped
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/barriers', methods=['GET'])
def list_barriers():
    """List all barriers grouped by category"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT barrier_id, barrier_name, barrier_category
            FROM barriers
            ORDER BY barrier_category, barrier_name
        """)
        
        barriers = cur.fetchall()
        
        # Group by category
        grouped = {}
        for bar in barriers:
            category = bar['barrier_category']
            if category not in grouped:
                grouped[category] = []
            grouped[category].append({
                'id': bar['barrier_id'],
                'name': bar['barrier_name']
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            'count': len(barriers),
            'barriers': grouped
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/accommodations/<int:accommodation_id>/related', methods=['GET'])
def get_related_accommodations(accommodation_id):
    """Get accommodations related to a specific accommodation"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Find related accommodations through shared disabilities, limitations, and barriers
        cur.execute("""
            WITH related_items AS (
                -- Find all disabilities connected to this accommodation
                SELECT disability_id as item_id, 'disability' as item_type
                FROM disability_accommodations WHERE accommodation_id = %s
                UNION
                -- Find all limitations connected to this accommodation
                SELECT limitation_id as item_id, 'limitation' as item_type
                FROM limitation_accommodations WHERE accommodation_id = %s
                UNION
                -- Find all barriers connected to this accommodation
                SELECT barrier_id as item_id, 'barrier' as item_type
                FROM barrier_accommodations WHERE accommodation_id = %s
            )
            SELECT DISTINCT
                a.accommodation_id,
                a.accommodation_text,
                a.accommodation_type,
                COUNT(DISTINCT ri.item_id) as shared_connections
            FROM accommodations a
            JOIN (
                SELECT accommodation_id
                FROM disability_accommodations da
                JOIN related_items ri ON da.disability_id = ri.item_id AND ri.item_type = 'disability'
                UNION ALL
                SELECT accommodation_id
                FROM limitation_accommodations la
                JOIN related_items ri ON la.limitation_id = ri.item_id AND ri.item_type = 'limitation'
                UNION ALL
                SELECT accommodation_id
                FROM barrier_accommodations ba
                JOIN related_items ri ON ba.barrier_id = ri.item_id AND ri.item_type = 'barrier'
            ) related ON a.accommodation_id = related.accommodation_id
            WHERE a.accommodation_id != %s
            GROUP BY a.accommodation_id, a.accommodation_text, a.accommodation_type
            ORDER BY shared_connections DESC
            LIMIT 10
        """, (accommodation_id, accommodation_id, accommodation_id, accommodation_id))
        
        related = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({
            'accommodation_id': accommodation_id,
            'related': related
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        stats = {}
        
        # Count main entities
        tables = ['disabilities', 'limitations', 'barriers', 'accommodations']
        for table in tables:
            cur.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = cur.fetchone()['count']
        
        # Count relationships
        relationships = [
            'disability_limitations',
            'limitation_barriers',
            'barrier_accommodations',
            'disability_accommodations',
            'limitation_accommodations'
        ]
        
        stats['relationships'] = {}
        for rel in relationships:
            cur.execute(f"SELECT COUNT(*) as count FROM {rel}")
            stats['relationships'][rel] = cur.fetchone()['count']
        
        # Get top categories
        cur.execute("""
            SELECT barrier_category, COUNT(*) as count
            FROM barriers
            GROUP BY barrier_category
            ORDER BY count DESC
        """)
        stats['barrier_categories'] = cur.fetchall()
        
        cur.execute("""
            SELECT category, COUNT(*) as count
            FROM limitations
            GROUP BY category
            ORDER BY count DESC
        """)
        stats['limitation_categories'] = cur.fetchall()
        
        cur.execute("""
            SELECT accommodation_type, COUNT(*) as count
            FROM accommodations
            GROUP BY accommodation_type
            ORDER BY count DESC
        """)
        stats['accommodation_types'] = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# SEARCH FUNCTIONS
# ============================================================================

def search_by_disability(cur, query, limit):
    """Search for accommodations by disability"""
    sql = """
        WITH disability_match AS (
            SELECT disability_id, name
            FROM disabilities
            WHERE to_tsvector('english', name) @@ plainto_tsquery('english', %s)
               OR name ILIKE %s
            LIMIT 1
        )
        SELECT DISTINCT
            a.accommodation_id,
            a.accommodation_text,
            a.accommodation_type,
            dm.name as disability_name
        FROM disability_match dm
        JOIN disability_accommodations da ON dm.disability_id = da.disability_id
        JOIN accommodations a ON da.accommodation_id = a.accommodation_id
        
        UNION
        
        SELECT DISTINCT
            a.accommodation_id,
            a.accommodation_text,
            a.accommodation_type,
            dm.name as disability_name
        FROM disability_match dm
        JOIN disability_limitations dl ON dm.disability_id = dl.disability_id
        JOIN limitation_accommodations la ON dl.limitation_id = la.limitation_id
        JOIN accommodations a ON la.accommodation_id = a.accommodation_id
        
        LIMIT %s
    """
    
    cur.execute(sql, (query, f'%{query}%', limit))
    return cur.fetchall()

def search_by_limitation(cur, query, limit):
    """Search for accommodations by limitation"""
    sql = """
        WITH limitation_match AS (
            SELECT limitation_id, limitation_name, category
            FROM limitations
            WHERE to_tsvector('english', limitation_name) @@ plainto_tsquery('english', %s)
               OR limitation_name ILIKE %s
        )
        SELECT DISTINCT
            a.accommodation_id,
            a.accommodation_text,
            a.accommodation_type,
            lm.limitation_name,
            lm.category as limitation_category
        FROM limitation_match lm
        JOIN limitation_accommodations la ON lm.limitation_id = la.limitation_id
        JOIN accommodations a ON la.accommodation_id = a.accommodation_id
        ORDER BY a.accommodation_type, a.accommodation_text
        LIMIT %s
    """
    
    cur.execute(sql, (query, f'%{query}%', limit))
    return cur.fetchall()

def search_by_barrier(cur, query, limit):
    """Search for accommodations by barrier"""
    sql = """
        WITH barrier_match AS (
            SELECT barrier_id, barrier_name, barrier_category
            FROM barriers
            WHERE to_tsvector('english', barrier_name) @@ plainto_tsquery('english', %s)
               OR barrier_name ILIKE %s
        )
        SELECT DISTINCT
            a.accommodation_id,
            a.accommodation_text,
            a.accommodation_type,
            bm.barrier_name,
            bm.barrier_category
        FROM barrier_match bm
        JOIN barrier_accommodations ba ON bm.barrier_id = ba.barrier_id
        JOIN accommodations a ON ba.accommodation_id = a.accommodation_id
        ORDER BY a.accommodation_type, a.accommodation_text
        LIMIT %s
    """
    
    cur.execute(sql, (query, f'%{query}%', limit))
    return cur.fetchall()

def search_accommodations(cur, query, filter_type, limit):
    """General search across all accommodations"""
    sql = """
        SELECT DISTINCT
            a.accommodation_id,
            a.accommodation_text,
            a.accommodation_type,
            ts_rank(to_tsvector('english', a.accommodation_text), 
                   plainto_tsquery('english', %s)) as relevance
        FROM accommodations a
        WHERE to_tsvector('english', accommodation_text) @@ plainto_tsquery('english', %s)
           OR accommodation_text ILIKE %s
    """
    
    params = [query, query, f'%{query}%']
    
    if filter_type:
        sql += " AND a.accommodation_type = %s"
        params.append(filter_type)
    
    sql += " ORDER BY relevance DESC LIMIT %s"
    params.append(limit)
    
    cur.execute(sql, params)
    return cur.fetchall()

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('API_DEBUG', 'False').lower() == 'true'
    
    print("=" * 60)
    print("  Accommodations Finder API")
    print("=" * 60)
    print(f"\n🚀 Starting server on http://{host}:{port}")
    print(f"📝 API documentation available at http://{host}:{port}/")
    print("\nEndpoints:")
    print("  • GET /api/search?q=<query>&type=<type>")
    print("  • GET /api/disabilities")
    print("  • GET /api/limitations")
    print("  • GET /api/barriers")
    print("  • GET /api/stats")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(host=host, port=port, debug=debug)
