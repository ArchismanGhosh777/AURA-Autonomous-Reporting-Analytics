import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import sqlite3
import pyodbc
import os
import threading
import re
from google import genai
from dotenv import load_dotenv # <--- NEW IMPORT

# ==========================================
# 1. APP SETTINGS & API KEY
# ==========================================
# Load the hidden variables from the .env file
load_dotenv() 

# Securely grab the key from the environment vault
API_KEY = os.getenv("GEMINI_API_KEY") 

if not API_KEY:
    print("CRITICAL ERROR: No API Key found in .env file.")

# ... (the rest of your code remains exactly the same)

ctk.set_appearance_mode("dark")  
ctk.set_default_color_theme("blue")  

# ==========================================
# 2. THE AI BACKEND ENGINE
# ==========================================
def run_pipeline(user_requirements, mode, target_data, save_path, sql_creds=None):
    try:
        client = genai.Client(api_key=API_KEY)
        
        def update_status(text, color="#F39C12"):
            app.after(0, lambda: status_label.configure(text=f"Status: {text}", text_color=color))

        excel_output = os.path.join(save_path, "AURA_Generated_Insights.xlsx")
        schemas = []
        conn = None

        # ==========================================
        # PHASE A: INGESTION & SCHEMA EXTRACTION
        # ==========================================
        if mode == "LOCAL":
            update_status("Scanning local files...")
            if os.path.isfile(target_data):
                files = [target_data]
            else:
                valid_exts = ('.csv', '.xlsx', '.xls')
                files = [os.path.join(target_data, f) for f in os.listdir(target_data) 
                         if f.lower().endswith(valid_exts) and not f.startswith('~$')]

            if not files: raise ValueError("No valid spreadsheet files found.")

            db_path = os.path.join(save_path, "aura_temp_db.sqlite")
            conn = sqlite3.connect(db_path)

            for f_path in files:
                raw_name, _ = os.path.splitext(os.path.basename(f_path))
                safe_table_name = re.sub(r'\W+', '_', raw_name).strip('_')
                try:
                    df = pd.read_csv(f_path) if f_path.lower().endswith('.csv') else pd.read_excel(f_path)
                    df.to_sql(safe_table_name, conn, if_exists="replace", index=False)
                    schemas.append(f"Table: {safe_table_name} | Columns: {', '.join(df.columns)}")
                except Exception as e:
                    print(f"Skipped {raw_name}: {e}")

        elif mode == "SQL_SERVER":
            update_status("Connecting to Remote SQL Server...")
            conn_str = f"DRIVER={{SQL Server}};SERVER={sql_creds['server']};DATABASE={sql_creds['db']};UID={sql_creds['uid']};PWD={sql_creds['pwd']}"
            conn = pyodbc.connect(conn_str)
            
            update_status("Extracting server schema...")
            schema_query = "SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'dbo'"
            df_schema = pd.read_sql(schema_query, conn)
            
            for table, group in df_schema.groupby('TABLE_NAME'):
                cols = ", ".join(group['COLUMN_NAME'].tolist())
                schemas.append(f"Table: {table} | Columns: {cols}")

        master_schema = "\n".join(schemas)

        # ==========================================
        # PHASE B: AI GENERATION
        # ==========================================
        update_status("AURA is architecting data extraction...")
        
        if mode == "LOCAL":
            prompt = f"""
            Write SQLite views for these requirements: {user_requirements}
            SCHEMA:\n{master_schema}
            RULES: 
            1. Output ONLY exact CREATE VIEW queries. Wrap view names in double quotes.
            2. Return raw SQL separated by semicolons. No markdown.
            """
        else:
            prompt = f"""
            Write pure T-SQL SELECT statements for these requirements: {user_requirements}
            SCHEMA:\n{master_schema}
            RULES: 
            1. DO NOT use CREATE VIEW. Write pure, read-only SELECT queries.
            2. Separate queries with semicolons (;).
            3. CRITICAL: Start each query with a SQL comment naming the output (e.g., -- Sales_By_Region \n SELECT ...)
            4. Return raw SQL only. No markdown.
            """

        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        ai_sql = response.text.strip().replace("```sql", "").replace("```", "")

        # ==========================================
        # PHASE C: EXECUTION & EXPORT
        # ==========================================
        update_status("Fetching data and formatting Excel...")
        
        with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
            
            if mode == "LOCAL":
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
                for view in cursor.fetchall():
                    try: cursor.execute(f'DROP VIEW IF EXISTS "{view[0]}";')
                    except: pass
                
                for query in ai_sql.split(';'):
                    if query.strip(): cursor.execute(query.strip())
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
                views = cursor.fetchall()
                if not views: raise ValueError("AURA generated no views.")
                for view in views:
                    df_view = pd.read_sql_query(f'SELECT * FROM "{view[0]}"', conn)
                    df_view.to_excel(writer, sheet_name=view[0][:31], index=False)
            
            elif mode == "SQL_SERVER":
                queries = [q.strip() for q in ai_sql.split(';') if q.strip()]
                if not queries: raise ValueError("AURA generated no queries.")
                
                for idx, query in enumerate(queries):
                    lines = query.split('\n')
                    sheet_name = f"Insight_{idx+1}"
                    if lines[0].startswith('--'):
                        sheet_name = lines[0].replace('--', '').strip()[:31]
                    
                    df_result = pd.read_sql(query, conn)
                    df_result.to_excel(writer, sheet_name=sheet_name, index=False)

        conn.close()
        if mode == "LOCAL":
            try: os.remove(db_path) 
            except: pass

        update_status("Success! Launching Excel...", "#2ECC71")
        os.startfile(excel_output)

    except Exception as e:
        app.after(0, lambda: status_label.configure(text="Status: Failed", text_color="#E74C3C"))
        app.after(0, lambda: messagebox.showerror("Error", str(e)))
        if 'conn' in locals() and conn: conn.close()
        
    finally:
        app.after(0, lambda: run_btn.configure(state="normal", text="🚀 Execute AURA Pipeline"))

# ==========================================
# 3. UI HELPER FUNCTIONS
# ==========================================
def get_file(): source_var.set(filedialog.askopenfilename(filetypes=[("Data", "*.csv *.xlsx *.xls")]))
def get_folder(): source_var.set(filedialog.askdirectory())
def get_save_dir(): save_var.set(filedialog.askdirectory())

def start_process():
    active_tab = tabs.get()
    save_path = save_var.get()
    reqs = text_area.get("1.0", "end").strip()
    
    if not save_path or not reqs:
        messagebox.showwarning("Missing Info", "Please provide a save destination and your requirements.")
        return

    run_btn.configure(state="disabled", text="⏳ Processing...")

    if active_tab == "Local Files":
        if not source_var.get():
            messagebox.showwarning("Missing Info", "Please select local data.")
            run_btn.configure(state="normal", text="🚀 Execute AURA Pipeline")
            return
        threading.Thread(target=run_pipeline, args=(reqs, "LOCAL", source_var.get(), save_path), daemon=True).start()
    
    elif active_tab == "SQL Server":
        creds = {
            "server": server_entry.get().strip(),
            "db": db_entry.get().strip(),
            "uid": uid_entry.get().strip(),
            "pwd": pwd_entry.get().strip()
        }
        if not all(creds.values()):
            messagebox.showwarning("Missing Info", "Please fill out all SQL Server credentials.")
            run_btn.configure(state="normal", text="🚀 Execute AURA Pipeline")
            return
        threading.Thread(target=run_pipeline, args=(reqs, "SQL_SERVER", None, save_path, creds), daemon=True).start()

# ==========================================
# 4. WINDOWS APP INTERFACE
# ==========================================
app = ctk.CTk()
app.title("AURA - Autonomous Reporting Analytics")
app.geometry("650x700")
app.resizable(False, False)

source_var, save_var = ctk.StringVar(), ctk.StringVar()

ctk.CTkLabel(app, text="AURA - Autonomous Reporting Analytics", font=("Segoe UI", 24, "bold")).pack(pady=(15, 0))
ctk.CTkLabel(app, text="Powered by Gemini AI", text_color="gray").pack(pady=(0, 10))

tabs = ctk.CTkTabview(app, height=140)
tabs.pack(padx=20, pady=(0, 10), fill="x")
tabs.add("Local Files")
tabs.add("SQL Server")

# Local Tab Content
ctk.CTkLabel(tabs.tab("Local Files"), text="Select Data Source:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(5, 5))
f1 = ctk.CTkFrame(tabs.tab("Local Files"), fg_color="transparent")
f1.pack(anchor="w", fill="x")
ctk.CTkButton(f1, text="📄 File", command=get_file, width=80).pack(side="left", padx=(0, 5))
ctk.CTkButton(f1, text="📁 Folder", command=get_folder, width=80).pack(side="left", padx=(0, 10))
ctk.CTkEntry(f1, textvariable=source_var, state="readonly", width=380).pack(side="left")

# SQL Server Tab Content
server_entry = ctk.CTkEntry(tabs.tab("SQL Server"), placeholder_text="Server Address (e.g., localhost)", width=280)
server_entry.grid(row=0, column=0, padx=5, pady=10)
db_entry = ctk.CTkEntry(tabs.tab("SQL Server"), placeholder_text="Database Name", width=280)
db_entry.grid(row=0, column=1, padx=5, pady=10)
uid_entry = ctk.CTkEntry(tabs.tab("SQL Server"), placeholder_text="Username", width=280)
uid_entry.grid(row=1, column=0, padx=5, pady=10)
pwd_entry = ctk.CTkEntry(tabs.tab("SQL Server"), placeholder_text="Password", show="*", width=280)
pwd_entry.grid(row=1, column=1, padx=5, pady=10)

card = ctk.CTkFrame(app, corner_radius=10)
card.pack(padx=20, fill="both", expand=True)

ctk.CTkLabel(card, text="Output Destination:", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
f2 = ctk.CTkFrame(card, fg_color="transparent")
f2.pack(anchor="w", padx=15, fill="x")
ctk.CTkButton(f2, text="📁 Browse", command=get_save_dir, width=80).pack(side="left", padx=(0, 10))
ctk.CTkEntry(f2, textvariable=save_var, state="readonly", width=465).pack(side="left")

ctk.CTkLabel(card, text="Requirements (Plain English):", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
text_area = ctk.CTkTextbox(card, height=100, width=570, border_width=1)
text_area.pack(padx=15, pady=(0, 10))
ctk.CTkButton(card, text="Clear", command=lambda: text_area.delete("1.0", "end"), fg_color="transparent", border_width=1, width=70).pack(anchor="e", padx=15)

run_btn = ctk.CTkButton(app, text="🚀 Execute AURA Pipeline", font=("Segoe UI", 14, "bold"), command=start_process, height=40)
run_btn.pack(pady=(15, 5))
status_label = ctk.CTkLabel(app, text="Status: Ready", text_color="gray", font=("Segoe UI", 12, "italic"))
status_label.pack(pady=(0, 15))

app.mainloop()