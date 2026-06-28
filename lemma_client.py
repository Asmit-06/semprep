"""
lemma_client.py
Single connection layer between SEMPREP and Lemma Cloud.

Auth priority:
  1. LEMMA_REFRESH_TOKEN env var → used by Streamlit Cloud (stable, long-lived)
  2. LEMMA_CONFIG_PATH env var   → used locally via WSL/native CLI config

Local dev:  set LEMMA_CONFIG_PATH in .env
Cloud host: set LEMMA_REFRESH_TOKEN in Streamlit Cloud secrets
"""

import os
import json
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from lemma_sdk import Lemma, Pod, LemmaAuthError

load_dotenv()


# ============================================================
# Configuration
# ============================================================
LEMMA_API_URL       = os.getenv("LEMMA_API_URL", "https://api.lemma.work")
LEMMA_POD_ID        = os.getenv("LEMMA_POD_ID")
LEMMA_ORG_ID        = os.getenv("LEMMA_ORG_ID")
LEMMA_CONFIG_PATH   = os.getenv("LEMMA_CONFIG_PATH")
LEMMA_REFRESH_TOKEN = os.getenv("LEMMA_REFRESH_TOKEN")
LEMMA_TIMEOUT       = float(os.getenv("LEMMA_TIMEOUT", "180"))

if not LEMMA_POD_ID:
    raise RuntimeError("LEMMA_POD_ID missing in .env or secrets")
if not LEMMA_ORG_ID:
    raise RuntimeError("LEMMA_ORG_ID missing in .env or secrets")

# Auth mode detection
LEMMA_CONFIG_JSON   = os.getenv("LEMMA_CONFIG_JSON")

_USE_CLOUD_AUTH  = bool(LEMMA_CONFIG_JSON)
_USE_CONFIG_AUTH = bool(LEMMA_CONFIG_PATH)

if not _USE_CLOUD_AUTH and not _USE_CONFIG_AUTH:
    raise RuntimeError(
        "No auth method found.\n"
        "  Local:  set LEMMA_CONFIG_PATH in .env\n"
        "  Cloud:  set LEMMA_CONFIG_JSON in Streamlit secrets"
    )

if _USE_CONFIG_AUTH and not _USE_CLOUD_AUTH:
    CONFIG_PATH = Path(LEMMA_CONFIG_PATH)
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"Lemma config not found at {CONFIG_PATH}")
else:
    CONFIG_PATH = None


# ============================================================
# Client Factories
# ============================================================
def get_client() -> Lemma:
    config_json = os.getenv("LEMMA_CONFIG_JSON")

    if config_json:
        # Cloud mode — write config JSON from env var to temp file
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".json", mode="w", encoding="utf-8"
        )
        tmp.write(config_json)
        tmp.close()
        return Lemma(
            config_path=Path(tmp.name),
            org_id=LEMMA_ORG_ID,
            pod_id=LEMMA_POD_ID,
            timeout=LEMMA_TIMEOUT,
        )
    else:
        # Local mode
        return Lemma(
            config_path=CONFIG_PATH,
            org_id=LEMMA_ORG_ID,
            pod_id=LEMMA_POD_ID,
            timeout=LEMMA_TIMEOUT,
        )

def get_pod() -> Pod:
    """Pod-scoped client. Use for tables, agents, records, workflows."""
    return get_client().pod(LEMMA_POD_ID)


# ============================================================
# Helpers to extract items from SDK responses
# ============================================================
def _items(response):
    """SDK responses wrap data in .items or .data. Handle both."""
    if hasattr(response, "items"):
        return response.items
    if hasattr(response, "data"):
        return response.data
    return list(response)


# ============================================================
# Health Check
# ============================================================
def check_connection() -> dict:
    try:
        pod = get_pod()
        tables = _items(pod.tables.list())
        agents = _items(pod.agents.list())
        return {
            "ok":       True,
            "tables":   len(tables),
            "agents":   len(agents),
            "pod_id":   LEMMA_POD_ID,
            "auth_mode": "refresh_token" if _USE_CLOUD_AUTH else "config_file",
        }
    except LemmaAuthError:
        hint = (
            "Refresh token expired. Run lemma auth login, get new refresh token, "
            "paste into Streamlit secrets."
            if _USE_CLOUD_AUTH else
            "Token expired. Run: lemma auth login"
        )
        return {
            "ok":      False,
            "error":   "TOKEN_EXPIRED",
            "message": hint,
        }
    except Exception as e:
        return {
            "ok":      False,
            "error":   type(e).__name__,
            "message": str(e),
        }


# ============================================================
# Standalone Test
# ============================================================
if __name__ == "__main__":
    auth_mode = "REFRESH TOKEN (cloud)" if _USE_CLOUD_AUTH else "CONFIG FILE (local)"
    print(f"Auth mode: {auth_mode}\n")
    print("Testing Lemma Cloud connection...\n")

    status = check_connection()

    if status["ok"]:
        print(f"Connected to pod: {status['pod_id']}")
        print(f"Auth mode:        {status['auth_mode']}")
        print(f"Tables:           {status['tables']}")
        print(f"Agents:           {status['agents']}")

        pod = get_pod()
        print("\nTable list:")
        for t in _items(pod.tables.list()):
            name = getattr(t, "name", None) or getattr(t, "table_name", str(t))
            print(f"  - {name}")

        print("\nAgent list:")
        for a in _items(pod.agents.list()):
            name = getattr(a, "name", None) or str(a)
            print(f"  - {name}")
    else:
        print(f"Failed: {status['error']}")
        print(status["message"])