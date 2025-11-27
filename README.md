# Amoura Backend

FastAPI + SQLModel backend for the **Amoura** cake e-commerce website.
Uses **Supabase** (Postgres + Auth + Storage) and **uv** for environment & dependency management.

---

## 1. Prerequisites

* **Python** 3.10+ (managed via `uv`)

* **uv** installed globally

  ```bash
  pip install uv
  # or follow the official installation instructions
  ```

* A **Supabase** project with:

  * Postgres database
  * Auth configured
  * Storage bucket (e.g. `assets`)

This project is configured via **`pyproject.toml`** only (no `requirements.txt`, no manual venv setup).

---

## 2. Configuration (`.env`)

Create a `.env` file in the project root with at least:

```env
# Supabase core
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# Supabase JWT verification
SUPABASE_JWT_SECRET=your-jwt-secret

# Database (Supabase Postgres, SQLModel/SQLAlchemy URL)
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE

# App meta
PROJECT_NAME="Amoura Backend"
API_V1_STR="/api/v1"
```

---

## 3. Install dependencies with `uv`

From the project root (where `pyproject.toml` lives):

```bash
uv sync
```

`uv sync` will:

* Create a **project-local virtual environment** (by default in `.venv/`)
* Install all dependencies defined in `pyproject.toml`

You don’t need to manually create a venv; `uv` handles it.

---

## 4. Run the app from the command line

From the project root:

```bash
uv run uvicorn app.main:app --reload
```

* `uv run` uses the environment created by `uv sync`
* `--reload` enables auto-reload on code changes (dev mode)

The app will be available at:

* Root health check: `http://127.0.0.1:8000/`
* Swagger UI: `http://127.0.0.1:8000/docs`
* ReDoc: `http://127.0.0.1:8000/redoc`

If something fails at startup, check:

* `.env` contents (missing/incorrect Supabase or DB URL)
* Database connectivity (Supabase Postgres reachable from your machine)

---

## 5. (If using PyCharm) Configure Interpreter and Run configuration

### 5.1. Configure the interpreter

1. Open **PyCharm**.

2. Go to
   `File` → `Settings` → `Project: Amoura_BackEnd` → **Python Interpreter**.

3. Click the gear icon → **Add** → **Add Local Interpreter**.

4. Choose **Existing environment** and point to the interpreter that `uv sync` created:

5. Click **OK** / **Apply**.

> Even though `uv` created the environment, PyCharm treats it like a normal virtualenv, which is exactly what we want.

---

### 5.2. Create a Run configuration 

1. Go to **Edit Configurations…**

2. Click **+** → choose **FastAPI**.

3. Fill in:

   * **Application file**: Point to the location of `main.py`
   * **Uvicorn option**: `--reload`
   * **Python interpreter**: select the `.venv` interpreter you added above, or create a new UV interpreter.

4. **Environment variables**:

   * If your `config.py` loads `.env` automatically (e.g. via `BaseSettings(env_file=".env")`), you don’t need to configure anything here.
   * Otherwise, you can manually add the same variables as in `.env` under **Environment variables…**

5. Click **OK** to save the configuration.

---

## 6. Quick health check

Once the server is running (CLI or PyCharm), verify:

```bash
curl http://127.0.0.1:8000/
```

You should see a simple JSON response confirming the backend is up.
