import os
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import smtplib
try:
    from segredos import BREVO_API_KEY
except ImportError:
    BREVO_API_KEY = ""

app = Flask(__name__)

# Caminho do banco SQLite (criado automaticamente na mesma pasta do app.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "modulo2_extensionista.db")

# ==========================================
# CONFIGURAÇÕES DE E-MAIL (SMTP / BREVO)
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
            status TEXT DEFAULT 'PENDENTE' CHECK(status in ('PENDENTE', 'APROVADO', 'REPROVADO')),
            parecer TEXT DEFAULT '',
            por TEXT DEFAULT '',
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (projeto_id) REFERENCES projetos(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS pareceres_conselho (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projeto_id INTEGER NOT NULL UNIQUE,
            status TEXT DEFAULT 'PENDENTE' CHECK(status in ('PENDENTE', 'APROVADO', 'REPROVADO')),
            parecer TEXT DEFAULT '',
            por TEXT DEFAULT '',
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (projeto_id) REFERENCES projetos(id) ON DELETE CASCADE
        );
    """)

    # Migrações seguras para bancos já existentes
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

    # Administrador inicial padrão
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

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
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
        return jsonify({"error": "Acesso bloqueado após 5 tentativas incorretas. Procure um Coordenador ou Administrador."}), 403

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
                return jsonify({"error": "Você atingiu 5 tentativas incorretas. Acesso bloqueado."}), 403
            else:
                restantes = 5 - novas_tentativas
                cursor.execute(
                    "UPDATE usuarios SET tentativas_falhas = ? WHERE id = ?",
                    (novas_tentativas, user["id"])
                )
                conn.commit()
                cursor.close()
                conn.close()
                return jsonify({"error": f"Senha incorreta. Restam {restantes} tentativa(s)."}), 401
        else:
            cursor.close()
            conn.close()
            return jsonify({"error": "Credenciais inválidas."}), 401

    cursor.execute("UPDATE usuarios SET tentativas_falhas = 0 WHERE id = ?", (user["id"],))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({
        "id": user["id"],
        "ra": user["ra"],
        "nome": user["nome"],
        "email": user["email"],
        "role": user["role"],
        "curso": user["curso"],
        "primeiro_acesso": bool(user["primeiro_acesso"])
    })

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

@app.route("/api/usuarios", methods=["GET"])
def listar_usuarios():
    actor_role = request.args.get("actor_role", "").strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()

    if actor_role == "admin":
        cursor.execute("SELECT id, ra, nome, email, role, COALESCE(curso, '') AS curso, COALESCE(primeiro_acesso, 0) AS primeiro_acesso, COALESCE(bloqueado, 0) AS bloqueado FROM usuarios ORDER BY id ASC")
    elif actor_role == "coordenador":
        cursor.execute("SELECT id, ra, nome, email, role, COALESCE(curso, '') AS curso, COALESCE(primeiro_acesso, 0) AS primeiro_acesso, COALESCE(bloqueado, 0) AS bloqueado FROM usuarios WHERE role IN ('orientador', 'aluno') ORDER BY id ASC")
    elif actor_role == "orientador":
        cursor.execute("SELECT id, ra, nome, email, role, COALESCE(curso, '') AS curso, COALESCE(primeiro_acesso, 0) AS primeiro_acesso, COALESCE(bloqueado, 0) AS bloqueado FROM usuarios WHERE role = 'aluno' ORDER BY id ASC")
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
    data = request.json or {}
    actor_role = data.get("actor_role")
    role = data.get("role")
    ra = data.get("ra", "").strip()
    nome = data.get("nome", "").strip()
    email = data.get("email", "").strip()
    senha = SENHA_PROVISORIA_PADRAO
    curso = data.get("curso", "").strip() if role == "aluno" else ""

    if actor_role not in ["admin", "coordenador", "orientador"]:
        return jsonify({"error": "Acesso negado"}), 403
    if role == "admin":
        return jsonify({"error": "Não é permitido criar novos administradores"}), 403

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
    return jsonify({"id": new_id, "ra": ra, "name": nome, "email": email, "role": role, "curso": curso})

@app.route("/api/projetos", methods=["GET"])
def listar_projetos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projetos ORDER BY id DESC")
    projetos = [dict(row) for row in cursor.fetchall()]

    for p in projetos:
        p["publicado"] = bool(p["publicado"])
        # Grupo e membros
        cursor.execute("SELECT * FROM grupos WHERE projeto_id = ?", (p["id"],))
        grupo_row = cursor.fetchone()
        if grupo_row:
            grupo = dict(grupo_row)
            cursor.execute("SELECT id, ra, nome, status_participacao, COALESCE(justificativa_recusa, '') AS justificativa_recusa FROM grupo_membros WHERE grupo_id = ?", (grupo["id"],))
            grupo["membros"] = [dict(m) for m in cursor.fetchall()]
            p["grupo"] = grupo
        else:
            p["grupo"] = {"id": None, "nome": "", "membros": []}

        # Pareceres ética e conselho
        cursor.execute("SELECT status, parecer, por FROM pareceres_etica WHERE projeto_id = ?", (p["id"],))
        et = cursor.fetchone()
        p["etica"] = dict(et) if et else {"status": "PENDENTE", "parecer": "", "por": ""}

        cursor.execute("SELECT status, parecer, por FROM pareceres_conselho WHERE projeto_id = ?", (p["id"],))
        co = cursor.fetchone()
        p["conselho"] = dict(co) if co else {"status": "PENDENTE", "parecer": "", "por": ""}

    cursor.close()
    conn.close()
    return jsonify(projetos)

@app.route("/api/projetos", methods=["POST"])
def criar_projeto():
    data = request.json or {}
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
            return jsonify({"error": f"O RA '{ra}' não pertence a nenhum aluno cadastrado."}), 400
        membros_validados.append(dict(aluno_acc))

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

    # Inserir pendentes iniciais para ética e conselho
    cursor.execute("INSERT INTO pareceres_etica (projeto_id, status) VALUES (?, 'PENDENTE')", (projeto_id,))
    cursor.execute("INSERT INTO pareceres_conselho (projeto_id, status) VALUES (?, 'PENDENTE')", (projeto_id,))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"id": projeto_id, "message": "Projeto registrado com sucesso"}), 201

@app.route("/api/projetos/<int:projeto_id>/status", methods=["PATCH"])
def alterar_status_projeto(projeto_id):
    data = request.json or {}
    novo_status = data.get("status")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Validação de pareceres para DESENVOLVIMENTO
    if novo_status == "DESENVOLVIMENTO":
        cursor.execute("SELECT status FROM pareceres_etica WHERE projeto_id = ?", (projeto_id,))
        et = cursor.fetchone()
        cursor.execute("SELECT status FROM pareceres_conselho WHERE projeto_id = ?", (projeto_id,))
        co = cursor.fetchone()
        if not et or not co or et["status"] != "APROVADO" or co["status"] != "APROVADO":
            cursor.close()
            conn.close()
            return jsonify({"error": "O projeto só pode ir para DESENVOLVIMENTO com pareceres da Ética e Conselho APROVADOS."}), 400

    cursor.execute("UPDATE projetos SET status = ? WHERE id = ?", (novo_status, projeto_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Status atualizado com sucesso"})

@app.route("/api/projetos/<int:projeto_id>/pareceres", methods=["PATCH"])
def atualizar_parecer(projeto_id):
    data = request.json or {}
    tipo = data.get("tipo") # 'etica' ou 'conselho'
    status = data.get("status")
    parecer = data.get("parecer", "")
    por = data.get("por", "Gestão")

    conn = get_db_connection()
    cursor = conn.cursor()
    if tipo == "etica":
        cursor.execute("UPDATE pareceres_etica SET status = ?, parecer = ?, por = ?, atualizado_em = CURRENT_TIMESTAMP WHERE projeto_id = ?", (status, parecer, por, projeto_id))
    elif tipo == "conselho":
        cursor.execute("UPDATE pareceres_conselho SET status = ?, parecer = ?, por = ?, atualizado_em = CURRENT_TIMESTAMP WHERE projeto_id = ?", (status, parecer, por, projeto_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Parecer atualizado com sucesso"})

@app.route("/api/carga-massiva", methods=["POST"])
def carga_massiva_json():
    data = request.json or {}
    tipo = data.get("tipo")
    registros = data.get("registros", [])

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
                role = str(u.get("role", "aluno")).strip().lower()
                curso = str(u.get("curso", "")).strip() if role == "aluno" else ""

                if not ra or not nome or not email:
                    ignorados += 1
                    continue
                try:
                    cursor.execute(
                        """INSERT INTO usuarios (ra, nome, email, senha, role, curso, primeiro_acesso, tentativas_falhas, bloqueado)
                           VALUES (?, ?, ?, ?, ?, ?, 1, 0, 0)""",
                        (ra, nome, email, SENHA_PROVISORIA_PADRAO, role, curso)
                    )
                    inseridos += 1
                except sqlite3.IntegrityError:
                    ignorados += 1

        elif tipo == "projetos":
            for p in registros:
                titulo = str(p.get("titulo", "")).strip()
                setor_externo = str(p.get("setor_externo", "Externo")).strip()
                areas_atuacao = str(p.get("areas_atuacao", "Geral")).strip()
                interdisciplinaridade = str(p.get("interdisciplinaridade", "Não")).strip()
                orientador_nome = str(p.get("orientador_nome", "Orientador")).strip()
                status = str(p.get("status", "NOVO")).strip().upper()
                grupo_nome = str(p.get("grupo_nome", "Grupo Padrão")).strip()

                if not titulo:
                    ignorados += 1
                    continue

                cursor.execute(
                    """INSERT INTO projetos (titulo, setor_externo, areas_atuacao, interdisciplinaridade, status, publicado, orientador_nome)
                       VALUES (?, ?, ?, ?, ?, 0, ?)""",
                    (titulo, setor_externo, areas_atuacao, interdisciplinaridade, status, orientador_nome)
                )
                pid = cursor.lastrowid
                cursor.execute("INSERT INTO grupos (projeto_id, nome) VALUES (?, ?)", (pid, grupo_nome))
                cursor.execute("INSERT INTO pareceres_etica (projeto_id, status) VALUES (?, 'PENDENTE')", (pid,))
                cursor.execute("INSERT INTO pareceres_conselho (projeto_id, status) VALUES (?, 'PENDENTE')", (pid,))
                inseridos += 1

        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": f"Importação concluída: {inseridos} inserido(s), {ignorados} ignorado(s)."})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
