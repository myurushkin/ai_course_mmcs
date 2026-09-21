"""Собирает poi.sqlite из снапшота OpenStreetMap по Ростову-на-Дону.

Данные настоящие и потому грязные: у части объектов нет названия, часов работы
или адреса. Это не баг набора, а его смысл — агент должен отличать «нет данных»
от «не подходит».

    python make_poi_dataset.py                      # из data/rostov_poi.json
    python make_poi_dataset.py --refresh            # заново выкачать из OSM

Источник: OpenStreetMap, лицензия ODbL. Снапшот лежит в репозитории, чтобы
результаты студентов были воспроизводимы.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "data" / "rostov_poi.json"
DB = HERE / "poi.sqlite"

BBOX = "47.15,39.50,47.35,39.90"
KEYS = ["amenity", "shop", "leisure", "tourism", "healthcare", "office"]
MIRRORS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

# что оставляем: остальное (парковки, скамейки, урны) для поиска бесполезно
KEEP = {
    "amenity": {"cafe", "restaurant", "bar", "pub", "fast_food", "ice_cream", "pharmacy", "bank",
                "hospital", "clinic", "doctors", "dentist", "veterinary", "library", "cinema",
                "theatre", "nightclub", "fuel", "post_office", "kindergarten", "school",
                "university", "college", "atm", "marketplace", "car_wash", "car_rental"},
    "shop": None,       # None — берём всё
    "leisure": {"fitness_centre", "sports_centre", "swimming_pool", "park", "playground", "stadium"},
    "tourism": {"hotel", "hostel", "museum", "gallery", "attraction", "guest_house", "apartment"},
    "healthcare": None,
    "office": {"coworking", "it", "company", "estate_agent", "lawyer", "travel_agent"},
}

SCHEMA = """
CREATE TABLE poi (
    id             INTEGER PRIMARY KEY,
    osm_type       TEXT NOT NULL,
    category       TEXT NOT NULL,      -- amenity, shop, leisure, tourism, healthcare, office
    kind           TEXT NOT NULL,      -- cafe, pharmacy, supermarket …
    name           TEXT,
    brand          TEXT,               -- Ozon, Магнит, Пятёрочка … (есть у 9% мест)
    street         TEXT,
    housenumber    TEXT,
    opening_hours  TEXT,
    is_24_7        INTEGER,            -- 1 круглосуточно, 0 нет, NULL неизвестно
    cuisine        TEXT,
    internet       INTEGER,            -- 1 есть wi-fi, 0 нет, NULL неизвестно
    wheelchair     INTEGER,            -- 1 доступно, 0 нет, NULL неизвестно
    outdoor_seating INTEGER,
    takeaway       INTEGER,
    phone          TEXT,
    website        TEXT,
    lat            REAL NOT NULL,
    lon            REAL NOT NULL
);
CREATE INDEX idx_poi_kind ON poi(kind);
CREATE INDEX idx_poi_category ON poi(category);
CREATE INDEX idx_poi_street ON poi(street);
CREATE INDEX idx_poi_brand ON poi(brand);
CREATE INDEX idx_poi_geo ON poi(lat, lon);
"""


def _tri(value: str | None) -> int | None:
    """yes/no/limited → 1/0/None: у OSM три состояния, и третье важно."""
    if value is None:
        return None
    v = value.strip().lower()
    if v in ("yes", "wlan", "wifi", "free", "designated", "public", "customers"):
        return 1
    if v in ("no", "none"):
        return 0
    return None


def fetch_raw() -> dict:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    elements, seen = [], set()
    for key in KEYS:
        q = f'[out:json][timeout:120];(node["{key}"]({BBOX});way["{key}"]({BBOX}););out tags center;'
        for mirror in MIRRORS:
            try:
                req = urllib.request.Request(
                    mirror, data=urllib.parse.urlencode({"data": q}).encode(),
                    headers={"User-Agent": "mmcs-agentic-course/1.0 (teaching materials)"})
                els = json.loads(urllib.request.urlopen(req, timeout=180, context=ctx).read())["elements"]
                print(f"{key:12} {len(els):6} объектов ({mirror.split('/')[2]})")
                for e in els:
                    eid = (e["type"], e["id"])
                    if eid not in seen:
                        seen.add(eid)
                        elements.append(e)
                break
            except Exception as exc:
                print(f"{key:12} {mirror.split('/')[2]}: {type(exc).__name__}")
                time.sleep(3)
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps({"elements": elements}, ensure_ascii=False), encoding="utf-8")
    return {"elements": elements}


def rows_from(raw: dict) -> list[tuple]:
    rows, next_id = [], 1
    for e in raw["elements"]:
        tags = e.get("tags", {})
        category = kind = None
        for key in KEYS:
            if key in tags:
                allowed = KEEP[key]
                if allowed is None or tags[key] in allowed:
                    category, kind = key, tags[key]
                break
        if not category:
            continue
        lat = e.get("lat") or (e.get("center") or {}).get("lat")
        lon = e.get("lon") or (e.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue
        hours = tags.get("opening_hours")
        rows.append((
            next_id, e["type"], category, kind,
            tags.get("name") or tags.get("name:ru"),
            tags.get("brand") or tags.get("operator"),
            tags.get("addr:street"), tags.get("addr:housenumber"),
            hours,
            1 if hours and re.fullmatch(r"\s*24/7\s*", hours) else (0 if hours else None),
            tags.get("cuisine"),
            _tri(tags.get("internet_access")),
            _tri(tags.get("wheelchair")),
            _tri(tags.get("outdoor_seating")),
            _tri(tags.get("takeaway")),
            tags.get("phone") or tags.get("contact:phone"),
            tags.get("website") or tags.get("contact:website"),
            float(lat), float(lon),
        ))
        next_id += 1
    return rows


def build(rows: list[tuple]) -> None:
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    con.executemany(f"INSERT INTO poi VALUES ({', '.join(['?'] * 19)})", rows)
    con.commit()
    con.close()


def report() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    total = con.execute("SELECT COUNT(*) FROM poi").fetchone()[0]
    print(f"\n{DB}: {total} объектов")
    print("\nтоп брендов:")
    for r in con.execute("SELECT brand, COUNT(*) n FROM poi WHERE brand IS NOT NULL "
                         "GROUP BY brand ORDER BY n DESC LIMIT 8"):
        print(f"  {r['brand']:18} {r['n']:5}")
    print("\nтоп категорий:")
    for r in con.execute("SELECT kind, COUNT(*) n FROM poi GROUP BY kind ORDER BY n DESC LIMIT 12"):
        print(f"  {r['kind']:18} {r['n']:5}")
    print("\nзаполненность полей:")
    for field in ("name", "brand", "street", "opening_hours", "cuisine", "internet", "phone", "website"):
        n = con.execute(f"SELECT COUNT(*) FROM poi WHERE {field} IS NOT NULL").fetchone()[0]
        print(f"  {field:16} {n:5}  {100 * n / total:5.1f}%")
    con.close()


def main() -> None:
    p = argparse.ArgumentParser(description="Сборка базы заведений Ростова из OSM")
    p.add_argument("--refresh", action="store_true", help="выкачать данные заново")
    args = p.parse_args()

    raw = fetch_raw() if args.refresh or not RAW.exists() else json.loads(RAW.read_text(encoding="utf-8"))
    rows = rows_from(raw)
    build(rows)
    report()


if __name__ == "__main__":
    main()
