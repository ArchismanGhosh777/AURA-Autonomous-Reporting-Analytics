# AURA: Autonomous Reporting Analytics 🧠📊

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![SQL](https://img.shields.io/badge/SQL-Relational_DB-orange)
![Power BI](https://img.shields.io/badge/Power_BI-Automated-yellow)
![AI](https://img.shields.io/badge/AI-NLP_to_SQL-success)

**AURA** is an end-to-end, zero-touch business intelligence engine designed to democratize data analytics. It empowers non-technical stakeholders to extract deep historical insights and generate interactive visualizations from unstructured data using only natural language queries.

## 🚀 Core Features

* **Autonomous Data Engineering Pipeline:** Ingests raw, unstructured datasets and dynamically maps them into fully normalized, relational SQL tables without human intervention.
* **NLP-to-SQL Translation Engine:** Leverages Generative AI APIs to translate conversational business questions (e.g., *"What are the core sales trends?"*) into highly optimized, executable SQL queries.
* **Zero-Touch Reporting:** Automatically extracts queried data to generate formatted Excel trend reports and dynamically constructs interactive Power BI dashboards.
* **No-Code Windows GUI:** A user-friendly desktop interface allowing business users to point the application at a local dataset and start chatting with their data immediately.

## 🏗️ System Architecture

1. **Ingestion:** User selects a raw dataset via the Windows GUI.
2. **Transformation:** Python engine parses the data, infers schema, and normalizes it into a relational SQL database.
3. **Interaction:** User inputs natural language business questions.
4. **Processing (AI):** The NLP engine analyzes the schema, generates the appropriate SQL query, and executes it against the database.
5. **Output:** The resulting dataset is automatically pushed into an Excel trend report and connected to a pre-architected Power BI template for visual analysis.

## 💼 Primary Use-Case: Apple Retail Sales

This repository includes a demonstration of AURA applied to an **Apple Retail Sales** dataset. 
* **The Problem:** Disparate flat files required manual consolidation to track Year-to-Date (YTD) and Start-of-Month metrics.
* **The AURA Solution:** The application autonomously mapped the flat files into a Star Schema, generated the necessary DAX logic, and output a complete dashboard tracking product pain points and sales trends based solely on conversational prompts.

## 💻 Tech Stack

* **Frontend:** Python (Tkinter / PyQt - *Update based on your exact library*)
* **Backend:** Python, SQLite / SQL Server 
* **AI Integration:** Generative AI APIs (LLMs for NLP-to-SQL)
* **Output Generation:** Pandas (Excel export), Microsoft Power BI (Automated Dashboarding)

## ⚙️ Local Setup & Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/yourusername/aura-analytics-engine.git](https://github.com/yourusername/aura-analytics-engine.git)
