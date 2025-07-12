import pandas as pd
import os

# Create a directory for generated files if it doesn't exist
os.makedirs('generated', exist_ok=True)

# Sample email addresses
emails = [
    'test1@example.com',
    'test2@example.com',
    'test3@example.com',
    'allowed1@iu.org',
    'allowed2@iu.org',
    'allowed3@iu.org'
]

# Create a DataFrame with emails
df = pd.DataFrame({'Email': emails})

# Save to Excel
excel_path = 'generated/allowed_emails.xlsx'
df.to_excel(excel_path, index=False)

print(f"Excel file with sample emails created at: {excel_path}")