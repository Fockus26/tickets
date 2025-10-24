from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from extensions import db
from models.ticket import Ticket
from utils.decorators import login_required
from utils.helpers import remove_accents
from utils.validators import (
    validate_event_range, validate_sections, is_max_length, is_non_empty_str, is_alphanumeric
)
import json, datetime

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def home():
    # Si no está logueado, mostrar login
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    tickets_ingresados = []
    tickets_completados = []

    # Obtener todos los tickets
    all_tickets = Ticket.query.all()

    # Función auxiliar para obtener una clave de orden usable (año ficticio)
    month_map = {
        'ene': 1, 'enero': 1,
        'feb': 2, 'febrero': 2,
        'mar': 3, 'marzo': 3,
        'abr': 4, 'abril': 4,
        'may': 5, 'mayo': 5,
        'jun': 6, 'junio': 6,
        'jul': 7, 'julio': 7,
        'ago': 8, 'agosto': 8,
        'sep': 9, 'septiembre': 9,
        'oct': 10, 'octubre': 10,
        'nov': 11, 'noviembre': 11,
        'dic': 12, 'diciembre': 12
    }

    def ticket_sort_key(ticket):
        try:
            month_raw = (ticket.event_month or '').strip().lower()
            month_num = month_map.get(month_raw[:3], month_map.get(month_raw, 12))
            days = ticket.event_day if isinstance(ticket.event_day, (list, tuple)) else [ticket.event_day]
            day = min(int(d) for d in days) if days else 31
            # usar hora si está disponible
            try:
                time_parts = ticket.event_time.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            except Exception:
                hour = 0; minute = 0
            # Construir tupla (mes, dia, hora, min) para ordenar
            return (month_num, day, hour, minute, ticket.id)
        except Exception:
            return (99, 99, 99, 99, ticket.id)

    # Clasificar primero en listas segun compra
    for ticket in all_tickets:
        sections = json.loads(ticket.tickets_data)
        if sections and all(section.get("is_purchase", False) for section in sections):
            tickets_completados.append(ticket)
        else:
            tickets_ingresados.append(ticket)

    # Ordenar por fecha (más temprana primero)
    tickets_ingresados.sort(key=ticket_sort_key)
    tickets_completados.sort(key=ticket_sort_key)

    return render_template(
        "dashboard.html",
        tickets_ingresados=tickets_ingresados,
        tickets_completados=tickets_completados
    )

@web_bp.route('/add_ticket', methods=['GET', 'POST'])
@login_required
def add_ticket():
    if request.method == "GET":
        source = request.args.get('source', 'ticketmaster')
        return render_template("add_ticket.html", source=source)

    # POST -> crear ticket
    concert_name = request.form.get('concert_name', '')
    event_name = request.form.get('event_name', '')

    # limites de longitud que pediste
    if not is_non_empty_str(concert_name) or not is_max_length(concert_name, 100):
        flash('El concierto es requerido y debe tener máximo 100 caracteres.')
        return redirect(url_for('web.add_ticket'))
    if not is_non_empty_str(event_name) or not is_max_length(event_name, 100):
        flash('El evento es requerido y debe tener máximo 100 caracteres.')
        return redirect(url_for('web.add_ticket'))

    concert_name = remove_accents(concert_name)
    event_name = remove_accents(event_name)

    page_name = request.form.get('page_name') 
    if not page_name:
        flash('Selecciona la pagina (ticketmaster o superboletos).')
        return redirect(url_for('web.add_ticket'))

    event_date_time = request.form.get('event_date_range') or ''
    # REQUERIMOS formato YYYY-MM-DDTHH:MM y fecha futura
    try:
        start_dt, end_dt = validate_event_range(event_date_time)
    except Exception as e:
        flash(str(e))
        return redirect(url_for('web.add_ticket'))

    # month translation (igual que antes)
    if page_name == "ticketmaster":
        month_translation = {
            'Jan': 'Ene', 'Feb': 'Feb', 'Mar': 'Mar', 'Apr': 'Abr', 'May': 'May', 'Jun': 'Jun',
            'Jul': 'Jul', 'Aug': 'Ago', 'Sep': 'Sep', 'Oct': 'Oct', 'Nov': 'Nov', 'Dec': 'Dic'
        }
    else:
        month_translation = {
            'Jan': 'Enero', 'Feb': 'Febrero', 'Mar': 'Marzo', 'Apr': 'Abril', 'May': 'Mayo', 'Jun': 'Junio',
            'Jul': 'Julio', 'Aug': 'Agosto', 'Sep': 'Septiembre', 'Oct': 'Octubre', 'Nov': 'Noviembre', 'Dec': 'Diciembre'
        }

    month_part = month_translation.get(start_dt.strftime('%b'), start_dt.strftime('%b'))
    time_part = start_dt.strftime('%H:%M')

    # Obtener secciones y validar
    section_names = request.form.getlist('section_name[]')
    num_tickets = request.form.getlist('num_tickets[]')
    event_dates_time_tickets = request.form.getlist('event_date_time_tickets[]')

    try:
        validated_sections = validate_sections(
            section_names,
            num_tickets,
            event_main_start=start_dt,
            event_main_end=end_dt,
            event_date_time_tickets=event_dates_time_tickets,
            page_name=page_name
        )
    except Exception as e:
        flash(str(e))
        return redirect(url_for('web.add_ticket'))

    # Construir tickets_data (compatibilidad con estructura previa)
    tickets_data = []
    for i, sec in enumerate(validated_sections):
        section_id = i + 1
        num_ticket_value = sec['num_tickets']
        if page_name == "superboletos":
            dt = sec.get('section_datetime')
            day_part2 = str(dt.day) if dt else str(start_dt.day)
            time_part2 = dt.strftime('%H:%M') if dt and dt.time() != datetime.time(0,0) else time_part
            section_data = {
                "section_id": section_id,
                "section_name": sec['section_name'],
                "num_tickets": num_ticket_value,
                "ticket_day": day_part2,
                "ticket_month": month_part,
                "ticket_time": time_part2,
                "is_purchase": False,
                "verification_code": '',
            }
        else:
            is_accurate_search_value = request.form.get(f'is_accurate_search_{section_id}')
            section_data = {
                "section_id": section_id,
                "section_name": sec['section_name'],
                "num_tickets": num_ticket_value,
                "is_purchase": False,
                "is_accurate_search": is_accurate_search_value == "true",
                "verification_code": '',
            }
        tickets_data.append(section_data)

    # Si el rango tiene más de un día, incluir ambos en event_day
    if end_dt.date() != start_dt.date():
        event_day_list = [start_dt.day, end_dt.day]
    else:
        event_day_list = [start_dt.day]

    new_ticket = Ticket(
        concert_name=concert_name,
        event_name=event_name,
        event_day=event_day_list,
        event_month=month_part,
        event_time=time_part,
        page_name=page_name,
        tickets_data=json.dumps(tickets_data)
    )

    db.session.add(new_ticket)
    db.session.commit()
    flash("Ticket Creado")
    return redirect(url_for('web.home'))

@web_bp.route('/edit_ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        flash("El ticket no existe.")
        return redirect(url_for('web.home'))

    if request.method == "POST":
        # Validación: en edición NO se permite ningún campo vacío
        page_name = request.form.get('page_name')
        section_names = request.form.getlist('section_name[]')
        num_tickets = request.form.getlist('num_tickets[]')
        verification_code_ticket = request.form.get('verification_code', '').strip()
        is_purchase_checked = request.form.getlist('section_is_purchase[]')

        # check ticket id corresponde (ya tenemos ticket por id), ahora validar sections
        if not page_name:
            flash('La pagina es requerida.')
            return redirect(url_for('web.edit_ticket', ticket_id=ticket_id))

        # Validar nombres y num_tickets no vacíos y reglas de num_tickets
        try:
            # Para la edición también utilizamos validate_sections
            event_date_time_tickets = request.form.getlist('event_date_time_tickets[]')
            # Determinar rango principal si viene event_date_range
            event_date_range = request.form.get('event_date_range')
            if event_date_range:
                try:
                    start_dt, end_dt = validate_event_range(event_date_range)
                except Exception:
                    # fallback: no se permite edit sin rango válido
                    flash('Fecha de evento inválida en edición.')
                    return redirect(url_for('web.edit_ticket', ticket_id=ticket_id))
            else:
                # si no viene rango, intentar recuperar desde ticket (fallback)
                # esto requiere que ticket.event_day/event_month/event_time existan
                # si no podemos construir un rango, forzamos a no permitir edición de fechas por-seccion fuera
                start_dt = None
                end_dt = None

            validated_sections = validate_sections(
                section_names,
                num_tickets,
                event_main_start=start_dt,
                event_main_end=end_dt,
                event_date_time_tickets=event_date_time_tickets,
                page_name=page_name
            )
        except Exception as e:
            flash(str(e))
            return redirect(url_for('web.edit_ticket', ticket_id=ticket_id))

        # Validar que verification_code sea alfanumérico si viene
        if verification_code_ticket and not verification_code_ticket.isalnum():
            flash('verification_code debe ser alfanumérico.')
            return redirect(url_for('web.edit_ticket', ticket_id=ticket_id))

        # construir secciones respetando existing values
        existing_sections = json.loads(ticket.tickets_data)
        existing_map = {s.get('section_id'): s for s in existing_sections}
        sections_data = []
        checked_set = set(int(x) for x in is_purchase_checked) if is_purchase_checked else set()

        for i, sec in enumerate(validated_sections):
            sec_id = i + 1
            num_ticket_value = sec['num_tickets']
            existing = existing_map.get(sec_id, {})

            # no permitir marcar compra si num_tickets == 0 (ya validado >0)
            is_purchase = sec_id in checked_set and num_ticket_value > 0

            section_obj = {
                "section_id": sec_id,
                "section_name": sec['section_name'],
                "num_tickets": num_ticket_value,
                "is_purchase": is_purchase,
                # preservar is_accurate_search si existe
                "is_accurate_search": existing.get('is_accurate_search', False),
                # verification_code a nivel ticket aplicado a cada sección
                "verification_code": verification_code_ticket or existing.get('verification_code', '')
            }

            # manejar campos de superboletos si aplican (conservando datos existentes si no vienen)
            if page_name == 'superboletos':
                dt_val = request.form.getlist('event_date_time_tickets[]')
                dt_raw = dt_val[i] if i < len(dt_val) else None
                if dt_raw:
                    try:
                        # validar rango principal ya hecho
                        # parse_section_datetime_loose usado en validate_sections, así tenemos la certeza
                        section_obj['ticket_day'] = str(sec.get('section_datetime').day) if sec.get('section_datetime') else existing.get('ticket_day')
                        section_obj['ticket_month'] = ticket.event_month if ticket.event_month else existing.get('ticket_month')
                        section_obj['ticket_time'] = sec.get('section_datetime').strftime('%H:%M') if sec.get('section_datetime') else existing.get('ticket_time')
                    except Exception:
                        # fallback: preservar
                        if existing.get('ticket_day') is not None:
                            section_obj['ticket_day'] = existing.get('ticket_day')
                        if existing.get('ticket_month') is not None:
                            section_obj['ticket_month'] = existing.get('ticket_month')
                        if existing.get('ticket_time') is not None:
                            section_obj['ticket_time'] = existing.get('ticket_time')
                else:
                    # preservar
                    if existing.get('ticket_day') is not None:
                        section_obj['ticket_day'] = existing.get('ticket_day')
                    if existing.get('ticket_month') is not None:
                        section_obj['ticket_month'] = existing.get('ticket_month')
                    if existing.get('ticket_time') is not None:
                        section_obj['ticket_time'] = existing.get('ticket_time')
            else:
                # preservar campos superboletos si existen
                if existing.get('ticket_day') is not None:
                    section_obj['ticket_day'] = existing.get('ticket_day')
                if existing.get('ticket_month') is not None:
                    section_obj['ticket_month'] = existing.get('ticket_month')
                if existing.get('ticket_time') is not None:
                    section_obj['ticket_time'] = existing.get('ticket_time')

            sections_data.append(section_obj)

        # actualizar tickets_data y campos generales: NO permitir campos vacíos en edición
        concert_name = request.form.get('concert_name', '').strip()
        event_name = request.form.get('event_name', '').strip()
        if not concert_name or not event_name:
            flash('concert_name y event_name son requeridos en edición y no pueden estar vacíos.')
            return redirect(url_for('web.edit_ticket', ticket_id=ticket_id))

        ticket.tickets_data = json.dumps(sections_data)
        ticket.page_name = page_name
        ticket.concert_name = concert_name
        ticket.event_name = event_name

        # manejar event_date_range si viene
        event_date_range = request.form.get('event_date_range')
        if event_date_range:
            try:
                parsed_start, parsed_end = validate_event_range(event_date_range)
                if parsed_end.date() != parsed_start.date():
                    ticket.event_day = [parsed_start.day, parsed_end.day]
                else:
                    ticket.event_day = [parsed_start.day]
                months_full = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
                ticket.event_month = months_full[parsed_start.month - 1]
                ticket.event_time = parsed_start.strftime('%H:%M')
            except Exception:
                # si no puede parsear no actualizamos el campo general
                pass

        db.session.commit()
        flash("Ticket Actualizado")
        return redirect(url_for('web.home'))

    else:
        # GET -> renderizar formulario con valores actuales (mantener tu lógica previa)
        sections = json.loads(ticket.tickets_data)
        # ... (mantener lógica previa para construir event_date_value y section_dt_values)
        # no la incluyo completa aquí; mantén tu código anterior para GET
        # pero asegúrate de usar same month_to_num mapping que ya tenías.
        current_year = datetime.datetime.now().year
        month_to_num = {
            'ene': '01', 'enero': '01',
            'feb': '02', 'febrero': '02',
            'mar': '03', 'marzo': '03',
            'abr': '04', 'abril': '04',
            'may': '05', 'mayo': '05',
            'jun': '06', 'junio': '06',
            'jul': '07', 'julio': '07',
            'ago': '08', 'agosto': '08',
            'sep': '09', 'septiembre': '09',
            'oct': '10', 'octubre': '10',
            'nov': '11', 'noviembre': '11',
            'dic': '12', 'diciembre': '12'
        }

        event_date_value = ''
        try:
            if ticket.event_day:
                day_val = ticket.event_day[0] if isinstance(ticket.event_day, (list, tuple)) else ticket.event_day
                month_raw = (ticket.event_month or '').strip().lower()
                month_num = month_to_num.get(month_raw[:3], month_to_num.get(month_raw, '01'))
                event_date_value = f"{current_year}-{month_num}-{int(day_val):02d}"
        except Exception:
            event_date_value = ''

        section_dt_values = []
        for sec in sections:
            s_dt = ''
            try:
                td = sec.get('ticket_day')
                tm = sec.get('ticket_month')
                tt = sec.get('ticket_time', '') or ''
                if td and tm:
                    month_num = month_to_num.get((tm or '').strip()[:3].lower(), month_to_num.get((tm or '').strip().lower(), '01'))
                    if tt:
                        s_dt = f"{current_year}-{month_num}-{int(td):02d}T{tt}"
                    else:
                        s_dt = f"{current_year}-{month_num}-{int(td):02d}"
                else:
                    s_dt = ''
            except Exception:
                s_dt = ''
            section_dt_values.append(s_dt)

        return render_template('edit_ticket.html',
                               ticket=ticket,
                               sections=sections,
                               ticket_id=ticket.id,
                               current_year=current_year,
                               event_date_value=event_date_value,
                               section_dt_values=section_dt_values)

@web_bp.route('/delete_ticket/<int:ticket_id>', methods=['POST'])
@login_required
def delete_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    db.session.delete(ticket)
    db.session.commit()
    flash('Ticket eliminado')
    return redirect(url_for('web.home'))
