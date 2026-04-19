#!/usr/bin/env sh
set -eu

mkdir -p /app/exports /config/streamrip /downloads

if [ ! -e "$HOME/Music" ]; then
  ln -s /downloads "$HOME/Music"
fi

exec "$@"
