#!/usr/bin/env bash
set -euo pipefail

APP_NAME="bandcamp-urlfilter"
SERVICE_NAME="${SERVICE_NAME:-$APP_NAME}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${APP_DIR:-$SCRIPT_DIR}"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
VENV_DIR="${VENV_DIR:-$CONFIG_HOME/venv/$SERVICE_NAME}"
STATE_DIR="${STATE_DIR:-$CONFIG_HOME/$SERVICE_NAME}"
ENV_FILE="${ENV_FILE:-$APP_DIR/.env}"
EXAMPLE_ENV_FILE="${APP_DIR}/.env.example"
PORT_FILE="${STATE_DIR}/port"
BIND_ADDRESS="${BIND_ADDRESS:-127.0.0.1}"
PORT="${PORT:-}"
NO_START=0

usage() {
  cat <<'EOF'
Usage: ./setup-hbd.sh [options]

Options:
  --port <port>           Use a specific Streamlit port.
  --bind <address>        Bind address for Streamlit. Default: 127.0.0.1
  --service-name <name>   Override the user systemd service name.
  --venv <path>           Override the virtualenv path.
  --app-dir <path>        Override the repository/app directory.
  --env-file <path>       Override the .env path.
  --no-start              Write/update the service without starting it.
  -h, --help              Show this help text.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      PORT="$2"
      shift 2
      ;;
    --bind)
      BIND_ADDRESS="$2"
      shift 2
      ;;
    --service-name)
      SERVICE_NAME="$2"
      shift 2
      ;;
    --venv)
      VENV_DIR="$2"
      shift 2
      ;;
    --app-dir)
      APP_DIR="$2"
      shift 2
      ;;
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --no-start)
      NO_START=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

APP_DIR="$(cd "$APP_DIR" && pwd)"
SYSTEMD_DIR="${CONFIG_HOME}/systemd/user"
SERVICE_FILE="${SYSTEMD_DIR}/${SERVICE_NAME}.service"
INSTALL_INFO="${STATE_DIR}/install.env"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command not found: $1" >&2
    exit 1
  fi
}

pick_port() {
  python3 - "${1:-8501}" "${2:-8999}" <<'PY'
import socket
import sys

start = int(sys.argv[1])
end = int(sys.argv[2])

for port in range(start, end + 1):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            continue
        print(port)
        break
else:
    raise SystemExit("No free port available in the requested range.")
PY
}

require_command python3
require_command systemctl

mkdir -p "$CONFIG_HOME" "$STATE_DIR" "$SYSTEMD_DIR" "$APP_DIR/exports"

if [[ -z "$PORT" && -f "$PORT_FILE" ]]; then
  PORT="$(tr -d '[:space:]' < "$PORT_FILE")"
fi

if [[ -z "$PORT" ]]; then
  PORT="$(pick_port 8501 8999)"
fi

if [[ ! "$PORT" =~ ^[0-9]+$ ]]; then
  echo "Port must be numeric." >&2
  exit 1
fi

echo "Preparing ${APP_NAME} for a HostingByDesign-style user service..."
echo "App directory: ${APP_DIR}"
echo "Virtualenv: ${VENV_DIR}"
echo "Service: ${SERVICE_NAME}"
echo "Bind: ${BIND_ADDRESS}:${PORT}"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

echo "Installing Python dependencies..."
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/python" -m pip install -r "${APP_DIR}/requirements.txt"

if [[ ! -f "$ENV_FILE" && -f "$EXAMPLE_ENV_FILE" ]]; then
  cp "$EXAMPLE_ENV_FILE" "$ENV_FILE"
  echo "Created ${ENV_FILE} from .env.example. Fill in your Qobuz token before live matching."
fi

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Bandcamp URL Filter Streamlit UI
After=network.target

[Service]
Type=simple
WorkingDirectory=${APP_DIR}
Environment=HOME=${HOME}
Environment=PYTHONPATH=${APP_DIR}
Environment=XDG_CONFIG_HOME=${CONFIG_HOME}
Environment=STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ExecStart=${VENV_DIR}/bin/python -m streamlit run ${APP_DIR}/app.py --server.headless=true --server.address=${BIND_ADDRESS} --server.port=${PORT}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

cat > "$INSTALL_INFO" <<EOF
APP_DIR=${APP_DIR}
ENV_FILE=${ENV_FILE}
PORT=${PORT}
BIND_ADDRESS=${BIND_ADDRESS}
SERVICE_NAME=${SERVICE_NAME}
SERVICE_FILE=${SERVICE_FILE}
VENV_DIR=${VENV_DIR}
EOF

printf '%s\n' "$PORT" > "$PORT_FILE"

echo "Reloading user systemd units..."
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME" >/dev/null

if [[ "$NO_START" -eq 0 ]]; then
  echo "Starting ${SERVICE_NAME}..."
  systemctl --user restart "$SERVICE_NAME"
fi

echo
echo "Setup complete."
echo "Service file: ${SERVICE_FILE}"
echo "Stored install info: ${INSTALL_INFO}"
echo "Port: ${PORT}"
echo
echo "Useful commands:"
echo "  systemctl --user status ${SERVICE_NAME}"
echo "  journalctl --user -u ${SERVICE_NAME} -f"
echo "  systemctl --user restart ${SERVICE_NAME}"
echo
if [[ "$BIND_ADDRESS" == "127.0.0.1" ]]; then
  echo "The app is bound to localhost for safety."
  echo "Open it with an SSH tunnel, for example:"
  echo "  ssh -N -L ${PORT}:127.0.0.1:${PORT} ${USER}@your-box"
else
  echo "Open: http://${BIND_ADDRESS}:${PORT}"
fi
