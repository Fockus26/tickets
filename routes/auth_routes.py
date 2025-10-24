# routes/auth_routes.py
from flask import render_template, redirect, url_for, flash, request, session, Blueprint
import os
from utils.validators import is_username_valid, is_password_valid, increment_failed_login, reset_failed_login, is_locked_out

auth_bp = Blueprint('auth', __name__)

MAX_LOGIN_ATTEMPTS = 3

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('web.home'))

    # lockout check
    if is_locked_out(MAX_LOGIN_ATTEMPTS):
        flash('Has alcanzado el máximo de intentos. Intenta más tarde.')
        return render_template('login.html')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Validar formato antes de comparar con env
        if not is_username_valid(username):
            flash('Usuario inválido: debe tener entre 6 y 24 caracteres.')
            increment_failed_login()
            return render_template('login.html')

        if not is_password_valid(password):
            flash('Contraseña inválida: mínimo 8 caracteres, 1 número, 1 mayúscula, 1 minúscula y 1 carácter especial.')
            increment_failed_login()
            return render_template('login.html')

        if username == os.getenv('ADMIN_USER') and password == os.getenv('ADMIN_PASS'):
            reset_failed_login()
            session['logged_in'] = True
            return redirect(url_for('web.home'))

        attempts = increment_failed_login()
        if attempts >= MAX_LOGIN_ATTEMPTS:
            flash('Has alcanzado el máximo de intentos. Intenta más tarde.')
        else:
            flash('Credenciales inválidas.')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    reset_failed_login()
    return redirect(url_for('auth.login'))
