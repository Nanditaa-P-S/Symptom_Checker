"""
Test email functionality for the Symptom Checker application
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'symptom_checker.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email_sending():
    """Test if email sending is working"""
    print("Testing email functionality...")
    print(f"Email Backend: {settings.EMAIL_BACKEND}")
    
    try:
        # Send a test email
        send_mail(
            subject='Test Email from Symptom Checker',
            message='This is a test email to verify email functionality is working.',
            from_email='noreply@symptomchecker.com',
            recipient_list=['test@example.com'],
            fail_silently=False,
        )
        
        print("✅ Email sent successfully!")
        print("Check your terminal output above to see the email content.")
        
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

if __name__ == "__main__":
    test_email_sending()
