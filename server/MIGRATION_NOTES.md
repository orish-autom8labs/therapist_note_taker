# Migration Notes

## Old JavaScript Files

The following JavaScript files are **no longer used** (backend is now Python):

- `index.js` - Old Node.js/Express server (replaced by `main.py`)
- `src/providers/*.js` - Old JS providers (replaced by `*.py`)
- `src/services/*.js` - Old JS services (replaced by `*.py`)
- `src/config.js` - Old JS config (replaced by `config.py`)

You can delete these files if you want, or keep them for reference.

## New Python Structure

All backend code is now in Python:

- `main.py` - FastAPI server with WebSocket
- `run.py` - Simple server runner
- `src/providers/*.py` - Python provider implementations
- `src/services/*.py` - Python service implementations
- `src/config.py` - Python configuration
- `requirements.txt` - Python dependencies

## Frontend Unchanged

The React frontend (`client/`) remains JavaScript - no changes needed!




