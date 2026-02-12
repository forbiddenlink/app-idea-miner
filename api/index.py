import os
import sys

# Add the project root to the python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    from apps.api.app.main import app
except Exception as e:
    import traceback

    print(f"Failed to import app: {e}", file=sys.stderr)
    traceback.print_exc()
    raise
