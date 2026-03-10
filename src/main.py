from dataclasses import dataclass
from datetime import datetime
import calendar


@dataclass
class TimePoint:
    year: int
    month: int | None = None
    day: int | None = None
    granularity: str = ""

@dataclass
class Interval:
    start: TimePoint
    end: TimePoint

@dataclass
class SemanticInterval:
    start: datetime
    end: datetime

@dataclass
class PossibleRange:
    earliest: datetime
    latest: datetime

@dataclass
class UncertainInterval:
    earliest: TimePoint
    latest: TimePoint

def main():
    with open("testCases.txt", "r") as file:
        for raw_line in file:
            line = raw_line.strip()

            if line == "":
                continue

            print("-------------------------------")
            handle_test_case(line)


def handle_test_case(line: str):
    parts = [part.strip() for part in line.split("|")]

    if len(parts) == 1:
        handle_conversion_case(parts[0])
    elif len(parts) == 3:
        handle_relation_case(parts[0], parts[1], parts[2])
    else:
        raise ValueError(f"Invalid test case: {line}")


def handle_conversion_case(text: str):
    parsed = parse_value(text)
    semantic = semanticize(parsed)

    print("parsed:")
    print(parsed)

    if isinstance(semantic, SemanticInterval):
        print("semantic interval:")
    elif isinstance(semantic, PossibleRange):
        print("possible range:")

    print(semantic)


def handle_relation_case(method: str, left_text: str, right_text: str):
    print("arithmetic")

    left_parsed = parse_value(left_text)
    right_parsed = parse_value(right_text)

    left_semantic = semanticize(left_parsed)
    right_semantic = semanticize(right_parsed)

    # print("left parsed:")
    # print(left_parsed)
    print("left semantic:")
    print(left_semantic)

    # print("right parsed:")
    # print(right_parsed)
    print("right semantic:")
    print(right_semantic)

    result = evaluate_relation(method, left_semantic, right_semantic)
    print(f"{method}: {result}")


def parse_value(text: str):
    text = text.strip()

    if text.startswith("{") and text.endswith("}") and ".." in text:
        return parse_uncertain(text)
        
    elif text.startswith("[") and text.endswith("]") and ".." in text:
        return parse_interval(text)
    return parse_timepoint(text)


def parse_uncertain(text: str) -> UncertainInterval:
    left_text, right_text = text[1:-1].split("..")

    earliest = parse_timepoint(left_text.strip())
    latest = parse_timepoint(right_text.strip())

    return UncertainInterval(earliest=earliest, latest=latest)

def parse_interval(text: str) -> Interval:
    left_text, right_text = text[1:-1].split("..")

    earliest = parse_timepoint(left_text.strip())
    latest = parse_timepoint(right_text.strip())

    return Interval(start=earliest, end=latest)


def parse_timepoint(text: str) -> TimePoint:
    parts = text.split("/")
    int_parts = list(map(int, parts))

    if len(int_parts) == 1:
        year = int_parts[0]
        return TimePoint(year=year, granularity="year")

    if len(int_parts) == 2:
        year, month = int_parts
        return TimePoint(year=year, month=month, granularity="month")

    if len(int_parts) == 3:
        year, month, day = int_parts
        return TimePoint(year=year, month=month, day=day, granularity="day")

    raise ValueError(f"Unsupported format: {text}")


def semanticize(value):
    if isinstance(value, TimePoint):
        return to_semantic_interval(value)

    if isinstance(value, Interval):
        return to_semantic_interval_from_interval(value)

    if isinstance(value, UncertainInterval):
        return to_possible_range(value)

    raise ValueError(f"Unsupported value: {value}")


def to_semantic_interval_from_interval(interval: Interval) -> SemanticInterval:
    start_sem = to_semantic_interval(interval.start)
    end_sem = to_semantic_interval(interval.end)

    return SemanticInterval(
        start=start_sem.start,
        end=end_sem.end
    )


def to_semantic_interval(tp: TimePoint) -> SemanticInterval:
    if tp.granularity == "year":
        start = datetime(tp.year, 1, 1, 0, 0, 0)
        end = datetime(tp.year, 12, 31, 23, 59, 59)
        return SemanticInterval(start, end)

    if tp.granularity == "month":
        last_day = calendar.monthrange(tp.year, tp.month)[1]
        start = datetime(tp.year, tp.month, 1, 0, 0, 0)
        end = datetime(tp.year, tp.month, last_day, 23, 59, 59)
        return SemanticInterval(start, end)

    if tp.granularity == "day":
        start = datetime(tp.year, tp.month, tp.day, 0, 0, 0)
        end = datetime(tp.year, tp.month, tp.day, 23, 59, 59)
        return SemanticInterval(start, end)

    raise ValueError("Unknown granularity")


def to_possible_range(u: UncertainInterval) -> PossibleRange:
    earliest_sem = to_semantic_interval(u.earliest)
    latest_sem = to_semantic_interval(u.latest)

    return PossibleRange(
        earliest=earliest_sem.start,
        latest=latest_sem.end
    )


def evaluate_relation(method: str, left, right) -> bool:
    if method == "contains":
        return contains(left, right)

    if method == "overlaps":
        return overlaps(left, right)

    if method == "before":
        return before(left, right)
    
    if method == "possibly_before":
        return possibly_before(left, right)

    if method == "possibly_overlaps":
        return possibly_overlaps(left, right)
    
    if method == "definitely_before":
        return definitely_before(left, right)
    
    if method == "definitely_overlaps":
        return definitely_overlaps(left, right)
    
    raise ValueError(f"Unknown method: {method}")

def get_earliest(value):
    if isinstance(value, SemanticInterval):
        return value.start
    if isinstance(value, PossibleRange):
        return value.earliest
    raise ValueError("Unsupported value")


def get_latest(value):
    if isinstance(value, SemanticInterval):
        return value.end
    if isinstance(value, PossibleRange):
        return value.latest
    raise ValueError("Unsupported value")


def contains(a: SemanticInterval, b: SemanticInterval) -> bool:
    return a.start <= b.start and a.end >= b.end

def overlaps(a: SemanticInterval, b: SemanticInterval) -> bool:
    return not (a.end < b.start or b.end < a.start)

def before(a: SemanticInterval, b: SemanticInterval) -> bool:
    return a.end < b.start

def possibly_before(a, b) -> bool:
    return get_earliest(a) < get_latest(b)

def possibly_overlaps(a, b) -> bool:
    return not (get_latest(a) < get_earliest(b) or get_latest(b) < get_earliest(a))

def definitely_before(a, b) -> bool:
    return get_latest(a) < get_earliest(b)

def definitely_overlaps(a, b) -> bool:
    a_start = get_earliest(a)
    a_end = get_latest(a)

    b_start = get_earliest(b)
    b_end = get_latest(b)

    return not (a_end < b_start or b_end < a_start)

if __name__ == "__main__":
    main()