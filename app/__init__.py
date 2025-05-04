"""app package initialization

* Loads environment variables from a `.env` file at project root (if it exists).
* Exposes a `ROOT_DIR` constant pointing at the repo root.
* Defines `__version__` for easy introspection.
"""

import os
from pathlib import Path
import logging
import shutil, sys

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# ─ Paths & env ─────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"

if load_dotenv is not None and ENV_FILE.exists():
    load_dotenv(ENV_FILE)
    logging.getLogger("uvicorn.error").info("Loaded environment from %s", ENV_FILE)
else:
    logging.getLogger("uvicorn.error").debug(".env file not found or python-dotenv missing")

# ─ Metadata ───────────────────────────────────────────────────────
__version__ = "0.1.0"
__all__ = ["ROOT_DIR", "__version__"]


# ──────────────────────────────────────────────────────────────
# Paths & env
# ──────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"

if load_dotenv is not None and ENV_FILE.exists():
    load_dotenv(ENV_FILE)  # noqa: S603 – safe: user‑controlled repo
    logging.getLogger("uvicorn.error").info("Loaded environment from %s", ENV_FILE)
else:
    logging.getLogger("uvicorn.error").debug(".env file not found or python-dotenv missing")

# ──────────────────────────────────────────────────────────────
# Metadata
# ──────────────────────────────────────────────────────────────
__version__ = "0.1.0"  # remember to bump when releasing

__all__ = [
    "ROOT_DIR",
    "__version__",
]

