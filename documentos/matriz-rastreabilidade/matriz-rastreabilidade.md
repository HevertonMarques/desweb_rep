# Matriz de rastreabilidade: Atores × Funcionalidades

Módulo 2: Controle (Registro). Cada linha corresponde a um caso de uso do [Diagrama de Caso de Uso](../caso-de-uso/caso-de-uso.md).

| Funcionalidade | Administrador | Coordenador | Orientador | Aluno | Acesso público |
|---|---|---|---|---|---|
| Carga massiva de projetos | ✔ | ✔ |  |  |  |
| Carga massiva de contas (professores e alunos) | ✔ | ✔ |  |  |  |
| Gerenciar contas de acesso | ✔ | ✔ | ✔ |  |  |
| Definir membros do Conselho | ✔ | ✔ |  |  |  |
| Registrar parecer de Ética | ✔ | ✔ |  |  |  |
| Votar no Conselho (membros incluídos) |  |  | ✔ |  |  |
| Consultar projetos | ✔ | ✔ | ✔ | ✔ | ✔ |
| Consultar histórico de projetos (do aluno: somente os próprios) | ✔ | ✔ | ✔ | ✔ |  |
| Visualizar RA e nome completo dos alunos | ✔ | ✔ | ✔ |  |  |
| Escolher exibição do nome (Meu perfil) |  |  |  | ✔ |  |
| Registrar trabalho, grupo e membros (CRUD de trabalhos) | ✔ | ✔ | ✔ |  |  |
| Informar áreas de atuação, interdisciplinaridade e setor externo | ✔ | ✔ | ✔ |  |  |
| Realizar status: todos, exceto Avaliado | ✔ | ✔ | ✔ |  |  |
| Realizar status Avaliado | ✔ | ✔ |  |  |  |
| Realizar status: Pendente, Cancelado, Concluído |  |  |  | ✔ |  |
| Confirmar participação no grupo (time) |  |  |  | ✔ |  |

Arquivo para planilha: [matriz-rastreabilidade.csv](matriz-rastreabilidade.csv)

## Observações

- A matriz é coerente com o Diagrama de Caso de Uso: cada ✔ corresponde a uma associação entre ator e caso de uso.
- Orientador só realiza status e edita os projetos em que consta como responsável. Aluno só realiza status nos projetos em que está confirmado.
- Coordenador não cria contas de Coordenador; Orientador cria apenas contas de Aluno; somente o Administrador redefine senhas.
- Consultar projetos: Administrador, Coordenador e Orientador veem todos; Aluno vê os publicados e os seus; Acesso público vê os publicados. Alunos e público nunca veem o RA.
- Votam no Conselho apenas os orientadores incluídos pela Coordenação ou pelo Administrador; cada um vota somente com o próprio login.
- Um professor pode acumular os perfis de Coordenador e Orientador.
