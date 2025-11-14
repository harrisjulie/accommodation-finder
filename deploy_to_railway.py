#!/usr/bin/env python3
"""
Automated Railway Deployment Script
Deploys the Accommodation Finder to Railway
"""

import os
import sys
import subprocess
import json

# Railway configuration
RAILWAY_TOKEN = "8c7aa644-15b5-4ac1-9cf1-9125486e216a"
RAILWAY_PROJECT_ID = "f53ac83d-1ad4-4f42-bda6-9b7834b0881f"

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def run_command(cmd, description, capture_output=False):
    """Run a shell command with error handling"""
    print(f"🔄 {description}...")
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, shell=True, text=True)

        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True, result.stdout if capture_output else ""
        else:
            print(f"❌ {description} - Failed")
            if capture_output:
                print(f"Error: {result.stderr}")
            return False, result.stderr if capture_output else ""
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False, str(e)

def check_node_npm():
    """Check if Node.js and npm are installed"""
    print_header("Checking Prerequisites")

    # Check Node.js
    success, output = run_command("node --version", "Checking Node.js", capture_output=True)
    if not success:
        print("❌ Node.js not found. Please install Node.js first.")
        print("   Visit: https://nodejs.org/")
        return False

    # Check npm
    success, output = run_command("npm --version", "Checking npm", capture_output=True)
    if not success:
        print("❌ npm not found. Please install npm first.")
        return False

    return True

def install_railway_cli():
    """Install Railway CLI"""
    print_header("Installing Railway CLI")

    # Check if already installed
    success, output = run_command("railway --version", "Checking if Railway CLI is already installed", capture_output=True)
    if success:
        print("✅ Railway CLI already installed")
        return True

    # Install Railway CLI
    print("📦 Installing Railway CLI globally...")
    success, output = run_command("npm install -g @railway/cli", "Installing Railway CLI")

    if not success:
        print("❌ Failed to install Railway CLI")
        print("   Try manually: npm install -g @railway/cli")
        return False

    return True

def authenticate_railway():
    """Authenticate with Railway using token"""
    print_header("Authenticating with Railway")

    # Set Railway token as environment variable
    os.environ['RAILWAY_TOKEN'] = RAILWAY_TOKEN

    # Verify authentication
    success, output = run_command("railway whoami", "Verifying Railway authentication", capture_output=True)

    if success:
        print(f"✅ Authenticated successfully")
        print(f"   {output.strip()}")
        return True
    else:
        print("❌ Authentication failed")
        print("   Please check your Railway token")
        return False

def link_railway_project():
    """Link to Railway project"""
    print_header("Linking to Railway Project")

    # Set environment variable for Railway token
    os.environ['RAILWAY_TOKEN'] = RAILWAY_TOKEN

    # Link to project using project ID
    cmd = f"railway link {RAILWAY_PROJECT_ID}"
    success, output = run_command(cmd, f"Linking to project {RAILWAY_PROJECT_ID}", capture_output=True)

    if success or "already linked" in output.lower():
        print(f"✅ Linked to Railway project: {RAILWAY_PROJECT_ID}")
        return True
    else:
        print("❌ Failed to link to Railway project")
        print(f"   Output: {output}")
        return False

def set_environment_variables():
    """Set Railway environment variables"""
    print_header("Setting Environment Variables")

    # Set environment variable for Railway token
    os.environ['RAILWAY_TOKEN'] = RAILWAY_TOKEN

    variables = {
        "PYTHON_VERSION": "3.11",
        "AUTO_CONFIRM": "true"
    }

    for key, value in variables.items():
        cmd = f'railway variables set {key}="{value}"'
        success, output = run_command(cmd, f"Setting {key}={value}", capture_output=True)
        if not success:
            print(f"⚠️  Warning: Failed to set {key}")

    return True

def deploy_to_railway():
    """Deploy the application to Railway"""
    print_header("Deploying to Railway")

    # Set environment variable for Railway token
    os.environ['RAILWAY_TOKEN'] = RAILWAY_TOKEN

    print("🚀 Starting deployment...")
    print("   This may take a few minutes...")

    # Deploy using railway up
    success, output = run_command("railway up --detach", "Deploying application")

    if success:
        print("✅ Deployment initiated successfully!")
        return True
    else:
        print("❌ Deployment failed")
        return False

def get_deployment_url():
    """Get the deployment URL"""
    print_header("Getting Deployment URL")

    # Set environment variable for Railway token
    os.environ['RAILWAY_TOKEN'] = RAILWAY_TOKEN

    print("🔗 Fetching deployment URL...")
    success, output = run_command("railway status", "Getting deployment status", capture_output=True)

    if success:
        print(output)

    return True

def main():
    """Main execution"""
    print_header("🚂 RAILWAY DEPLOYMENT - ACCOMMODATION FINDER")

    print(f"Railway Token: {RAILWAY_TOKEN[:20]}...")
    print(f"Project ID: {RAILWAY_PROJECT_ID}")

    # Step 1: Check prerequisites
    if not check_node_npm():
        print("\n❌ Prerequisites check failed")
        print("   Please install Node.js and npm first")
        sys.exit(1)

    # Step 2: Install Railway CLI
    if not install_railway_cli():
        print("\n❌ Railway CLI installation failed")
        sys.exit(1)

    # Step 3: Authenticate
    if not authenticate_railway():
        print("\n❌ Railway authentication failed")
        sys.exit(1)

    # Step 4: Link to project
    if not link_railway_project():
        print("\n❌ Failed to link to Railway project")
        sys.exit(1)

    # Step 5: Set environment variables
    if not set_environment_variables():
        print("\n⚠️  Warning: Some environment variables may not be set")

    # Step 6: Deploy
    if not deploy_to_railway():
        print("\n❌ Deployment failed")
        sys.exit(1)

    # Step 7: Get deployment URL
    get_deployment_url()

    # Success summary
    print_header("✅ DEPLOYMENT COMPLETE")

    print("🎉 Your Accommodation Finder has been deployed to Railway!")
    print("\n📋 Next steps:")
    print("1. Check Railway dashboard: https://railway.app/dashboard")
    print("2. View your project: https://railway.app/project/" + RAILWAY_PROJECT_ID)
    print("3. Monitor deployment logs: railway logs")
    print("4. Test your API once deployment is complete")

    print("\n🔗 Useful commands:")
    print("   railway logs          - View application logs")
    print("   railway status        - Check deployment status")
    print("   railway open          - Open project in browser")
    print("   railway variables     - View environment variables")

    print("\n⚠️  Note: If you need a PostgreSQL database:")
    print("   1. Go to Railway dashboard")
    print("   2. Click 'New' → 'Database' → 'PostgreSQL'")
    print("   3. Railway will automatically inject DATABASE_URL")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Deployment cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
