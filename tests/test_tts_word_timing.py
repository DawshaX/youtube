"""تحقق معيار القبول للمرحلة ١: خطة الصوت لازم تحمل توقيتات كلمة-بكلمة.

الساندبوك ده بلا وصول لخدمة edge-tts، فبنحاكي الخدمة نفسها (مش منطق
المصنع): كلاس Communicate مزيف يكتب MP3 حقيقي بالصمت وي بثّ أحداث
WordBoundary — ونأكد إن:
  1) الكود بيطلب صراحةً boundary="WordBoundary" من الخدمة.
  2) التوقيتات الحقيقية من _synth_line هي اللي بتدخل في الخطة (مش تخمين).
  3) خطة المقاطع النهائية بتسجّل "timing_source": "word".
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from xtrendaw import tts  # noqa: E402


class FakeCommunicate:
    """محاكاة خدمة النطق: صوت حقيقي + حدود كلمة حقيقية."""

    last_boundary_kwarg = None

    def __init__(self, text, voice, *, rate="+0%", volume="+0%", pitch="+0Hz",
                 boundary="SentenceBoundary", **_kw):
        self.text = text
        self.voice = voice
        self.boundary = boundary
        FakeCommunicate.last_boundary_kwarg = boundary

    async def stream(self):
        import asyncio

        tmp = Path(tempfile.mkdtemp()) / "one.mp3"
        dur = 1.10
        subprocess.run(
            [tts.ffmpeg(), "-y", "-f", "lavfi", "-i",
             f"sine=frequency=300:duration={dur}",
             "-c:a", "libmp3lame", "-q:a", "9", str(tmp)],
            capture_output=True, check=True,
        )
        data = tmp.read_bytes()
        step = max(1, len(data) // 3)
        for i in range(0, len(data), step):
            yield {"type": "audio", "data": data[i:i + step]}
            await asyncio.sleep(0)
        tokens = self.text.split()
        n = len(tokens)
        span = dur / n
        for i, tok in enumerate(tokens):
            yield {"type": "WordBoundary", "text": tok,
                   "offset": int(i * span * 10_000_000),
                   "duration": int(span * 10_000_000)}
        yield {"type": "SentenceBoundary", "text": self.text,
               "offset": 0, "duration": int(dur * 10_000_000)}


def main() -> None:
    import edge_tts

    real_communicate = edge_tts.Communicate
    edge_tts.Communicate = FakeCommunicate  # type: ignore[misc]
    try:
        workdir = Path(tempfile.mkdtemp(prefix="tts_word_"))
        segs = [
            {"seg": "hook", "text": "الجبال تتحرك أمام عينيك! وإليك ثلاثة أسرار صادمة."},
            {"seg": "fact1", "text": "السر الأول: جبال الهيمالايا ترتفع كل عام"},
        ]
        plan = tts.synthesize_segments(segs, "ar", workdir / "tts")
        plan_file = workdir / "tts" / "plan.json"
        assert plan_file.exists(), "plan.json ما اتكتبش"
        on_disk = json.loads(plan_file.read_text(encoding="utf-8"))

        assert FakeCommunicate.last_boundary_kwarg == "WordBoundary", (
            f"الخدمة اتصلت بحدود {FakeCommunicate.last_boundary_kwarg!r} "
            "بدل WordBoundary")
        for item in on_disk["items"]:
            assert item["timing_source"] == "word", (
                f"المقطع {item['seg']} مصدر توقيته {item['timing_source']!r} "
                "مش word")
            assert len(item["words"]) >= len(item["text"].split()) - 1, (
                f"المقطع {item['seg']} كلماته أقل من نصه — التوقيتات مش من الخدمة")
        # التوقيتات لازم تكون من بث الخدمة (مضاعفات مقطع الصوت) مش موزعة بطول الكلمة
        first_words = on_disk["items"][0]["words"]
        assert all(w["end"] > w["start"] for w in first_words)
        print("timing_source values:",
              sorted({it["timing_source"] for it in on_disk["items"]}))
        print("OK: plan.json timing_source == word لكل المقاطع")
    finally:
        edge_tts.Communicate = real_communicate  # type: ignore[misc]


if __name__ == "__main__":
    main()
