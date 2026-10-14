"""🎬 الاستوديو الاحترافي — طبقة ترقية كاملة فوق مصنع نور.

مكوّنات:
    hooks      محرّك الهوك (أول ٣ ثواني)
    music_pro  محرّك الموسيقى بالمقامات العربية + ducking حقيقي
    effects    محرّك المؤثرات السينمائية
    covers     محرّك الأغلفة عالية النقر
    metadata   محرّك العنوان/الوصف/الوسوم (SEO)
    integrate  اللي بيربطهم بالمصنع

الاستخدام:
    from xtrendaw.pro import integrate
    integrate.activate()
"""
from . import covers, effects, hooks, integrate, metadata, music_pro

__all__ = ["hooks", "music_pro", "effects", "covers", "metadata", "integrate"]
