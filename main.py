from flask import Flask, render_template, request, redirect,  url_for, session, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timezone
import os
from zoneinfo import ZoneInfo

#load_dotenv() # inicializando o arquivo .env com as credenciais do supabase
url=os.getenv("SUPABASE_URL")
key=os.getenv("ANON_KEY")

supabase: Client = create_client(url, key)
supabase_admin = create_client(url, os.getenv("SERVICE_ROLE_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("secret_key")  

#Variaveis globais

SAO_PAULO_TIMEZONE = ZoneInfo("America/Sao_Paulo")

insert_data=None

@app.template_filter("sao_paulo_datetime")
def format_sao_paulo_datetime(value):
    if not value:
        return ""
    
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(SAO_PAULO_TIMEZONE).strftime("%d/%m/%Y - %H:%M")

@app.context_processor
def set_global_html_variable_values():
    user_name = session.get("user_name")
    first_name = user_name.split()[0] if user_name else None
    return {"username": first_name}

#Páginas de login

@app.route ('/')
def home():
    if "user" not in session: 
        return redirect(url_for("login"))
    return render_template('it_dash/dash.html')

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

@app.route('/tickets')
def tickets():
    if "user" not in session: 
        return redirect(url_for("login"))
    new=supabase_admin.table('Ticket').select("*").eq("status","Novo").execute()
    in_progress=supabase_admin.table('Ticket').select("*").eq("status","Em andamento").order('created_at', desc=True).execute()
    awaiting_customer=supabase_admin.table('Ticket').select("*").eq("status","Aguardando").execute()
    solved=supabase_admin.table('Ticket').select("*").eq("status","Resolvido").execute()
    return render_template('it_dash/tickets.html',new=new.data, in_progress=in_progress.data, awaiting_customer=awaiting_customer.data,solved=solved.data)

@app.route('/new_ticket',methods=["GET","POST"])
def new_ticket():
    if "user" not in session: 
        return redirect(url_for("login"))
    if request.method == "POST":
        subject = request.form["subject"]
        name = request.form["name"]
        email = request.form["email"]
        ticket_type = request.form["ticket_type"]
        priority = request.form["priority"]
        description = request.form["description"]
        insert_data=(\
            supabase_admin.table('Ticket').insert({'subject': subject, 'name': name,\
            'email': email, 'ticket_type': ticket_type, 'priority' : priority, 'description' : description}).select().execute()\
                )
        print(insert_data)
        ticket_id=insert_data.data[0].get("id")
        return redirect(url_for("ticket",id=ticket_id))
    return render_template('it_dash/new_ticket.html')

@app.route('/tickets/<id>')
def ticket(id):
    if "user" not in session: 
        return redirect(url_for("login"))
    response = supabase_admin.table('Ticket').select("*").eq("id",id).single().execute()
    if not response.data:
        return render_template("errors/404.html"), 404
    return render_template('it_dash/open_tickets.html')

#Base de conhecimento

@app.route('/documents')
def documents():
    if "user" not in session: 
        return redirect(url_for("login"))
    documents_data=supabase_admin.table('Documentacao').select("*").execute()
    return render_template('it_dash/documents.html',documents=documents_data.data)

@app.route('/new_document', methods=["GET","POST"])
def new_document():
    if "user" not in session: 
        return redirect(url_for("login"))
    if request.method == "POST":
        subject = request.form["subject"]
        tag = request.form["tag"]
        content = request.form["editordata"]
        response=(\
            supabase_admin.table('Documentacao').insert({'subject': subject, 'tag': tag,\
            'content': content}).select().execute()\
                )
        document_id=response.data[0].get("id")
        return redirect(url_for("document",id=document_id))
    return render_template('it_dash/new_document.html')

@app.route('/documents/<id>', methods=["GET","POST"])
def document(id):
    if "user" not in session: 
        return redirect(url_for("login"))
    response = supabase_admin.table('Documentacao').select("*").eq("id",id).single().execute()
    if not response.data:
        return render_template("errors/404.html"), 404
    if request.method == "POST":
        subject = request.form["subject"]
        tag = request.form["tag"]
        content = request.form["editordata"]
        response=(\
            supabase_admin.table('Documentacao').update({'subject': subject, 'tag': tag,\
            'content': content}).eq("id",id).execute())
        return redirect(url_for("document",id=id))
    return render_template('it_dash/open_document.html',document=response.data)

###########

@app.route('/config')
def config():
    if "user" not in session: 
        return redirect(url_for("login"))
    return render_template('it_dash/config.html')

#Erros

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


#Para testes
@app.route('/teste')
def teste():
    return render_template('it_dash/open_tickets.html')


#Execução
if __name__ == '__main__':
    app.run(debug=True)