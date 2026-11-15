import os
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, session

import smtplib
try:
    import sib_api_v3_sdk
    from sib_api_v3_sdk.rest import ApiException
except ImportError:
    sib_api_v3_sdk = None
    ApiException = Exception
# A SECRET_KEY é obrigatória e fica guardada no arquivo privado segredos.py.
from segredos import SECRET_KEY

# A integração com a Brevo continua opcional.
try:
    from segredos import BREVO_API_KEY
except ImportError:
    BREVO_API_KEY = ""

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

# Caminho do banco SQLite (criado automaticamente na mesma pasta do app.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "modulo2_extensionista.db")

# ==========================================
# CONFIGURAÇÕES DE E-MAIL (SMTP)
# ==========================================

SMTP_ENABLED = False
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = ""
SMTP_PASSWORD = ""
BREVO_ENABLED = False
SENHA_PROVISORIA_PADRAO = "123456"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Cria as tabelas SQL automaticamente, aplica migrações e insere o Administrador inicial."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ra TEXT NOT NULL UNIQUE,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'coordenador', 'orientador', 'aluno')),
            curso TEXT DEFAULT '',
            primeiro_acesso INTEGER DEFAULT 1,
            tentativas_falhas INTEGER DEFAULT 0,
            bloqueado INTEGER DEFAULT 0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS projetos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            setor_externo TEXT NOT NULL,
            areas_atuacao TEXT NOT NULL,
            interdisciplinaridade TEXT NOT NULL,
            status TEXT DEFAULT 'NOVO',
            publicado INTEGER DEFAULT 0,
            orientador_nome TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS grupos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projeto_id INTEGER NOT NULL UNIQUE,
            nome TEXT NOT NULL,
            FOREIGN KEY (projeto_id) REFERENCES projetos(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS grupo_membros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grupo_id INTEGER NOT NULL,
            ra TEXT NOT NULL,
            nome TEXT NOT NULL,
            status_participacao TEXT DEFAULT 'PENDENTE' CHECK(status_participacao IN ('PENDENTE', 'CONFIRMADO', 'RECUSADO')),
            justificativa_recusa TEXT DEFAULT '',
            FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS pareceres_etica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projeto_id INTEGER NOT NULL UNIQUE,
            status TEXT DEFAULT 'PENDENTE' CHECK(status IN ('PENDENTE', 'APROVADO', 'REPROVADO')),
            parecer TEXT DEFAULT '',
            por TEXT DEFAULT '',
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (projeto_id) REFERENCES projetos(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS pareceres_conselho (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projeto_id INTEGER NOT NULL UNIQUE,
            status TEXT DEFAULT 'PENDENTE' CHECK(status IN ('PENDENTE', 'APROVADO', 'REPROVADO')),
            parecer TEXT DEFAULT '',
            por TEXT DEFAULT '',
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (projeto_id) REFERENCES projetos(id) ON DELETE CASCADE
        );
    """)

    # Migração segura para bancos já existentes
    cursor.execute("PRAGMA table_info(usuarios)")
    colunas_user = [col["name"] for col in cursor.fetchall()]
    if "curso" not in colunas_user:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN curso TEXT DEFAULT ''")
    if "primeiro_acesso" not in colunas_user:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN primeiro_acesso INTEGER DEFAULT 0")
    if "tentativas_falhas" not in colunas_user:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN tentativas_falhas INTEGER DEFAULT 0")
    if "bloqueado" not in colunas_user:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN bloqueado INTEGER DEFAULT 0")

    cursor.execute("PRAGMA table_info(grupo_membros)")
    colunas_membros = [col["name"] for col in cursor.fetchall()]
    if "justificativa_recusa" not in colunas_membros:
        cursor.execute("ALTER TABLE grupo_membros ADD COLUMN justificativa_recusa TEXT DEFAULT ''")

    # Garante pareceres pendentes também para projetos que já existiam antes da atualização.
    cursor.execute("INSERT OR IGNORE INTO pareceres_etica (projeto_id, status) SELECT id, 'PENDENTE' FROM projetos")
    cursor.execute("INSERT OR IGNORE INTO pareceres_conselho (projeto_id, status) SELECT id, 'PENDENTE' FROM projetos")

    # Insere APENAS o Administrador inicial caso ainda não exista
    cursor.execute("SELECT id FROM usuarios WHERE email = ?", ("admin@faccamp.com",))
    if not cursor.fetchone():
        cursor.execute(
            """INSERT INTO usuarios (ra, nome, email, senha, role, curso, primeiro_acesso, tentativas_falhas, bloqueado)
               VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0)""",
            ("ADMIN01", "Administrador FACCAMP", "admin@faccamp.com", "adminhrv2026", "admin", "")
        )

    conn.commit()
    cursor.close()
    conn.close()



def usuario_logado():
    """Obtém a identidade do usuário pela sessão assinada e pelo banco."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT id, ra, nome, email, role, COALESCE(curso, '') AS curso, "
            "COALESCE(primeiro_acesso, 0) AS primeiro_acesso "
            "FROM usuarios WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def exigir_acesso_relatorios():
    usuario = usuario_logado()
    if usuario and usuario["role"] in ("admin", "coordenador", "orientador"):
        return usuario
    return None


def enviar_notificacao_email(destinatario_email, nome_aluno, titulo_projeto, nome_grupo, orientador):
    assunto = f"Convite de Projeto Extensionista: {titulo_projeto}"
    corpo = f"""
Olá, {nome_aluno}!

Você foi incluído(a) no grupo "{nome_grupo}" do projeto extensionista:
Projeto: {titulo_projeto}
Orientador(a): {orientador}

Acesse o sistema com seu RA ou E-mail para ACEITAR ou REJEITAR sua participação no projeto.
    """.strip()

    if SMTP_ENABLED:
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
        except Exception as e:
            print(f"[ERRO SMTP] Falha ao enviar e-mail para {destinatario_email}: {e}")


init_db()


# ==========================================
# ROTA PRINCIPAL DO SITE
# ==========================================
@app.route("/")
def index():
    return render_template("index.html")


# ==========================================
# ROTAS DE AUTENTICAÇÃO, BLOQUEIO E SENHAS
# ==========================================
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    identifier = data.get("identifier", "").strip().lower()
    senha = data.get("senha", "")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, ra, nome, email, senha, role, COALESCE(curso, '') AS curso,
                  COALESCE(primeiro_acesso, 0) AS primeiro_acesso,
                  COALESCE(tentativas_falhas, 0) AS tentativas_falhas,
                  COALESCE(bloqueado, 0) AS bloqueado
           FROM usuarios
           WHERE LOWER(email) = ? OR LOWER(ra) = ?""",
        (identifier, identifier)
    )
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        return jsonify({"error": "Credenciais inválidas."}), 401

    if user["bloqueado"] == 1:
        cursor.close()
        conn.close()
        return jsonify({"error": "Acesso bloqueado após 5 tentativas incorretas. Solicite o desbloqueio a um Coordenador ou Administrador."}), 403

    if user["senha"] != senha:
        if user["role"] == "aluno":
            novas_tentativas = user["tentativas_falhas"] + 1
            if novas_tentativas >= 5:
                cursor.execute(
                    "UPDATE usuarios SET tentativas_falhas = ?, bloqueado = 1 WHERE id = ?",
                    (novas_tentativas, user["id"])
                )
                conn.commit()
                cursor.close()
                conn.close()
                return jsonify({"error": "Você atingiu 5 tentativas incorretas. Seu acesso foi BLOQUEADO. Procure um Coordenador ou Administrador."}), 403
            else:
                restantes = 5 - novas_tentativas
                cursor.execute(
                    "UPDATE usuarios SET tentativas_falhas = ? WHERE id = ?",
                    (novas_tentativas, user["id"])
                )
                conn.commit()
                cursor.close()
                conn.close()
                return jsonify({"error": f"Senha incorreta. Restam {restantes} tentativa(s) antes do bloqueio."}), 401
        else:
            cursor.close()
            conn.close()
            return jsonify({"error": "Credenciais inválidas."}), 401

    cursor.execute("UPDATE usuarios SET tentativas_falhas = 0 WHERE id = ?", (user["id"],))
    conn.commit()
    cursor.close()
    conn.close()

    session.clear()
    session["user_id"] = user["id"]

    return jsonify({
        "id": user["id"],
        "ra": user["ra"],
        "nome": user["nome"],
        "email": user["email"],
        "role": user["role"],
        "curso": user["curso"],
        "primeiro_acesso": bool(user["primeiro_acesso"])
    })



@app.route("/api/session", methods=["GET"])
def verificar_sessao():
    usuario = usuario_logado()
    if not usuario:
        return jsonify({"authenticated": False}), 401
    return jsonify({"authenticated": True, **usuario})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Sessão encerrada."})



@app.route("/api/usuarios/<int:user_id>/alterar-senha", methods=["PATCH"])
def alterar_senha_usuario(user_id):
    data = request.json or {}
    nova_senha = data.get("nova_senha", "").strip()
    senha_atual = data.get("senha_atual", "").strip()
    forcar_primeiro_acesso = bool(data.get("forcar_primeiro_acesso", False))

    if len(nova_senha) < 6 or len(nova_senha) > 18:
        return jsonify({"error": "A nova senha deve ter entre 6 e 18 caracteres."}), 400
    if nova_senha == SENHA_PROVISORIA_PADRAO:
        return jsonify({"error": "A nova senha não pode ser igual à senha provisória (123456)."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT senha FROM usuarios WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return jsonify({"error": "Usuário não encontrado."}), 404

    if not forcar_primeiro_acesso and senha_atual and row["senha"] != senha_atual:
        cursor.close()
        conn.close()
        return jsonify({"error": "A senha atual informada está incorreta."}), 400

    cursor.execute(
        "UPDATE usuarios SET senha = ?, primeiro_acesso = 0, tentativas_falhas = 0 WHERE id = ?",
        (nova_senha, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Senha alterada com sucesso!"})


@app.route("/api/usuarios/<int:user_id>/redefinir-senha", methods=["PATCH"])
def redefinir_senha_provisoria(user_id):
    data = request.json or {}
    actor_role = data.get("actor_role")
    if actor_role != "admin":
        return jsonify({"error": "Apenas o Administrador pode redefinir senhas para a provisória."}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM usuarios WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row or row["role"] == "admin":
        cursor.close()
        conn.close()
        return jsonify({"error": "Operação não permitida para este usuário."}), 400

    cursor.execute(
        "UPDATE usuarios SET senha = ?, primeiro_acesso = 1, tentativas_falhas = 0 WHERE id = ?",
        (SENHA_PROVISORIA_PADRAO, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Senha redefinida para a provisória (123456). O usuário deverá trocá-la no próximo acesso."})


@app.route("/api/usuarios/<int:user_id>/desbloquear", methods=["PATCH"])
def desbloquear_usuario(user_id):
    data = request.json or {}
    actor_role = data.get("actor_role")
    if actor_role not in ["admin", "coordenador"]:
        return jsonify({"error": "Apenas Coordenadores e Administrador podem desbloquear usuários."}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE usuarios SET bloqueado = 0, tentativas_falhas = 0 WHERE id = ?",
        (user_id,)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Usuário desbloqueado com sucesso!"})


@app.route("/api/usuarios", methods=["GET"])
def listar_usuarios():
    actor_role = request.args.get("actor_role", "").strip().lower()

    conn = get_db_connection()
    cursor = conn.cursor()

    if actor_role == "admin":
        cursor.execute(
            """SELECT id, ra, nome, email, role, COALESCE(curso, '') AS curso,
                      COALESCE(primeiro_acesso, 0) AS primeiro_acesso,
                      COALESCE(tentativas_falhas, 0) AS tentativas_falhas,
                      COALESCE(bloqueado, 0) AS bloqueado
               FROM usuarios ORDER BY id ASC"""
        )
    elif actor_role == "coordenador":
        cursor.execute(
            """SELECT id, ra, nome, email, role, COALESCE(curso, '') AS curso,
                      COALESCE(primeiro_acesso, 0) AS primeiro_acesso,
                      COALESCE(tentativas_falhas, 0) AS tentativas_falhas,
                      COALESCE(bloqueado, 0) AS bloqueado
               FROM usuarios WHERE role IN ('orientador', 'aluno') ORDER BY id ASC"""
        )
    elif actor_role == "orientador":
        cursor.execute(
            """SELECT id, ra, nome, email, role, COALESCE(curso, '') AS curso,
                      COALESCE(primeiro_acesso, 0) AS primeiro_acesso,
                      COALESCE(tentativas_falhas, 0) AS tentativas_falhas,
                      COALESCE(bloqueado, 0) AS bloqueado
               FROM usuarios WHERE role = 'aluno' ORDER BY id ASC"""
        )
    else:
        cursor.close()
        conn.close()
        return jsonify([])

    users = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify(users)

@app.route("/api/usuarios", methods=["POST"])
def criar_usuario():
    data = request.get_json(silent=True) or {}
    actor_role = data.get("actor_role")
    role = data.get("role")
    ra = data.get("ra", "").strip()
    nome = data.get("nome", "").strip()
    email = data.get("email", "").strip()
    senha = SENHA_PROVISORIA_PADRAO
    curso = data.get("curso", "").strip() if role == "aluno" else ""

    if actor_role not in ["admin", "coordenador", "orientador"]:
        return jsonify({"error": "Acesso negado"}), 403
    if actor_role == "orientador" and role != "aluno":
        return jsonify({"error": "Orientadores só podem criar contas de Alunos"}), 403
    if actor_role == "coordenador" and role in ["coordenador", "admin"]:
        return jsonify({"error": "Coordenadores só podem criar Orientadores e Alunos"}), 403
    if role == "admin":
        return jsonify({"error": "Não é permitido criar novos administradores"}), 403
    if role == "aluno" and not curso:
        return jsonify({"error": "Selecione o curso ao cadastrar uma conta de Aluno."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO usuarios (ra, nome, email, senha, role, curso, primeiro_acesso, tentativas_falhas, bloqueado)
               VALUES (?, ?, ?, ?, ?, ?, 1, 0, 0)""",
            (ra, nome, email, senha, role, curso)
        )
        conn.commit()
        new_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor.close()
        conn.close()
        return jsonify({"error": "Já existe um usuário com este RA ou E-mail."}), 400

    cursor.close()
    conn.close()

    # Envia o e-mail via Brevo (API HTTP) de forma isolada para não travar o cadastro
    try:
        if not BREVO_ENABLED:
            raise Exception("envio de e-mail desativado")
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = BREVO_API_KEY
        configuration.host = "https://api.brevo.com/v3"
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        subject = "Bem-vindo ao DevTrack System - Suas Credenciais de Acesso"
        html_content = f"""
            <div style="font-family: Arial, sans-serif; color: #333;">
                <h2>Olá, {nome}!</h2>
                <p>Sua conta no DevTrack System foi criada com sucesso.</p>
                <p><b>Seus dados de acesso:</b></p>
                <ul>
                    <li><b>RA:</b> {ra}</li>
                    <li><b>E-mail:</b> {email}</li>
                    <li><b>Senha Provisória:</b> {SENHA_PROVISORIA_PADRAO}</li>
                </ul>
                <p>Recomendamos que altere a sua senha após o primeiro acesso.</p>
                <p>Atenciosamente,<br>Equipa do DevTrack System</p>
            </div>
        """

        sender = {"name": "DevTrack System", "email": "victor.victorhollanda.hollanda@gmail.com"}
        to = [{"email": email}]

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to,
            html_content=html_content,
            sender=sender,
            subject=subject
        )

        api_instance.send_transac_email(send_smtp_email)
    except Exception as e:
        print(f"Erro ao enviar e-mail via Brevo: {e}")

    return jsonify({"id": new_id, "ra": ra, "name": nome, "email": email, "role": role, "curso": curso})

@app.route("/api/usuarios/<int:user_id>", methods=["DELETE"])
def deletar_usuario(user_id):
    data = request.json or {}
    actor_role = data.get("actor_role", "")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM usuarios WHERE id = ?", (user_id,))
    target = cursor.fetchone()
    if not target or target["role"] == "admin":
        cursor.close()
        conn.close()
        return jsonify({"error": "Operação não permitida."}), 403

    if actor_role == "coordenador" and target["role"] not in ["orientador", "aluno"]:
        cursor.close()
        conn.close()
        return jsonify({"error": "Coordenadores só podem remover Orientadores e Alunos."}), 403
    if actor_role == "orientador" and target["role"] != "aluno":
        cursor.close()
        conn.close()
        return jsonify({"error": "Orientadores só podem remover contas de Alunos."}), 403
    if actor_role not in ["admin", "coordenador", "orientador"]:
        cursor.close()
        conn.close()
        return jsonify({"error": "Sem permissão."}), 403

    cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
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
    cursor = conn.cursor()

    usuario = usuario_logado()
    if usuario and usuario["role"] in ("admin", "coordenador", "orientador"):
        cursor.execute("SELECT * FROM projetos ORDER BY id DESC")
    elif usuario and usuario["role"] == "aluno":
        cursor.execute(
            """SELECT DISTINCT p.* FROM projetos p
               LEFT JOIN grupos g ON g.projeto_id = p.id
               LEFT JOIN grupo_membros gm ON gm.grupo_id = g.id
               WHERE p.publicado = 1 OR LOWER(gm.ra) = LOWER(?)
               ORDER BY p.id DESC""",
            (usuario["ra"],)
        )
    else:
        cursor.execute("SELECT * FROM projetos WHERE publicado = 1 ORDER BY id DESC")
    projetos = [dict(row) for row in cursor.fetchall()]

    for p in projetos:
        p["publicado"] = bool(p["publicado"])
        cursor.execute("SELECT * FROM grupos WHERE projeto_id = ?", (p["id"],))
        grupo_row = cursor.fetchone()
        if grupo_row:
            grupo = dict(grupo_row)
            cursor.execute(
                """SELECT id, ra, nome, status_participacao, COALESCE(justificativa_recusa, '') AS justificativa_recusa
                   FROM grupo_membros WHERE grupo_id = ?""",
                (grupo["id"],)
            )
            grupo["membros"] = [dict(m) for m in cursor.fetchall()]
            p["grupo"] = grupo
        else:
            p["grupo"] = {"id": None, "nome": "", "membros": []}

        cursor.execute("SELECT status, parecer, por, atualizado_em FROM pareceres_etica WHERE projeto_id = ?", (p["id"],))
        etica = cursor.fetchone()
        p["etica"] = dict(etica) if etica else {"status": "PENDENTE", "parecer": "", "por": "", "atualizado_em": None}

        cursor.execute("SELECT status, parecer, por, atualizado_em FROM pareceres_conselho WHERE projeto_id = ?", (p["id"],))
        conselho = cursor.fetchone()
        p["conselho"] = dict(conselho) if conselho else {"status": "PENDENTE", "parecer": "", "por": "", "atualizado_em": None}

    cursor.close()
    conn.close()
    return jsonify(projetos)



@app.route("/api/estatisticas", methods=["GET"])
def obter_estatisticas():
    if not exigir_acesso_relatorios():
        return jsonify({"error": "Acesso restrito a Administradores, Coordenadores e Orientadores."}), 403
    return jsonify(listar_projetos().get_json())



@app.route("/api/projetos", methods=["POST"])
def criar_projeto():
    data = request.get_json(silent=True) or {}
    titulo = data.get("titulo")
    setor_externo = data.get("setor_externo")
    areas_atuacao = data.get("areas_atuacao")
    interdisciplinaridade = data.get("interdisciplinaridade")
    orientador_nome = data.get("orientador_nome")
    grupo_nome = data.get("grupo_nome")
    membros = data.get("membros", [])

    conn = get_db_connection()
    cursor = conn.cursor()

    membros_validados = []
    ras_vistos = set()
    for m in membros:
        ra = m.get("ra", "").strip()
        if not ra or ra.lower() in ras_vistos:
            continue
        ras_vistos.add(ra.lower())
        cursor.execute("SELECT ra, nome, email FROM usuarios WHERE LOWER(ra) = LOWER(?) AND role = 'aluno'", (ra,))
        aluno_acc = cursor.fetchone()
        if not aluno_acc:
            cursor.close()
            conn.close()
            return jsonify({"error": f"O RA '{ra}' não pertence a nenhum aluno cadastrado com acesso no sistema."}), 400
        membros_validados.append(dict(aluno_acc))

    if not membros_validados:
        cursor.close()
        conn.close()
        return jsonify({"error": "Inclua pelo menos 1 aluno cadastrado com acesso no sistema."}), 400

    cursor.execute(
        """INSERT INTO projetos (titulo, setor_externo, areas_atuacao, interdisciplinaridade, status, publicado, orientador_nome)
           VALUES (?, ?, ?, ?, 'NOVO', 0, ?)""",
        (titulo, setor_externo, areas_atuacao, interdisciplinaridade, orientador_nome)
    )
    projeto_id = cursor.lastrowid

    cursor.execute("INSERT INTO grupos (projeto_id, nome) VALUES (?, ?)", (projeto_id, grupo_nome))
    grupo_id = cursor.lastrowid

    for aluno_acc in membros_validados:
        cursor.execute(
            "INSERT INTO grupo_membros (grupo_id, ra, nome, status_participacao, justificativa_recusa) VALUES (?, ?, ?, 'PENDENTE', '')",
            (grupo_id, aluno_acc["ra"], aluno_acc["nome"])
        )
        enviar_notificacao_email(aluno_acc["email"], aluno_acc["nome"], titulo, grupo_nome, orientador_nome)

    cursor.execute("INSERT INTO pareceres_etica (projeto_id, status) VALUES (?, 'PENDENTE')", (projeto_id,))
    cursor.execute("INSERT INTO pareceres_conselho (projeto_id, status) VALUES (?, 'PENDENTE')", (projeto_id,))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"id": projeto_id, "message": "Projeto registrado com sucesso"}), 201


@app.route("/api/projetos/<int:projeto_id>", methods=["PUT"])
def editar_projeto(projeto_id):
    data = request.get_json(silent=True) or {}
    actor_role = data.get("actor_role")
    actor_nome = data.get("actor_nome", "").strip()

    if actor_role not in ["admin", "coordenador", "orientador"]:
        return jsonify({"error": "Sem permissão para editar projeto"}), 403

    conn = get_db_connection()
    cursor = conn.cursor()

    if actor_role == "orientador":
        cursor.execute("SELECT orientador_nome FROM projetos WHERE id = ?", (projeto_id,))
        proj = cursor.fetchone()
        if not proj or actor_nome.lower() not in proj["orientador_nome"].lower():
            cursor.close()
            conn.close()
            return jsonify({"error": "Apenas o orientador responsável por este projeto pode editá-lo."}), 403

    membros_validados = []
    ras_vistos = set()
    for m in data.get("membros", []):
        ra = m.get("ra", "").strip()
        if not ra or ra.lower() in ras_vistos:
            continue
        ras_vistos.add(ra.lower())
        cursor.execute("SELECT ra, nome, email FROM usuarios WHERE LOWER(ra) = LOWER(?) AND role = 'aluno'", (ra,))
        aluno_acc = cursor.fetchone()
        if not aluno_acc:
            cursor.close()
            conn.close()
            return jsonify({"error": f"O RA '{ra}' não pertence a nenhum aluno cadastrado com acesso no sistema."}), 400
        membros_validados.append({
            "ra": aluno_acc["ra"],
            "nome": aluno_acc["nome"],
            "email": aluno_acc["email"],
            "status_participacao": m.get("status_participacao", "PENDENTE"),
            "justificativa_recusa": m.get("justificativa_recusa", "")
        })

    novo_orientador = data.get("orientador_nome", actor_nome).strip()
    cursor.execute(
        """UPDATE projetos SET titulo=?, setor_externo=?, areas_atuacao=?, interdisciplinaridade=?, orientador_nome=?
           WHERE id=?""",
        (data["titulo"], data["setor_externo"], data["areas_atuacao"], data["interdisciplinaridade"], novo_orientador, projeto_id)
    )

    cursor.execute("SELECT id FROM grupos WHERE projeto_id = ?", (projeto_id,))
    grupo = cursor.fetchone()
    if grupo:
        grupo_id = grupo["id"]
        cursor.execute("UPDATE grupos SET nome = ? WHERE id = ?", (data["grupo_nome"], grupo_id))

        cursor.execute("SELECT ra, COALESCE(justificativa_recusa, '') AS justificativa_recusa FROM grupo_membros WHERE grupo_id = ?", (grupo_id,))
        existentes_map = {row["ra"]: row["justificativa_recusa"] for row in cursor.fetchall()}

        cursor.execute("DELETE FROM grupo_membros WHERE grupo_id = ?", (grupo_id,))
        for aluno_acc in membros_validados:
            justificativa = existentes_map.get(aluno_acc["ra"], "") if aluno_acc["status_participacao"] == "RECUSADO" else ""
            cursor.execute(
                "INSERT INTO grupo_membros (grupo_id, ra, nome, status_participacao, justificativa_recusa) VALUES (?, ?, ?, ?, ?)",
                (grupo_id, aluno_acc["ra"], aluno_acc["nome"], aluno_acc["status_participacao"], justificativa)
            )

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Projeto atualizado com sucesso"})


@app.route("/api/projetos/<int:projeto_id>/status", methods=["PATCH"])
def alterar_status_projeto(projeto_id):
    data = request.get_json(silent=True) or {}
    actor_role = data.get("actor_role")
    actor_nome = data.get("actor_nome", "").strip()
    novo_status = str(data.get("status", "")).strip().upper()
    if novo_status not in ["NOVO", "EM ANDAMENTO", "DESENVOLVIMENTO", "CONCLUIDO", "CANCELADO"]:
        return jsonify({"error": "Status de projeto inválido."}), 400

    if actor_role in ["aluno", "public"]:
        return jsonify({"error": "Alunos e visitantes não podem alterar o status do projeto"}), 403

    conn = get_db_connection()
    cursor = conn.cursor()

    if novo_status == "DESENVOLVIMENTO":
        cursor.execute("SELECT status FROM pareceres_etica WHERE projeto_id = ?", (projeto_id,))
        parecer_etica = cursor.fetchone()
        cursor.execute("SELECT status FROM pareceres_conselho WHERE projeto_id = ?", (projeto_id,))
        parecer_conselho = cursor.fetchone()
        if (not parecer_etica or not parecer_conselho or
                parecer_etica["status"] != "APROVADO" or parecer_conselho["status"] != "APROVADO"):
            cursor.close()
            conn.close()
            return jsonify({"error": "O projeto só pode ir para DESENVOLVIMENTO com os pareceres de Ética e Conselho APROVADOS."}), 400

    if actor_role in ["admin", "coordenador"]:
        cursor.execute("UPDATE projetos SET status = ? WHERE id = ?", (novo_status, projeto_id))
    else:
        cursor.execute("SELECT orientador_nome FROM projetos WHERE id = ?", (projeto_id,))
        proj = cursor.fetchone()
        if not proj or actor_nome.lower() not in proj["orientador_nome"].lower():
            cursor.close()
            conn.close()
            return jsonify({"error": "Você não tem permissão para alterar este projeto, pois não consta como orientador responsável."}), 403
        cursor.execute("UPDATE projetos SET status = ? WHERE id = ?", (novo_status, projeto_id))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Status atualizado"})


@app.route("/api/projetos/<int:projeto_id>/publicar", methods=["PATCH"])
def publicar_projeto(projeto_id):
    data = request.get_json(silent=True) or {}
    actor_role = data.get("actor_role")
    actor_nome = data.get("actor_nome", "").strip()
    publicado = 1 if data.get("publicado", True) else 0

    if actor_role not in ["admin", "coordenador", "orientador"]:
        return jsonify({"error": "Sem permissão para publicar projeto"}), 403

    conn = get_db_connection()
    cursor = conn.cursor()

    if actor_role in ["admin", "coordenador"]:
        cursor.execute("UPDATE projetos SET publicado = ? WHERE id = ?", (publicado, projeto_id))
    else:
        cursor.execute("SELECT orientador_nome FROM projetos WHERE id = ?", (projeto_id,))
        proj = cursor.fetchone()
        if not proj or actor_nome.lower() not in proj["orientador_nome"].lower():
            cursor.close()
            conn.close()
            return jsonify({"error": "Você não tem permissão para publicar este projeto."}), 403
        cursor.execute("UPDATE projetos SET publicado = ? WHERE id = ?", (publicado, projeto_id))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Estado de publicação atualizado", "publicado": bool(publicado)})


@app.route("/api/projetos/<int:projeto_id>", methods=["DELETE"])
def deletar_projeto(projeto_id):
    data = request.json or {}
    actor_role = data.get("actor_role")
    actor_nome = data.get("actor_nome", "").strip()

    if actor_role not in ["admin", "coordenador", "orientador"]:
        return jsonify({"error": "Sem permissão para excluir projeto"}), 403

    conn = get_db_connection()
    cursor = conn.cursor()

    if actor_role == "orientador":
        cursor.execute("SELECT orientador_nome FROM projetos WHERE id = ?", (projeto_id,))
        proj = cursor.fetchone()
        if not proj or actor_nome.lower() not in proj["orientador_nome"].lower():
            cursor.close()
            conn.close()
            return jsonify({"error": "Apenas o orientador responsável por este projeto pode excluí-lo."}), 403

    cursor.execute("DELETE FROM projetos WHERE id = ?", (projeto_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Projeto excluído com sucesso"})


@app.route("/api/projetos/<int:projeto_id>/pareceres", methods=["PATCH"])
def atualizar_parecer(projeto_id):
    data = request.get_json(silent=True) or {}
    tipo = str(data.get("tipo", "")).strip().lower()
    status = str(data.get("status", "")).strip().upper()
    parecer = str(data.get("parecer", "")).strip()
    por = str(data.get("por", "Gestão")).strip() or "Gestão"
    actor_role = str(data.get("actor_role", "")).strip().lower()
    actor_nome = str(data.get("actor_nome", "")).strip()

    if actor_role not in ["admin", "coordenador", "orientador"]:
        return jsonify({"error": "Sem permissão para registrar pareceres."}), 403
    if tipo not in ("etica", "conselho"):
        return jsonify({"error": "Tipo de parecer inválido. Use 'etica' ou 'conselho'."}), 400
    if status not in ("PENDENTE", "APROVADO", "REPROVADO"):
        return jsonify({"error": "Status de parecer inválido."}), 400

    tabela = "pareceres_etica" if tipo == "etica" else "pareceres_conselho"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, orientador_nome FROM projetos WHERE id = ?", (projeto_id,))
    projeto = cursor.fetchone()
    if not projeto:
        cursor.close()
        conn.close()
        return jsonify({"error": "Projeto não encontrado."}), 404
    if actor_role == "orientador" and (not actor_nome or actor_nome.lower() not in projeto["orientador_nome"].lower()):
        cursor.close()
        conn.close()
        return jsonify({"error": "Você não é o orientador responsável por este projeto."}), 403

    cursor.execute(
        f"INSERT INTO {tabela} (projeto_id, status, parecer, por, atualizado_em) "
        "VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP) "
        "ON CONFLICT(projeto_id) DO UPDATE SET status=excluded.status, parecer=excluded.parecer, "
        "por=excluded.por, atualizado_em=CURRENT_TIMESTAMP",
        (projeto_id, status, parecer, por)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Parecer atualizado com sucesso."})


# ==========================================
# CARGA MASSIVA VIA JSON (ACERVO PROJETOS / PROFESSORES)
# ==========================================
@app.route("/api/carga-massiva", methods=["POST"])
def carga_massiva_json():
    data = request.json or {}
    actor_role = data.get("actor_role")
    tipo = data.get("tipo")
    registros = data.get("registros", [])

    if actor_role not in ["admin", "coordenador"]:
        return jsonify({"error": "Apenas Administrador ou Coordenador podem importar acervos"}), 403

    if not isinstance(registros, list) or len(registros) == 0:
        return jsonify({"error": "O JSON deve conter uma lista [...] com pelo menos 1 registro"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    inseridos = 0
    ignorados = 0

    try:
        if tipo == "usuarios":
            for u in registros:
                ra = str(u.get("ra", "")).strip()
                nome = str(u.get("nome", "")).strip()
                email = str(u.get("email", "")).strip()
                senha = SENHA_PROVISORIA_PADRAO
                role = str(u.get("role", "orientador")).strip().lower()
                curso = str(u.get("curso", "")).strip() if role == "aluno" else ""

                if role not in ["coordenador", "orientador", "aluno"] or (actor_role == "coordenador" and role == "coordenador"):
                    ignorados += 1
                    continue
                if not ra or not nome or not email:
                    ignorados += 1
                    continue

                try:
                    cursor.execute(
                        """INSERT INTO usuarios (ra, nome, email, senha, role, curso, primeiro_acesso, tentativas_falhas, bloqueado)
                           VALUES (?, ?, ?, ?, ?, ?, 1, 0, 0)""",
                        (ra, nome, email, senha, role, curso)
                    )
                    inseridos += 1
                except sqlite3.IntegrityError:
                    ignorados += 1

        elif tipo == "projetos":
            for p in registros:
                titulo = str(p.get("titulo", "")).strip()
                setor_externo = str(p.get("setor_externo", "Não informado")).strip()
                areas_atuacao = str(p.get("areas_atuacao", "Geral")).strip()
                interdisciplinaridade = str(p.get("interdisciplinaridade", "Não especificada")).strip()
                orientador_nome = str(p.get("orientador_nome", "Orientador")).strip()
                status = str(p.get("status", "NOVO")).strip().upper()
                if status not in ["NOVO", "EM ANDAMENTO", "CONCLUIDO", "CANCELADO"] or status == "DESENVOLVIMENTO":
                    status = "NOVO"
                publicado = 1 if p.get("publicado", False) else 0
                grupo_nome = str(p.get("grupo_nome", f"Grupo - {titulo[:25]}")).strip()
                membros = p.get("membros", [])

                if not titulo:
                    ignorados += 1
                    continue

                cursor.execute(
                    """INSERT INTO projetos (titulo, setor_externo, areas_atuacao, interdisciplinaridade, status, publicado, orientador_nome)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (titulo, setor_externo, areas_atuacao, interdisciplinaridade, status, publicado, orientador_nome)
                )
                projeto_id = cursor.lastrowid
                cursor.execute("INSERT INTO pareceres_etica (projeto_id, status) VALUES (?, 'PENDENTE')", (projeto_id,))
                cursor.execute("INSERT INTO pareceres_conselho (projeto_id, status) VALUES (?, 'PENDENTE')", (projeto_id,))
                cursor.execute("INSERT INTO grupos (projeto_id, nome) VALUES (?, ?)", (projeto_id, grupo_nome))
                grupo_id = cursor.lastrowid

                for m in membros:
                    m_ra = str(m.get("ra", "")).strip()
                    m_status = str(m.get("status_participacao", "PENDENTE")).strip().upper()
                    if m_status not in ["PENDENTE", "CONFIRMADO", "RECUSADO"]:
                        m_status = "PENDENTE"
                    if m_ra:
                        cursor.execute("SELECT ra, nome FROM usuarios WHERE LOWER(ra) = LOWER(?) AND role = 'aluno'", (m_ra,))
                        aluno_acc = cursor.fetchone()
                        if aluno_acc:
                            cursor.execute(
                                "INSERT INTO grupo_membros (grupo_id, ra, nome, status_participacao, justificativa_recusa) VALUES (?, ?, ?, ?, '')",
                                (grupo_id, aluno_acc["ra"], aluno_acc["nome"], m_status)
                            )
                inseridos += 1
        else:
            return jsonify({"error": "Tipo de acervo inválido"}), 400

        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": f"Importação concluída: {inseridos} registro(s) inserido(s), {ignorados} ignorado(s)."})


# ==========================================
# ROTAS DO ALUNO (ACEITAR/REJEITAR COM JUSTIFICATIVA E EDITAR NOME PRÓPRIO)
# ==========================================
@app.route("/api/membros/<int:membro_id>/resposta", methods=["PATCH"])
def responder_convite_aluno(membro_id):
    data = request.get_json(silent=True) or {}
    status_participacao = data.get("status_participacao")
    justificativa = str(data.get("justificativa", "")).strip() if status_participacao == "RECUSADO" else ""

    if status_participacao not in ["CONFIRMADO", "RECUSADO"]:
        return jsonify({"error": "Status inválido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE grupo_membros SET status_participacao = ?, justificativa_recusa = ? WHERE id = ?",
        (status_participacao, justificativa, membro_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Resposta registrada"})


@app.route("/api/membros/<int:membro_id>/aluno-self", methods=["PATCH"])
def editar_dados_proprios_aluno(membro_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    novo_nome = data.get("nome", "").strip()

    if not novo_nome:
        return jsonify({"error": "O nome não pode ficar em branco."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT ra FROM grupo_membros WHERE id = ?", (membro_id,))
    membro = cursor.fetchone()
    if membro:
        cursor.execute("UPDATE grupo_membros SET nome = ? WHERE LOWER(ra) = LOWER(?)", (novo_nome, membro["ra"]))
    if user_id:
        cursor.execute("UPDATE usuarios SET nome = ? WHERE id = ? AND role = 'aluno'", (novo_nome, user_id))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Nome atualizado com sucesso"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
