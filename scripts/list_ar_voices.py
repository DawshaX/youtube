#!/usr/bin/env python3
"""طباعة قائمة أصوات edge-tts العربية مرتبة (الأمر الرسمي للمرحلة ٢).

يحتاج اتصال بـ speech.platform.bing.com (خدمة مايكروسوفت) — شغّله من أي
ماكينة بإنترنت مفتوح أو من GitHub Actions. لو نجح، بيتخزن نسخة في
state/ar_voices.txt للمراجعة من غير إعادة الاتصال.
"""
import asyncio
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parent.parent


async def main() -> None:
    voices = await edge_tts.list_voices()
    names = sorted(v["ShortName"] for v in voices
                   if v["Locale"].startswith("ar"))
    out = "\n".join(names)
    print(out)
    state = ROOT / "state"
    state.mkdir(parents=True, exist_ok=True)
    (state / "ar_voices.txt").write_text(out + "\n", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
