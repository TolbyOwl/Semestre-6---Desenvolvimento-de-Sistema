from flask import Flask, render_template, request, redirect,  url_for, session, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
import os

#load_dotenv() initilizando o arquivo .env com as credenciais do supabase
# url=os.getenv("SUPABASE_URL")
# key=os.getenv("ANON_KEY")

# supabase: Client = create_client(url, key)
# supabase_admin = create_client(url, os.getenv("SERVICE_ROLE_KEY"))

app = Flask(__name__)
# app.secret_key = os.getenv("secret_key")  


#Páginas de login

@app.route('/login')
def login():
    return render_template('session/login.html')

@app.route('/forgot-password')
def forgot_password():
    return render_template('session/forgot-password.html')

@app.route('/register')
def register():
    return render_template('session/register.html')

#Páginas da Dashboard (pós-login apenas)

@app.route('/users')
def users():
    return render_template('it_dash/users.html')

@app.route('/dash')
def dash():
    return render_template('it_dash/dash.html')


@app.route('/new_ticket')
def new_ticket():
    return render_template('it_dash/new_ticket.html')

@app.route('/tickets')
def tickets():
    return render_template('it_dash/tickets.html')

@app.route('/config')
def config():
    return render_template('it_dash/config.html')

#Erros

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

#Execução
if __name__ == '__main__':
    app.run(debug=True)