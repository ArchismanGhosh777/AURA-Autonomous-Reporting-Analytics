import pandas as pd
import sqlite3
import os
import sys
from google import genai

# ==========================================
# 1. CONFIGURATION & SETUP
# ==========================================
API_KEY = "AIzaSyDLnU076NF-TLccDUA_P7Fu2j-qjYnTyjE"
client = genai.Client(api_key=API_KEY)

raw_data_folder = r"C:\Users\Archisman Ghosh\Documents\Apple_AI\Raw_Data"
script_folder = r"C:\Users\Archisman Ghosh\Documents\Apple_AI\scripts"

# ==========================================
# 2. DYNAMIC MULTI-FILE INGESTION
# ==========================================
print(f"\nScanning folder for datasets: {raw_data_folder}")
conn = sqlite3.connect(os.path.join(raw_data_folder, "apple_db.sqlite"))
all_schemas = []

for file_name in os.listdir(raw_data_folder):
    file_path = os.path.join(raw_data_folder, file_name)
    
    if file_name.endswith('.csv') or file_name.endswith('.xlsx'):
        table_name = file_name.replace('.csv', '').replace('.xlsx', '')
        print(f" -> Loading '{file_name}' into SQL table: [{table_name}]")
        
        if file_name.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        schema_str = f"Table Name: {table_name}. Columns: {', '.join(df.columns)}"
        all_schemas.append(schema_str)

master_database_schema = "\n".join(all_schemas)
print("All datasets successfully loaded into the database.")

# ==========================================
# 3. READ THE REQUIREMENT FILE
# ==========================================
req_file_path = os.path.join(script_folder, "requirements.txt")
with open(req_file_path, "r", encoding="utf-8") as file:
    user_requirements = file.read()

# ==========================================
# 4. CALL GEMINI AI (WITH HYPER-STRICT LEASH)
# ==========================================
print("\nAsking Gemini 2.5 Flash to generate SQL...")

# THE FIX: This prompt now strictly forbids bonus queries.
prompt = f"""
You are an automated SQL script generator. You have ONE job: translate the user's exact requirements into SQLite views.

SCHEMA:
{master_database_schema}

USER REQUIREMENTS:
{user_requirements}

CRITICAL RULES - YOU MUST OBEY THESE:
1. ZERO BONUS QUERIES: You must ONLY generate code for the exact requirements written by the user. Do not add any "extra" or "helpful" views.
2. EXACT MATCH: If the user writes 2 logical requirements, output exactly 2 CREATE VIEW statements.
3. QUOTE YOUR NAMES: Every single view name MUST be wrapped in double quotes to prevent syntax errors (e.g., CREATE VIEW "Sales_By_Region" AS...).
4. RAW CODE ONLY: Return ONLY valid SQL separated by semicolons. No markdown, no commentary, no explanations.
"""

try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    ai_sql_code = response.text.strip().replace("```sql", "").replace("```", "")
    print(f"\n--- Gemini Generated SQL ---\n{ai_sql_code}\n----------------------------\n")

except Exception as e:
    print("\n[!] API CONNECTION ERROR:")
    print("Google's Gemini servers are currently experiencing high demand and are temporarily unavailable.")
    print(f"Technical details: {e}")
    sys.exit(1)

# ==========================================
# 5. WIPE THE SLATE CLEAN (BUG FIXED)
# ==========================================
print("Cleaning up old views from the database...")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
old_views = cursor.fetchall()

for view in old_views:
    view_name = view[0]
    # THE FIX: Added double quotes around the view_name to handle spaces correctly
    try:
        cursor.execute(f'DROP VIEW IF EXISTS "{view_name}";')
        print(f" -> Deleted old view: [{view_name}]")
    except sqlite3.Error as e:
        print(f" -> Warning: Could not delete view {view_name}: {e}")

conn.commit() # Save the deletions before moving on!

# ==========================================
# 6. EXECUTE NEW GEMINI SQL
# ==========================================
print("Executing strictly formatted SQL in the database...")

queries = ai_sql_code.split(';')
for query in queries:
    cleaned_query = query.strip()
    if cleaned_query:
        try:
            cursor.execute(cleaned_query)
        except sqlite3.Error as e:
            print(f"\n[!] SQL ERROR CAUGHT:")
            print(f"Failed Query: {cleaned_query}")
            print(f"Reason: {e}\n")

conn.commit()

# ==========================================
# 7. AUTO-EXPORT & LAUNCH FOR EXECUTIVES
# ==========================================
print("\nExporting final views to Microsoft Excel...")
excel_path = os.path.join(raw_data_folder, "AI_Generated_Insights.xlsx")

# Ask SQLite for the names of the views the AI JUST created
cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
current_views = cursor.fetchall()

if current_views:
    # Create a new Excel workbook
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for view in current_views:
            view_name = view[0]
            # Read the AI's view into a Pandas DataFrame
            df_view = pd.read_sql_query(f'SELECT * FROM "{view_name}"', conn)
            
            # Save it to a tab in Excel (Excel sheet names have a 31-character limit)
            safe_sheet_name = view_name[:31]
            df_view.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            print(f" -> Exported tab: {safe_sheet_name}")

    print("Forcing Windows to open Excel...")
    # This Windows-specific command instantly launches the file in the default app
    os.startfile(excel_path)
    
else:
    print("Warning: No views were generated to export.")

conn.close()
print("Pipeline complete! The results are now on screen.")