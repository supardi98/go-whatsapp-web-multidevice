#!/bin/sh
set -e

# Bind mounts are often root-owned on the host; the app runs as gowauser and SQLite
# needs write access (DB + WAL). Fix ownership at start (requires container root).
for d in /app/storages /app/storages/ui /app/statics /app/statics/qrcode /app/statics/senditems /app/statics/media; do
	[ -d "$d" ] || mkdir -p "$d"
	chown -R gowauser:gowa "$d" 2>/dev/null || true
done

# If an embedded/built UI index.html exists in /app/ui-dist, update /app/storages/ui/index.html
if [ -f /app/ui-dist/index.html ]; then
	cp -f /app/ui-dist/index.html /app/storages/ui/index.html
	chown gowauser:gowa /app/storages/ui/index.html 2>/dev/null || true
fi

exec su-exec gowauser /app/whatsapp "$@"
