import pandas as pd
from datetime import datetime

# Read the Excel file
df1 = pd.read_excel('Data New System.xlsx', sheet_name='Sheet1')
df2 = pd.read_excel('Data New System.xlsx', sheet_name='Sheet2')

print("Sheet1 columns:", df1.columns.tolist())
print("\nSheet2 columns:", df2.columns.tolist())

# Find the correct column names
passport_col_sheet1 = None
expiry_col_sheet1 = None

for col in df1.columns:
    if 'PASSPORT' in str(col).upper() and 'NO' in str(col).upper():
        passport_col_sheet1 = col
    if 'EXPIRY' in str(col).upper() and 'PASSPORT' in str(col).upper():
        expiry_col_sheet1 = col

print(f"\nFound Passport column in Sheet1: {passport_col_sheet1}")
print(f"Found Expiry column in Sheet1: {expiry_col_sheet1}")

# CONVERT THE EXPIRY COLUMN TO STRING FIRST
if expiry_col_sheet1:
    df1[expiry_col_sheet1] = df1[expiry_col_sheet1].astype(str)

# Create mapping from Sheet2
passport_map = {}
expiry_map = {}

for idx, row in df2.iterrows():
    name = str(row.get('NAME', '')).strip().upper()
    if name and name != 'NAN' and name != '':
        # Get passport number
        passport = row.get('Passport No', '')
        if pd.notna(passport):
            passport_map[name] = str(passport)
        
        # Get expiry date and convert to string
        expiry = row.get('Passport Expiry Date', '')
        if pd.notna(expiry):
            if isinstance(expiry, (datetime, pd.Timestamp)):
                # Format date nicely
                expiry_map[name] = expiry.strftime('%d-%m-%Y')
            else:
                expiry_map[name] = str(expiry)

print(f"\nFound {len(passport_map)} names with passport data in Sheet2")

# Update Sheet1
matches_found = 0
for idx, row in df1.iterrows():
    candidate_name = str(row.get("CANDIDATE'S NAME", '')).strip().upper()
    if candidate_name and candidate_name != 'NAN' and candidate_name != '':
        if candidate_name in passport_map:
            # Update passport number
            if passport_col_sheet1:
                df1.at[idx, passport_col_sheet1] = passport_map[candidate_name]
            
            # Update expiry date
            if expiry_col_sheet1 and candidate_name in expiry_map:
                df1.at[idx, expiry_col_sheet1] = expiry_map[candidate_name]
            
            matches_found += 1
            print(f"✓ Updated: {row.get('CANDIDATE\'S NAME', '')}")

print(f"\nTotal matches found and updated: {matches_found}")

# Save to new file
output_file = 'Data New System_UPDATED.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df1.to_excel(writer, sheet_name='Sheet1', index=False)
    df2.to_excel(writer, sheet_name='Sheet2', index=False)

print(f"\n✅ Done! Updated file saved as: {output_file}")