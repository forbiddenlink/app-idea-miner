import json
import os
import sys
import traceback

# Add the project root to the python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

error_info = None

# Try to import the app
try:
    from apps.api.app.main import app
except Exception as e:
    error_info = {
        "error": str(e),
        "traceback": traceback.format_exc(),
        "type": type(e).__name__,
    }

    # Try creating a minimal FastAPI app
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse

        app = FastAPI()

        @app.get("/")
        @app.get("/health")
        @app.get("/{path:path}")
        async def diagnostic(path: str = ""):
            return JSONResponse(
                status_code=500,
                content={
                    "status": "import_error",
                    "error": error_info["error"],
                    "traceback": error_info["traceback"].split("\n"),
                    "env": {
                        "DATABASE_URL": "set"
                        if os.getenv("DATABASE_URL")
                        else "not set",
                        "VERCEL": os.getenv("VERCEL", "not set"),
                    },
                },
            )

    except Exception as e2:
        # Even FastAPI failed - create raw ASGI app
        error_info["fastapi_error"] = str(e2)
        error_info["fastapi_traceback"] = traceback.format_exc()

        async def app(scope, receive, send):
            if scope["type"] == "http":
                await send(
                    {
                        "type": "http.response.start",
                        "status": 500,
                        "headers": [[b"content-type", b"application/json"]],
                    }
                )
                body = json.dumps(error_info, indent=2).encode()
                await send({"type": "http.response.body", "body": body})
