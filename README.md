# Accommodations Finder Tool - Complete Setup Guide

## 📋 Overview
This tool processes disability accommodation data from AskJAN.org and creates a searchable REST API for finding accommodations based on disabilities, limitations, or barriers.

## 🚀 Quick Start for Claude Code

### Prerequisites
- Python 3.8+
- PostgreSQL (local or cloud)
- The disability database document (text file)

### Step 1: Project Setup
```bash
# Create project directory
mkdir accommodations-finder
cd accommodations-finder

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Database Setup

#### Option A: Local PostgreSQL
```bash
# Mac
brew install postgresql
brew services start postgresql
createdb accommodations_db

# Linux
sudo apt-get install postgresql
sudo service postgresql start
sudo -u postgres createdb accommodations_db

# Windows - Use PostgreSQL installer from postgresql.org
```

#### Option B: Docker PostgreSQL
```bash
docker run -d \
  --name postgres-accommodations \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=accommodations_db \
  -p 5432:5432 \
  postgres:15
```

### Step 3: Configure Environment
Create a `.env` file:
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=accommodations_db
DB_USER=postgres
DB_PASSWORD=password

# Or use Railway/cloud database URL
# DATABASE_URL=postgresql://user:password@host:port/database

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=False
```

### Step 4: Process the Data
```bash
# Process the disability document
python process_askjan_data.py disability_database.txt

# This will create a 'processed_data' folder with JSON files
```

### Step 5: Load into Database
```bash
# Initialize database and load data
python load_to_database.py

# Answer 'yes' when prompted to create schema
```

### Step 6: Start the API
```bash
# Run the Flask API
python app.py

# API will be available at http://localhost:5000
```

## 📡 API Endpoints

### Search Accommodations
```
GET /api/search?q=fatigue&type=limitation
GET /api/search?q=diabetes&type=disability
GET /api/search?q=sitting&type=barrier
GET /api/search?q=flexible&type=accommodation
```

### List Resources
```
GET /api/disabilities          # List all disabilities
GET /api/limitations          # List all limitations
GET /api/barriers            # List all barriers
GET /api/stats              # Database statistics
```

### Get Details
```
GET /api/disabilities/1      # Get specific disability with accommodations
GET /api/accommodations/1/related  # Get related accommodations
```

## 🌐 Deployment to Railway

### 1. Prepare for Deployment
```bash
# Create Procfile
echo "web: python app.py" > Procfile

# Create railway.json
cat > railway.json << EOF
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python app.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF

# Update app.py to use PORT from environment
# Railway sets PORT environment variable
```

### 2. Deploy to Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize new project
railway init

# Add PostgreSQL database
railway add

# Deploy
railway up

# Get your app URL
railway open
```

## 📊 Expected Data Structure

After processing, you'll have:
- **~100 disabilities**
- **200-500 unique limitations**
- **100-300 unique barriers**
- **500-2000 unique accommodations**
- **Thousands of relationships** between them

## 🧪 Testing the API

### Test with curl
```bash
# Search for accommodations for fatigue
curl "http://localhost:5000/api/search?q=fatigue&type=limitation"

# Get all disabilities
curl "http://localhost:5000/api/disabilities"

# Get statistics
curl "http://localhost:5000/api/stats"
```

### Test with Python
```python
import requests

# Search for accommodations
response = requests.get('http://localhost:5000/api/search', 
                        params={'q': 'diabetes', 'type': 'disability'})
data = response.json()
print(f"Found {data['count']} accommodations")
for acc in data['results'][:5]:
    print(f"- {acc['accommodation_text']}")
```

## 🔧 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Check connection string
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('DATABASE_URL'))"
```

### Data Processing Issues
```bash
# Validate input file
head -100 disability_database.txt

# Check processed data
ls -la processed_data/
cat processed_data/disabilities.json | python -m json.tool | head -20
```

### API Issues
```bash
# Check Flask is installed
python -c "import flask; print(flask.__version__)"

# Run with debug mode
API_DEBUG=True python app.py
```

## 📁 Project Structure
```
accommodations-finder/
├── .env                      # Environment variables
├── requirements.txt          # Python dependencies
├── process_askjan_data.py    # Data parser and normalizer
├── load_to_database.py       # Database loader
├── app.py                    # Flask API server
├── Procfile                  # For deployment
├── railway.json              # Railway configuration
└── processed_data/           # Generated JSON files
    ├── disabilities.json
    ├── limitations.json
    ├── barriers.json
    ├── accommodations.json
    └── relationships/
        ├── disability_limitations.json
        ├── limitation_barriers.json
        ├── barrier_accommodations.json
        ├── disability_accommodations.json
        └── limitation_accommodations.json
```

## 🎯 Next Steps

1. **Add Frontend**: Create a React/Vue/HTML interface
2. **Enhanced Search**: Add fuzzy matching and synonyms
3. **Caching**: Add Redis for faster responses
4. **Analytics**: Track popular searches
5. **Export**: Add CSV/PDF export functionality
6. **AI Enhancement**: Use Claude API to suggest accommodations

## 📞 Support

If you encounter issues:
1. Check the error messages carefully
2. Verify all dependencies are installed
3. Ensure PostgreSQL is running
4. Check the .env file configuration
5. Look at the Flask debug output

## 📜 License

This tool processes publicly available information from AskJAN.org for accessibility purposes.

---

**Ready to start?** Run the commands above in order and you'll have a working accommodations finder API!
