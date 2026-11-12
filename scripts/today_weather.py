"""코디 추천용 한국 날씨 요약.

k-skill-proxy(기상청 단기예보·초단기실황 중계 서버)를 호출해서
하루 최저·최고기온, 강수 시간대, 바람, 체감온도, 일교차를 JSON 한 덩어리로 정리한다.
API 키는 필요 없다. 쇼핑몰이나 다른 사이트는 호출하지 않는다.

사용 예:
  python today_weather.py --city 서울
  python today_weather.py --lat 35.1796 --lon 129.0756 --day tomorrow
"""

import argparse
import json
import math
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
BASE = os.environ.get("KSKILL_PROXY_BASE_URL") or "https://k-skill-proxy.nomadamas.org"

CITIES = {
    "서울": (37.5665, 126.9780), "부산": (35.1796, 129.0756), "대구": (35.8714, 128.6014),
    "인천": (37.4563, 126.7052), "광주": (35.1595, 126.8526), "대전": (36.3504, 127.3845),
    "울산": (35.5384, 129.3114), "세종": (36.4800, 127.2890), "수원": (37.2636, 127.0286),
    "성남": (37.4200, 127.1267), "고양": (37.6584, 126.8320), "용인": (37.2411, 127.1776),
    "창원": (35.2280, 128.6811), "청주": (36.6424, 127.4890), "전주": (35.8242, 127.1480),
    "천안": (36.8151, 127.1139), "제주": (33.4996, 126.5312), "서귀포": (33.2541, 126.5600),
    "강릉": (37.7519, 128.8761), "춘천": (37.8813, 127.7298), "포항": (36.0190, 129.3435),
    "여수": (34.7604, 127.6622), "김해": (35.2285, 128.8894), "원주": (37.3422, 127.9202),
}

PTY = {"0": "없음", "1": "비", "2": "비/눈", "3": "눈", "4": "소나기", "5": "빗방울", "6": "빗방울눈날림", "7": "눈날림"}
SKY = {"1": "맑음", "3": "구름많음", "4": "흐림"}


def get(path, params):
    url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "k-weather-coordi"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    header = data.get("response", {}).get("header", {})
    if header.get("resultCode") not in (None, "00"):
        raise RuntimeError(f"{path}: {header}")
    return data["response"]["body"]["items"]["item"]


def wind_chill(t, v_ms):
    """기상청 겨울철 체감온도 식. 10도 이하·풍속 1.3m/s 이상일 때만 의미가 있다."""
    if t is None or v_ms is None or t > 10 or v_ms < 1.3:
        return None
    v = (v_ms * 3.6) ** 0.16
    return round(13.12 + 0.6215 * t - 11.37 * v + 0.3965 * v * t, 1)


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None  # "강수없음", "1mm 미만" 같은 글자 값


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--day", choices=["today", "tomorrow", "dayafter"], default="today",
                    help="today=오늘, tomorrow=내일, dayafter=모레 (단기예보 범위는 모레까지가 안전)")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # 윈도우에서도 한글이 깨지지 않게
    sys.stderr.reconfigure(encoding="utf-8")

    if a.city:
        name = a.city.replace("시", "") if a.city.endswith("시") else a.city
        if name not in CITIES:
            sys.exit(json.dumps({"error": f"모르는 도시: {a.city}. --lat/--lon 으로 넣어주세요.", "known": list(CITIES)}, ensure_ascii=False))
        lat, lon = CITIES[name]
    elif a.lat is not None and a.lon is not None:
        lat, lon, name = a.lat, a.lon, None
    else:
        (lat, lon), name = CITIES["서울"], "서울(기본값)"

    now = datetime.now(KST)
    offset = {"today": 0, "tomorrow": 1, "dayafter": 2}[a.day]
    target = (now + timedelta(days=offset)).strftime("%Y%m%d")

    # 02시 발표 단기예보에는 오늘 하루 전체(최저·최고기온 포함)가 들어 있다.
    # 02:15 전이면 아직 안 나왔으므로 전날 23시 발표를 쓴다.
    if a.day == "today":
        if now.hour > 2 or (now.hour == 2 and now.minute >= 15):
            base = {"baseDate": now.strftime("%Y%m%d"), "baseTime": "0200"}
        else:
            base = {"baseDate": (now - timedelta(days=1)).strftime("%Y%m%d"), "baseTime": "2300"}
    else:
        base = {}  # 내일은 가장 최신 발표를 쓴다

    td = now + timedelta(days=offset)
    weekday = "월화수목금토일"[td.weekday()]
    out = {"location": name or f"{lat},{lon}", "lat": lat, "lon": lon, "day": a.day,
           "date": f"{td.month}월 {td.day}일 ({weekday})",
           "queried_at": now.strftime("%Y-%m-%d %H:%M KST"), "failures": []}

    try:
        items = get("/v1/korea-weather/forecast", {"lat": lat, "lon": lon, **base})
        day = [i for i in items if i.get("fcstDate") == target]
        if items:
            bd, bt = items[0]["baseDate"], items[0]["baseTime"]
            out["forecast_base"] = f"{int(bd[4:6])}월 {int(bd[6:8])}일 {int(bt[:2])}시 발표"
        by = {}
        for i in day:
            by.setdefault(i["category"], []).append((i["fcstTime"], i["fcstValue"]))
        tmp = [(t, num(v)) for t, v in by.get("TMP", []) if num(v) is not None]
        tmn = next((num(v) for _, v in by.get("TMN", [])), None)
        tmx = next((num(v) for _, v in by.get("TMX", [])), None)
        lo = tmn if tmn is not None else (min(v for _, v in tmp) if tmp else None)
        hi = tmx if tmx is not None else (max(v for _, v in tmp) if tmp else None)
        pop = [(t, int(v)) for t, v in by.get("POP", [])]
        rain_hours = [t[:2] + "시" for t, v in by.get("PTY", []) if v != "0"]
        pcp = {t[:2]: v for t, v in by.get("PCP", []) if v not in ("강수없음", "0")}
        wsd_by = {t: num(v) for t, v in by.get("WSD", []) if num(v) is not None}
        wsd = list(wsd_by.values())
        reh = [num(v) for _, v in by.get("REH", []) if num(v) is not None]
        sky_by = {t: SKY.get(v, v) for t, v in by.get("SKY", [])}
        ptys = sorted({PTY.get(v, v) for _, v in by.get("PTY", []) if v != "0"})

        def at(hh):
            return next((v for t, v in tmp if t == hh), None)

        def sky_mode(hours):
            s = [sky_by[h] for h in hours if h in sky_by]
            return max(set(s), key=s.count) if s else None

        out["temp"] = {"min": lo, "max": hi, "daily_range": round(hi - lo, 1) if lo is not None and hi is not None else None,
                       "morning_08": at("0800"), "afternoon_14": at("1400"), "evening_19": at("1900"),
                       "hourly": {t[:2]: v for t, v in tmp}}
        out["rain"] = {"max_pop_percent": max((v for _, v in pop), default=None),
                       "types": ptys,
                       "hours": rain_hours,  # 실제 비·눈이 예보된 시각(강수형태가 '없음'이 아닌 시각)
                       "amount_by_hour": pcp,  # 1시간 강수량. 예: "1mm 미만", "3.0mm"
                       "pop_hourly": {t[:2]: v for t, v in pop}}  # 시각별 강수확률(%)
        out["wind_max_ms"] = max(wsd) if wsd else None
        out["humidity_avg"] = round(sum(reh) / len(reh)) if reh else None
        out["sky"] = {"morning_06_11": sky_mode([f"{h:02d}00" for h in range(6, 12)]),
                      "afternoon_12_17": sky_mode([f"{h:02d}00" for h in range(12, 18)]),
                      "evening_18_23": sky_mode([f"{h:02d}00" for h in range(18, 24)])}
        # 체감온도는 10도 이하이면서 바람이 1.3m/s 이상일 때만 계산된다. null이면 기온과 거의 같다는 뜻.
        out["feels_like_morning"] = wind_chill(at("0800"), wsd_by.get("0800"))
        out["feels_like_evening"] = wind_chill(at("1900"), wsd_by.get("1900"))
        if not tmp:
            out["failures"].append("해당 날짜 예보 시간대가 비어 있음")
    except Exception as e:  # 한 곳이 실패해도 나머지는 돌려준다
        out["failures"].append(f"forecast: {e}")

    if a.day == "today":
        try:
            obs = {i["category"]: i["obsrValue"] for i in get("/v1/korea-weather/now", {"lat": lat, "lon": lon})}
            t, w = num(obs.get("T1H")), num(obs.get("WSD"))
            out["now"] = {"temp": t, "rain_1h_mm": num(obs.get("RN1")), "precip": PTY.get(obs.get("PTY"), obs.get("PTY")),
                          "wind_ms": w, "humidity": num(obs.get("REH")), "feels_like": wind_chill(t, w)}
        except Exception as e:
            out["failures"].append(f"now: {e}")

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
