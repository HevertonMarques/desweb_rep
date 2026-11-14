import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Caminho do banco SQLite (criado automaticamente na mesma pasta do app.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "modulo2_extensionista.db")

# ==========================================
# CONFIGURAÇÕES DE E-MAIL (SMTP)
# ==========================================
SMTP_ENABLED = False  # Mude para True se configurar SMTP externo
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "seu_email@gmail.com"
SMTP_PASSWORD = "sua_senha_de_app_google"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Cria as tabelas SQL automaticamente, aplica migração de curso e insere o Administrador inicial."""
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
            FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE
        );
    """)

    # Migração segura: adiciona a coluna 'curso' caso o banco já existisse antes
    cursor.execute("PRAGMA table_info(usuarios)")
    colunas = [col["name"] for col in cursor.fetchall()]
    if "curso" not in colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN curso TEXT DEFAULT ''")

    # Insere APENAS o Administrador inicial caso ainda não exista
    cursor.execute("SELECT id FROM usuarios WHERE email = ?", ("admin@faccamp.com",))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO usuarios (ra, nome, email, senha, role, curso) VALUES (?, ?, ?, ?, ?, ?)",
            ("ADMIN01", "Administrador FACCAMP", "admin@faccamp.com", "adminhrv2026", "admin", "")
        )

    conn.commit()
    cursor.close()
    conn.close()


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


# Inicializa o banco automaticamente ao carregar a aplicação
init_db()


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
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, ra, nome, email, role, curso FROM usuarios WHERE (LOWER(email) = ? OR LOWER(ra) = ?) AND senha = ?",
        (identifier, identifier, senha)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return jsonify({"error": "Credenciais inválidas"}), 401

    return jsonify(dict(row))


@app.route("/api/usuarios", methods=["GET"])
def listar_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, ra, nome, email, role, COALESCE(curso, '') AS curso FROM usuarios ORDER BY id ASC")
    users = [dict(row) for row in cursor.fetchall()]
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
    curso = data.get("curso", "").strip() if role == "aluno" else ""

    if len(senha) < 6 or len(senha) > 18:
        return jsonify({"error": "A senha deve ter entre 6 e 18 caracteres."}), 400
    if actor_role not in ["admin", "coordenador", "orientador"]:
        return jsonify({"error": "Acesso negado"}), 403
    if actor_role == "orientador" and role != "aluno":
        return jsonify({"error": "Orientadores só podem criar contas de Alunos"}), 403
    if actor_role == "coordenador" and role in ["coordenador", "admin"]:
        return jsonify({"error": "Coordenadores só podem criar Orientadores e Alunos"}), 403
    if role == "admin":
        return jsonify({"error": "Não é permitido criar novos administradores"}), 403
    if role == "aluno" and not curso:
        return jsonify({"error": "Informe o curso ao cadastrar uma conta de Aluno."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO usuarios (ra, nome, email, senha, role, curso) VALUES (?, ?, ?, ?, ?, ?)",
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
    return jsonify({"id": new_id, "ra": ra, "nome": nome, "email": email, "role": role, "curso": curso}), 201


@app.route("/api/usuarios/<int:user_id>", methods=["PUT"])
def editar_usuario(user_id):
    data = request.json
    actor_role = data.get("actor_role")
    ra = data.get("ra", "").strip()
    nome = data.get("nome", "").strip()
    email = data.get("email", "").strip()
    senha = data.get("senha", "").strip()
    role = data.get("role")
    curso = data.get("curso", "").strip() if role == "aluno" else ""

    if actor_role == "coordenador" and role == "coordenador":
        return jsonify({"error": "Coordenador não pode editar outro Coordenador"}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    if senha:
        cursor.execute(
            "UPDATE usuarios SET ra=?, nome=?, email=?, senha=?, role=?, curso=? WHERE id=?",
            (ra, nome, email, senha, role, curso, user_id)
        )
    else:
        cursor.execute(
            "UPDATE usuarios SET ra=?, nome=?, email=?, role=?, curso=? WHERE id=?",
            (ra, nome, email, role, curso, user_id)
        )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Usuário atualizado com sucesso"})


@app.route("/api/usuarios/<int:user_id>", methods=["DELETE"])
def deletar_usuario(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ? AND role != 'admin'", (user_id,))
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

    cursor.execute("SELECT * FROM projetos ORDER BY id DESC")
    projetos = [dict(row) for row in cursor.fetchall()]

    for p in projetos:
        p["publicado"] = bool(p["publicado"])
        cursor.execute("SELECT * FROM grupos WHERE projeto_id = ?", (p["id"],))
        grupo_row = cursor.fetchone()
        if grupo_row:
            grupo = dict(grupo_row)
            cursor.execute("SELECT id, ra, nome, status_participacao FROM grupo_membros WHERE grupo_id = ?", (grupo["id"],))
            grupo["membros"] = [dict(m) for m in cursor.fetchall()]
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
    cursor = conn.cursor()

    # Valida se todos os integrantes possuem conta de 'aluno' no sistema
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
            "INSERT INTO grupo_membros (grupo_id, ra, nome, status_participacao) VALUES (?, ?, ?, 'PENDENTE')",
            (grupo_id, aluno_acc["ra"], aluno_acc["nome"])
        )
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
    cursor = conn.cursor()

    # Valida se todos os integrantes possuem conta de 'aluno' no sistema
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
            "status_participacao": m.get("status_participacao", "PENDENTE")
        })

    if actor_role == "admin" and data.get("orientador_nome"):
        cursor.execute(
            """UPDATE projetos SET titulo=?, setor_externo=?, areas_atuacao=?, interdisciplinaridade=?, orientador_nome=?
               WHERE id=?""",
            (data["titulo"], data["setor_externo"], data["areas_atuacao"], data["interdisciplinaridade"], data["orientador_nome"], projeto_id)
        )
    else:
        cursor.execute(
            """UPDATE projetos SET titulo=?, setor_externo=?, areas_atuacao=?, interdisciplinaridade=?
               WHERE id=?""",
            (data["titulo"], data["setor_externo"], data["areas_atuacao"], data["interdisciplinaridade"], projeto_id)
        )

    cursor.execute("SELECT id FROM grupos WHERE projeto_id = ?", (projeto_id,))
    grupo = cursor.fetchone()
    if grupo:
        grupo_id = grupo["id"]
        cursor.execute("UPDATE grupos SET nome = ? WHERE id = ?", (data["grupo_nome"], grupo_id))

        cursor.execute("SELECT ra FROM grupo_membros WHERE grupo_id = ?", (grupo_id,))
        ras_existentes = {row["ra"] for row in cursor.fetchall()}

        cursor.execute("DELETE FROM grupo_membros WHERE grupo_id = ?", (grupo_id,))
        for aluno_acc in membros_validados:
            cursor.execute(
                "INSERT INTO grupo_membros (grupo_id, ra, nome, status_participacao) VALUES (?, ?, ?, ?)",
                (grupo_id, aluno_acc["ra"], aluno_acc["nome"], aluno_acc["status_participacao"])
            )
            if aluno_acc["ra"] not in ras_existentes:
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

    if actor_role in ["aluno", "public"]:
        return jsonify({"error": "Alunos e visitantes não podem alterar o status do projeto"}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE projetos SET status = ? WHERE id = ?", (novo_status, projeto_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Status atualizado"})


@app.route("/api/projetos/<int:projeto_id>/publicar", methods=["PATCH"])
def publicar_projeto(projeto_id):
    data = request.json
    actor_role = data.get("actor_role")
    publicado = 1 if data.get("publicado", True) else 0

    if actor_role not in ["admin", "coordenador", "orientador"]:
        return jsonify({"error": "Sem permissão para publicar projeto"}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE projetos SET publicado = ? WHERE id = ?", (publicado, projeto_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Estado de publicação atualizado", "publicado": bool(publicado)})


@app.route("/api/projetos/<int:projeto_id>", methods=["DELETE"])
def deletar_projeto(projeto_id):
    data = request.json or {}
    actor_role = data.get("actor_role")

    if actor_role not in ["admin", "coordenador", "orientador"]:
        return jsonify({"error": "Sem permissão para excluir projeto"}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projetos WHERE id = ?", (projeto_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Projeto excluído com sucesso"})


# ==========================================
# CARGA MASSIVA VIA JSON (ACERVO PROJETOS / PROFESSORES)
# ==========================================
@app.route("/api/carga-massiva", methods=["POST"])
def carga_massiva_json():
    data = request.json or {}
    actor_role = data.get("actor_role")
    tipo = data.get("tipo")  # 'usuarios' ou 'projetos'
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
                senha = str(u.get("senha", "123456")).strip()
                role = str(u.get("role", "orientador")).strip().lower()
                curso = str(u.get("curso", "")).strip() if role == "aluno" else ""

                if role not in ["coordenador", "orientador", "aluno"] or (actor_role == "coordenador" and role == "coordenador"):
                    ignorados += 1
                    continue
                if not ra or not nome or not email or len(senha) < 6 or len(senha) > 18:
                    ignorados += 1
                    continue

                try:
                    cursor.execute(
                        "INSERT INTO usuarios (ra, nome, email, senha, role, curso) VALUES (?, ?, ?, ?, ?, ?)",
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
                if status not in ["NOVO", "EM ANDAMENTO", "CONCLUIDO", "CANCELADO"]:
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
                                "INSERT INTO grupo_membros (grupo_id, ra, nome, status_participacao) VALUES (?, ?, ?, ?)",
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
    cursor.execute("UPDATE grupo_membros SET status_participacao = ? WHERE id = ?", (status_participacao, membro_id))
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
    cursor.execute("UPDATE grupo_membros SET nome = ?, ra = ? WHERE id = ?", (novo_nome, novo_ra, membro_id))
    if user_id:
        cursor.execute("UPDATE usuarios SET nome = ?, ra = ? WHERE id = ? AND role = 'aluno'", (novo_nome, novo_ra, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Dados atualizados"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
