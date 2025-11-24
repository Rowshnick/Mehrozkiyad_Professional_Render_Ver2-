import swisseph as swe
from datetime import datetime

def get_horoscope(birth_date: datetime) -> str:
    """
    تولید متن هوروسکوپ بر اساس موقعیت سیارات
    """

    jd = swe.julday(
        birth_date.year,
        birth_date.month,
        birth_date.day
    )

    planets = {
        "خورشید": swe.SUN,
        "ماه": swe.MOON,
        "عطارد": swe.MERCURY,
        "ناهید": swe.VENUS,
        "مریخ": swe.MARS,
        "مشتری": swe.JUPITER,
        "زحل": swe.SATURN,
        "اورانوس": swe.URANUS,
        "نپتون": swe.NEPTUNE,
        "پلوتو": swe.PLUTO
    }

    text = "🔮 **تحلیل ستاره‌شناسی روز تولد شما**\n\n"

    for name, code in planets.items():
        lon, lat, dist = swe.calc(jd, code)[:3]
        text += f"{name}: طول = {lon:.2f}°  | عرض = {lat:.2f}°\n"

    text += "\n✨ **توصیه کلی:**\n" \
            "امروز انرژی‌های مثبتی پیرامون شما جریان دارد. به احساسات درونی خود توجه کنید و تصمیم‌های مهم را با آرامش بگیرید."

    return text
