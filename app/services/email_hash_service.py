import hashlib
import hmac
import os
from typing import List
import pandas as pd
from sqlalchemy.orm import Session
from app.models.allowed_emails import AllowedEmail
from app.core.security import get_random_token

# Get secret key from environment
EMAIL_HASH_SECRET = os.getenv("EMAIL_HASH_SECRET")

def _check_email_hash_secret():
    """Check if EMAIL_HASH_SECRET is configured"""
    if not EMAIL_HASH_SECRET:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("EMAIL_HASH_SECRET not configured - email allowed list feature is disabled")
        return False
    return True

def hash_email(email: str) -> str:
    """
    Hash an email address using HMAC and SHA-256
    """
    if not _check_email_hash_secret():
        raise ValueError("EMAIL_HASH_SECRET not configured")
    
    # Normalize email by converting to lowercase
    normalized_email = email.lower().strip()
    
    print(f"Hashing email: {normalized_email}")
    
    # Create HMAC using SHA-256
    digest = hmac.new(
        key=EMAIL_HASH_SECRET.encode(),
        msg=normalized_email.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    print(f"Hashed result: {digest}")
    
    return digest

def is_email_allowed(db: Session, email: str) -> bool:
    """
    Check if an email is in the allowed list
    """
    # If EMAIL_HASH_SECRET is not configured, return False (email not allowed)
    if not _check_email_hash_secret():
        print(f"EMAIL_HASH_SECRET not configured - treating email {email} as not allowed")
        return False
    
    try:
        print(f"Checking if email is allowed: {email}")
        hashed_email = hash_email(email)
        
        result = db.query(AllowedEmail).filter(AllowedEmail.hashed_email == hashed_email).first() is not None
        print(f"Email {email} is {'allowed' if result else 'not allowed'}")
        
        return result
    except Exception as e:
        print(f"Error checking if email is allowed: {str(e)}")
        return False

def process_excel_file(db: Session, file_content: bytes) -> dict:
    """
    Process an Excel file containing email addresses
    """
    if not _check_email_hash_secret():
        return {"success": False, "message": "EMAIL_HASH_SECRET not configured - cannot process allowed emails"}
    
    try:
        print(f"Starting to process Excel file, content size: {len(file_content)} bytes")
        
        # Read Excel file
        df = pd.read_excel(file_content)
        
        print(f"Excel file loaded, shape: {df.shape}")
        
        # Check if the dataframe has at least one column
        if df.shape[1] < 1:
            print("Error: Excel file has no columns")
            return {"success": False, "message": "Excel file must have at least one column"}
        
        # Get the first column, which should contain emails
        emails = df.iloc[:, 0].tolist()
        print(f"Extracted {len(emails)} email entries from first column")
        
        # Filter out any non-string values or empty strings
        emails = [str(email).strip() for email in emails if email and str(email).strip()]
        print(f"After filtering, {len(emails)} valid emails remain")
        
        # Hash and store emails
        added_count = 0
        for email in emails:
            print(f"Processing email: {email}")
            hashed_email = hash_email(email)
            
            # Check if this hashed email already exists
            existing = db.query(AllowedEmail).filter(AllowedEmail.hashed_email == hashed_email).first()
            if not existing:
                print(f"Adding new allowed email: {email}")
                new_allowed_email = AllowedEmail(
                    id=get_random_token(),
                    hashed_email=hashed_email
                )
                db.add(new_allowed_email)
                added_count += 1
            else:
                print(f"Email already exists in allowed list: {email}")
        
        db.commit()
        print(f"Commit successful. Added {added_count} new entries out of {len(emails)} total")
        return {
            "success": True, 
            "message": f"Processed {len(emails)} emails, added {added_count} new entries"
        }
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        db.rollback()
        return {"success": False, "message": f"Error processing file: {str(e)}"}