from flask import Flask, render_template, request, redirect,  url_for, session, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv() #initilizando o arquivo .env com as credenciais do supabase
url=os.getenv("SUPABASE_URL")
key=os.getenv("ANON_KEY")

supabase: Client = create_client(url, key)
supabase_admin = create_client(url, os.getenv("SERVICE_ROLE_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("secret_key")  

@app.route('/')
def home():
    return #Espaço para tela inicial ou de login, dependendo da sessão iniciada