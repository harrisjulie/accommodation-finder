# 🚀 Deploy to Railway NOW - Quick Guide

## Your Railway Details
- **Project ID**: `f53ac83d-1ad4-4f42-bda6-9b7834b0881f`
- **Project Dashboard**: https://railway.app/project/f53ac83d-1ad4-4f42-bda6-9b7834b0881f
- **GitHub Repo**: https://github.com/harrisjulie/accommodation-finder

## Option 1: Deploy via Railway Dashboard (Recommended - 5 minutes)

### Step 1: Open Your Railway Project
1. Go to: https://railway.app/project/f53ac83d-1ad4-4f42-bda6-9b7834b0881f
2. Log in with your Railway account

### Step 2: Create a New Service
1. Click **"+ New"** button
2. Select **"GitHub Repo"**
3. If prompted, authorize Railway to access your GitHub account
4. Select repository: **harrisjulie/accommodation-finder**
5. Select branch: **main** (or the branch with your code)
6. Click **"Deploy Now"**

### Step 3: Railway Auto-Detects Everything
Railway will automatically:
- ✅ Detect it's a Python application
- ✅ Find `requirements.txt` and install dependencies
- ✅ Find `Procfile` and run: `web: python app.py`
- ✅ Use `railway.json` for build configuration
- ✅ Assign a public URL

### Step 4: Wait for Deployment (2-3 minutes)
- Watch the deployment logs in real-time
- Look for: "✓ Build successful" and "✓ Deployment live"

### Step 5: Get Your URL
1. Once deployed, click on your service
2. Go to **"Settings"** → **"Networking"**
3. Click **"Generate Domain"**
4. Your app will be live at: `https://your-service.railway.app`

## Option 2: Deploy via Railway CLI (If Network Allows)

### Install Railway CLI:
```bash
npm install -g @railway/cli
```

### Set Environment Variable:
```bash
export RAILWAY_TOKEN="8c7aa644-15b5-4ac1-9cf1-9125486e216a"
```

### Link and Deploy:
```bash
# Link to your project
railway link f53ac83d-1ad4-4f42-bda6-9b7834b0881f

# Set environment variables
railway variables set PYTHON_VERSION="3.11"

# Deploy
railway up
```

## Option 3: Auto-Deploy from GitHub (Set and Forget)

### Enable Auto-Deployment:
1. Go to your Railway service settings
2. Under **"Source"**, enable:
   - ✅ **"Automatic deployments"**
   - ✅ **"Watch paths"**: Leave empty to watch all files

### Now Every Git Push Auto-Deploys:
```bash
git add .
git commit -m "Update accommodation data"
git push origin main
```
Railway will automatically deploy within 30 seconds!

## What Gets Deployed

Your Railway deployment includes:

**Application Files:**
- ✅ `app.py` - Flask API server
- ✅ `index.html` - Frontend interface
- ✅ All JSON data files (accommodations, disabilities, etc.)

**Configuration:**
- ✅ `Procfile` - Start command
- ✅ `railway.json` - Build settings
- ✅ `requirements.txt` - Python dependencies

**Runtime:**
- 🐍 Python 3.11
- 🌐 Flask web server
- 📊 Static JSON database (no PostgreSQL needed for current setup)

## Environment Variables (Optional)

If you want to customize:

```bash
railway variables set PYTHON_VERSION="3.11"
railway variables set API_DEBUG="False"
railway variables set API_HOST="0.0.0.0"
railway variables set API_PORT="$PORT"
```

## After Deployment - Test Your API

Once deployed, test these endpoints:

### 1. Health Check
```bash
curl https://your-service.railway.app/health
```

### 2. Get All Accommodations
```bash
curl https://your-service.railway.app/api/accommodations
```

### 3. Get All Disabilities
```bash
curl https://your-service.railway.app/api/disabilities
```

### 4. Search
```bash
curl "https://your-service.railway.app/api/search?q=ADHD"
```

### 5. View Frontend
Open in browser:
```
https://your-service.railway.app/
```

## Adding PostgreSQL Database (Future Enhancement)

If you want to upgrade to PostgreSQL later:

1. In Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway auto-injects `DATABASE_URL` environment variable
4. Update `app.py` to use PostgreSQL instead of JSON files

## Troubleshooting

### Deployment Failed?
- Check build logs in Railway dashboard
- Verify `requirements.txt` lists all dependencies
- Ensure Python version is compatible (3.11)

### Can't Access URL?
- Check if service is running (green indicator)
- Verify domain is generated in Settings → Networking
- Check for port binding issues in logs

### Need Database?
- Current setup uses JSON files (no database needed)
- PostgreSQL optional for future scaling

## Cost Estimate

**Railway Pricing:**
- Free tier: $5 credits/month
- This app (without database): ~$3-5/month
- With PostgreSQL: ~$8-12/month

## Success Checklist

After deployment, you should see:

- [ ] Service shows as "Active" (green)
- [ ] Public URL is generated
- [ ] Health endpoint returns 200 OK
- [ ] Frontend loads in browser
- [ ] API endpoints return data
- [ ] No errors in deployment logs

## Next Steps

1. ✅ Deploy via Railway dashboard (5 minutes)
2. ✅ Test all endpoints
3. ✅ Enable auto-deployment from GitHub
4. ✅ Share your live URL!

---

**Need Help?**
- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Issues: https://github.com/harrisjulie/accommodation-finder/issues

**Your deployment is ready to go! Just click deploy in Railway dashboard.** 🚀
