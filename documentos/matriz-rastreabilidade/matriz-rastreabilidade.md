# Matriz de rastreabilidade: Atores × Funcionalidades

Módulo 2: Controle (Registro). Cada linha corresponde a um caso de uso do [Diagrama de Caso de Uso](../caso-de-uso/caso-de-uso.md).

| Funcionalidade | Administrador | Coordenador | Orientador | Aluno | Acesso público |
|---|---|---|---|---|---|
| Carga massiva de projetos | ✔ | ✔ |  |  |  |
| Carga massiva de contas (professores e alunos) | ✔ | ✔ |  |  |  |
| Gerenciar contas de acesso | ✔ | ✔ | ✔ |  |  |
| Definir membros do Conselho (geral ou por curso) | ✔ | ✔ |  |  |  |
| Registrar parecer de Ética | ✔ | ✔ |  |  |  |
| Votar no Conselho e acessar Pareceres (membros incluídos) |  |  | ✔ |  |  |
| Consultar projetos | ✔ | ✔ | ✔ | ✔ | ✔ |
| Consultar histórico de projetos (do aluno: somente os próprios) | ✔ | ✔ | ✔ | ✔ |  |
| Visualizar nome completo e RA dos alunos (formulários de projeto, exportação CSV e Gerenciar Contas) | ✔ | ✔ | ✔ |  |  |
| Escolher exibição do nome (Meu perfil) | ✔ | ✔ | ✔ | ✔ |  |
| Registrar trabalho, grupo e membros (CRUD de trabalhos) | ✔ | ✔ | ✔ |  |  |
| Informar áreas de atuação e setor externo (interdisciplinaridade opcional) | ✔ | ✔ | ✔ |  |  |
| Realizar status: todos, exceto Avaliado | ✔ | ✔ | ✔ |  |  |
| Realizar status Avaliado | ✔ | ✔ |  |  |  |
| Reabrir projeto Finalizado (volta a Concluído ou Desenvolvimento) | ✔ | ✔ |  |  |  |
| Realizar status: Pendente, Cancelado, Concluído |  |  |  | ✔ |  |
| Confirmar participação no grupo (time) |  |  |  | ✔ |  |

Arquivo para planilha: [matriz-rastreabilidade.csv](matriz-rastreabilidade.csv)

## Observações

- A matriz é coerente com o Diagrama de Caso de Uso: cada ✔ corresponde a uma associação entre ator e caso de uso.
- Orientador só realiza status e edita os projetos em que consta como responsável. Um projeto Finalizado só é reaberto pela Coordenação ou pelo Administrador, para corrigir finalizações feitas por engano. Aluno só realiza status nos projetos em que está confirmado.
- Coordenador não cria contas de Coordenador; Orientador cria apenas contas de Aluno; somente o Administrador redefine senhas.
- Consultar projetos: Administrador, Coordenador e Orientador veem todos; Aluno vê os publicados e os seus; Acesso público vê os publicados. Alunos e público nunca veem o RA.
- Votam no Conselho apenas os orientadores incluídos pela Coordenação ou pelo Administrador, no Conselho geral ou no de um curso (neste caso só nos projetos com alunos do curso); cada um vota somente com o próprio login. O menu Pareceres fica oculto para orientadores fora do Conselho.
- Projetos novos, manuais ou por carga massiva, entram em visualização interna e passam sozinhos para Desenvolvimento quando Ética e Conselho aprovam (inclusive os que estiverem Pendentes).
- Um professor pode acumular os perfis de Coordenador e Orientador.
- Meu perfil: todo usuário logado escolhe como o próprio nome aparece, e a escolha vale para todos os perfis nas telas de consulta, inclusive para a própria pessoa. O nome completo e o RA aparecem só para a gestão nos formulários de criar e editar projeto, na exportação CSV e em Gerenciar Contas.
- O orientador responsável de um projeto é escolhido entre as contas de Orientador e Coordenador cadastradas; a edição do projeto exige que o nome da conta conste inteiro no campo Orientador.
