import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import sqlite3
import os
import threading
import re
from google import genai

# ==========================================
# 1. APP SETTINGS & API KEY
# ==========================================
API_KEY = "AIzaSyDLnU076NF-TLccDUA_P7Fu2j-qjYnTyjE"

ctk.set_appearance_mode("dark")  
ctk.set_default_color_theme("blue")  

# ==========================================
# 2. THE AI BACKEND ENGINE
# ==========================================
def run_pipeline(user_requirements, source_path, save_path):
    try:
        client = genai.Client(api_key=API_KEY)
        
        def update_status(text, color="#F39C12"):
            app.after(0, lambda: status_label.configure(text=f"Status: {text}", text_color=color))

        # Setup paths
        db_path = os.path.join(save_path, "ai_temp_db.sqlite")
        excel_output = os.path.join(save_path, "AI_Generated_Insights.xlsx")
        
        # Determine if source is a single file or a whole folder
        if os.path.isfile(source_path):
            files = [source_path]
            update_status("Processing single file...")
        else:
            valid_exts = ('.csv', '.xlsx', '.xls')
            files = [os.path.join(source_path, f) for f in os.listdir(source_path) 
                     if f.lower().endswith(valid_exts) and not f.startswith('~$')]
            update_status(f"Scanning folder ({len(files)} files found)...")

        if not files:
            raise ValueError("No valid spreadsheet files found.")

        # --- STEP A: Load Data & Clean Filenames ---
        conn = sqlite3.connect(db_path)
        schemas = []

        for f_path in files:
            raw_name, _ = os.path.splitext(os.path.basename(f_path))
            # Automatically clean messy filenames to prevent SQL crashes
            safe_table_name = re.sub(r'\W+', '_', raw_name).strip('_')
            
            try:
                df = pd.read_csv(f_path) if f_path.lower().endswith('.csv') else pd.read_excel(f_path)
                df.to_sql(safe_table_name, conn, if_exists="replace", index=False)
                schemas.append(f"Table: {safe_table_name} | Columns: {', '.join(df.columns)}")
            except Exception as e:
                print(f"Skipped {raw_name}: {e}")

        # --- STEP B: Ask AI for SQL ---
        update_status("AI is generating data architecture...")
        prompt = f"""
        You are an expert SQL generator. Write SQLite views for these requirements: {user_requirements}
        DATABASE SCHEMA:\n{chr(10).join(schemas)}
        RULES: 
        1. Output ONLY exact CREATE VIEW queries based on the requirements. No extra views.
        2. Wrap all view names in double quotes. 
        3. Return raw SQL separated by semicolons. No markdown.
        """
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        ai_sql = response.text.strip().replace("```sql", "").replace("```", "")

        # --- STEP C: Execute SQL in Database ---
        update_status("Applying AI architecture to data...")
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
        for view in cursor.fetchall():
            try: cursor.execute(f'DROP VIEW IF EXISTS "{view[0]}";')
            except: pass
        conn.commit()

        for query in ai_sql.split(';'):
            if query.strip(): cursor.execute(query.strip())
        conn.commit()

        # --- STEP D: Export Final Excel & Cleanup ---
        update_status("Exporting final insights to Excel...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
        views = cursor.fetchall()
        
        if views:
            with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
                for view in views:
                    df_view = pd.read_sql_query(f'SELECT * FROM "{view[0]}"', conn)
                    df_view.to_excel(writer, sheet_name=view[0][:31], index=False)
            
            conn.close()
            try: os.remove(db_path) # Delete the temp database invisibly
            except: pass

            update_status("Success! Launching Excel...", "#2ECC71")
            os.startfile(excel_output)
        else:
            conn.close()
            update_status("Error: No data generated.", "#E74C3C")
            app.after(0, lambda: messagebox.showwarning("Warning", "AI generated no data."))

    except Exception as e:
        app.after(0, lambda: status_label.configure(text="Status: Failed", text_color="#E74C3C"))
        app.after(0, lambda: messagebox.showerror("Error", str(e)))
        
    finally:
        app.after(0, lambda: run_btn.configure(state="normal", text="🚀 Execute AI Pipeline"))

# ==========================================
# 3. UI HELPER FUNCTIONS
# ==========================================
def get_file(): source_var.set(filedialog.askopenfilename(filetypes=[("Data", "*.csv *.xlsx *.xls")]))
def get_folder(): source_var.set(filedialog.askdirectory())
def get_save_dir(): save_var.set(filedialog.askdirectory())

def start_process():
    if not source_var.get() or not save_var.get() or not text_area.get("1.0", "end").strip():
        messagebox.showwarning("Missing Info", "Please fill out all fields.")
        return
    run_btn.configure(state="disabled", text="⏳ Processing...")
    threading.Thread(target=run_pipeline, args=(text_area.get("1.0", "end").strip(), source_var.get(), save_var.get()), daemon=True).start()

# ==========================================
# 4. WINDOWS APP INTERFACE
# ==========================================
app = ctk.CTk()
app.title("Enterprise AI Data Architect")
app.geometry("650x650")
app.resizable(False, False)

source_var, save_var = ctk.StringVar(), ctk.StringVar()

# Header
ctk.CTkLabel(app, text="Zero-Touch Data Pipeline", font=("Segoe UI", 24, "bold")).pack(pady=(20, 0))
ctk.CTkLabel(app, text="Powered by Gemini AI", text_color="gray").pack(pady=(0, 15))

card = ctk.CTkFrame(app, corner_radius=10)
card.pack(padx=20, fill="both", expand=True)

# 1. Source Data
ctk.CTkLabel(card, text="1. Select Data Source:", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
f1 = ctk.CTkFrame(card, fg_color="transparent")
f1.pack(anchor="w", padx=15, fill="x")
ctk.CTkButton(f1, text="📄 File", command=get_file, width=80).pack(side="left", padx=(0, 5))
ctk.CTkButton(f1, text="📁 Folder", command=get_folder, width=80).pack(side="left", padx=(0, 10))
ctk.CTkEntry(f1, textvariable=source_var, state="readonly", width=380).pack(side="left")

# 2. Save Destination
ctk.CTkLabel(card, text="2. Output Destination:", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
f2 = ctk.CTkFrame(card, fg_color="transparent")
f2.pack(anchor="w", padx=15, fill="x")
ctk.CTkButton(f2, text="📁 Browse", command=get_save_dir, width=80).pack(side="left", padx=(0, 10))
ctk.CTkEntry(f2, textvariable=save_var, state="readonly", width=465).pack(side="left")

# 3. Requirements Input
ctk.CTkLabel(card, text="3. Requirements (Plain English):", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
text_area = ctk.CTkTextbox(card, height=100, width=570, border_width=1)
text_area.pack(padx=15, pady=(0, 10))
ctk.CTkButton(card, text="Clear", command=lambda: text_area.delete("1.0", "end"), fg_color="transparent", border_width=1, width=70).pack(anchor="e", padx=15)

# Footer
run_btn = ctk.CTkButton(app, text="🚀 Execute AI Pipeline", font=("Segoe UI", 14, "bold"), command=start_process, height=40)
run_btn.pack(pady=(15, 5))
status_label = ctk.CTkLabel(app, text="Status: Ready", text_color="gray", font=("Segoe UI", 12, "italic"))
status_label.pack(pady=(0, 15))

app.mainloop()