"""
Axio Bootstrap Utilities (Updated)
----------------------------------

Paste this cell into a fresh ChatGPT Python environment after uploading
your latest `search-index.json`.

Provides:
- Navigation & browsing over the Axio corpus
- TUI-like viewer
- Search and analysis helpers
- Sequence and Index generators
- Consolidated help() menu

This version fixes `list_posts()` so the output is always visible.
"""

import json
import math
import re
from pathlib import Path
from typing import List, Dict, Optional

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

AXIO_INDEX_PATH = Path("/mnt/data/search-index.json")

# Global cache of the corpus and pagination state
_AXIO_DATA: Optional[List[Dict]] = None
_PAGINATION = {
    "page": 1,        # 1-based current page
    "page_size": 20,  # posts per page
}

# ---------------------------------------------------------------------
# Internal loading
# ---------------------------------------------------------------------

def _load_axio_data() -> List[Dict]:
    global _AXIO_DATA
    if _AXIO_DATA is None:
        if not AXIO_INDEX_PATH.exists():
            raise FileNotFoundError(
                f"Axio index not found at {AXIO_INDEX_PATH}. "
                f"Upload `search-index.json` and/or adjust AXIO_INDEX_PATH."
            )
        with AXIO_INDEX_PATH.open("r", encoding="utf-8") as f:
            _AXIO_DATA = json.load(f)
    return _AXIO_DATA

# Initialize corpus and total count
_AXIO_DATA = _load_axio_data()
TOTAL_POSTS = len(_AXIO_DATA)

# ---------------------------------------------------------------------
# FIXED: Core browsing — list_posts
# ---------------------------------------------------------------------

def list_posts(
