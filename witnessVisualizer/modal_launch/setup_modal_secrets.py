"""
Setup Modal Secrets for Congressional Hearings Scraper

Automatically creates Modal secrets from your .env file with all 82 API keys.
"""

import os
import subprocess
import sys
from dotenv import load_dotenv

def setup_modal_secrets():
    """Create Modal secrets from environment variables"""
    
    # Load environment variables
    load_dotenv()
    
    print("🔑 Setting up Modal secrets for Congressional Hearings Scraper...")
    
    # Extract all Congress.gov API keys
    api_keys = {}
    for i in range(1, 83):  # Keys 1-82
        key_name = f"CONGRESS_GOV_API_KEY" if i == 1 else f"CONGRESS_GOV_API_KEY_{i}"
        key_value = os.getenv(key_name)
        if key_value:
            api_keys[key_name] = key_value
    
    print(f"📋 Found {len(api_keys)} Congress.gov API keys")
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    witness_supabase_url = os.getenv('WITNESS_SUPABASE_URL')
    witness_supabase_key = os.getenv('WITNESS_SUPABASE_SERVICE_ROLE_KEY')
    
    if not ((supabase_url and supabase_key) or (witness_supabase_url and witness_supabase_key)):
        print("❌ Missing Supabase credentials in .env file")
        print("   Required: Either SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY")
        print("   Or: WITNESS_SUPABASE_URL + WITNESS_SUPABASE_SERVICE_ROLE_KEY")
        return False
    
    # Combine all secrets
    secrets = {
        **api_keys
    }
    
    # Add Supabase credentials
    if supabase_url and supabase_key:
        secrets['SUPABASE_URL'] = supabase_url
        secrets['SUPABASE_SERVICE_ROLE_KEY'] = supabase_key
    
    if witness_supabase_url and witness_supabase_key:
        secrets['WITNESS_SUPABASE_URL'] = witness_supabase_url
        secrets['WITNESS_SUPABASE_SERVICE_ROLE_KEY'] = witness_supabase_key
    
    print(f"🛠️  Creating Modal secret with {len(secrets)} environment variables...")
    
    # Build modal secret command
    cmd = ['modal', 'secret', 'create', 'congressional-secrets']
    for key, value in secrets.items():
        if value:
            cmd.append(f'{key}={value}')
    
    try:
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Modal secrets created successfully!")
        print(f"   Secret name: congressional-secrets")
        print(f"   Variables: {len(secrets)} environment variables")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating Modal secrets:")
        print(f"   Command: {' '.join(cmd[:5])}... (truncated)")
        print(f"   Error: {e.stderr}")
        
        # Check if secret already exists
        if "already exists" in e.stderr:
            print("\n💡 Secret already exists. To update:")
            print("   modal secret delete congressional-secrets")
            print("   python setup_modal_secrets.py")
        
        return False
    
    except FileNotFoundError:
        print("❌ Modal CLI not found. Please install it:")
        print("   pip install modal")
        print("   modal token new")
        return False

def verify_modal_setup():
    """Verify Modal CLI is installed and authenticated"""
    
    try:
        # Check if modal is installed
        result = subprocess.run(['modal', '--version'], capture_output=True, text=True, check=True)
        print(f"✅ Modal CLI installed: {result.stdout.strip()}")
        
        # Check if authenticated
        result = subprocess.run(['modal', 'token', 'current'], capture_output=True, text=True, check=True)
        print("✅ Modal authentication verified")
        
        return True
        
    except subprocess.CalledProcessError:
        print("❌ Modal authentication required:")
        print("   modal token new")
        return False
        
    except FileNotFoundError:
        print("❌ Modal CLI not found. Please install:")
        print("   pip install modal")
        return False

def main():
    """Main setup function"""
    print("🚀 Congressional Hearings Scraper - Modal Setup")
    print("=" * 50)
    
    # Verify Modal setup
    if not verify_modal_setup():
        print("\n🛠️  Please set up Modal CLI first, then run this script again.")
        return
    
    # Create secrets
    if setup_modal_secrets():
        print("\n🎯 Setup complete! Next steps:")
        print("   1. Deploy: modal deploy modal_launch/congressional_hearings_modal.py")
        print("   2. Run: modal run modal_launch/congressional_hearings_modal.py")
        print("\n📊 Expected results:")
        print("   - 1000+ congressional hearings scraped")
        print("   - 60-80% with witness data")
        print("   - 10-20 minute runtime")
    else:
        print("\n❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    main()