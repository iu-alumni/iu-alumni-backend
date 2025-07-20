import pandas as pd
from sqlalchemy.orm import Session

from app.core.security import get_random_token
from app.models.users import Alumni


def import_graduates_from_excel(db: Session, file_path: str):
    """Import graduates from Excel file."""
    graduates_df = pd.read_excel(file_path)

    # Validate columns
    required_columns = ["email", "first_name", "last_name", "graduation_year"]
    if not all(col in graduates_df.columns for col in required_columns):
        raise ValueError(f"Excel file must contain columns: {required_columns}")

    for _, row in graduates_df.iterrows():
        email = row["email"].strip()

        # Check if user already exists
        existing_user = db.query(Alumni).filter(Alumni.email == email).first()
        if existing_user:
            continue

        # Create new user with pending verification
        user = Alumni(
            id=get_random_token(),
            email=email,
            first_name=row["first_name"],
            last_name=row["last_name"],
            graduation_year=row["graduation_year"],
            is_verified=False,
        )

        db.add(user)
        db.commit()
