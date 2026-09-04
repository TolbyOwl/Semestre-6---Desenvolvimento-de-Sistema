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

@app.route('/login')
def login():
    return render_template('session/login.html')

@app.route('/forgot-password')
def forgot_password():
    return render_template('session/forgot-password.html')

@app.route('/register')
def register():
    return render_template('session/register.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

#Execução
if __name__ == '__main__':
    app.run(debug=True)