# Assignment 1

This repository is the starting point for Assignment 1: a small full-stack application with a FastAPI backend and a Vue frontend.

## Project structure

```text
.
├── backend/          # FastAPI application
├── frontend/         # Vue application (Vite)
├── AGENTS.md         # Project rules for contributors and coding agents
└── README.md
```

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer
- npm 10 or newer

## Backend setup

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On Windows, activate the virtual environment with `.venv\Scripts\activate`.

The API will be available at `http://localhost:8000`. Its interactive documentation will be at `http://localhost:8000/docs`.

## Frontend setup

In a separate terminal, from the repository root:

```bash
cd frontend
npm install
npm run dev
```

The frontend development server will print its local URL, typically `http://localhost:5173`.

## Current status

Only the initial project structure is included. Dependencies have not been installed.
