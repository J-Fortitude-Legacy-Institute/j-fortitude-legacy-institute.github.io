#!/usr/bin/env bash
# =====================================================================
# launch_unk.sh — POSIX supervisor for the Unk Desktop Companion.
# Doctrine: stay alive. Restart on any crash, exponential backoff.
# Usage: ./launch_unk.sh   (Ctrl+C to stop)
# Autostart on macOS: use launchd; on Linux: systemd --user unit.
# =====================================================================
set -u
cd "$(dirname "$0")"

BACKOFF=3
MAX_BACKOFF=30
LOG="unk_supervisor.log"

echo "" >> "$LOG"
echo "[$(date -Iseconds)] Supervisor starting." >> "$LOG"
echo "Unk supervisor starting. Restart log: $LOG"
echo "Press Ctrl+C to stop."

trap 'echo "[$(date -Iseconds)] Supervisor stopped by signal." >> "$LOG"; exit 0' INT TERM

while true; do
  START=$(date +%s)
  echo "[$(date -Iseconds)] Launching unk_companion.py" >> "$LOG"
  python3 unk_companion.py
  CODE=$?
  END=$(date +%s)
  RUNTIME=$((END - START))
  echo "[$(date -Iseconds)] Exit=$CODE runtime=${RUNTIME}s backoff=${BACKOFF}s" >> "$LOG"
  echo "=== Companion exited (code $CODE, ran ${RUNTIME}s). Restarting in ${BACKOFF}s ==="

  # If the last run stayed up more than 10 minutes it was healthy; reset backoff.
  if [ "$RUNTIME" -gt 600 ]; then
    BACKOFF=3
  else
    BACKOFF=$((BACKOFF * 2))
    [ "$BACKOFF" -gt "$MAX_BACKOFF" ] && BACKOFF=$MAX_BACKOFF
  fi

  sleep "$BACKOFF"
done
