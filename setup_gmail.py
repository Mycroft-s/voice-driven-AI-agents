#!/usr/bin/env python3
"""
Gmail API 快速设置脚本
帮助用户快速配置Gmail API并获取访问令牌
"""

import os
import sys
import json
import webbrowser
from urllib.parse import urlencode

def print_banner():
    """Print welcome banner"""
    print("=" * 60)
    print("🤖 AI Health Assistant - Gmail API Quick Setup")
    print("=" * 60)
    print("This tool will help you configure Gmail API for hm3424@nyu.edu")
    print()

def check_credentials_file():
    """Check if credentials file exists"""
    credentials_file = "gmail_credentials.json"
    
    if os.path.exists(credentials_file):
        print(f"✅ Found Gmail credentials file: {credentials_file}")
        return True
    else:
        print(f"❌ Gmail credentials file not found: {credentials_file}")
        print()
        print("Please follow these steps to get the credentials file:")
        print()
        print("1. Visit Google Cloud Console:")
        print("   https://console.cloud.google.com/")
        print()
        print("2. Create a new project or select an existing project")
        print()
        print("3. Enable Gmail API:")
        print("   - Go to 'APIs & Services' > 'Library'")
        print("   - Search for 'Gmail API' and enable it")
        print()
        print("4. Create OAuth2 credentials:")
        print("   - Go to 'APIs & Services' > 'Credentials'")
        print("   - Click 'Create Credentials' > 'OAuth client ID'")
        print("   - Select 'Desktop application'")
        print("   - Enter name: 'Health Assistant Gmail'")
        print("   - Click 'Create'")
        print()
        print("5. Download the JSON file and rename it to 'gmail_credentials.json'")
        print("6. Place the file in the project root directory")
        print()
        return False

def setup_gmail_auth():
    """Setup Gmail authentication"""
    print("Starting Gmail API authentication...")
    print()
    
    try:
        from gmail_service import GmailService
        
        gmail_service = GmailService()
        
        print("Opening browser for OAuth2 authorization...")
        print("Please log in with hm3424@nyu.edu account and authorize")
        print()
        
        success = gmail_service.authenticate()
        
        if success:
            print("✅ Gmail API authentication successful!")
            print("Access token saved to: gmail_token.json")
            print()
            return True
        else:
            print("❌ Gmail API authentication failed")
            print("Please check network connection and credentials configuration")
            return False
            
    except ImportError:
        print("❌ Unable to import Gmail service module")
        print("Please ensure required dependencies are installed: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return False
    except Exception as e:
        print(f"❌ Error occurred during authentication: {e}")
        return False

def test_email_sending():
    """Test email sending functionality"""
    print("Testing email sending functionality...")
    print()
    
    try:
        from gmail_service import GmailService
        
        gmail_service = GmailService()
        
        if not gmail_service.authenticate():
            print("❌ Unable to authenticate with Gmail")
            return False
        
        # Send test email
        test_email = "hm3424@nyu.edu"
        subject = "AI Health Assistant - Gmail API Test"
        body = """
        Congratulations! Gmail API integration successful!
        
        This is a test email from your AI Health Assistant.
        Now you can:
        - Receive health reminder emails
        - Receive medication reminder emails
        - Receive appointment reminder emails
        - Receive custom notification emails
        
        This email was automatically sent by AI Health Assistant.
        """
        
        print(f"Sending test email to: {test_email}")
        
        success = gmail_service.send_email(
            to_email=test_email,
            subject=subject,
            body=body,
            is_html=False
        )
        
        if success:
            print("✅ Test email sent successfully!")
            print("Please check your email inbox")
            return True
        else:
            print("❌ Test email sending failed")
            return False
            
    except Exception as e:
        print(f"❌ Error occurred during testing: {e}")
        return False

def main():
    """Main function"""
    print_banner()
    
    # Check credentials file
    if not check_credentials_file():
        print("Please complete Gmail API credentials configuration first, then run this script again")
        return False
    
    print()
    
    # Setup Gmail authentication
    if not setup_gmail_auth():
        return False
    
    print()
    
    # Test email sending
    if not test_email_sending():
        return False
    
    print()
    print("🎉 Gmail API setup completed!")
    print()
    print("Now you can:")
    print("1. Use email functionality in AI Health Assistant")
    print("2. Run 'python test_gmail.py' for more testing")
    print("3. Request email notifications in chat")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
