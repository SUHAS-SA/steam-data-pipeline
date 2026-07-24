# Steam Data Extraction & Storage - Setup & Execution Guide

This document provides step-by-step instructions on setting up all prerequisites, configuring virtual environments, initializing the database schema, and running the ETL pipeline.

---

## 📋 1. Prerequisites Checklist

Before starting, ensure you have the following installed on your system:

| Prerequisite | Minimum Version | Installation Link |
| :--- | :--- | :--- |
| **Python** | 3.8+ | [python.org](https://www.python.org/downloads/) |
| **PostgreSQL** | 12.0+ | [postgresql.org](https://www.postgresql.org/download/) |
| **Git** | 2.20+ | [git-scm.com](https://git-scm.com/) |
| **Steam API Key** | Web API Key | [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey) |

---

## ⚙️ 2. Virtual Environment & Dependencies Setup

Setting up an isolated Python virtual environment (`venv`) prevents dependency conflicts with system packages.

### Step 2.1: Clone Repository
```bash
git clone https://github.com/your-username/steam-data-pipeline.git
cd steam-data-pipeline
```

### Step 2.2: Create Virtual Environment

#### Windows (PowerShell / Command Prompt):
```powershell
python -m venv venv
```

#### macOS / Linux (Terminal):
```bash
python3 -m venv venv
```

### Step 2.3: Activate Virtual Environment

#### Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```
*(If PowerShell blocks activation script, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`)*

#### Windows (Command Prompt):
```cmd
venv\Scripts\activate.bat
```

#### macOS / Linux:
```bash
source venv/bin/activate
```

### Step 2.4: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔑 3. Environment Variables Configuration

1. Copy the template `.env.example` file to create your active `.env` file:
   ```bash
   cp .env.example .env
   ```
   *(On Windows Command Prompt, use: `copy .env.example .env`)*

2. Open `.env` in a text editor and fill in your credentials:
   ```env
   # Steam API Configuration
   STEAM_API_KEY=YOUR_ACTUAL_STEAM_API_KEY

   # PostgreSQL Database Configuration
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=gamecheck
   DB_USER=postgres
   DB_PASS=your_postgres_password

   # Pipeline Settings
   CHUNK_SIZE=10000
   RATE_LIMIT_DELAY=1.5
   ```

---

## 🗄️ 4. PostgreSQL Database & Schema Setup

### Step 4.1: Create PostgreSQL Database
Using `psql` command line or pgAdmin, create a database named `gamecheck`:

```sql
CREATE DATABASE gamecheck;
```

### Step 4.2: Apply Schema DDL
Execute the schema script to create the relational tables and performance indexes:

#### Using `psql` CLI:
```bash
psql -h localhost -U postgres -d gamecheck -f sql/schema.sql
```

#### Using pgAdmin / DBeaver:
Open `sql/schema.sql` inside your SQL editor connected to `gamecheck` database and execute the query.

---

## 🚀 5. How to Run the Pipeline

The pipeline is organized into three stages:
1. **Extract**: Scrapes Steam API, tracks processed state, saves chunked raw JSONL files.
2. **Transform**: Parses HTML system requirements, converts data types, formats SQL statements.
3. **Load**: Connects to PostgreSQL and executes the generated SQL script.

### Option A: Run Full Pipeline (Recommended)
Executes all stages sequentially:
```bash
python -m src.pipeline --stage all
```

### Option B: Run Specific Pipeline Stages

#### Stage 1: Extraction Only
```bash
python -m src.pipeline --stage extract
```

#### Stage 2: Transformation & SQL Generation Only
```bash
python -m src.pipeline --stage transform
```

#### Stage 3: Database Import Only
```bash
python -m src.pipeline --stage load
```

---

## 🛠️ 6. Troubleshooting & Common Issues

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `psycopg2.OperationalError: connection to server failed` | PostgreSQL service not running or invalid password | Ensure PostgreSQL service is active (`services.msc` on Windows or `sudo systemctl status postgresql`) and verify `.env` credentials. |
| `HTTP 429 Too Many Requests` | Steam API rate limit reached | The extractor automatically pauses for 60 seconds when rate-limited. You can increase `RATE_LIMIT_DELAY` in `.env` to `2.0` or higher. |
| `ModuleNotFoundError: No module named 'src'` | Running script outside project root | Ensure you execute commands using `python -m src.pipeline` from the `steam-data-pipeline/` root directory. |
