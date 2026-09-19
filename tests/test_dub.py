# اختبارات الدبلجة العالمية — الأصوات، الدوران، النصوص الجاهزة، عقد الإنتاج
import inspect

import pytest

from xtrendaw import content, dub, produce


def test_voice_for_english():
    assert dub.voice_for("en").startswith("en-")


def test_voice_for_all_world_langs():
    for lang in dub.DUB_ORDER:
        assert dub.voice_for(lang)


def test_voice_for_unknown_raises():
    with pytest.raises(ValueError):
        dub.voice_for("zz")


def test_voice_for_ar_rejected():
    with pytest.raises(ValueError):
        dub.voice_for("ar")


def test_native_langs_have_ready_scripts():
    assert set(dub.NATIVE_LANGS) == {"ar", "en"}


def test_english_script_ready_for_any_episode():
    t = content.SEED_TOPICS[0]
    segs = content.compose_script(t, "en")
    assert len(segs) == 7
    assert all(s["text"].strip() for s in segs)


def test_rotation_cycles_all_langs():
    seen = [dub.rotate([])]
    for _ in range(len(dub.DUB_ORDER) - 1):
        seen.append(dub.rotate(seen))
    assert set(seen) == set(dub.DUB_ORDER)


def test_translate_topic_without_llm_is_honest():
    t = dict(content.SEED_TOPICS[0])
    if not dub._llm_ok():
        assert dub.translate_topic(t, "es") is None
    else:
        assert dub.translate_topic(t, "es") is not None


def test_dub_topic_english_ready():
    t = dict(content.SEED_TOPICS[0])
    t["id"] = "ep1"
    d = dub.dub_topic_for(t, "en")
    assert d["id"] == "ep1-en"
    assert d["_dub_lang"] == "en"
    assert d["hook_ar"] == t["hook_en"] or d.get("hook_ar")


def test_produce_supports_dub_language():
    sig = inspect.signature(produce.produce_episode)
    assert "narration_lang" in sig.parameters
    assert "narration_voice" in sig.parameters
