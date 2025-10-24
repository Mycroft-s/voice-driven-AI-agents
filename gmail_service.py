"""
Gmail API Integration Module
Handles Gmail authentication and email sending functionality
"""

import os
import base64
import json
import logging
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GmailService:
    """Gmail API Service Class"""
    
    # Gmail API permission scopes
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    def __init__(self, credentials_file: str = "gmail_credentials.json", 
                 token_file: str = "gmail_token.json", sender_email: str = "hm3424@nyu.edu"):
        """
        Initialize Gmail service
        
        Args:
            credentials_file: Google OAuth2 credentials file path
            token_file: Access token storage file path
            sender_email: Sender email address
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.sender_email = sender_email
        self.service = None
        self.credentials = None
        
    def authenticate(self) -> bool:
        """
        Perform Gmail API authentication
        
        Returns:
            bool: Whether authentication is successful
        """
        try:
            # Check if stored token exists
            if os.path.exists(self.token_file):
                self.credentials = Credentials.from_authorized_user_file(
                    self.token_file, self.SCOPES
                )
            
            # If no valid credentials, perform OAuth2 flow
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    # Refresh token
                    self.credentials.refresh(Request())
                else:
                    # Perform OAuth2 authorization flow
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Gmail credentials file not found: {self.credentials_file}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES
                    )
                    self.credentials = flow.run_local_server(port=0)
                
                # Save credentials for next use
                with open(self.token_file, 'w') as token:
                    token.write(self.credentials.to_json())
            
            # Build Gmail API service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            logger.info("Gmail API authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Gmail API authentication failed: {e}")
            return False
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   is_html: bool = False, cc_emails: list = None, 
                   bcc_emails: list = None, attachments: list = None) -> bool:
        """
        Send email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether it's HTML format
            cc_emails: CC email list
            bcc_emails: BCC email list
            attachments: Attachment file path list
            
        Returns:
            bool: Whether sending is successful
        """
        try:
            if not self.service:
                logger.error("Gmail service not initialized, please authenticate first")
                return False
            
            # Create email message
            message = MIMEMultipart()
            message['from'] = self.sender_email
            message['to'] = to_email
            message['subject'] = subject
            
            # Add CC and BCC
            if cc_emails:
                message['cc'] = ', '.join(cc_emails)
            if bcc_emails:
                message['bcc'] = ', '.join(bcc_emails)
            
            # Add email body
            if is_html:
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        message.attach(part)
            
            # Encode email message
            raw_message = base64.urlsafe_b64encode(message.as_string().encode('utf-8')).decode()
            
            # Send email
            send_message = self.service.users().messages().send(
                userId='me', body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent successfully, message ID: {send_message['id']}")
            return True
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def send_health_reminder(self, user_email: str, user_name: str, 
                            reminder_type: str, reminder_content: str) -> bool:
        """
        Send health reminder email
        
        Args:
            user_email: User email address
            user_name: User name
            reminder_type: Reminder type
            reminder_content: Reminder content
            
        Returns:
            bool: Whether sending is successful
        """
        subject = f"Health Reminder - {reminder_type}"
        
        # HTML format email body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px;">
                    Health Assistant Reminder
                </h2>
                
                <p>Dear {user_name},</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #2c5aa0; margin-top: 0;">Reminder Content:</h3>
                    <p style="margin-bottom: 0;">{reminder_content}</p>
                </div>
                
                <p>Please handle related matters promptly and maintain a healthy lifestyle.</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666;">
                    <p>This email is automatically sent by AI Health Assistant, please do not reply.</p>
                    <p>Sender: {self.sender_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to_email=user_email,
            subject=subject,
            body=html_body,
            is_html=True
        )
    
    def send_medication_reminder(self, user_email: str, user_name: str,
                                medication_name: str, dosage: str, 
                                frequency: str) -> bool:
        """
        Send medication reminder email
        
        Args:
            user_email: User email address
            user_name: User name
            medication_name: Medication name
            dosage: Dosage
            frequency: Frequency
            
        Returns:
            bool: Whether sending is successful
        """
        subject = f"Medication Reminder - {medication_name}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #d32f2f; border-bottom: 2px solid #d32f2f; padding-bottom: 10px;">
                    💊 Medication Reminder
                </h2>
                
                <p>Dear {user_name},</p>
                
                <div style="background-color: #fff3e0; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ff9800;">
                    <h3 style="color: #d32f2f; margin-top: 0;">Medication Information:</h3>
                    <ul style="margin-bottom: 0;">
                        <li><strong>Medication Name:</strong>{medication_name}</li>
                        <li><strong>Dosage:</strong>{dosage}</li>
                        <li><strong>Frequency:</strong>{frequency}</li>
                    </ul>
                </div>
                
                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #2e7d32;"><strong>⚠️ Important Reminder:</strong></p>
                    <ul style="margin: 10px 0 0 0;">
                        <li>Please take medication on time</li>
                        <li>Seek medical attention if you feel unwell</li>
                        <li>Do not change dosage without doctor's advice</li>
                    </ul>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666;">
                    <p>This email is automatically sent by AI Health Assistant, please do not reply.</p>
                    <p>Sender: {self.sender_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to_email=user_email,
            subject=subject,
            body=html_body,
            is_html=True
        )
    
    def send_appointment_reminder(self, user_email: str, user_name: str,
                                doctor_name: str, appointment_time: str,
                                department: str, reason: str) -> bool:
        """
        Send appointment reminder email
        
        Args:
            user_email: User email address
            user_name: User name
            doctor_name: Doctor name
            appointment_time: Appointment time
            department: Department
            reason: Reason for appointment
            
        Returns:
            bool: Whether sending is successful
        """
        subject = f"Appointment Reminder - {department}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1976d2; border-bottom: 2px solid #1976d2; padding-bottom: 10px;">
                    🏥 Appointment Reminder
                </h2>
                
                <p>Dear {user_name},</p>
                
                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #1976d2; margin-top: 0;">Appointment Details:</h3>
                    <ul style="margin-bottom: 0;">
                        <li><strong>Department:</strong>{department}</li>
                        <li><strong>Doctor:</strong>{doctor_name}</li>
                        <li><strong>Time:</strong>{appointment_time}</li>
                        <li><strong>Reason:</strong>{reason}</li>
                    </ul>
                </div>
                
                <div style="background-color: #f3e5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #7b1fa2;"><strong>📋 Important Notes:</strong></p>
                    <ul style="margin: 10px 0 0 0;">
                        <li>Please arrive 15 minutes early</li>
                        <li>Bring ID card and insurance card</li>
                        <li>Contact hospital if there are any changes</li>
                    </ul>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666;">
                    <p>This email is automatically sent by AI Health Assistant, please do not reply.</p>
                    <p>Sender: {self.sender_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to_email=user_email,
            subject=subject,
            body=html_body,
            is_html=True
        )


# Global Gmail service instance - using hm3424@nyu.edu as sender
gmail_service = GmailService(sender_email="hm3424@nyu.edu")
