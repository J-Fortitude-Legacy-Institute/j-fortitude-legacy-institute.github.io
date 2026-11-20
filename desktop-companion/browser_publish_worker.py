"""Isolated browser publisher worker.

Runs Playwright sync publishers in a fresh Python process so they cannot inherit
any asyncio loop owned by the long-running companion process.
"""

from __future__ import annotations

import importlib
import json
import sys
import threading
import traceback
from pathlib import Path
from queue import Queue


def _call_in_clean_thread(fn, kwargs: dict) -> dict:
    """Run the publisher on a brand-new thread.

    Playwright's sync API refuses to run on any thread where an asyncio loop is
    active. Some launch environments can attach loop state even to this worker's
    main thread, so the actual browser automation runs on a fresh thread and
    returns a structured envelope instead of bubbling an exception.
    """
    q: Queue[dict] = Queue(maxsize=1)

    def _target() -> None:
        try:
            result = fn(**kwargs)
            if not isinstance(result, dict):
                result = {"ok": False, "error": "publisher_returned_non_object", "detail": repr(result)}
            q.put(result)
        except Exception as exc:
            q.put({
                "ok": False,
                "error": "browser_worker_publisher_exception",
                "detail": str(exc),
                "trace": traceback.format_exc(limit=8),
            })

    thread = threading.Thread(target=_target, name="unk-browser-publisher", daemon=False)
    thread.start()
    thread.join()
    return q.get() if not q.empty() else {"ok": False, "error": "browser_worker_thread_no_result"}


def main() -> int:
    try:
        # Make sibling publisher modules importable no matter where Python was
        # launched from by the supervisor.
        script_dir = Path(__file__).resolve().parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))

        payload = json.loads(sys.stdin.read() or "{}")
        module_name = str(payload.get("module") or "")
        function_name = str(payload.get("function") or "")
        kwargs = payload.get("kwargs") if isinstance(payload.get("kwargs"), dict) else {}
        if not module_name or not function_name:
            raise ValueError("missing_module_or_function")

        module = importlib.import_module(module_name)
        fn = getattr(module, function_name)
        result = _call_in_clean_thread(fn, kwargs)
        print(json.dumps(result, default=str), flush=True)
        return 0 if result.get("ok") else 2
    except Exception as exc:
        print(json.dumps({
            "ok": False,
            "error": "browser_worker_exception",
            "detail": str(exc),
            "trace": traceback.format_exc(limit=8),
        }), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())