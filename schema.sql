-- Ativar chaves estrangeiras no SQLite
PRAGMA foreign_keys = ON;

-- Tabela de Usuários (Administradores, Coordenadores, Orientadores e Alunos)
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
    exibicao_nome TEXT DEFAULT 'completo',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Projetos Extensionistas
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

-- Tabela de Grupos vinculados aos Projetos
CREATE TABLE IF NOT EXISTS grupos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projeto_id INTEGER NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    FOREIGN KEY (projeto_id) REFERENCES projetos(id) ON DELETE CASCADE
);

-- Tabela de Membros do Grupo (Alunos vinculados)
CREATE TABLE IF NOT EXISTS grupo_membros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grupo_id INTEGER NOT NULL,
    ra TEXT NOT NULL,
    nome TEXT NOT NULL,
    status_participacao TEXT DEFAULT 'PENDENTE' CHECK(status_participacao IN ('PENDENTE', 'CONFIRMADO', 'RECUSADO')),
    justificativa_recusa TEXT DEFAULT '',
    FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE
);

-- Tabela de Pareceres de Ética por Projeto
CREATE TABLE IF NOT EXISTS pareceres_etica (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projeto_id INTEGER NOT NULL UNIQUE,
    status TEXT DEFAULT 'PENDENTE' CHECK(status IN ('PENDENTE', 'APROVADO', 'REPROVADO')),
    parecer TEXT DEFAULT '',
    por TEXT DEFAULT '',
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (projeto_id) REFERENCES projetos(id) ON DELETE CASCADE
);

-- Tabela de Membros do Conselho de Orientadores
CREATE TABLE IF NOT EXISTS conselho_membros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orientador_id INTEGER NOT NULL UNIQUE,
    adicionado_por TEXT DEFAULT '',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (orientador_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Tabela de Votos do Conselho por Projeto
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
