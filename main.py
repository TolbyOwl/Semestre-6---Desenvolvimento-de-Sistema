from flask import Flask, render_template, request, redirect,  url_for, session, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
import os

#load_dotenv() initilizando o arquivo .env com as credenciais do supabase
url=os.getenv("SUPABASE_URL")
key=os.getenv("ANON_KEY")

supabase: Client = create_client(url, key)
supabase_admin = create_client(url, os.getenv("SERVICE_ROLE_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("secret_key")  

#Páginas de login

@app.context_processor
def set_global_html_variable_values():
    user_name = session.get("user_name")
    first_name = user_name.split()[0] if user_name else None
    return {"username": first_name}

@app.route ('/')
def default():
    return redirect(url_for("login"))

@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        except:
            return render_template("login.html", message="Usuário ou senha inválido")
        if response.user:
            session["user"] = response.user.email
            session["user_id"] = response.user.id
            session["user_name"] = response.user.user_metadata.get("name")
    if "user" in session: 
        return redirect(url_for("dash"))
    return render_template('session/login.html')

@app.route('/forgot_password', methods=["GET","POST"])
def forgot_password():
    return render_template('session/forgot-password.html')

@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        name = request.form["name"]

        response = supabase.auth.sign_up(\
            {"email": email, "password": password, "options": {"data": {"name": name}}})
    return render_template('session/register.html')

@app.route("/logout")
def logout():
    session.pop("user", None)
    supabase.auth.sign_out()
    return redirect(url_for("login"))

#Páginas da Dashboard (pós-login apenas)

@app.route('/users')
def users():
    if "user" not in session: 
        return redirect(url_for("login"))
    return render_template('it_dash/users.html')

@app.route('/dash')
def dash():
    if "user" not in session: 
        return redirect(url_for("login"))
    return render_template('it_dash/dash.html')

@app.route('/new_ticket')
def new_ticket():
    if "user" not in session: 
        return redirect(url_for("login"))
    return render_template('it_dash/new_ticket.html')

@app.route('/tickets')
def tickets():
    if "user" not in session: 
        return redirect(url_for("login"))
    return render_template('it_dash/tickets.html')

@app.route('/tickets/<id>')
def ticket(id):
    pass

@app.route('/documents')
def documents():
    if "user" not in session: 
        return redirect(url_for("login"))
    return render_template('it_dash/documents.html')

@app.route('/new_document')
def new_document():
    if "user" not in session: 
        return redirect(url_for("login"))
    return render_template('it_dash/new_document.html')

@app.route('/documents/<id>')
def document(id):
    pass

@app.route('/config')
def config():
    if "user" not in session: 
        return redirect(url_for("login"))
    return render_template('it_dash/config.html',username=session["user_fname"])

#Erros

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


#Funções que se repetem:


#Execução
if __name__ == '__main__':
    app.run(debug=True)