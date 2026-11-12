# Sistema de Chamados de TI (Helpdesk)

Projeto desenvolvido para a matéria de Projeto de Extensão em Desenvolvimento de Sistemas (6º Semestre).

O objetivo do sistema é facilitar o suporte técnico interno, permitindo que usuários abram chamados para relatar problemas ou dúvidas e que a equipe de TI faça o gerenciamento, acompanhamento de status e troca de mensagens sobre cada ticket.

---

## Funcionalidades

- **Autenticação:** Login, cadastro e recuperação de senha.
- **Controle de Acesso:** Telas diferentes dependendo se o usuário é do setor de TI ou solicitante comum.
- **Chamados (Tickets):**
  - Abertura de chamados com nível de prioridade.
  - Acompanhamento do status (_Novo_, _Em andamento_, _Resolvido_).
  - Chat interno em cada ticket para comunicação entre solicitante e técnico.
- **Painel de TI (Dashboard):** Visão geral da quantidade de chamados e métricas de atendimento.

---

## Tecnologias

- **Backend:** Python + Flask
- **Banco de Dados e Auth:** Supabase (PostgreSQL)
- **Frontend:** HTML, CSS, JavaScript (Bootstrap)
- **Editor de texto:** Summernote

---

## Como rodar o projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/SEU_USUARIO/Semestre-6---Desenvolvimento-de-Sistema.git
cd Semestre-6---Desenvolvimento-de-Sistema
```

### 2. Ambiente virtual

PowerShell ou Prompt de Comando:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instalar as dependências

```bash
pip install flask supabase python-dotenv
```

### 4. Configurar as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com as credenciais do Supabase:

```env
SUPABASE_URL="sua-url-do-supabase"
SERVICE_ROLE_KEY="sua-service-role-key"
ANON_KEY="sua-anon-key"
secret_key="sua-chave-secreta-flask"
```

### 5. Rodar a aplicação

```bash
python main.py
```

Acesse no navegador: **`http://127.0.0.1:5000`**
