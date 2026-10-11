"""فهرس خزنة الميديا. الإضافة بس. مفيش ملف من غير مصدر وترخيص."""
from __future__ import annotations

import json
from pathlib import Path

REQUIRED = ("id", "kind", "source", "license", "commercial", "no_faces", "calm")
KINDS = {"video", "image", "music", "sfx", "font"}


def empty_index() -> dict:
    return {
        "note": "خزنة فاضية وقابلة تكبر. كل ملف يتضاف بمصدره وترخيصه. البيع المنفصل ممنوع.",
        "factory_connected": False,
        "publish": False,
        "items": [],
    }


def load(path: Path) -> dict:
    if not path.exists():
        return empty_index()
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("items", [])
    return data


def validate_item(item: dict) -> None:
    missing = [k for k in REQUIRED if k not in item]
    if missing:
        raise ValueError("الملف ناقصه: " + "، ".join(missing))
    if item["kind"] not in KINDS:
        raise ValueError("نوع الخزنة مش معروف")
    if not item.get("source") or not item.get("license"):
        raise ValueError("من غير مصدر أو ترخيص الملف ما يدخلش")
    if not item.get("commercial"):
        raise ValueError("الرخصة لازم تسمح بالاستخدام على القناة")
    if item["kind"] in ("video", "image") and not item.get("no_faces"):
        raise ValueError("اللقطة لازم تكون من غير وجوه")


def add_item(index: dict, item: dict) -> dict:
    validate_item(item)
    items = index.setdefault("items", [])
    if any(old.get("id") == item["id"] for old in items):
        raise ValueError("الملف متسجل قبل كده. الإضافة مش تكرار.")
    items.append(item)
    return index


def match(index: dict, *, kind: str, palette: str, query: str = "") -> dict | None:
    """يرجّع أول ملف مناسب. لو الخزنة فاضية، None، والمصنع يستخدم كارت لون."""
    words = [w.lower() for w in query.split() if len(w) > 2]
    for item in index.get("items") or []:
        if item.get("kind") != kind or not item.get("calm") or not item.get("no_faces"):
            continue
        if item.get("palette") not in (palette, "", None, "any"):
            continue
        blob = (item.get("query") or "").lower()
        if words and not any(w in blob for w in words):
            continue
        return item
    return None
