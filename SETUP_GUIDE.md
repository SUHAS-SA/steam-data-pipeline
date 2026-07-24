# Steam Data Extraction & Storage - Setup & Execution Guide

This document provides step-by-step instructions on setting up all prerequisites, configuring virtual environments, initializing the database schema, and running the ETL pipeline.

---

## 📋 1. Prerequisites Checklist

Before starting, ensure you have the following installed on your system:

| Prerequisite            | Minimum Version | Installation Link                                                     |
| :---------------------- | :-------------- | :-------------------------------------------------------------------- |
| **Python**        | 3.8+            | [python.org](https://www.python.org/downloads/)                        |
| **PostgreSQL**    | 12.0+           | [postgresql.org](https://www.postgresql.org/download/)                 |
| **Git**           | 2.20+           | [git-scm.com](https://git-scm.com/)                                    |
| **Steam API Key** | Web API Key     | [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey) |

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

Before applying the schema, you must create an empty database named `gamecheck`.

#### Method A: Via Command Line (psql)

```sql
psql -U postgres -c "CREATE DATABASE gamecheck;"
```

#### Method B: Via pgAdmin 4

1. Open pgAdmin 4 and connect to your local server.
2. Right-click **Databases** -> **Create** -> **Database...**
3. Name the database `gamecheck` and click **Save**.

---

### Step 4.2: Apply Schema DDL (`sql/schema.sql`)

The command to apply the database schema is:

```bash
psql -h localhost -U postgres -d gamecheck -f sql/schema.sql
```

#### 🔍 Breakdown of the Command Options:

* `-h localhost`: Specifies the database host server (your local machine).
* `-U postgres`: Specifies the PostgreSQL username (`postgres` is default).
* `-d gamecheck`: Specifies the target database name.
* `-f sql/schema.sql`: Specifies the path to the SQL schema file to execute.

---

### 📍 Where & How to Run the Schema Command

#### Option 1: Standard Terminal / PowerShell / Command Prompt (Recommended)

1. **Open Terminal / PowerShell / Command Prompt** on your computer.
2. **Navigate to the root directory** of your project where `sql/schema.sql` is located:
   ```bash
   cd C:\Users\hp\Desktop\steam-data-pipeline
   ```
3. **Execute the command**:
   ```bash
   psql -h localhost -U postgres -d gamecheck -f sql/schema.sql
   ```
4. **Enter Password**: PostgreSQL will prompt you for the `postgres` user password. Type your password and press **Enter** (the characters will remain invisible while typing).

> [!NOTE]
> **Windows Troubleshooting (`'psql' is not recognized`)**:
> If Windows says `'psql' is not recognized as an internal or external command`, PostgreSQL is not in your system's PATH variable. You can run the command by using the full path to `psql.exe` (replace `16` with your installed PostgreSQL version):
>
> ```powershell
> & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U postgres -d gamecheck -f sql/schema.sql
> ```

---

#### Option 2: Using SQL Shell (`psql`) Interactive Application (Windows Start Menu)

If you prefer using the built-in Windows PostgreSQL GUI interactive console:

1. Open **Windows Start Menu** -> search for **SQL Shell (psql)** and launch it.
2. Press **Enter** to accept the defaults for Server [`localhost`], Database [`postgres`], Port [`5432`], and Username [`postgres`].
3. Enter your password when prompted.
4. Connect to the `gamecheck` database:
   ```sql
   \c gamecheck
   ```
5. Execute the schema file using the `\i` (import) command (forward slashes required):
   ```sql
   \i sql/schema.sql
   ```

   *(Or specify absolute path: `\i 'C:/Users/hp/Desktop/steam-data-pipeline/sql/schema.sql'`)*

---

#### Option 3: Using pgAdmin 4 or DBeaver (Graphical User Interface)

If you prefer using a visual SQL editor:

1. Open **pgAdmin 4** or **DBeaver**.
2. Connect to your local PostgreSQL server and expand the **gamecheck** database.
3. Open the **Query Tool** (In pgAdmin: Right-click `gamecheck` -> **Query Tool**).
4. Click the **Open File** folder icon (or press `Ctrl + O`) and navigate to `steam-data-pipeline/sql/schema.sql`.
5. Click the **Execute / Play** button (or press `F5`) to run the script.
6. Verify in the left panel under `gamecheck -> Schemas -> public -> Tables` that 6 tables (`games`, `genres`, `tags`, `game_genres`, `game_tags`, `game_requirements`) have been created.

---

## 🚀 5. How to Run the Pipeline

The pipeline is organized into three stages:

1. **Extract**: Scrapes Steam API, tracks processed state, saves chunked raw JSONL files.
2. **Transform**: Parses HTML system requirements, converts data types, formats SQL statements.
3. **Load**: Connects to PostgreSQL and executes the generated SQL script.

> [!IMPORTANT]
> ⏱️ **Execution Duration & Rate-Limit Notice for Stage 1 (Extraction)**:
> * **Catalog Scale**: The Steam catalog currently contains **over 170,000+ total apps**.
> * **API Rate Limits**: To prevent IP blocking and respect Steam's Web API limits, the scraper enforces a mandatory **1.5-second delay per request** (with automatic 60-second backoff when encountering HTTP 429 rate limit responses).
> * **Estimated Timeframe**:
>   - Scraping the entire catalog from scratch (~170,000+ apps) sequentially will take **approx. 50 to 70 hours** of continuous background execution.
>   - **Incremental Tracking**: The pipeline tracks progress state in `steam_apps.json`. Once an initial run or batch is saved, subsequent runs **only fetch brand-new game releases**, which typically completes in just a few minutes.
>   - **Safe Resumption**: Progress state is committed every 50 games. You can safely pause/cancel (`Ctrl + C`) and resume extraction anytime without losing past work.

### Option A: Run Full Pipeline (Recommended for Automation)

Executes all stages sequentially:

```bash
python -m src.pipeline --stage all
```

### Option B: Run Specific Pipeline Stages

#### Stage 1: Extraction Only (Long Running Process)

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

| Issue                                                      | Cause                                              | Solution                                                                                                                                    |
| :--------------------------------------------------------- | :------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------ |
| `psycopg2.OperationalError: connection to server failed` | PostgreSQL service not running or invalid password | Ensure PostgreSQL service is active (`services.msc` on Windows or `sudo systemctl status postgresql`) and verify `.env` credentials.  |
| `HTTP 429 Too Many Requests`                             | Steam API rate limit reached                       | The extractor automatically pauses for 60 seconds when rate-limited. You can increase`RATE_LIMIT_DELAY` in `.env` to `2.0` or higher. |
| `ModuleNotFoundError: No module named 'src'`             | Running script outside project root                | Ensure you execute commands using`python -m src.pipeline` from the `steam-data-pipeline/` root directory.                               |
