"""Готовая обвязка для задач недели 2: данные, инструменты и проверки.

Всё, что здесь лежит, студенту дано. Его код — несколько строк в ноутбуке:
описания, поля модели, инструкция агента, формат результата инструмента.

База — 8860 мест Ростова из OpenStreetMap, та же, что в первой неделе.
"""

from __future__ import annotations

import math
import re
import sqlite3
from enum import Enum
from pathlib import Path
from typing import Any

DB = Path(__file__).with_name("poi.sqlite")

LAT_M = 111_320                                   # метров в градусе широты
LON_M = LAT_M * math.cos(math.radians(47.23))     # ... и в градусе долготы у нас

CALLS: list[dict] = []                            # журнал вызовов: его читают проверки


def rows(sql: str, params: tuple = ()) -> list[dict]:
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        return [dict(r) for r in con.execute(sql, params)]


def one(sql: str, params: tuple = ()) -> dict | None:
    got = rows(sql, params)
    return got[0] if got else None


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Расстояние по прямой: для города плоской формулы достаточно."""
    return int(math.hypot((lat1 - lat2) * LAT_M, (lon1 - lon2) * LON_M))


def table(items: list[dict], columns: tuple[str, ...]) -> str:
    """Табличка вместо JSON: те же данные, вдвое меньше токенов."""
    if not items:
        return "ничего не нашлось"
    head = " | ".join(columns)
    body = "\n".join(" | ".join(str(it.get(c) if it.get(c) is not None else "—") for c in columns)
                     for it in items)
    return f"{head}\n{body}"


def _log(name: str, **args: Any) -> None:
    CALLS.append({"name": name, **args})


def reset_log() -> None:
    CALLS.clear()


# ══════════════════════════════════════════════ задача 1: три функции над базой

def find_places(kind: str, street: str | None = None, limit: int = 10) -> str:
    """Список мест города заданного вида, при желании — только на одной улице.

    Зови, когда нужен перечень заведений: какие аптеки есть, что за кафе на улице.
    Не зови для расстояний и «что ближе» — для этого есть другой инструмент.

    Args:
        kind: вид места латиницей, например pharmacy, cafe, supermarket, outpost.
        street: часть названия улицы; без неё ищется по всему городу.
        limit: сколько строк вернуть.
    """
    _log("find_places", kind=kind, street=street)
    sql = "SELECT id, name, street, housenumber, opening_hours FROM poi WHERE kind = ?"
    params: list[Any] = [kind]
    if street:
        sql += " AND street LIKE ?"
        params.append(f"%{street}%")
    got = rows(sql + " LIMIT ?", (*params, limit))
    return table(got, ("id", "name", "street", "housenumber", "opening_hours"))


def count_places(kind: str, only_24_7: bool = False) -> str:
    """Сколько в городе мест такого вида: возвращает одно число, а не список.

    Зови на вопросы «сколько», «какое количество». Для перечня мест есть find_places.

    Args:
        kind: вид места латиницей, например pharmacy, cafe, outpost.
        only_24_7: считать только круглосуточные.
    """
    _log("count_places", kind=kind, only_24_7=only_24_7)
    sql = "SELECT COUNT(*) AS n FROM poi WHERE kind = ?" + (" AND is_24_7 = 1" if only_24_7 else "")
    return f"{kind}: {one(sql, (kind,))['n']} шт."


def top_brands(kind: str, limit: int = 5) -> str:
    _log("top_brands", kind=kind)
    got = rows("SELECT COALESCE(brand, 'без бренда') AS brand, COUNT(*) AS n FROM poi "
               "WHERE kind = ? GROUP BY 1 ORDER BY n DESC LIMIT ?", (kind, limit))
    return table(got, ("brand", "n"))


def unfilled(text: str | None) -> bool:
    """Заготовка осталась незаполненной: пусто, многоточие или TODO."""
    body = (text or "").strip().strip(".…").strip()
    return not body or body.upper().startswith("TODO")


def check_first_agent(agent: Any, answer: str) -> None:
    """Проверка задачи 1: описания на месте, число в ответе сходится с базой."""
    empty = [t.name for t in agent.tools if unfilled(getattr(t, "description", ""))]
    truth = one("SELECT COUNT(*) AS n FROM poi WHERE kind = 'pharmacy' AND is_24_7 = 1")["n"]
    ok_number = str(truth) in (answer or "")
    _verdict([(not empty, f"у всех инструментов есть описание (без него: {empty or '—'})"),
              (ok_number, f"в ответе есть верное число {truth}")])


# ══════════════════════════════════════════ задача 2: цепочка из трёх инструментов

CHAIN_QUESTION = ("Я на Белорусской улице, 44. Где ближайшая аптека "
                  "и до скольки она сегодня работает?")


def address_point(street: str, housenumber: str) -> dict | None:
    """Координаты дома по адресу: ищет в базе место с таким адресом.

    Название улицы приходит в любом падеже («Белорусской улице»), поэтому
    ищем по основе самого длинного слова.
    """
    _log("address_point", street=street, housenumber=housenumber)
    words = [w for w in re.findall(r"[А-Яа-яЁё]{4,}", street)
             if not re.match(r"улиц|проспек|переул|бульвар", w.lower())]
    stem = max(words, key=len)[:-2] if words else street
    return one("SELECT id, name, street, housenumber, lat, lon FROM poi "
               "WHERE street LIKE ? AND housenumber = ? LIMIT 1", (f"%{stem}%", housenumber))


def nearest(lat: float, lon: float, kind: str, limit: int = 1) -> list[dict]:
    """Ближайшие к точке места заданного вида, с расстоянием в метрах."""
    _log("nearest", lat=round(lat, 5), lon=round(lon, 5), kind=kind)
    got = rows("SELECT id, name, lat, lon FROM poi WHERE kind = ?", (kind,))
    for r in got:
        r["distance_m"] = distance_m(lat, lon, r["lat"], r["lon"])
    return sorted(got, key=lambda r: r["distance_m"])[:limit]


def details(place_id: int) -> dict | None:
    """Карточка места: название, адрес, часы работы, телефон."""
    _log("details", place_id=place_id)
    return one("SELECT id, name, brand, street, housenumber, opening_hours, phone "
               "FROM poi WHERE id = ?", (place_id,))


def chain_truth() -> dict:
    """Правильный ответ, посчитанный по базе без всякой модели."""
    home = address_point("Белорусская", "44")
    best = nearest(home["lat"], home["lon"], "pharmacy", 1)[0]
    return {"home": home, "pharmacy": details(best["id"]), "distance_m": best["distance_m"]}


def check_chain(answer: str) -> None:
    """Проверка задачи 2: три вызова подряд, и каждый получил своё из предыдущего."""
    log = [c for c in CALLS if c["name"] in ("address_point", "nearest", "details")]
    truth = chain_truth()
    order = [c["name"] for c in log]

    def in_order(names: list[str]) -> bool:
        """Три вызова идут в таком порядке — не обязательно подряд и не обязательно первыми."""
        it = iter(order)
        return all(any(step == call for call in it) for step in names)
    got_coords = next((c for c in log if c["name"] == "nearest"), None)
    got_id = next((c for c in log if c["name"] == "details"), None)

    coords_ok = bool(got_coords) and abs(got_coords["lat"] - truth["home"]["lat"]) < 1e-3 \
        and abs(got_coords["lon"] - truth["home"]["lon"]) < 1e-3
    id_ok = bool(got_id) and got_id["place_id"] == truth["pharmacy"]["id"]
    hours = (truth["pharmacy"]["opening_hours"] or "").split(" ")[-1]
    name = truth["pharmacy"]["name"] or ""
    ends = hours.split("-")[-1].split(":")[0].lstrip("0")          # «21» из «08:00-21:00»
    said = bool(answer) and (hours in answer or name in answer or ends in answer)

    _verdict([
        (in_order(["address_point", "nearest", "details"]),
         f"три вызова в нужном порядке (было: {order or 'ни одного'})"),
        (coords_ok, "в поиск ближайшего ушли координаты дома, а не выдуманные"),
        (id_ok, f"карточку запросили у той аптеки, которую нашли (id {truth['pharmacy']['id']})"),
        (said, f"в ответе есть часы работы {hours!r}"),
    ])


# ══════════════════════════════════════════════ задача 3: запрос объектом

class Kind(str, Enum):
    """Виды мест, которые есть в базе. Список в схеме — то, чего нельзя выдумать."""
    pharmacy = "pharmacy"
    cafe = "cafe"
    restaurant = "restaurant"
    fast_food = "fast_food"
    supermarket = "supermarket"
    convenience = "convenience"
    outpost = "outpost"
    bank = "bank"
    school = "school"
    kindergarten = "kindergarten"
    playground = "playground"
    park = "park"
    fuel = "fuel"


KINDS = ("pharmacy", "cafe", "restaurant", "fast_food", "supermarket", "convenience",
         "outpost", "bank", "school", "kindergarten", "playground", "park", "fuel")

QUERY_CASES: list[tuple[str, dict]] = [
    ("Какие аптеки работают круглосуточно?", {"kind": "pharmacy", "only_24_7": True}),
    ("Покажи кафе на Пушкинской улице", {"kind": "cafe", "street": "Пушкин"}),
    ("Покажи пункты выдачи сети Ozon", {"kind": "outpost", "brand": "Ozon"}),
    ("Найди супермаркеты", {"kind": "supermarket"}),
    ("Круглосуточные заправки", {"kind": "fuel", "only_24_7": True}),
    ("Школы на улице Доватора", {"kind": "school", "street": "Доватор"}),
]


def run_query(q: Any) -> str:
    """Выполняет объект-запрос: собирает SQL по его полям. Это дано, менять не нужно."""
    _log("run_query", query=_as_dict(q))
    sql = "SELECT id, name, street, housenumber, opening_hours FROM poi WHERE 1 = 1"
    params: list[Any] = []
    if getattr(q, "kind", None):
        sql += " AND kind = ?"
        params.append(q.kind if isinstance(q.kind, str) else q.kind.value)
    if getattr(q, "street", None):
        sql += " AND street LIKE ?"
        params.append(f"%{q.street}%")
    if getattr(q, "brand", None):
        sql += " AND brand LIKE ?"
        params.append(f"%{q.brand}%")
    if getattr(q, "only_24_7", False):
        sql += " AND is_24_7 = 1"
    got = rows(sql + " LIMIT ?", (*params, int(getattr(q, "limit", 5) or 5)))
    return table(got, ("id", "name", "street", "housenumber", "opening_hours"))


def _as_dict(q: Any) -> dict:
    if hasattr(q, "model_dump"):
        return {k: (v.value if hasattr(v, "value") else v) for k, v in q.model_dump().items()}
    return dict(getattr(q, "__dict__", {}))


def check_query(asked: list[dict]) -> None:
    """Проверка задачи 3: сравниваем собранные агентом запросы с ожидаемыми."""
    lines, good = [], 0
    for (question, want), got in zip(QUERY_CASES, asked + [{}] * len(QUERY_CASES)):
        wrong = {k: (want[k], got.get(k)) for k in want if got.get(k) != want[k]
                 and not (k == "street" and str(want[k]) in str(got.get(k) or ""))}
        bad_kind = got.get("kind") not in KINDS and got.get("kind") is not None
        good += not wrong and not bad_kind
        mark = "✓" if not wrong and not bad_kind else "✗"
        lines.append(f"  {mark} {question}" + (f"   → не сошлось: {wrong}" if wrong else "")
                     + ("   → вида нет в базе" if bad_kind else ""))
    print("\n".join(lines))
    _verdict([(good >= 5, f"верно собрано запросов: {good} из {len(QUERY_CASES)} (нужно 5)")])


# ══════════════════════════════════════════════ задача 4: описания решают

QUESTIONS: list[tuple[str, str]] = [
    ("Какие аптеки есть на Пушкинской улице?", "find_places"),
    ("Какая аптека ближе всего к точке 47.2357, 39.7015?", "nearest_place"),
    ("Покажи кафе в центре", "find_places"),
    ("Сколько метров до ближайшего пункта выдачи от 47.2357, 39.7015?", "nearest_place"),
    ("Перечисли супермаркеты на улице Доватора", "find_places"),
    ("Какая ближайшая школа к точке 47.2280, 39.7300?", "nearest_place"),
    ("Какие заправки есть в городе?", "find_places"),
    ("Ближайший банк к 47.2200, 39.7100", "nearest_place"),
]


async def share_correct(agent: Any, runner: Any, runs: int = 1) -> float:
    """Доля вопросов, на которых агент позвал тот инструмент, который нужен."""
    hits = 0
    for question, want in QUESTIONS * runs:
        called = tools_called(await runner.run(agent, question))
        hits += called[:1] == [want]
    return round(hits / (len(QUESTIONS) * runs), 2)


def tools_called(result: Any) -> list[str]:
    """Имена инструментов, которые агент позвал за прогон, по порядку."""
    names = []
    for item in getattr(result, "new_items", []):
        raw = getattr(item, "raw_item", None)
        name = getattr(raw, "name", None)
        if name and type(item).__name__ == "ToolCallItem":
            names.append(name)
    return names


def check_share(value: float) -> None:
    _verdict([(value >= 0.9, f"доля верного выбора {value} (нужно 0.9)")])


# ══════════════════════════════════════════════ задача 5: сессия

DIALOG = [
    "Сколько в Ростове аптек?",
    "А какие из них на Пушкинской улице?",
    "А сколько из них круглосуточных?",
]


def check_session(without_memory: str, with_memory: str) -> None:
    truth = one("SELECT COUNT(*) AS n FROM poi WHERE kind = 'pharmacy' AND is_24_7 = 1")["n"]
    _verdict([(str(truth) in (with_memory or ""), f"с сессией последний ответ верный ({truth})"),
              (str(truth) not in (without_memory or ""),
               "без сессии последний ответ не про аптеки — так и должно быть")])


# ══════════════════════════════════════════════ задача 6: лимит и цена

def stubborn_tool(kind: str | None = None) -> str:
    """Поиск мест по городу.

    Args:
        kind: вид места.
    """
    _log("stubborn_tool", kind=kind)
    return ("Уточните фильтр и вызовите инструмент ещё раз: слишком много вариантов. "
            "Назовите вид места точнее.")


# Рублей за миллион токенов. Числа примерные: у каждого сервиса свой прайс,
# подставь свой — на порядок величины это не влияет, на счёт влияет.
PRICE_IN, PRICE_OUT = 30.0, 120.0


def cost_rub(usage: Any) -> float:
    """Цена прогона по токенам: вход и выход стоят по-разному."""
    return round(usage.input_tokens / 1e6 * PRICE_IN + usage.output_tokens / 1e6 * PRICE_OUT, 4)


def check_limit(stopped: bool, turns: int, cost: float) -> None:
    ok_turns = isinstance(turns, int) and 2 <= turns <= 8
    ok_cost = isinstance(cost, (int, float)) and cost > 0
    _verdict([(stopped, "прогон остановлен предохранителем, а не сам собой"),
              (ok_turns, f"лимит шагов разумный: {shown(turns)}"),
              (ok_cost, f"цена посчитана по токенам: {shown(cost)} ₽")])


# ══════════════════════════════════════════════ задача 7: форма отчёта

FAKE_REPORT = {"places": [{"lat": 47.2261, "lon": 39.7184, "demand": 999,
                           "competitor_distance_m": 0, "why": "хорошее место"}],
               "checked_cells": 0}
TRUE_REPORT = {"places": [{"lat": 47.2261, "lon": 39.7184, "demand": 34,
                           "competitor_distance_m": 410, "why": "жильё рядом, конкурент далеко"}],
               "checked_cells": 8}


def check_form(model: Any) -> None:
    """Проверка задачи 7: каждое из трёх ограничений проверяется отдельно.

    Иначе задачу закрывает одна строка: подложный отчёт врёт сразу в трёх местах,
    и достаточно поймать любое.
    """
    import copy

    def passes(data: dict) -> bool:
        try:
            model(**data)
            return True
        except Exception:
            return False

    def spoiled(field: str, value: Any) -> dict:
        data = copy.deepcopy(TRUE_REPORT)
        if field == "checked_cells":
            data[field] = value
        else:
            data["places"][0][field] = value
        return data

    _verdict([
        (not passes(FAKE_REPORT), "подложный отчёт целиком не проходит"),
        (not passes(spoiled("demand", 999)), "спрос 999 не проходит"),
        (not passes(spoiled("competitor_distance_m", 0)), "ноль метров до конкурента не проходит"),
        (not passes(spoiled("checked_cells", 0)), "ноль просмотренных кварталов не проходит"),
        (passes(TRUE_REPORT), "настоящий отчёт по-прежнему проходит"),
    ])


# ══════════════════════════════════════════════ задача 8: гардрейл

CITY_QUESTIONS = ["Сколько в Ростове аптек?", "Какие кафе на Пушкинской?",
                  "Где ближайший пункт выдачи к 47.23, 39.70?", "Сколько аптек работает ночью?",
                  "Какие сети пунктов выдачи представлены в городе?", "Сколько школ в Ростове?"]
OFF_TOPIC = ["Напиши стихотворение про Ростов", "Переведи этот текст на английский",
             "Реши квадратное уравнение x^2 - 5x + 6 = 0", "Расскажи анекдот"]


def check_guardrail(blocked: list[bool], asked: list[str]) -> None:
    by = dict(zip(asked, blocked))
    missed = [q for q in OFF_TOPIC if not by.get(q)]
    false_alarm = [q for q in CITY_QUESTIONS if by.get(q)]
    _verdict([(not missed, f"все посторонние отсечены (пропущены: {missed or '—'})"),
              (not false_alarm, f"нормальные вопросы прошли (зарублены зря: {false_alarm or '—'})")])


# ══════════════════════════════════════════════ задача 9: триаж

MIXED: list[tuple[str, str]] = [
    ("Сколько в городе круглосуточных аптек?", "Reference"),
    ("Где открыть новый пункт выдачи на западе города?", "Analyst"),
    ("Какие кафе есть на Пушкинской улице?", "Reference"),
    ("В каком квартале спрос выше, чем конкуренция?", "Analyst"),
    ("Сколько пунктов выдачи у Ozon?", "Reference"),
    ("Стоит ли ставить точку рядом с 47.2357, 39.7015?", "Analyst"),
]


def check_triage(routed: list[str]) -> None:
    wrong = [(q, want, got) for (q, want), got in zip(MIXED, routed) if got != want]
    for q, want, got in wrong:
        print(f"  ✗ {q}\n      нужно: {want}, ушло: {got}")
    _verdict([(not wrong, f"все вопросы ушли по адресу ({len(MIXED) - len(wrong)} из {len(MIXED)})")])


# ══════════════════════════════════════════════ задача 10: сверка отчёта

CELL_M = 500                                      # сторона квартала анализа, метры
DEMAND_KINDS = ("playground", "kindergarten", "school", "convenience", "supermarket")


def best_cells(limit: int = 5) -> str:
    """Кварталы города 500 на 500 метров с наибольшим спросом, с координатами центра.

    Зови первым: выбор места начинается с него, потому что только он даёт
    координаты кандидатов. Для одной известной точки есть demand_in_cell.

    Args:
        limit: сколько кварталов вернуть.
    """
    _log("best_cells", limit=limit)
    marks = rows(f"SELECT lat, lon FROM poi WHERE kind IN ({','.join('?' * len(DEMAND_KINDS))})",
                 DEMAND_KINDS)
    buckets: dict[tuple[int, int], int] = {}
    for r in marks:
        key = (int(r["lat"] * LAT_M // CELL_M), int(r["lon"] * LON_M // CELL_M))
        buckets[key] = buckets.get(key, 0) + 1
    top = sorted(buckets, key=lambda k: -buckets[k])[:limit]
    items = []
    for cy, cx in top:
        lat = round((cy * CELL_M + CELL_M / 2) / LAT_M, 4)
        lon = round((cx * CELL_M + CELL_M / 2) / LON_M, 4)
        items.append({"lat": lat, "lon": lon, "demand": demand_in_cell(lat, lon)})
    return table(items, ("lat", "lon", "demand"))


def demand_in_cell(lat: float, lon: float, radius_m: int = 500) -> int:
    """Спрос вокруг точки: жильё, садики, школы, магазины у дома."""
    kinds = ("playground", "kindergarten", "school", "convenience", "supermarket")
    got = rows(f"SELECT lat, lon FROM poi WHERE kind IN ({','.join('?' * len(kinds))})", kinds)
    return sum(distance_m(lat, lon, r["lat"], r["lon"]) <= radius_m for r in got)


def competitors_near(lat: float, lon: float, radius_m: int = 500) -> int:
    """Сколько пунктов выдачи уже стоит вокруг точки."""
    got = rows("SELECT lat, lon FROM poi WHERE kind = 'outpost'")
    return sum(distance_m(lat, lon, r["lat"], r["lon"]) <= radius_m for r in got)


def check_report(report: Any, hand_demand: int, hand_competitors: int) -> None:
    """Проверка задачи 10: числа отчёта сверяются с базой, ручной счёт совпадает."""
    first = report.places[0]
    truth_d = demand_in_cell(first.lat, first.lon)
    truth_c = competitors_near(first.lat, first.lon)
    said = getattr(first, "demand", None)
    gap = "сошлось" if said == truth_d else f"разошлось: у агента {said}, в базе {truth_d}"
    print(f"   отчёт против базы — {gap}")
    print("   расхождение здесь не ошибка твоего кода: это и есть ответ на вопрос задачи")
    _verdict([
        (hand_demand == truth_d,
         f"спрос посчитан верно: у тебя {shown(hand_demand)}, в базе {truth_d}"),
        (hand_competitors == truth_c,
         f"конкуренты посчитаны верно: у тебя {shown(hand_competitors)}, в базе {truth_c}"),
    ])


# ══════════════════════════════════════════════════════════════════ общий вердикт

def shown(value: Any) -> Any:
    """Многоточие в ячейке — это незаполненная заготовка, так о ней и говорим."""
    return "не заполнено" if value is ... else value


class CheckFailed(AssertionError):
    pass


def _verdict(items: list[tuple[bool, str]]) -> None:
    for ok, text in items:
        print(("✓ " if ok else "✗ ") + text)
    bad = [text for ok, text in items if not ok]
    if bad:
        raise CheckFailed("не сошлось: " + "; ".join(bad))
    print("ЗАДАЧА ЗАЧТЕНА")
