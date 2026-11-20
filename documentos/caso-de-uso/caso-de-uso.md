# Diagrama de Caso de Uso: Módulo 2 Controle (Registro)

![Diagrama de caso de uso](caso-de-uso.png)

Versão vetorial: [caso-de-uso.svg](caso-de-uso.svg)

## Atores

| Ator | Funcionalidades |
|---|---|
| Administrador | Carga massiva de projetos e de contas; gerenciar todas as contas; definir os membros do Conselho (geral ou de um curso específico); registrar o parecer de Ética; registrar projetos; consultar projetos e o histórico completo, com RA e nome completo; realizar qualquer status, inclusive Avaliado, e reabrir projetos finalizados; escolher como o nome é exibido (Meu perfil) |
| Coordenador | Carga massiva de projetos e de contas (sem criar coordenadores); gerenciar contas de orientadores e alunos; definir os membros do Conselho (geral ou de um curso específico); registrar o parecer de Ética; registrar projetos; consultar projetos e o histórico completo, com RA e nome completo; realizar qualquer status, inclusive Avaliado, e reabrir projetos finalizados; escolher como o nome é exibido (Meu perfil) |
| Orientador (professor) | Cadastrar trabalhos (CRUD) e informar áreas de atuação e setor externo, e a interdisciplinaridade quando houver (opcional); criar contas de alunos; votar no Conselho quando for membro (geral ou do curso dos alunos do projeto), com comentário, e ver o menu Pareceres só nesse caso; consultar projetos e o histórico completo, com RA e nome completo; realizar os status dos projetos em que é o responsável (exceto Avaliado); escolher como o nome é exibido (Meu perfil) |
| Aluno (membro de time) | Confirmar ou recusar participação no grupo; realizar os status Pendente, Cancelado e Concluído nos projetos em que está confirmado; escolher como o nome é exibido (Meu perfil); consultar os projetos publicados e o histórico dos projetos em que participa ou participou, sem ver RA de ninguém |
| Acesso público | Consulta de informações dos projetos publicados, sem RA e com os nomes conforme a preferência de cada pessoa (alunos e gestão); o nome completo e o RA ficam só para a gestão em formulários, exportação CSV e Gerenciar Contas |

## Fluxo resumido de uso

Orientador registra o projeto → informa áreas e setor externo (e interdisciplinaridade, se houver) → adiciona grupo e membros → alunos confirmam participação → comitê de ética avalia fora do sistema e a coordenação registra o parecer de Ética → membros do Conselho votam com o próprio login → com os dois pareceres aprovados, o projeto vai para Desenvolvimento → orientador e alunos acompanham e realizam status → ao final, a coordenação registra Avaliado, ou o projeto é Finalizado e segue consultável no histórico.
