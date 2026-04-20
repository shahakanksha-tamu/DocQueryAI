from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any, Dict, List

# On-disk PDF copies for preview (project/.pdf_cache).
_CACHE_ROOT = Path(__file__).resolve().parent.parent / ".pdf_cache"


def cache_root() -> Path:
    _CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    return _CACHE_ROOT


def batch_dir(batch_id: str) -> Path:
    d = cache_root() / str(batch_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def is_valid_cache_filename(name: str) -> bool:
    """True if name looks like our cached file (no path tricks)."""
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
    """Write uploads under .pdf_cache/<batch_id>/; return name/size/cache_file per file."""
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
    """Delete the entire .pdf_cache directory."""
    root = cache_root()
    if root.is_dir():
        shutil.rmtree(root, ignore_errors=True)

