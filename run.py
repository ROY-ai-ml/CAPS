"""Root Entrypoint to launch the ReRun Backend Server."""
import argparse
import os
import sys
from pathlib import Path

# Add backend directory to Python sys.path
root_dir = Path(__file__).resolve().parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Ensure working directory is workspace root
os.chdir(root_dir)

if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings
    from app.core.logging import logger

    parser = argparse.ArgumentParser(description="ReRun Backend Application Server")
    parser.add_argument("--host", type=str, default=settings.HOST, help="Host interface to bind")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Port to bind")
    parser.add_argument("--reload", action="store_true", default=settings.DEBUG, help="Enable hot reload")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print(f"  Starting ReRun Backend Server ({settings.APP_NAME})")
    print(f"  Interface: http://{args.host}:{args.port}")
    print(f"  LLM Provider: {settings.LLM_PROVIDER} (model: {settings.LLM_MODEL})")
    print(f"  Database: {settings.DATABASE_URL.split('///')[-1] if 'sqlite' in settings.DATABASE_URL else 'PostgreSQL'}")
    print("=" * 70 + "\n")

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
