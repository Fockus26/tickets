import re
import datetime
from flask import session

# ---------- formatos ----------
DATETIME_FORMAT = "%Y-%m-%dT%H:%M"  # formato que pediste

# ---------- validadores básicos ----------
def is_non_empty_str(s):
    return isinstance(s, str) and s.strip() != ""

def is_max_length(s, max_len):
    return isinstance(s, str) and len(s) <= max_len

def is_username_valid(username):
    # longitud 6-24
    return isinstance(username, str) and 6 <= len(username) <= 24

def is_password_valid(password):
    # longitud 8-24, al menos 1 número, 1 mayúscula, 1 minúscula, 1 especial
    if not isinstance(password, str) or not (8 <= len(password) <= 24):
        return False
    # patrón: positivo lookahead
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,24}$'
    return re.match(pattern, password) is not None

def is_hex32(s):
    return isinstance(s, str) and re.fullmatch(r'^[0-9a-fA-F]{32}$', s) is not None

def is_alphanumeric(s):
    return isinstance(s, str) and re.fullmatch(r'^[A-Za-z0-9]+$', s) is not None

# ---------- datetime ----------
def parse_strict_datetime(s):
    """
    Parse a string in YYYY-MM-DDTHH:MM. Raises ValueError if invalid.
    """
    if not isinstance(s, str):
        raise ValueError("No es una cadena de texto")
    return datetime.datetime.strptime(s, DATETIME_FORMAT)

def now_utc_or_local():
    # usa timezone local del servidor; si quieres UTC adapta aquí
    return datetime.datetime.now()

def validate_event_range(event_date_range_str):
    """
    event_date_range_str puede ser:
      - "YYYY-MM-DDTHH:MM" (single)
      - "YYYY-MM-DDTHH:MM to YYYY-MM-DDTHH:MM" (range)
    Devuelve (start_dt, end_dt) como datetime objects.
    Lanza ValueError si formato inválido o fechas en el pasado.
    """
    if not isinstance(event_date_range_str, str) or not event_date_range_str.strip():
        raise ValueError("La fecha esta vacia")
    s = event_date_range_str.strip()
    now = now_utc_or_local()

    if " to " in s:
        parts = s.split(" to ", 1)
        start = parse_strict_datetime(parts[0].strip())
        end = parse_strict_datetime(parts[1].strip())
    else:
        start = parse_strict_datetime(s)
        end = start

    # validar que sean posteriores a la fecha actual
    if start <= now:
        raise ValueError("La fecha de inicio debe ser posterior a la fecha actual.")
    if end < start:
        raise ValueError("La fecha final no puede ser anterior a la de inicio.")
    return start, end

def parse_section_datetime_loose(s):
    """
    Para fechas por-sección: acepta "YYYY-MM-DDTHH:MM" o "YYYY-MM-DD" (sin tiempo).
    Devuelve datetime si incluye hora, o datetime con time 00:00 si sólo fecha.
    Lanza ValueError si formato no reconocido.
    """
    if not s:
        raise ValueError("Fecha de la seccion vacia")
    s = s.strip()
    # intentar formato completo primero
    try:
        return datetime.datetime.strptime(s, DATETIME_FORMAT)
    except Exception:
        pass
    # intentar solo fecha YYYY-MM-DD
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except Exception:
        raise ValueError("Formato de fecha de sección inválido. Use YYYY-MM-DD o YYYY-MM-DDTHH:MM")

# ---------- secciones ----------
def validate_sections(section_names, num_tickets, event_main_start=None, event_main_end=None, event_date_time_tickets=None, page_name=None):
    """
    section_names: list
    num_tickets: list (strings or numbers)
    event_main_start, event_main_end: datetime or None
    event_date_time_tickets: list of strings (optional)
    page_name: if 'superboletos' se validan las fechas por-seccion dentro del rango

    Retorna lista de dict con valores normalizados o lanza ValueError con mensaje legible.
    """
    if not section_names or len(section_names) == 0:
        raise ValueError("Debes agregar al menos una sección.")

    sections = []
    for i, name in enumerate(section_names):
        if not is_non_empty_str(name):
            raise ValueError(f"Nombre de sección en posición {i+1} está vacío.")
        # num_tickets puede faltar -> invalid
        if i >= len(num_tickets):
            raise ValueError(f"Falta la cantida de tickets para la sección {name}.")
        try:
            n_raw = num_tickets[i]
            n = int(n_raw) if n_raw not in (None, '') else None
        except Exception:
            raise ValueError(f"Cantidad de tickets inválido para la sección {name}.")
        if n is None:
            raise ValueError(f"Cantidad de tickets vacío para la sección {name}.")
        if n <= 0:
            raise ValueError(f"Cantidad de tickets debe ser mayor a 0 para la sección {name}.")
        if n > 10:
            raise ValueError(f"Cantidad de tickets no puede ser mayor a 10 para la sección {name}.")

        sec = {
            "section_name": name.strip(),
            "num_tickets": n
        }

        # validar fecha por sección si aplica
        if page_name == 'superboletos' and event_date_time_tickets:
            dt_val = event_date_time_tickets[i] if i < len(event_date_time_tickets) else None
            if dt_val:
                dt_parsed = parse_section_datetime_loose(dt_val)
                # validar rango principal
                if event_main_start and event_main_end:
                    # permitir equality inclusive: sección dentro del rango [start, end]
                    if not (event_main_start <= dt_parsed <= event_main_end):
                        raise ValueError(f"La fecha de la sección '{name}' está fuera del rango del evento principal.")
                sec['section_datetime'] = dt_parsed
        sections.append(sec)
    return sections

# ---------- helpers login attempts ----------
def increment_failed_login():
    attempts = session.get('failed_logins', 0) + 1
    session['failed_logins'] = attempts
    return attempts

def reset_failed_login():
    session.pop('failed_logins', None)

def is_locked_out(max_attempts=3):
    return session.get('failed_logins', 0) >= max_attempts
