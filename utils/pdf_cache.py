from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any, Dict, List

# Session-scoped preview cache (stored on disk in project workspace).
_CACHE_ROOT = Path(__file__).resolve().parent.parent / ".pdf_cache"


def cache_root() -> Path:
    _CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    return _CACHE_ROOT


def batch_dir(batch_id: str) -> Path:
    d = cache_root() / str(batch_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def is_valid_cache_filename(name: str) -> bool:
    """
    Reject path traversal and unexpected names; must match files written by save_uploaded_pdfs_for_batch.
    """
    if not name or len(name) > 200:
        return False
    if any(bad in name for bad in ("/", "\\", "..")):
        return False
    return bool(re.fullmatch(r"\d+_[A-Za-z0-9._-]+\.pdf", name, re.IGNORECASE))


def _safe_filename(name: str, max_len: int = 110) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("._")
    safe = safe[:max_len] if len(safe) > max_len else safe
    return safe or "document.pdf"


def save_uploaded_pdfs_for_batch(uploaded_files, batch_id: str) -> List[Dict[str, Any]]:
    """
    Save each uploaded PDF to disk and return lightweight metadata for chat sidebar.
    """
    out: List[Dict[str, Any]] = []
    dest_dir = batch_dir(batch_id)

    for i, f in enumerate(uploaded_files):
        raw = f.getvalue()
        original_name = getattr(f, "name", None) or "document.pdf"

        original_base = Path(original_name).name
        safe = _safe_filename(original_base)
        if not safe.lower().endswith(".pdf"):
            safe += ".pdf"

        cache_file = f"{i}_{safe}"
        dest_path = dest_dir / cache_file
        dest_path.write_bytes(raw)

        out.append(
            {
                "name": original_name,
                "size_bytes": len(raw),
                "cache_file": cache_file,
            }
        )

    return out


def remove_batch_cache(batch_id: str | None) -> None:
    if not batch_id:
        return
    d = cache_root() / str(batch_id)
    if d.is_dir():
        shutil.rmtree(d, ignore_errors=True)


def remove_all_cache() -> None:
    """
    Remove all cached preview PDFs across batches.

    Use this for strict privacy cleanup flows (e.g. explicit reset/new upload).
    """
    root = cache_root()
    if root.is_dir():
        shutil.rmtree(root, ignore_errors=True)

