import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify
import mysql.connector

app = Flask(__name__)

# ==========================================
# CONFIGURAÇÕES DO BANCO DE DADOS MYSQL
# ==========================================
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""), # Preencha no servidor/PythonAnywhere
    "database": os.environ.get("DB_NAME", "modulo2_extensionista")
}

# ==========================================
# CONFIGURAÇÕES DE E-MAIL (SMTP)
# ==========================================
SMTP_ENABLED = False  # Mude para True após preencher seu e-mail e Senha de App
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "seu_email@gmail.com"
SMTP_PASSWORD = "sua_senha_de_app_google"


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def enviar_notificacao_email(destinatario_email, nome_aluno, titulo_projeto, nome_grupo, orientador):
    assunto = f"Convite de Projeto Extensionista: {titulo_projeto}"
    corpo = f"""
Olá, {nome_aluno}!

Você foi incluído(a) no grupo "{nome_grupo}" do projeto extensionista:
Projeto: {titulo_projeto}
Orientador(a): {orientador}

Acesse o sistema com seu RA ou E-mail para ACEITAR ou REJEITAR sua participação no projeto.
    """.strip()

    if not SMTP_ENABLED:
        print(f"\n[SIMULAÇÃO DE E-MAIL] Para: {destinatario_email} | Assunto: {assunto}\n{corpo}\n")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = destinatario_email
        msg["Subject"] = assunto
        msg.attach(MIMEText(corpo, "plain", "utf-8"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[E-MAIL ENVIADO] Notificação enviada para {destinatario_email}")
    except Exception as e:
        print(f"[ERRO SMTP] Falha ao enviar e-mail para {destinatario_email}: {e}")


# ==========================================
# ROTA PRINCIPAL DO SITE
# ==========================================
@app.route("/")
def index():
    return render_template("index.html")


# ==========================================
# ROTAS DE AUTENTICAÇÃO E CONTAS
# ==========================================
@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    identifier = data.get("identifier", "").strip().lower()
    senha = data.get("senha", "")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, ra, nome, email, role FROM usuarios WHERE (LOWER(email) = %s OR LOWER(ra) = %s) AND senha = %s",
        (identifier, identifier, senha)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return jsonify({"error": "Credenciais inválidas"}), 401

    return jsonify(user)


@app.route("/api/usuarios", methods=["GET"])
def listar_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, ra, nome, email, role FROM usuarios ORDER BY id ASC")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)


@app.route("/api/usuarios", methods=["POST"])
def criar_usuario():
    data = request.json
    actor_role = data.get("actor_role")
    role = data.get("role")
    ra = data.get("ra", "").strip()
    nome = data.get("nome", "").strip()
    email = data.get("email", "").strip()
    senha = data.get("senha", "").strip()

    # Validação hierárquica no backend
    if actor_role not in ["admin", "coordenador", "orientador"]:
        return jsonify({"error": "Acesso negado"}), 403
    if actor_role == "orientador" and role != "aluno":
        return jsonify({"error": "Orientadores só podem criar contas de Alunos"}), 403
    if actor_role == "coordenador" and role in ["coordenador", "admin"]:
        return jsonify({"error": "Coordenadores só podem criar Orientadores e Alunos"}), 403
    if role == "admin":
        return jsonify({"error": "Não é permitido criar novos administradores"}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO usuarios (ra, nome, email, senha, role) VALUES (%s, %s, %s, %s, %s)",
            (ra, nome, email, senha, role)
        )
        conn.commit()
        new_id = cursor.lastrowid
    except mysql.connector.IntegrityError:
        cursor.close()
        conn.close()
        return jsonify({"error": "Já existe um usuário com este RA ou E-mail."}), 400

    cursor.close()
    conn.close()
    return jsonify({"id": new_id, "ra": ra, "nome": nome, "email": email, "role": role}), 201


@app.route("/api/usuarios/<int:user_id>", methods=["PUT"])
def editar_usuario(user_id):
    data = request.json
    actor_role = data.get("actor_role")
    ra = data.get("ra", "").strip()
    nome = data.get("nome", "").strip()
    email = data.get("email", "").strip()
    senha = data.get("senha", "").strip()
    role = data.get("role")

    if actor_role == "coordenador" and role == "coordenador":
        return jsonify({"error": "Coordenador não pode editar outro Coordenador"}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    if senha:
        cursor.execute(
            "UPDATE usuarios SET ra=%s, nome=%s, email=%s, senha=%s, role=%s WHERE id=%s",
            (ra, nome, email, senha, role, user_id)
        )
    else:
        cursor.execute(
            "UPDATE usuarios SET ra=%s, nome=%s, email=%s, role=%s WHERE id=%s",
            (ra, nome, email, role, user_id)
        )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Usuário atualizado com sucesso"})


@app.route("/api/usuarios/<int:user_id>", methods=["DELETE"])
def deletar_usuario(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = %s AND role != 'admin'", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Usuário removido"})


# ==========================================
# ROTAS DE PROJETOS, GRUPOS E PUBLICAÇÃO
# ==========================================
@app.route("/api/projetos", methods=["GET"])
def listar_projetos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM projetos ORDER BY id DESC")
    projetos = cursor.fetchall()

    for p in projetos:
        p["publicado"] = bool(p["publicado"])
        cursor.execute("SELECT * FROM grupos WHERE projeto_id = %s", (p["id"],))
        grupo = cursor.fetchone()
        if grupo:
            cursor.execute("SELECT id, ra, nome, status_participacao FROM grupo_membros WHERE grupo_id = %s", (grupo["id"],))
            grupo["membros"] = cursor.fetchall()
            p["grupo"] = grupo
        else:
            p["grupo"] = {"id": None, "nome": "", "membros": []}

    cursor.close()
    conn.close()
    return jsonify(projetos)


@app.route("/api/projetos", methods=["POST"])
def criar_projeto():
    data = request.json
    titulo = data.get("titulo")
    setor_externo = data.get("setor_externo")
    areas_atuacao = data.get("areas_atuacao")
    interdisciplinaridade = data.get("interdisciplinaridade")
    orientador_nome = data.get("orientador_nome")
    grupo_nome = data.get("grupo_nome")
    membros = data.get("membros", [])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """INSERT INTO projetos (titulo, setor_externo, areas_atuacao, interdisciplinaridade, status, publicado, orientador_nome)
           VALUES (%s, %s, %s, %s, 'NOVO', FALSE, %s)""",
        (titulo, setor_externo, areas_atuacao, interdisciplinaridade, orientador_nome)
    )
    projeto_id = cursor.lastrowid

    cursor.execute("INSERT INTO grupos (projeto_id, nome) VALUES (%s, %s)", (projeto_id, grupo_nome))
    grupo_id = cursor.lastrowid

    for m in membros:
        ra = m["ra"].strip()
        nome = m["nome"].strip()
        cursor.execute(
            "INSERT INTO grupo_membros (grupo_id, ra, nome, status_participacao) VALUES (%s, %s, %s, 'PENDENTE')",
            (grupo_id, ra, nome)
        )
        # Busca o e-mail do aluno pelo RA para enviar notificação
        cursor.execute("SELECT email, nome FROM usuarios WHERE ra = %s AND role = 'aluno'", (ra,))
        aluno_acc = cursor.fetchone()
        if aluno_acc:
            enviar_notificacao_email(aluno_acc["email"], aluno_acc["nome"], titulo, grupo_nome, orientador_nome)

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"id": projeto_id, "message": "Projeto registrado com sucesso"}), 201


@app.route("/api/projetos/<int:projeto_id>", methods=["PUT"])
def editar_projeto(projeto_id):
    data = request.json
    actor_role = data.get("actor_role")
    if actor_role not in ["admin", "coordenador", "orientador"]:
        return jsonify({"error": "Sem permissão para editar projeto"}), 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if actor_role == "admin" and data.get("orientador_nome"):
        cursor.execute(
            """UPDATE projetos SET titulo=%s, setor_externo=%s, areas_atuacao=%s, interdisciplinaridade=%s, orientador_nome=%s
               WHERE id=%s""",
            (data["titulo"], data["setor_externo"], data["areas_atuacao"], data["interdisciplinaridade"], data["orientador_nome"], projeto_id)
        )
    else:
        cursor.execute(
            """UPDATE projetos SET titulo=%s, setor_externo=%s, areas_atuacao=%s, interdisciplinaridade=%s
               WHERE id=%s""",
            (data["titulo"], data["setor_externo"], data["areas_atuacao"], data["interdisciplinaridade"], projeto_id)
        )

    cursor.execute("SELECT id FROM grupos WHERE projeto_id = %s", (projeto_id,))
    grupo = cursor.fetchone()
    if grupo:
        grupo_id = grupo["id"]
        cursor.execute("UPDATE grupos SET nome = %s WHERE id = %s", (data["grupo_nome"], grupo_id))

        # Captura RAs antigos para notificar apenas os recém-adicionados
        cursor.execute("SELECT ra FROM grupo_membros WHERE grupo_id = %s", (grupo_id,))
        ras_existentes = {row["ra"] for row in cursor.fetchall()}

        cursor.execute("DELETE FROM grupo_membros WHERE grupo_id = %s", (grupo_id,))
        for m in data.get("membros", []):
            ra = m["ra"].strip()
            nome = m["nome"].strip()
            status_part = m.get("status_participacao", "PENDENTE")
            cursor.execute(
                "INSERT INTO grupo_membros (grupo_id, ra, nome, status_participacao) VALUES (%s, %s, %s, %s)",
                (grupo_id, ra, nome, status_part)
            )
            if ra not in ras_existentes:
                cursor.execute("SELECT email, nome FROM usuarios WHERE ra = %s AND role = 'aluno'", (ra,))
                aluno_acc = cursor.fetchone()
                if aluno_acc:
                    enviar_notificacao_email(aluno_acc["email"], aluno_acc["nome"], data["titulo"], data["grupo_nome"], data.get("orientador_nome", "Orientador"))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Projeto atualizado com sucesso"})


@app.route("/api/projetos/<int:projeto_id>/status", methods=["PATCH"])
def alterar_status_projeto(projeto_id):
    data = request.json
    actor_role = data.get("actor_role")
    novo_status = data.get("status")

    # Bloqueio explícito: Aluno NÃO pode alterar status do projeto
    if actor_role in ["aluno", "public"]:
        return jsonify({"error": "Alunos e visitantes não podem alterar o status do projeto"}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE projetos SET status = %s WHERE id = %s", (novo_status, projeto_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Status atualizado"})


@app.route("/api/projetos/<int:projeto_id>/publicar", methods=["PATCH"])
def publicar_projeto(projeto_id):
    data = request.json
    actor_role = data.get("actor_role")
    publicado = bool(data.get("publicado", True))

    if actor_role not in ["admin", "coordenador", "orientador"]:
        return jsonify({"error": "Sem permissão para publicar projeto"}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE projetos SET publicado = %s WHERE id = %s", (publicado, projeto_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Estado de publicação atualizado", "publicado": publicado})


# ==========================================
# ROTAS DO ALUNO (ACEITAR/REJEITAR E EDITAR DADOS PRÓPRIOS)
# ==========================================
@app.route("/api/membros/<int:membro_id>/resposta", methods=["PATCH"])
def responder_convite_aluno(membro_id):
    data = request.json
    status_participacao = data.get("status_participacao")
    if status_participacao not in ["CONFIRMADO", "RECUSADO"]:
        return jsonify({"error": "Status inválido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE grupo_membros SET status_participacao = %s WHERE id = %s", (status_participacao, membro_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Resposta registrada"})


@app.route("/api/membros/<int:membro_id>/aluno-self", methods=["PATCH"])
def editar_dados_proprios_aluno(membro_id):
    data = request.json
    user_id = data.get("user_id")
    novo_nome = data.get("nome", "").strip()
    novo_ra = data.get("ra", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE grupo_membros SET nome = %s, ra = %s WHERE id = %s", (novo_nome, novo_ra, membro_id))
    if user_id:
        cursor.execute("UPDATE usuarios SET nome = %s, ra = %s WHERE id = %s AND role = 'aluno'", (novo_nome, novo_ra, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Dados atualizados"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
