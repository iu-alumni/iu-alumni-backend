import pandas as pd
from sqlalchemy.orm import Session
from app.models.users import Alumni, Admin
from app.models.enums import GraduationCourse
from app.core.security import get_random_token

def import_graduates_from_excel(db: Session, file_path: str):
    """Import graduates from Excel file."""
    df = pd.read_excel(file_path)
    
    # Validate columns
    required_columns = ['email', 'graduation_year', 'first_name', 'last_name']
    if not all(col in df.columns for col in required_columns):
        raise ValueError("Excel file missing required columns")
    
    for _, row in df.iterrows():
        email = row['email'].strip()
        
        # Check if user already exists
        existing_user = db.query(Alumni).filter(Alumni.email == email).first()
        if existing_user:
            continue
            
        # Create new user with pending verification
        user = Alumni(
            id=get_random_token(),
            email=email,
            first_name=row['first_name'],
            last_name=row['last_name'],
            graduation_year=row['graduation_year'],
            course=GraduationCourse.NONE, # will be updated during verification
            is_verified=False
        )
        
        db.add(user)
        db.commit() 