# Contributing

## Setup (Windows)

```powershell
# Clone
git clone <repo-url>
cd product-tool

# Backend
cd backend
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt

# Frontend
cd landing
npm install
```

## Development

```bash
# Terminal 1: Backend
cd backend
.\venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend
cd landing
npm run dev
# → http://localhost:3000 points to http://127.0.0.1:8000 for API
```

## Environment Variables

Copy `backend/.env.example` (if exists) to `backend/.env` and fill in:
- `JWT_SECRET_KEY` (required)
- `DEEPSEEK_API_KEY` (required for Smart Paste)
- Others optional — see README.md

## Code Style

- **Python:** 4-space indent, snake_case, type hints where helpful
- **JavaScript:** 2-space indent, ES6+, `'use client'` for React components
- **Commit messages:** Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`)

## Testing

```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Frontend lint
cd landing
npm run lint
```

## Pull Requests

1. Create a feature branch from `master`
2. Make changes, test locally
3. Run `npm run lint` in `landing/`
4. Run `pytest` in `backend/` (when tests exist)
5. Commit with conventional commit message
6. Push and create PR

## Project Structure

See [ARCHITECTURE.md](./ARCHITECTURE.md) for details.
