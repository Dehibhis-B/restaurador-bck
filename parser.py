import re


def parse_bck_line(raw_line):
    raw_line = raw_line.strip()
    if not raw_line:
        return None

    cleaned = re.sub(r' +', ' ', raw_line)
    parts = cleaned.split(' ')

    if len(parts) < 25:
        return None

    device = parts[0]
    year = parts[1]
    month = parts[2]
    day = parts[3]
    hour = parts[4]
    minute = parts[5]
    second = parts[6]
    event = parts[7]
    event_code = parts[-2]
    dni = parts[-1]

    mark_date = f"{year}-{month}-{day} {hour}:{minute}:{second}"

    return {
        "device": device,
        "mark_date": mark_date,
        "event": event,
        "event_code": event_code,
        "dni": dni,
        "raw_line": raw_line,
    }
