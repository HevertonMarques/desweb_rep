CREATE DATABASE IF NOT EXISTS modulo2_extensionista CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE modulo2_extensionista;

-- Tabela de Usuários (Admin, Coordenador, Orientador, Aluno)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ra VARCHAR(50) NOT NULL UNIQUE,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    role ENUM('admin', 'coordenador', 'orientador', 'aluno') NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Projetos Extensionistas
CREATE TABLE IF NOT EXISTS projetos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    setor_externo VARCHAR(255) NOT NULL,
    areas_atuacao VARCHAR(255) NOT NULL,
    interdisciplinaridade VARCHAR(255) NOT NULL,
    status ENUM('NOVO', 'PENDENTE', 'DESENVOLVIMENTO', 'CANCELADO', 'CONCLUIDO', 'FINALIZADO', 'LIBERADO_APRESENTACAO', 'AVALIADO') DEFAULT 'NOVO',
    publicado BOOLEAN DEFAULT FALSE,
    orientador_nome VARCHAR(150) NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Grupos
CREATE TABLE IF NOT EXISTS grupos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    projeto_id INT NOT NULL UNIQUE,
    nome VARCHAR(150) NOT NULL,
    FOREIGN KEY (projeto_id) REFERENCES projetos(id) ON DELETE CASCADE
);

-- Tabela de Membros do Grupo (Vinculação por RA)
CREATE TABLE IF NOT EXISTS grupo_membros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grupo_id INT NOT NULL,
    ra VARCHAR(50) NOT NULL,
    nome VARCHAR(150) NOT NULL,
    status_participacao ENUM('PENDENTE', 'CONFIRMADO', 'RECUSADO') DEFAULT 'PENDENTE',
    FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE
);

-- Inserção APENAS do Administrador inicial
INSERT INTO usuarios (ra, nome, email, senha, role)
SELECT 'ADMIN01', 'Administrador FACCAMP', 'admin@faccamp.com', 'adminhrv2026', 'admin'
WHERE NOT EXISTS (
    SELECT 1 FROM usuarios WHERE email = 'admin@faccamp.com'
);
