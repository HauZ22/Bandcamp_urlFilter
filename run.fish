#!/usr/bin/env fish

echo "Starting Bandcamp to Qobuz Matcher Web UI..."

if not type -q python
    echo "Error: Python is required but was not found on PATH. Install Python 3.10+ and try again."
    exit 1
end

if not test -d .venv/bin
    echo "Creating virtual environment..."
    python -m venv .venv; or exit 1
end

echo "Activating virtual environment..."
if test -f .venv/bin/activate.fish
    source .venv/bin/activate.fish
else
    echo "Error: Expected .venv/bin/activate.fish but it was not found."
    exit 1
end

echo "Checking dependencies (quiet mode)..."
python -m pip install --disable-pip-version-check -q --upgrade pip; or exit 1
python -m pip install --disable-pip-version-check -q -r requirements.txt; or exit 1

echo "Checking Qobuz environment variables (optional for Dry Run)..."
python -c "
import os, pathlib
path = pathlib.Path('.env')
if path.exists():
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip(\"\\\"\").strip(\"'\"))
if not os.environ.get('QOBUZ_USER_AUTH_TOKEN'):
    print('Warning: QOBUZ_USER_AUTH_TOKEN is missing.')
    print()
    print('Dry Run mode will still work, but Qobuz matching requires this in .env:')
    print('PYTHONPATH=.')
    print('# Optional: QOBUZ_APP_ID (auto-fetched if omitted)')
    print('QOBUZ_USER_AUTH_TOKEN=your_qobuz_token_here')
"

python -m streamlit run app.py
