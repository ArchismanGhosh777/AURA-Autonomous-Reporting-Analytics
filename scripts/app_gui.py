import customtkinter as ctk
from tkinter import messagebox
import subprocess
import os

# ==========================================
# 1. MODERN THEME SETUP
# ==========================================
# Sets the app to Dark Mode with a blue accent theme
ctk.set_appearance_mode("dark")  
ctk.set_default_color_theme("blue")  

# ==========================================
# 2. FILE PATHS
# ==========================================
req_file_path = r"C:\Users\Archisman Ghosh\Documents\Apple_AI\scripts\requirements.txt"
pipeline_script = r"C:\Users\Archisman Ghosh\Documents\Apple_AI\scripts\apple_pipeline.py"

# ==========================================
# 3. APPLICATION LOGIC
# ==========================================
def execute_pipeline():
    selected_system = system_dropdown.get()
    
    if selected_system != "SQL Database (Phase 1)":
        messagebox.showinfo("Phase 2 Notice", f"You selected {selected_system}.\nThis architecture phase is scheduled for deployment soon.")
        return

    user_input = text_area.get("1.0", "end").strip()
    
    if not user_input:
        messagebox.showwarning("Input Required", "Please outline your data requirements before execution.")
        return

    # Save requirements to text file
    try:
        with open(req_file_path, "w", encoding="utf-8") as file:
            file.write(user_input)
    except Exception as e:
        messagebox.showerror("File Error", f"Could not save requirements:\n{e}")
        return

    # UI Update: Processing State
    run_button.configure(state="disabled", text="⏳ Processing AI Pipeline...")
    status_label.configure(text="Status: AI is scanning datasets and translating SQL...", text_color="#F39C12") # Warning Orange
    app.update() 

    # Execute Background Pipeline
    try:
        result = subprocess.run(["python", pipeline_script], capture_output=True, text=True)
        
        if result.returncode == 0:
            status_label.configure(text="Status: Pipeline Execution Complete", text_color="#2ECC71") # Success Green
            messagebox.showinfo("Success", "The AI Data Architect has successfully completed the pipeline.\n\nYour automated views are now available in the SQLite database.")
            text_area.delete("1.0", "end") # Auto-wipe
            
        else:
            status_label.configure(text="Status: Execution Error", text_color="#E74C3C") # Danger Red
            messagebox.showerror("Pipeline Error", f"The AI encountered an error:\n{result.stderr}\n\n{result.stdout}")
            
    except Exception as e:
        status_label.configure(text="Status: System Failure", text_color="#E74C3C")
        messagebox.showerror("System Error", f"Could not start pipeline:\n{e}")
        
    finally:
        # Reset UI
        run_button.configure(state="normal", text="🚀 Execute AI Pipeline")

def clear_text():
    text_area.delete("1.0", "end")

# ==========================================
# 4. DRAW THE WINDOWS GUI (ENTERPRISE UI)
# ==========================================
# Main Window Setup
app = ctk.CTk()
app.title("Enterprise AI Data Architect")
app.geometry("700x550")
app.resizable(False, False) # Lock window size for a clean look

# --- Header Section ---
header_frame = ctk.CTkFrame(app, fg_color="transparent")
header_frame.pack(pady=(25, 10), padx=30, fill="x")

title_label = ctk.CTkLabel(header_frame, text="Zero-Touch Data Pipeline", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"))
title_label.pack(anchor="w")

subtitle_label = ctk.CTkLabel(header_frame, text="Powered by Gemini 2.5 Flash | Apple Retail Sales Architecture", font=ctk.CTkFont(family="Segoe UI", size=13), text_color="gray")
subtitle_label.pack(anchor="w")

# --- Main Content Frame (Card Layout) ---
main_frame = ctk.CTkFrame(app, corner_radius=15)
main_frame.pack(pady=10, padx=30, fill="both", expand=True)

# 1. Target System Dropdown
ctk.CTkLabel(main_frame, text="1. Target Architecture:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
system_dropdown = ctk.CTkComboBox(main_frame, values=["SQL Database (Phase 1)", "Microsoft Excel (Phase 2)", "Microsoft Power BI (Phase 2)"], width=300, font=ctk.CTkFont(size=13))
system_dropdown.set("SQL Database (Phase 1)")
system_dropdown.pack(anchor="w", padx=20)

# 2. Natural Language Input Area
ctk.CTkLabel(main_frame, text="2. Natural Language Requirements:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
text_area = ctk.CTkTextbox(main_frame, height=140, width=600, font=ctk.CTkFont(size=14), corner_radius=8, border_width=1)
text_area.pack(padx=20, pady=(0, 10))

# Clear Button (Secondary Action)
clear_btn = ctk.CTkButton(main_frame, text="Clear Input", command=clear_text, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), width=100)
clear_btn.pack(anchor="e", padx=20)

# --- Footer & Controls Section ---
footer_frame = ctk.CTkFrame(app, fg_color="transparent")
footer_frame.pack(pady=(10, 20), padx=30, fill="x")

# Execute Button (Primary Action)
run_button = ctk.CTkButton(footer_frame, text="🚀 Execute AI Pipeline", font=ctk.CTkFont(size=15, weight="bold"), command=execute_pipeline, height=45, corner_radius=8)
run_button.pack(pady=(0, 10))

# Live Status Indicator
status_label = ctk.CTkLabel(footer_frame, text="Status: System Ready & Waiting", font=ctk.CTkFont(size=12, slant="italic"), text_color="gray")
status_label.pack()

# Start the application
app.mainloop()