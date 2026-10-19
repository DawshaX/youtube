"""الساوندسكيب: توليد أجواء بلا شبكة/حقوق + اختيار ذكي من المحتوى."""
from pathlib import Path

from xtrendaw import soundscape


def test_ambience_generates(tmp_path: Path):
    for kind in ("rain", "night", "birds", "fire", "ocean", "wind"):
        p = soundscape.ambience_wav(kind, 4.0, "seed-x", tmp_path)
        assert p is not None and p.exists() and p.stat().st_size > 50_000, kind


def test_seed_varies_but_deterministic(tmp_path: Path):
    import hashlib
    # نفس البذرة = نفس الصوت (رندر معاد لازم يطلع نفسه)
    # نقرأ البايتات فور التوليد — كل ملف اسمه amb_rain.wav جوه فولدره
    a = soundscape.ambience_wav("rain", 3.0, "same", tmp_path / "a").read_bytes()
    b = soundscape.ambience_wav("rain", 3.0, "same", tmp_path / "b").read_bytes()
    assert hashlib.sha256(a).digest() == hashlib.sha256(b).digest()
    # بذرة مختلفة = بصمة مختلفة (شرط «كل فيديو غير التاني»)
    c = soundscape.ambience_wav("rain", 3.0, "other", tmp_path / "c").read_bytes()
    assert hashlib.sha256(a).digest() != hashlib.sha256(c).digest()


def test_keyword_pick():
    assert soundscape.pick_ambience({"title": "قصة يونس والحوت"}) == "ocean"
    assert soundscape.pick_ambience({"title": "عذاب النار"}) == "fire"
    assert soundscape.pick_ambience({"kind": "quran"}) == "rain"
    assert soundscape.pick_ambience({"kind": "مجهول", "id": "z1"}) \
        in soundscape.GENERATORS


def test_levels_and_sfx(tmp_path: Path):
    assert soundscape.level_for({"kind": "quran"}) < soundscape.level_for({"kind": "facts"})
    assert soundscape.sfx_wav("whoosh", "s", tmp_path) is not None
    assert soundscape.sfx_wav("chime", "s", tmp_path) is not None
    assert soundscape.ambience_wav("مش-موجود", 5.0, "s", tmp_path) is None
    assert soundscape.ambience_wav("rain", 1.0, "s", tmp_path) is None  # قصير جدًا ⇒ None
