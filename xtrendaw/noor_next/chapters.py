"""⏱️ فهرس الجلسة (chapters) — للفيديو الطويل بس.

ليه ده موجود؟
    الفيديو الطويل (١٠–٢٠ دقيقة) هو المحرّك الحقيقي لوقت المشاهدة والمشتركين.
    والفهرس بيفرق فعلًا:
      • المشاهد بيقفز للجزء اللي يهمه بدل ما يمشي ⇒ **احتفاظ أعلى**
      • يوتيوب بيعرض الفصول في الوصف وفي نتائج البحث ⇒ **نقرات أعلى**
      • بيدّي إشارة للخوارزمية إن الفيديو منظّم ومقسّم لمواضيع

    وقواعد يوتيوب للفصول صريحة: أول فصل **00:00**، و**٣ فصول على الأقل**،
    وكل فصل **١٠ ثواني على الأقل**، والعنوان نص مش رقم.

قاعدة الأمانة (مهمة):
    مفيش فصول ملفّقة. الفصول بتتولّد من **حدود النص الحقيقية** اللي مصنع
    الطويل سجّلها وهو بيبني الحلقة (`chapters_hint`)، والوقت بيتحسب من
    **المدة المقيسة الحقيقية** للصوت — مش من تخمين سرعة كلام.
"""
from __future__ import annotations

import re

MIN_CHAPTERS = 3        # شرط يوتيوب
MIN_GAP_SEC = 25.0      # مباعدة مريحة (يوتيوب بيطلب ١٠)
TAIL_GUARD_SEC = 12.0   # مفيش فصل قبل آخر ١٢ ثانية
LIMIT = 9               # سقف العرض في القائمة الجانبية


def _stamp(sec: float) -> str:
    total = max(0, int(sec))
    return f"{total // 60:02d}:{total % 60:02d}"


def _label(text: str) -> str:
    t = re.sub(r"\s+", " ", str(text or "")).strip(" ·-—:.،")
    if len(t) > 26:
        t = t[:26].rsplit(" ", 1)[0].rstrip(" ·-—:.،")
    return t


def chapter_lines(hint, words, duration, *, first: str = "البداية",
                  min_gap: float = MIN_GAP_SEC, limit: int = LIMIT,
                  tail_guard: float = TAIL_GUARD_SEC) -> list[str]:
    """يرجّع سطور الفهرس جاهزة للوصف (أو [] لو مش كفاية/مش موثوق).

    hint: [{"at_word": int, "label": str}, ...] — من مصنع الطويل.
    words: عدد كلمات النص المنطوق · duration: المدة المقيسة بالثواني.
    """
    try:
        words = int(words or 0)
        duration = float(duration or 0)
    except Exception:
        return []
    if words <= 0 or duration <= 0:
        return []

    marks: list[tuple[int, str]] = []
    for h in list(hint or []):
        if isinstance(h, dict):
            at, raw = h.get("at_word"), h.get("label")
        elif isinstance(h, (list, tuple)) and len(h) >= 2:
            at, raw = h[0], h[1]
        else:
            continue
        try:
            at = int(at)
        except Exception:
            continue
        lab = _label(raw)
        if at < 0 or not lab:
            continue
        marks.append((at, lab))
    marks.sort(key=lambda x: x[0])

    rows: list[tuple[float, str]] = [(0.0, _label(first) or "البداية")]
    for at, lab in marks:
        t = at / float(words) * duration
        if t < rows[-1][0] + float(min_gap):
            continue
        if t > duration - float(tail_guard):
            continue
        if lab == rows[-1][1]:
            continue
        rows.append((t, lab))

    if len(rows) < MIN_CHAPTERS:
        return []
    if len(rows) > limit:
        step = (len(rows) - 1) / float(max(1, limit - 1))
        keep = {0} | {int(round(i * step)) for i in range(1, limit)}
        rows = [r for i, r in enumerate(rows) if i in keep][:limit]
    return [f"{_stamp(t)} {lab}" for t, lab in rows]


def block(hint, words, duration, *, title: str = "⏱️ فهرس الجلسة:",
          first: str = "البداية") -> str:
    """نص الفهرس جاهز للزق في الوصف (سطور يوتيوب)، أو "" لو مفيش."""
    lines = chapter_lines(hint, words, duration, first=first)
    if not lines:
        return ""
    return title + "\n" + "\n".join(lines)
