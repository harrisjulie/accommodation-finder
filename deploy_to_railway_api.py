#!/usr/bin/env python3
"""
Railway API Deployment Script
Deploys using Railway's GraphQL API directly (no CLI needed)
"""

import requests
import json
import sys

# Railway configuration
RAILWAY_TOKEN = "8c7aa644-15b5-4ac1-9cf1-9125486e216a"
RAILWAY_PROJECT_ID = "f53ac83d-1ad4-4f42-bda6-9b7834b0881f"
RAILWAY_API_URL = "https://backboard.railway.app/graphql/v2"

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def railway_api_request(query, variables=None):
    """Make a request to Railway GraphQL API"""
    headers = {
        "Authorization": f"Bearer {RAILWAY_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": query,
        "variables": variables or {}
    }

    try:
        response = requests.post(RAILWAY_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ API Request failed: {e}")
        return None

def verify_authentication():
    """Verify Railway authentication"""
    print_header("Verifying Authentication")

    query = """
    query {
        me {
            id
            name
            email
        }
    }
    """

    result = railway_api_request(query)

    if result and "data" in result and result["data"].get("me"):
        user = result["data"]["me"]
        print(f"✅ Authenticated as: {user.get('name', 'Unknown')} ({user.get('email', 'No email')})")
        return True
    else:
        print("❌ Authentication failed")
        print(f"   Response: {result}")
        return False

def get_project_info():
    """Get information about the Railway project"""
    print_header("Getting Project Information")

    query = """
    query project($id: String!) {
        project(id: $id) {
            id
            name
            description
            services {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
    }
    """

    variables = {"id": RAILWAY_PROJECT_ID}
    result = railway_api_request(query, variables)

    if result and "data" in result and result["data"].get("project"):
        project = result["data"]["project"]
        print(f"✅ Project: {project.get('name', 'Unknown')}")
        print(f"   ID: {project['id']}")

        services = project.get("services", {}).get("edges", [])
        if services:
            print(f"   Services: {len(services)}")
            for service in services:
                print(f"      - {service['node']['name']} (ID: {service['node']['id']})")
        else:
            print("   No services found")

        return project
    else:
        print("❌ Failed to get project information")
        print(f"   Response: {result}")
        return None

def trigger_deployment(service_id=None):
    """Trigger a deployment"""
    print_header("Triggering Deployment")

    if not service_id:
        print("⚠️  No service ID provided - deployment may not work")
        print("   Please create a service in Railway dashboard first")
        return False

    query = """
    mutation serviceInstanceRedeploy($serviceId: String!) {
        serviceInstanceRedeploy(serviceId: $serviceId) {
            id
        }
    }
    """

    variables = {"serviceId": service_id}
    result = railway_api_request(query, variables)

    if result and "data" in result:
        print(f"✅ Deployment triggered successfully!")
        return True
    else:
        print("❌ Failed to trigger deployment")
        print(f"   Response: {result}")
        return False

def main():
    """Main execution"""
    print_header("🚂 RAILWAY API DEPLOYMENT - ACCOMMODATION FINDER")

    print(f"Railway Token: {RAILWAY_TOKEN[:20]}...")
    print(f"Project ID: {RAILWAY_PROJECT_ID}")
    print(f"API URL: {RAILWAY_API_URL}")

    # Step 1: Verify authentication
    if not verify_authentication():
        print("\n❌ Authentication failed")
        print("   Please check your Railway token")
        sys.exit(1)

    # Step 2: Get project information
    project = get_project_info()
    if not project:
        print("\n❌ Failed to get project information")
        sys.exit(1)

    # Step 3: Get service ID (if available)
    services = project.get("services", {}).get("edges", [])
    service_id = None
    if services:
        service_id = services[0]["node"]["id"]
        print(f"\n🎯 Using service: {services[0]['node']['name']}")

    # Step 4: Trigger deployment
    if service_id:
        if not trigger_deployment(service_id):
            print("\n⚠️  Deployment trigger may have failed")
    else:
        print("\n⚠️  No services found in project")
        print("   You need to create a service in Railway first:")
        print("   1. Go to https://railway.app/project/" + RAILWAY_PROJECT_ID)
        print("   2. Click 'New Service'")
        print("   3. Select 'GitHub Repo'")
        print("   4. Connect to harrisjulie/accommodation-finder")
        print("   5. Railway will automatically detect and deploy")

    # Success summary
    print_header("📋 DEPLOYMENT INFORMATION")

    print("✅ Railway project verified and accessible")
    print(f"\n🔗 Project Dashboard:")
    print(f"   https://railway.app/project/{RAILWAY_PROJECT_ID}")

    print("\n📝 Next steps:")
    if not service_id:
        print("1. Create a new service in Railway dashboard")
        print("2. Connect to your GitHub repository: harrisjulie/accommodation-finder")
        print("3. Railway will auto-detect Python and deploy")
    else:
        print("1. Monitor deployment in Railway dashboard")
        print("2. Check logs for any errors")
        print("3. Test your API once deployed")

    print("\n💡 To deploy from GitHub:")
    print("1. Push your code to main branch")
    print("2. Railway will automatically deploy on new commits")
    print("3. Configure auto-deployment in Railway settings")

    print("\n⚠️  If you need a PostgreSQL database:")
    print("   1. Go to Railway dashboard")
    print("   2. Click 'New' → 'Database' → 'PostgreSQL'")
    print("   3. Railway will automatically inject DATABASE_URL")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
