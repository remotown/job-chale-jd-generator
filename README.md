# Job Chale JD Generator Backend

This repository handles Job Description (JD) generation specifically for Job Chale with their unique field requirements.

## Project Structure

```
job-chale-jd-generator/
├── src/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entrypoint
│   └── config.py        # Configuration & environment variable handling
├── tests/
│   └── test_main.py     # Unit/Integration tests
├── .env.example         # Environment variable templates
├── .gitignore
├── requirements.txt     # Python dependencies
└── README.md
```

## Setup & Running Locally

### 1. Prerequisites
- Python 3.9+

### 2. Installation
Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` and set your variables:

```bash
cp .env.example .env
```

### 4. Running the API Server
Start the local FastAPI dev server with Uvicorn:

```bash
uvicorn src.main:app --reload
```

The server will start at `http://127.0.0.1:8000`. You can access the interactive API docs at `http://127.0.0.1:8000/docs`.

### 5. Running Tests
Run pytest to execute tests:

```bash
pytest
```
