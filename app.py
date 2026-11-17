import os
import sqlite3
from flask import Flask, render_template, request, jsonify, session

# A SECRET_KEY é obrigatória e fica guardada no arquivo privado segredos.py.
from segredos import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

# Caminho do banco SQLite (criado automaticamente na mesma pasta do app.py)

# Caminho do banco SQLite
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "modulo2_extensionista.db")


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

        CREATE TABLE IF NOT EXISTS conselho_membros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orientador_id INTEGER NOT NULL UNIQUE,
            adicionado_por TEXT DEFAULT '',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (orientador_id) REFERENCES usuarios(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS votos_conselho (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projeto_id INTEGER NOT NULL,
            orientador_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('APROVADO', 'REPROVADO')),
            comentario TEXT DEFAULT '',
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(projeto_id, orientador_id),
            FOREIGN KEY (projeto_id) REFERENCES projetos(id) ON DELETE CASCADE,
            FOREIGN KEY (orientador_id) REFERENCES usuarios(id) ON DELETE CASCADE
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


def ator_atual():
    """Perfil e nome de quem está logado, lidos da sessão do servidor (nunca do corpo da requisição)."""
    usuario = usuario_logado()
    if not usuario:
        return "", ""
    return usuario["role"], usuario["nome"]


def exigir_acesso_relatorios():
    usuario = usuario_logado()
    if usuario and usuario["role"] in ("admin", "coordenador", "orientador"):
        return usuario
    return None


def calcular_conselho(cursor, projeto_id):
    """Monta o parecer do Conselho a partir do voto individual de cada orientador.

    Participam apenas os orientadores incluídos no Conselho por Coordenador/Administrador.
    Regra: APROVADO quando mais da metade dos membros aprovou;
    REPROVADO quando a aprovação deixou de ser possível; senão PENDENTE.
    """
    cursor.execute(
        """SELECT u.id AS orientador_id, u.nome AS nome,
                  COALESCE(v.status, 'PENDENTE') AS status,
                  COALESCE(v.comentario, '') AS comentario,
                  v.atualizado_em AS atualizado_em
           FROM conselho_membros cm
           JOIN usuarios u ON u.id = cm.orientador_id AND u.role = 'orientador'
           LEFT JOIN votos_conselho v ON v.orientador_id = u.id AND v.projeto_id = ?
           ORDER BY u.nome COLLATE NOCASE""",
        (projeto_id,)
    )
    votos = [dict(r) for r in cursor.fetchall()]
    total = len(votos)
    aprovados = sum(1 for v in votos if v["status"] == "APROVADO")
    reprovados = sum(1 for v in votos if v["status"] == "REPROVADO")

    if total == 0:
        status = "PENDENTE"
    elif aprovados * 2 > total:
        status = "APROVADO"
    elif reprovados * 2 >= total:
        status = "REPROVADO"
    else:
        status = "PENDENTE"

    return {
        "status": status,
        "total": total,
        "aprovados": aprovados,
        "reprovados": reprovados,
        "votos": votos
    }



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
    usuario = usuario_logado()
    if not usuario:
        return jsonify({"error": "Faça login para continuar."}), 401
    if usuario["id"] != user_id:
        return jsonify({"error": "Você só pode alterar a sua própria senha."}), 403

    data = request.get_json(silent=True) or {}
    nova_senha = str(data.get("nova_senha", "")).strip()
    senha_atual = str(data.get("senha_atual", "")).strip()
    forcar_primeiro_acesso = bool(usuario["primeiro_acesso"])

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

    if not forcar_primeiro_acesso and row["senha"] != senha_atual:
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
    data = request.get_json(silent=True) or {}
    actor_role, _ = ator_atual()
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
    data = request.get_json(silent=True) or {}
    actor_role, _ = ator_atual()
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
    actor_role, _ = ator_atual()

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
    cursor.execute("SELECT orientador_id FROM conselho_membros")
    ids_conselho = {r["orientador_id"] for r in cursor.fetchall()}
    for u in users:
        u["conselho"] = u["id"] in ids_conselho
    cursor.close()
    conn.close()
    return jsonify(users)


@app.route("/api/usuarios/<int:user_id>/conselho", methods=["PATCH"])
def alterar_membro_conselho(user_id):
    """Inclui ou remove um orientador do Conselho (somente Coordenador ou Administrador)."""
    usuario = usuario_logado()
    if not usuario:
        return jsonify({"error": "Faça login para continuar."}), 401
    if usuario["role"] not in ("admin", "coordenador"):
        return jsonify({"error": "Apenas Coordenadores e o Administrador podem definir os membros do Conselho."}), 403

    data = request.get_json(silent=True) or {}
    membro = bool(data.get("membro", True))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM usuarios WHERE id = ?", (user_id,))
    alvo = cursor.fetchone()
    if not alvo or alvo["role"] != "orientador":
        cursor.close()
        conn.close()
        return jsonify({"error": "Somente contas de Orientador podem participar do Conselho."}), 400

    if membro:
        cursor.execute(
            "INSERT OR IGNORE INTO conselho_membros (orientador_id, adicionado_por) VALUES (?, ?)",
            (user_id, usuario["nome"])
        )
    else:
        cursor.execute("DELETE FROM conselho_membros WHERE orientador_id = ?", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Orientador incluído no Conselho." if membro else "Orientador removido do Conselho."})


@app.route("/api/usuarios", methods=["POST"])
def criar_usuario():
    data = request.get_json(silent=True) or {}
    actor_role, _ = ator_atual()
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

    return jsonify({"id": new_id, "ra": ra, "name": nome, "email": email, "role": role, "curso": curso})

@app.route("/api/usuarios/<int:user_id>", methods=["DELETE"])
def deletar_usuario(user_id):
    data = request.get_json(silent=True) or {}
    actor_role, _ = ator_atual()

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

        p["conselho"] = calcular_conselho(cursor, p["id"])

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

    cursor.execute("INSERT INTO pareceres_etica (projeto_id, status) VALUES (?, 'PENDENTE')", (projeto_id,))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"id": projeto_id, "message": "Projeto registrado com sucesso"}), 201


@app.route("/api/projetos/<int:projeto_id>", methods=["PUT"])
def editar_projeto(projeto_id):
    data = request.get_json(silent=True) or {}
    actor_role, actor_nome = ator_atual()

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
    actor_role, actor_nome = ator_atual()
    novo_status = str(data.get("status", "")).strip().upper()
    if novo_status not in ["NOVO", "EM ANDAMENTO", "DESENVOLVIMENTO", "CONCLUIDO", "CANCELADO"]:
        return jsonify({"error": "Status de projeto inválido."}), 400

    if actor_role not in ["admin", "coordenador", "orientador"]:
        return jsonify({"error": "Alunos e visitantes não podem alterar o status do projeto"}), 403

    conn = get_db_connection()
    cursor = conn.cursor()

    if novo_status == "DESENVOLVIMENTO":
        cursor.execute("SELECT status FROM pareceres_etica WHERE projeto_id = ?", (projeto_id,))
        parecer_etica = cursor.fetchone()
        parecer_conselho = calcular_conselho(cursor, projeto_id)
        if (not parecer_etica or
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
    actor_role, actor_nome = ator_atual()
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
    data = request.get_json(silent=True) or {}
    actor_role, actor_nome = ator_atual()

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
    """Parecer de Ética: somente Coordenador ou Administrador (identidade vem da sessão)."""
    usuario = usuario_logado()
    if not usuario:
        return jsonify({"error": "Faça login para registrar pareceres."}), 401
    if usuario["role"] not in ("admin", "coordenador"):
        return jsonify({"error": "Apenas Coordenadores e o Administrador podem registrar o parecer de Ética."}), 403

    data = request.get_json(silent=True) or {}
    status = str(data.get("status", "")).strip().upper()
    parecer = str(data.get("parecer", "")).strip()

    if status not in ("PENDENTE", "APROVADO", "REPROVADO"):
        return jsonify({"error": "Status de parecer inválido."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM projetos WHERE id = ?", (projeto_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Projeto não encontrado."}), 404

    cursor.execute(
        "INSERT INTO pareceres_etica (projeto_id, status, parecer, por, atualizado_em) "
        "VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP) "
        "ON CONFLICT(projeto_id) DO UPDATE SET status=excluded.status, parecer=excluded.parecer, "
        "por=excluded.por, atualizado_em=CURRENT_TIMESTAMP",
        (projeto_id, status, parecer, usuario["nome"])
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Parecer de Ética atualizado com sucesso."})


@app.route("/api/projetos/<int:projeto_id>/conselho/voto", methods=["PUT"])
def votar_conselho(projeto_id):
    """Voto do Conselho: cada orientador só registra o próprio voto (identidade vem da sessão)."""
    usuario = usuario_logado()
    if not usuario:
        return jsonify({"error": "Faça login para votar."}), 401
    if usuario["role"] != "orientador":
        return jsonify({"error": "Apenas Orientadores incluídos no Conselho podem votar."}), 403

    data = request.get_json(silent=True) or {}
    status = str(data.get("status", "")).strip().upper()
    comentario = str(data.get("comentario", "")).strip()

    if status not in ("PENDENTE", "APROVADO", "REPROVADO"):
        return jsonify({"error": "Voto inválido."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM conselho_membros WHERE orientador_id = ?", (usuario["id"],))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Você não foi incluído no Conselho. Solicite a um Coordenador ou ao Administrador."}), 403
    cursor.execute("SELECT id FROM projetos WHERE id = ?", (projeto_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Projeto não encontrado."}), 404

    if status == "PENDENTE":
        cursor.execute(
            "DELETE FROM votos_conselho WHERE projeto_id = ? AND orientador_id = ?",
            (projeto_id, usuario["id"])
        )
    else:
        cursor.execute(
            "INSERT INTO votos_conselho (projeto_id, orientador_id, status, comentario, atualizado_em) "
            "VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(projeto_id, orientador_id) DO UPDATE SET status=excluded.status, "
            "comentario=excluded.comentario, atualizado_em=CURRENT_TIMESTAMP",
            (projeto_id, usuario["id"], status, comentario)
        )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Seu voto no Conselho foi registrado."})


# ==========================================
# CARGA MASSIVA VIA JSON (ACERVO PROJETOS / PROFESSORES)
# ==========================================
@app.route("/api/carga-massiva", methods=["POST"])
def carga_massiva_json():
    data = request.get_json(silent=True) or {}
    actor_role, _ = ator_atual()
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
    usuario = usuario_logado()
    if not usuario or usuario["role"] != "aluno":
        return jsonify({"error": "Apenas o aluno convidado pode responder ao convite."}), 403

    data = request.get_json(silent=True) or {}
    status_participacao = data.get("status_participacao")
    justificativa = str(data.get("justificativa", "")).strip() if status_participacao == "RECUSADO" else ""

    if status_participacao not in ["CONFIRMADO", "RECUSADO"]:
        return jsonify({"error": "Status inválido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ra FROM grupo_membros WHERE id = ?", (membro_id,))
    membro = cursor.fetchone()
    if not membro or membro["ra"].lower() != usuario["ra"].lower():
        cursor.close()
        conn.close()
        return jsonify({"error": "Este convite não pertence a você."}), 403
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
    usuario = usuario_logado()
    if not usuario or usuario["role"] != "aluno":
        return jsonify({"error": "Apenas o próprio aluno pode editar o seu nome."}), 403

    data = request.get_json(silent=True) or {}
    novo_nome = str(data.get("nome", "")).strip()

    if not novo_nome:
        return jsonify({"error": "O nome não pode ficar em branco."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT ra FROM grupo_membros WHERE id = ?", (membro_id,))
    membro = cursor.fetchone()
    if not membro or membro["ra"].lower() != usuario["ra"].lower():
        cursor.close()
        conn.close()
        return jsonify({"error": "Este vínculo não pertence a você."}), 403

    cursor.execute("UPDATE grupo_membros SET nome = ? WHERE LOWER(ra) = LOWER(?)", (novo_nome, usuario["ra"]))
    cursor.execute("UPDATE usuarios SET nome = ? WHERE id = ? AND role = 'aluno'", (novo_nome, usuario["id"]))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Nome atualizado com sucesso"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
