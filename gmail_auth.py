#!/usr/bin/env python3
"""
Gmail API Authentication Script
Used to obtain Gmail API access tokens
"""

import os
import sys
from gmail_service import GmailService

def main():
    """Main function: perform Gmail API authentication"""
    print("=== Gmail API Authentication Tool ===")
    print("This tool will help you obtain Gmail API access tokens")
    print("Target email: hm3424@nyu.edu")
    print()
    
    # Check if credentials file exists
    credentials_file = "gmail_credentials.json"
    if not os.path.exists(credentials_file):
        print(f"❌ Error: Credentials file not found '{credentials_file}'")
        print()
        print("Please follow these steps:")
        print("1. Visit Google Cloud Console (https://console.cloud.google.com/)")
        print("2. Create project and enable Gmail API")
        print("3. Create OAuth2 credentials (desktop application)")
        print("4. Download JSON file and rename to 'gmail_credentials.json'")
        print("5. Place file in project root directory")
        print()
        print("For detailed instructions, please refer to: GMAIL_SETUP.md")
        return False
    
    print(f"✅ Found credentials file: {credentials_file}")
    print()
    
    # Create Gmail service instance
    gmail_service = GmailService(credentials_file, "gmail_token.json")
    
    print("Starting Gmail API authentication...")
    print("This will open browser for OAuth2 authorization")
    print("Please login with hm3424@nyu.edu account and authorize")
    print()
    
    try:
        # Perform authentication
        success = gmail_service.authenticate()
        
        if success:
            print("✅ Gmail API authentication successful!")
            print("Access token saved to: gmail_token.json")
            print()
            print("Now you can:")
            print("1. Run 'python test_gmail.py' to test email sending")
            print("2. Use email functionality in AI Health Assistant")
            return True
        else:
            print("❌ Gmail API authentication failed")
            print("Please check:")
            print("1. Network connection is normal")
            print("2. Gmail API is enabled")
            print("3. OAuth2 credentials are correct")
            return False
            
    except KeyboardInterrupt:
        print("\n❌ Authentication cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Error occurred during authentication: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
