#!/usr/bin/env python3
"""
Setup script for Modal deployment of witness scrapers.
This script helps configure Modal secrets and deploy the scraping infrastructure.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any

def check_modal_installation():
    """Check if Modal CLI is installed."""
    try:
        result = subprocess.run(['modal', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Modal CLI installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Modal CLI not working properly")
            return False
    except FileNotFoundError:
        print("❌ Modal CLI not found")
        return False

def check_modal_auth():
    """Check if user is authenticated with Modal."""
    try:
        result = subprocess.run(['modal', 'profile', 'current'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Modal authentication verified")
            return True
        else:
            print("❌ Modal authentication failed")
            return False
    except Exception as e:
        print(f"❌ Error checking Modal auth: {e}")
        return False

def setup_modal_secrets():
    """Setup Modal secrets if .env file exists."""
    env_file = Path(__file__).parent / '.env'
    
    if not env_file.exists():
        print("⚠️  No .env file found. Skipping secrets setup.")
        print("   If you need environment variables, create a .env file first.")
        return
    
    print("🔐 Setting up Modal secrets from .env file...")
    
    # Read .env file
    env_vars = {}
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return
    
    if not env_vars:
        print("⚠️  No environment variables found in .env file")
        return
    
    # Group related secrets
    secret_groups = {
        'database-credentials': [
            'DATABASE_URL', 'SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_SERVICE_KEY'
        ],
        'aws-credentials': [
            'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION', 'S3_BUCKET_NAME'
        ],
        'proxy-credentials': [
            'PROXY_ENABLED', 'PROXY_SERVER', 'PROXY_USERNAME', 'PROXY_PASSWORD'
        ],
        'scraper-config': [
            'BROWSER_HEADLESS', 'BROWSER_TIMEOUT', 'LOG_LEVEL'
        ]
    }
    
    for secret_name, var_names in secret_groups.items():
        secret_vars = {var: env_vars[var] for var in var_names if var in env_vars}
        
        if secret_vars:
            print(f"   Creating secret: {secret_name}")
            try:
                # Create temporary file with secret variables
                temp_env_file = Path(f"/tmp/{secret_name}.env")
                with open(temp_env_file, 'w') as f:
                    for var, value in secret_vars.items():
                        f.write(f"{var}={value}\n")
                
                # Create Modal secret
                cmd = ['modal', 'secret', 'create', secret_name, '--from-dotenv', str(temp_env_file)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"      ✅ {secret_name} created")
                else:
                    print(f"      ⚠️  {secret_name} may already exist or failed: {result.stderr}")
                
                # Clean up temp file
                temp_env_file.unlink(missing_ok=True)
                
            except Exception as e:
                print(f"      ❌ Error creating {secret_name}: {e}")

def deploy_modal_app():
    """Deploy the Modal app."""
    print("🚀 Deploying Modal witness scraper app...")
    
    try:
        cmd = ['modal', 'deploy', 'modal_witness_scraper.py']
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ Modal app deployed successfully!")
            print("   You can now run the scraper with:")
            print("   modal run modal_witness_scraper.py")
            return True
        else:
            print(f"❌ Deployment failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error during deployment: {e}")
        return False

def test_deployment():
    """Test the deployed Modal app."""
    print("🧪 Testing deployed Modal app...")
    
    try:
        cmd = ['modal', 'run', 'modal_witness_scraper.py', '--test-only']
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ Modal app test successful!")
            print(result.stdout)
            return True
        else:
            print(f"❌ Modal app test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def main():
    """Main setup function."""
    print("🔧 Setting up Modal deployment for witness scrapers...")
    print()
    
    # Check prerequisites
    if not check_modal_installation():
        print("\n📦 Please install Modal CLI first:")
        print("   pip install modal")
        return False
    
    if not check_modal_auth():
        print("\n🔑 Please authenticate with Modal first:")
        print("   modal auth set-token <your-token>")
        return False
    
    print()
    
    # Setup secrets
    setup_modal_secrets()
    print()
    
    # Deploy app
    if not deploy_modal_app():
        return False
    
    print()
    
    # Test deployment
    if not test_deployment():
        print("⚠️  Deployment test failed, but app may still work")
    
    print()
    print("🎉 Setup complete! You can now run:")
    print("   modal run modal_witness_scraper.py --max-events 10")
    print("   modal run modal_witness_scraper.py --test-only")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)