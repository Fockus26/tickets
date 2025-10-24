import json, os
from flask import request, jsonify
from flask_restful import Resource, reqparse
from models.ticket import Ticket
from extensions import db
from utils.validators import is_hex32, is_alphanumeric

def json_error(message, code=400):
    return jsonify({"status": "error", "message": message}), code

def json_success(message, code=200):
    return jsonify({"status": "success", "message": message}), code

class GetTickets(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('api_key', type=str, required=True, location='args')
        self.reqparse.add_argument('page', type=str, required=True, location='args')
        self.reqparse.add_argument('id_event', type=int, required=False, location='args')
        self.reqparse.add_argument('id_ticket', type=int, required=False, location='args')

    def get(self):
        args = self.reqparse.parse_args()        
        api_key = args['api_key']
        page = args['page'].lower()
        event_id = args['id_event']
        ticket_id = args['id_ticket']

        if not is_hex32(api_key) or api_key != os.getenv('API_KEY'):
            return json_error('Unauthorized access', 401)

        # validar que id_event e id_ticket existan en la BD si están presentes
        if ticket_id is not None:
            ticket = Ticket.query.get(ticket_id)
            if not ticket:
                return json_error('Ticket not found', 404)
            tickets = [ticket]
        else:
            tickets = Ticket.query.filter_by(page_name=page).all()

        # cuando vienen ambos id_event y id_ticket hacemos filtro puntual
        if event_id is not None and ticket_id is not None:
            ticket = tickets[0] if tickets else None
            if not ticket:
                return json_error('Ticket not found', 404)
            sections = json.loads(ticket.tickets_data)
            filtered_sections = [section for section in sections if not section.get("is_purchase", False)]
            for filtered_section in filtered_sections:
                if event_id == filtered_section.get('section_id'):
                    return jsonify(filtered_section)
            return json_error('Section not found', 404)
        else:
            tickets_data = []
            for ticket in tickets:
                sections = json.loads(ticket.tickets_data)
                filtered_sections = [section for section in sections if not section.get("is_purchase", False)]
                if filtered_sections:
                    ticket_info = {
                        'id': ticket.id,
                        'page_name': ticket.page_name,
                        'concert_name': ticket.concert_name,
                        'event_name': ticket.event_name,
                        'event_day': ticket.event_day,
                        'event_month': ticket.event_month,
                        'event_time': ticket.event_time,
                        'tickets_data': filtered_sections
                    }
                    tickets_data.append(ticket_info)
            return jsonify({'tickets': tickets_data})

class BuyTicket(Resource):
    def post(self):
        api_key = request.args.get('api_key')
        ticket_id = request.args.get('id_ticket', type=int)
        event_id = request.args.get('id_event', type=int)

        if not is_hex32(api_key) or api_key != os.getenv('API_KEY'):
            return json_error("Unauthorized access", 401)

        if ticket_id is None or event_id is None:
            return json_error("id_ticket and id_event are required", 400)

        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return json_error("Ticket not found", 404)

        tickets_data = json.loads(ticket.tickets_data)
        section_found = False

        for section in tickets_data:
            if section.get('section_id') == event_id:
                section_found = True
                if section.get('is_purchase', False):
                    return json_error("Section already purchased", 400)
                section['is_purchase'] = True
                break

        if not section_found:
            return json_error("Section not found in ticket", 404)

        ticket.tickets_data = json.dumps(tickets_data)
        db.session.commit()
        return json_success("Ticket updated successfully")

class UpdateTicket(Resource):
    def post(self):
        api_key = request.args.get('api_key')
        ticket_id = request.args.get('id_ticket', type=int)
        event_id = request.args.get('id_event', type=int)

        verification_code = request.form.get('verification')

        if not is_hex32(api_key) or api_key != os.getenv('API_KEY'):
            return json_error("Unauthorized access", 401)

        if ticket_id is None or event_id is None:
            return json_error("id_ticket and id_event are required", 400)

        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return json_error("Ticket not found", 404)

        tickets_data = json.loads(ticket.tickets_data)
        section_found = False

        for section in tickets_data:
            if section.get('section_id') == event_id:
                section_found = True
                if section.get('is_purchase', False):
                    return json_error("Cannot update a purchased section", 400)
                if verification_code:
                    if not is_alphanumeric(verification_code):
                        return json_error("verification_code must be alphanumeric", 400)
                    section['verification_code'] = verification_code
                break

        if not section_found:
            return json_error("Section not found in ticket", 404)

        ticket.tickets_data = json.dumps(tickets_data)
        db.session.commit()
        return json_success("Ticket updated successfully")

def register_api_routes(api):
    api.add_resource(GetTickets, '/get_tickets')
    api.add_resource(BuyTicket, '/buy_ticket')
    api.add_resource(UpdateTicket, '/update_ticket')
