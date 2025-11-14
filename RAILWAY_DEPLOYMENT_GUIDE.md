# 🚂 Railway Deployment Guide for Accommodations Finder

## Prerequisites
- GitHub account (for code repository)
- Railway account (sign up at railway.app)
- Processed data (we'll create this once you upload the document)

## Step 1: Prepare Your GitHub Repository

1. Create a new repository on GitHub called `accommodations-finder`

2. Clone it locally:
```bash
git clone https://github.com/YOUR_USERNAME/accommodations-finder.git
cd accommodations-finder
```

3. Add all the files I've created:
```bash
# Copy all files from Claude's output
# Add them to your repository
git add .
git commit -m "Initial commit - Accommodations Finder API"
git push origin main
```

## Step 2: Sign Up for Railway

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub (recommended for easy deployment)
3. You get $5 free credits monthly (enough for this project initially)

## Step 3: Create New Project on Railway

1. Click "New Project" in Railway dashboard
2. Choose "Deploy from GitHub repo"
3. Select your `accommodations-finder` repository
4. Railway will automatically detect it's a Python app

## Step 4: Add PostgreSQL Database

1. In your Railway project, click "+ New"
2. Choose "Database" → "Add PostgreSQL"
3. Railway will automatically create a PostgreSQL instance
4. It will inject the `DATABASE_URL` environment variable

## Step 5: Configure Environment Variables

In Railway project settings, add these variables:

```env
API_DEBUG=False
PYTHON_VERSION=3.11
```

Railway automatically provides:
- `DATABASE_URL` (PostgreSQL connection string)
- `PORT` (port number for your app)

## Step 6: Initial Data Load

Since we need to process and load your data, we have two options:

### Option A: One-Time Setup Service (Recommended)
1. Create a temporary "setup" service in Railway
2. Set the start command to:
   ```
   python process_askjan_data.py disability_database.txt && python load_to_database.py
   ```
3. Run it once to populate the database
4. Then switch to the main API service

### Option B: Include Data in Repository
1. Process data locally first
2. Commit the `processed_data/` folder to Git
3. Add a startup script that loads data if tables are empty

## Step 7: Deploy the API

1. Push your code to GitHub:
```bash
git add .
git commit -m "Add Railway configuration"
git push origin main
```

2. Railway will automatically deploy when you push

3. Your API will be available at:
   ```
   https://YOUR-APP-NAME.railway.app
   ```

## Step 8: Test Your Deployment

```bash
# Check health
curl https://YOUR-APP-NAME.railway.app/health

# Get statistics
curl https://YOUR-APP-NAME.railway.app/api/stats

# Search for accommodations
curl "https://YOUR-APP-NAME.railway.app/api/search?q=fatigue&type=limitation"
```

## 📊 Railway Pricing (as of 2024)

- **Free tier**: $5 credits/month
- **Hobby tier**: $5/month (includes $5 credits)
- **Pro tier**: $20/month (includes $20 credits)

Your app will likely use:
- PostgreSQL: ~$5-7/month
- API service: ~$3-5/month
- **Total: ~$8-12/month**

## 🚀 Quick Deploy Script

Create `deploy.sh`:
```bash
#!/bin/bash
echo "🚀 Deploying to Railway..."

# Process data
python process_askjan_data.py disability_database.txt

# Commit changes
git add .
git commit -m "Update data and deploy"
git push origin main

echo "✅ Deployment triggered! Check Railway dashboard for status."
```

## 🔧 Troubleshooting

### Database Connection Issues
Check that Railway injected `DATABASE_URL`:
```python
import os
print(os.environ.get('DATABASE_URL'))
```

### Port Binding Issues
Ensure your app binds to `0.0.0.0:$PORT`:
```python
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
```

### Memory Issues
If you exceed memory limits:
1. Upgrade to Hobby plan
2. Optimize data processing (batch operations)
3. Add pagination to API responses

## 📝 Railway CLI Alternative

Install Railway CLI for easier management:
```bash
# Install
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Deploy
railway up

# View logs
railway logs

# Run commands
railway run python process_askjan_data.py disability_database.txt
```

## ✅ Final Checklist

- [ ] GitHub repository created
- [ ] All Python files added to repo
- [ ] requirements.txt included
- [ ] railway.json configured
- [ ] Procfile created
- [ ] Railway project created
- [ ] PostgreSQL database added
- [ ] Environment variables set
- [ ] Data processed and loaded
- [ ] API deployed and tested

## 🎉 Success Metrics

When everything is working, you should see:
- API responding at https://YOUR-APP.railway.app
- `/api/stats` showing your data counts
- `/api/search` returning accommodations
- Response times under 200ms
- 99.9% uptime

## Need Help?

- Railway Discord: https://discord.gg/railway
- Railway Docs: https://docs.railway.app
- Status Page: https://status.railway.app

---

**Ready to deploy?** First, upload your disability_database.txt file so we can process it!
