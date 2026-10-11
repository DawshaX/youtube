"""يختار حلقة لم تتنشر، يرندرها بلقطات حية، وينشرها من نفس حارس الكوتة."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EPISODES = ROOT / "data" / "noor_next" / "episodes.jsonl"
LEDGER = ROOT / "state" / "noor_library.json"

from .produce import render
from .timeline import sacred_text


def _load() -> dict:
    if not LEDGER.exists():
        return {"served": []}
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _episodes() -> list[dict]:
    if not EPISODES.exists():
        return []
    rows = []
    for line in EPISODES.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def next_episode(form: str = "short") -> dict | None:
    done = set(_load().get("served") or [])
    last_series = str(_load().get("last_series") or "")
    pool = []
    for ep in _episodes():
        if ep.get("id") in done or ep.get("factory"):
            continue
        if sacred_text(ep.get("spoken") or ""):
            continue
        if form == "long" and ep.get("kind") != "long":
            continue
        if form != "long" and ep.get("kind") == "long":
            continue
        pool.append(ep)
    if not pool:
        return None
    fresh = [ep for ep in pool if ep.get("series_id") != last_series]
    return (fresh or pool)[0]


def _runner():
    import importlib.util
    import sys
    name = "noor_runner_live"
    if name in sys.modules:
        return sys.modules[name]
    path = ROOT / "scripts" / "noor_runner.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def publish_next(form: str = "short") -> int:
    """0 ات نشر أو اتخزن. 1 الرندر وقع فنرجع للمسار القديم. 2 الكوتة أو المسافة قفلت."""
    runner = _runner()

    tried = 0
    while tried < 3:
        ep = next_episode(form)
        if not ep:
            print("[library] المخزون خلص أو مش موجود", flush=True)
            return 1
        tried += 1
        work = runner.WORK / f"lib_{ep['id']}"
        made = render(ep, work)
        if not made:
            st = _load()
            st.setdefault("skipped", []).append(ep["id"])
            st["served"] = list(dict.fromkeys([*(st.get("served") or []), ep["id"]]))
            _save(st)
            continue
        title = f"{made['lines'][0][:70]} | {ep.get('series_title') or 'نور'}"
        credits = "\n".join(made["credits"]) or "لقطات مرخّصة من مكتبات حرة."
        desc = (
            f"{ep.get('spoken') or ''}\n\n"
            f"{ep.get('benefit') or ''}\n\n"
            f"المصادر:\n{credits}\n\n"
            "من غير وجوه. النص المقدس من مصدره، ومش متألف هنا."
        )
        tags = ["نور", ep.get("series_title") or "خير", "shorts" if form != "long" else "فيديو"]
        url, err = runner._publish(made["video"], None, title[:95], desc, tags, synthetic=True)
        if err in ("quota_guard", "too_soon"):
            print(f"[library] النشر استنى: {err}", flush=True)
            return 2
        vault_url = ""
        if not url and not runner.DRY:
            vault_url = runner._vault(
                made["video"], None,
                {"kind": "library", "title": title, "tags": ",".join(tags),
                 "caption": desc, "live_clips": 1, "synthetic": True},
            )
        st = _load()
        st["served"] = list(dict.fromkeys([*(st.get("served") or []), ep["id"]]))
        st["last_series"] = ep.get("series_id") or ""
        st.setdefault("done", []).append({
            "id": ep["id"], "title": title, "url": url or "", "vault": vault_url, "err": err,
        })
        _save(st)
        print(f"[library] {'اتنشر' if url else 'اتخزن'} {ep['id']} {url or vault_url}", flush=True)
        return 0 if (url or vault_url or runner.DRY) else 1
    return 1
