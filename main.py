from flask import Flask, render_template, request, redirect,  url_for, session, jsonify, abort
from supabase import create_client, Client
from supabase_auth.errors import AuthError
from dotenv import load_dotenv
from datetime import datetime, timezone
import os
from zoneinfo import ZoneInfo
import math
from functools import wraps


## Configurações do Flask e Supabase (inclusive variáveis de ambiente) ##

load_dotenv()
url=os.getenv("SUPABASE_URL")
key=os.getenv("ANON_KEY")
service_key=os.getenv("SERVICE_ROLE_KEY")

supabase_admin = create_client(url,service_key)

app = Flask(__name__)
app.secret_key = os.getenv("secret_key")  
app.config['SUPABASE_URL'] = url
app.config['SUPABASE_KEY'] = key


##Variaveis globais, Filtros e processadores de contexto ##

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

@app.context_processor
def check_sector():
    if "user_id" in session:
        user_id = session["user_id"]
        sector = supabase_admin.auth.admin.get_user_by_id(user_id).user.user_metadata.get("sector")
        return {"sector": sector}
    return {"sector": None}

####### funções auxiliares (Que se repetem em várias rotas ou decorators) ########

def get_user_sector(user_id):
    user = supabase_admin.auth.admin.get_user_by_id(user_id).user
    if user:
        return user.user_metadata.get("sector")
    return None

def required_sector(*sectors):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get("user_id")
            if not user_id:
                return redirect(url_for("login"))
            user_sector = get_user_sector(user_id)
            if user_sector not in sectors:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

## Páginas de login - Compartilham base da "Basic Session" ##

@app.route ('/')
def home():
    if "user" not in session: 
        return redirect(url_for("login"))
    if get_user_sector(session["user_id"]) != "TI":
        return redirect(url_for("all_tickets"))
    return redirect(url_for('dash'))

@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        auth_client: Client = create_client(url, key)

        try:
            response = auth_client.auth.sign_in_with_password({"email": email, "password": password})
        except AuthError:
            return render_template("session/login.html", message="Usuário ou senha inválido.")
        if response.user:
            session["user"] = response.user.email
            session["user_id"] = response.user.id
            session["user_name"] = response.user.user_metadata.get("name")
    if "user" in session: 
        return redirect(url_for("home"))
    return render_template('session/login.html')

@app.route('/forgot_password', methods=["GET","POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            return render_template(
                "session/forgot-password.html",
                message="Enter an email address.",
                message_type="danger",
            )

        auth_client: Client = create_client(url, key)
        try:
            auth_client.auth.reset_password_for_email(
                email,
                {"redirect_to": url_for("reset_password", _external=True)},
            )
        except AuthError:
            return render_template(
                "session/forgot-password.html",
                message="We couldn't send the reset link. Please try again.",
                message_type="danger",
            )

        return render_template(
            "session/forgot-password.html",
            message="If an account uses that email, a password reset link has been sent.",
            message_type="success",
        )
    return render_template('session/forgot-password.html')

@app.route('/reset_password', methods=["GET", "POST"])
def reset_password():
    if request.method == "GET":
        return render_template("session/reset-password.html")

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Invalid reset request."), 400

    access_token = payload.get("access_token")
    refresh_token = payload.get("refresh_token")
    new_password = payload.get("password")
    if (
        not isinstance(access_token, str)
        or len(access_token.split(".")) != 3
        or not isinstance(refresh_token, str)
        or not refresh_token
        or not isinstance(new_password, str)
        or len(new_password) < 6
    ):
        return jsonify(error="O link para redefinição não é válido."), 400

    auth_client: Client = create_client(url, key)
    try:
        auth_client.auth.set_session(access_token, refresh_token)
        auth_client.auth.update_user({"password": new_password})
    except AuthError:
        return jsonify(error="Este link para redefinição é inválido ou expirou. Solicite um novo."), 400

    return jsonify(message="Sua senha foi alterada.")

@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        name = request.form["name"]

        auth_client: Client = create_client(url, key)
        response = auth_client.auth.sign_up(\
            {"email": email, "password": password, "options": {"data": {"name": name}}})
    return render_template('session/register.html')

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

## Páginas da Dashboard (pós-login apenas) - Compartilham a base da "Basic Dash" ##

@app.route('/users')
@required_sector("TI")
def users(requested_page=None):
    count_response = supabase_admin.rpc("get_total_auth_users").execute()
    total_users = count_response.data 

    per_page = 20
    total_pages = math.ceil(total_users / per_page)

    requested_page=1 if requested_page==None else requested_page
    users=[]
    if requested_page > total_pages or requested_page < 1:
        print("Error: # de páginas inválido")
    else:
        users=supabase_admin.auth.admin.list_users(
            page=requested_page,
            per_page=per_page
        )
    personals = []
    for user in users:
        personal={
            "email": user.email,
            "name": user.user_metadata.get("name"),
            "sector": user.user_metadata.get("sector"),
            "status":user.user_metadata.get("status"),
            "started":user.created_at
        }
        personals.append(personal)
    print(personals[0])
    return render_template('it_dash/users.html', personals=personals,request_page=requested_page,total_pages=total_pages)

@app.route('/dash')
@required_sector("TI")
def dash():
    tickets_count = supabase_admin.table('Ticket').select("status").execute()
    print(tickets_count.data)
    count_tickets = {
        "open": len([
            ticket for ticket in tickets_count.data 
            if ticket.get("status") in ["Novo", "Em andamento", "Aguardando"]
        ]),
        "solved": len([
            ticket for ticket in tickets_count.data 
            if ticket.get("status") == "Resolvido"
        ])
    }
    active_users= supabase_admin.auth.admin.list_users()
    count_active_users=0
    for user in active_users:
        if user.user_metadata.get("status") == "Ativo":
            count_active_users += 1
    recent_tickets = supabase_admin.table('Ticket').select("*").order('created_at', desc=True).limit(5).execute()
    return render_template('it_dash/dash.html', count_tickets=count_tickets, count_active_users=count_active_users,recent_tickets=recent_tickets.data)

@app.route('/tickets')
@required_sector("TI")
def tickets():
    row_limit=3
    new=supabase_admin.table('Ticket').select("*").eq("status","Novo").order('created_at', desc=True).limit(row_limit).execute()
    in_progress=supabase_admin.table('Ticket').select("*").eq("status","Em andamento").order('created_at', desc=True).limit(row_limit).execute()
    awaiting_customer=supabase_admin.table('Ticket').select("*").eq("status","Aguardando").order('created_at', desc=True).limit(row_limit).execute()
    solved=supabase_admin.table('Ticket').select("*").eq("status","Resolvido").order('created_at', desc=True).limit(row_limit).execute()
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
        if get_user_sector(session["user_id"]) != "IT":
            return redirect(url_for("all_tickets"))
        return redirect(url_for("ticket",id=ticket_id))
    if get_user_sector(session["user_id"]) != "IT":
        return render_template('it_dash/new_ticket.html',user_name=session["user_name"],user_email=session["user"])
    return render_template('it_dash/new_ticket.html')

## Gestão de Tickets e Chat ao vivo ##

@app.route('/tickets/<id>')
def ticket(id):
    if "user" not in session: 
        return redirect(url_for("login"))
    open_tickets = []
    try:
        open_res = supabase_admin.table('Ticket').select("*").order('created_at', desc=True).execute()
        open_tickets = open_res.data or []
    except Exception:
        pass

    total_abertos = sum(1 for t in open_tickets if t.get('status') != 'Resolvido')
    total_finalizados = len(open_tickets) - total_abertos

    ticket_data = next((t for t in open_tickets if str(t.get('id')) == str(id)), None)
    if not ticket_data:
        try:
            res = supabase_admin.table('Ticket').select("*").eq("id", id).single().execute()
            ticket_data = res.data
        except Exception:
            ticket_data = {'id': id, 'subject': f'Chamado #{id}', 'status': 'Novo', 'name': 'Cliente'}

    messages = []
    try:
        m_res = supabase_admin.table('messages').select("*").eq("ticket_id", str(id)).order('created_at', desc=False).execute()
        messages = m_res.data or []
    except Exception:
        pass

    return render_template(
        'it_dash/open_tickets.html', 
        ticket=ticket_data, 
        open_tickets=open_tickets,
        messages=messages,
        total_abertos=total_abertos,
        total_finalizados=total_finalizados
    )

@app.route('/tickets/<id>/status', methods=['POST'])
def update_ticket_status(id):
    supabase_admin.table('Ticket').update({'status': request.json.get('status')}).eq('id', id).execute()
    return jsonify({'success': True})

@app.route('/api/tickets/<id>')
def api_ticket(id):
    if "user" not in session: 
        return jsonify({'error': 'Não autorizado'}), 401
    try:
        t_res = supabase_admin.table('Ticket').select("*").eq("id", id).single().execute()
        ticket_data = t_res.data
    except Exception:
        ticket_data = {'id': id, 'subject': f'Chamado #{id}', 'status': 'Novo', 'name': 'Cliente'}

    try:
        m_res = supabase_admin.table('messages').select("*").eq("ticket_id", str(id)).order('created_at', desc=False).execute()
        messages = m_res.data or []
    except Exception:
        messages = []

    return jsonify({'ticket': ticket_data, 'messages': messages})

@app.route('/test_chat')
@app.route('/test_chat/<ticket_id>')
def test_chat(ticket_id=None):
    if not ticket_id:
        res = supabase_admin.table('Ticket').insert({'subject': 'Novo Atendimento', 'name': 'Cliente', 'ticket_type': 'Suporte', 'status': 'Novo'}).execute()
        return redirect(url_for('test_chat', ticket_id=res.data[0]['id']))

    try:
        m_res = supabase_admin.table('messages').select("*").eq("ticket_id", str(ticket_id)).order('created_at', desc=False).execute()
        messages = m_res.data or []
    except Exception:
        messages = []
    return render_template('it_dash/test_chat.html', ticket_id=ticket_id, messages=messages)

@app.route('/api/send_message', methods=['POST'])
def send_message_api():
    data = request.json or {}
    ticket_id = data.get('ticket_id')
    content = data.get('content')
    if not ticket_id or not content:
        return jsonify({'error': 'Campos obrigatórios'}), 400

    try:
        supabase_admin.table('messages').insert({
            'ticket_id': str(ticket_id),
            'user_id': str(data.get('user_id', session.get('user_id', 'anon-user'))),
            'user_name': str(data.get('user_name', session.get('user_name', 'Atendente'))),
            'content': content
        }).execute()
    except Exception:
        pass
    return jsonify({'success': True})


@app.route('/tickets/all')
def all_tickets():
    sector_check = get_user_sector(session["user_id"])
    if sector_check == "TI":
        tickets= supabase_admin.table('Ticket').select("*").order('created_at', desc=True).execute()
    else:
        tickets= supabase_admin.table('Ticket').select("*").eq("email", session["user"]).order('created_at', desc=True).execute()
    return render_template('it_dash/all_tickets.html',tickets=tickets.data)

## Base de conhecimento ##

@app.route('/documents')
@required_sector("TI")
def documents():
    documents_data=supabase_admin.table('Documentacao').select("*").execute()
    return render_template('it_dash/documents.html',documents=documents_data.data)

@app.route('/new_document', methods=["GET","POST"])
@required_sector("TI")
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
@required_sector("TI")
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

@app.route('/documents/<id>/delete', methods=['POST'])
@required_sector("TI")
def delete_document(id):
    if "user" not in session: 
        return redirect(url_for("login"))
    supabase_admin.table('Documentacao').delete().eq("id",id).execute()
    return redirect(url_for("documents"))

###########

@app.route('/config', methods=["GET","POST"])
def config():
    if "user" not in session: 
        return redirect(url_for("login"))
    if request.method=="POST":
        name=request.form["name"]
        email=request.form["email"]
        phone=request.form["phone"]
        sector=request.form["sector"]
        supabase_admin.auth.admin.update_user_by_id(session["user_id"],{
            "email": email,
            "user_metadata": {
                "name": name,
                "phone": phone,
                "sector": sector
            }
        })
        session["user_name"]=name
    user_data=supabase_admin.auth.admin.get_user_by_id(session["user_id"]).user.user_metadata
    personalinfo={
        "email": user_data.get("email"),
        "fullname": user_data.get("name"),
        "phone": user_data.get("phone", ""),
        "sector": user_data.get("sector", "")
    }
    return render_template('it_dash/config.html', personalinfo=personalinfo)

@app.route('/change_password', methods=["POST"])
def change_password():
    if "user" not in session:
        return redirect(url_for("login"))
    new_password=request.form["newPassword"]
    current_password=request.form["oldPassword"]
    auth_client: Client = create_client(url, key)
    try:
        auth_client.auth.sign_in_with_password({"email":session["user"],"password":current_password})
        auth_client.auth.update_user({"password": new_password})
    except AuthError:
        return render_template("it_dash/config.html",message="Senha atual incorreta.")
    return redirect(url_for("config"))

#Erros

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

#Para testes
@app.route('/teste')
def teste():
    return render_template('errors/500.html')

#Execução
if __name__ == '__main__':
    app.run(debug=True)