# Diagramas de Atividade: Módulo 2 Controle (Registro)

Legenda de cores: azul = ação do ator; cinza = ação do sistema; amarelo = decisão; vermelho = recusa/erro.

## 1. Registrar trabalho, grupo e membros

Ator: Orientador. Imagem: [01-registrar-trabalho-grupo-membros.png](01-registrar-trabalho-grupo-membros.png)

```mermaid
flowchart TD
  ini(("Início")) --> a1["Orientador acessa o sistema"]
  a1 --> a2["Orientador informa os dados do trabalho"]
  a2 --> a3["Orientador informa áreas de atuação, interdisciplinaridade e setor externo"]
  a3 --> d1{"Dados válidos?"}
  d1 -- Não --> s1["Sistema exibe os erros"]
  s1 --> a2
  d1 -- Sim --> s2["Sistema registra o projeto com status NOVO"]
  s2 --> a4["Orientador adiciona o grupo"]
  a4 --> a5["Orientador adiciona um membro (aluno)"]
  a5 --> d2{"Aluno localizado?"}
  d2 -- Não --> s3["Sistema informa que o aluno não foi encontrado"]
  s3 --> a5
  d2 -- Sim --> s4["Sistema vincula o aluno ao grupo, aguardando confirmação"]
  s4 --> d3{"Adicionar outro membro?"}
  d3 -- Sim --> a5
  d3 -- Não --> s5["Sistema salva o grupo e os membros"]
  s5 --> fim((Fim))
  classDef ator fill:#E6F1FB,stroke:#185FA5,color:#0C447C
  classDef sis fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
  classDef dec fill:#FAEEDA,stroke:#854F0B,color:#633806
  class a1,a2,a3,a4,a5 ator
  class s1,s2,s3,s4,s5 sis
  class d1,d2,d3 dec
```

## 2. Realizar status (andamento)

Ator: Orientador, Coordenador, Administrador e Aluno. Imagem: [02-realizar-status-andamento.png](02-realizar-status-andamento.png)

```mermaid
flowchart TD
  ini(("Início")) --> a1["Ator abre o projeto"]
  a1 --> a2["Ator seleciona o novo status"]
  a2 --> d1{"Ator é aluno?"}
  d1 -- Sim --> d2{"Aluno é membro confirmado do grupo?"}
  d2 -- Não --> e1["Sistema recusa: participação não confirmada"]
  d2 -- Sim --> d3{"Status é Pendente, Cancelado ou Concluído?"}
  d3 -- Não --> e2["Sistema recusa: status não permitido ao aluno"]
  d3 -- Sim --> d6{"Transição válida a partir do status atual?"}
  d1 -- "Não" --> d4{"Ator é Coordenador, Administrador ou o orientador responsável?"}
  d4 -- Não --> e4["Sistema recusa: sem permissão sobre o projeto"]
  d4 -- Sim --> d5{"Status é Avaliado e o ator não é Coordenador nem Administrador?"}
  d5 -- Sim --> e5["Sistema recusa: Avaliado é registrado pela coordenação"]
  d5 -- Não --> d6
  d6 -- Não --> e3["Sistema recusa: transição inválida"]
  d6 -- Sim --> d7{"Novo status é Desenvolvimento?"}
  d7 -- Sim --> d8{"Ética e Conselho estão aprovados?"}
  d8 -- Não --> e6["Sistema recusa: pareceres pendentes ou reprovados"]
  d8 -- Sim --> s1["Sistema atualiza o status do projeto"]
  d7 -- Não --> s1
  s1 --> fim((Fim))
  e1 --> fim
  e2 --> fim
  e3 --> fim
  e4 --> fim
  e5 --> fim
  e6 --> fim
  classDef ator fill:#E6F1FB,stroke:#185FA5,color:#0C447C
  classDef sis fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
  classDef dec fill:#FAEEDA,stroke:#854F0B,color:#633806
  classDef err fill:#FCEBEB,stroke:#A32D2D,color:#791F1F
  class a1,a2 ator
  class s1 sis
  class d1,d2,d3,d4,d5,d6,d7,d8 dec
  class e1,e2,e3,e4,e5,e6 err
```

## 3. Confirmar participação no grupo

Ator: Aluno. Imagem: [03-confirmar-participacao-grupo.png](03-confirmar-participacao-grupo.png)

```mermaid
flowchart TD
  ini(("Início")) --> a1["Aluno acessa o sistema"]
  a1 --> s1["Sistema lista os grupos em que o aluno foi adicionado"]
  s1 --> d1{"Há participação pendente?"}
  d1 -- Não --> s2["Sistema informa que não há pendências"]
  d1 -- Sim --> a2["Aluno seleciona o grupo"]
  a2 --> d2{"Aluno confirma a participação?"}
  d2 -- Sim --> s3["Sistema registra a participação como confirmada"]
  d2 -- Não --> s4["Sistema mantém a participação pendente"]
  s2 --> fim((Fim))
  s3 --> fim
  s4 --> fim
  classDef ator fill:#E6F1FB,stroke:#185FA5,color:#0C447C
  classDef sis fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
  classDef dec fill:#FAEEDA,stroke:#854F0B,color:#633806
  class a1,a2 ator
  class s1,s2,s3,s4 sis
  class d1,d2 dec
```

## 4. Carga massiva (professores ou projetos)

Ator: Administrador. Imagem: [04-carga-massiva.png](04-carga-massiva.png)

```mermaid
flowchart TD
  ini(("Início")) --> a1["Administrador acessa a carga massiva"]
  a1 --> a2["Administrador escolhe o tipo: professores ou projetos"]
  a2 --> a3["Administrador envia o arquivo"]
  a3 --> d1{"Formato do arquivo válido?"}
  d1 -- Não --> e1["Sistema rejeita o arquivo e informa o erro"]
  d1 -- Sim --> s1["Sistema lê o próximo registro"]
  s1 --> d2{"Registro válido?"}
  d2 -- Sim --> s2["Sistema grava o registro"]
  d2 -- Não --> s3["Sistema anota o registro como rejeitado"]
  s2 --> d3{"Há mais registros?"}
  s3 --> d3
  d3 -- Sim --> s1
  d3 -- Não --> s4["Sistema exibe o resumo: importados e rejeitados"]
  s4 --> fim((Fim))
  e1 --> fim
  classDef ator fill:#E6F1FB,stroke:#185FA5,color:#0C447C
  classDef sis fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
  classDef dec fill:#FAEEDA,stroke:#854F0B,color:#633806
  classDef err fill:#FCEBEB,stroke:#A32D2D,color:#791F1F
  class a1,a2,a3 ator
  class s1,s2,s3,s4 sis
  class d1,d2,d3 dec
  class e1 err
```

## 5. Registrar parecer de Ética

Ator: Coordenador e Administrador. Imagem: [05-registrar-parecer-etica.png](05-registrar-parecer-etica.png)

```mermaid
flowchart TD
  ini(("Início")) --> x1["Comitê de ética avalia o projeto fora do sistema"]
  x1 --> a1["Coordenador ou Administrador acessa Pareceres"]
  a1 --> a2["Ator seleciona o projeto"]
  a2 --> a3["Ator informa Aprovado, Reprovado ou Pendente e a observação"]
  a3 --> d1{"Ator é Coordenador ou Administrador?"}
  d1 -- Não --> e1["Sistema recusa: parecer de Ética restrito à coordenação"]
  d1 -- Sim --> s1["Sistema grava o parecer, o nome de quem registrou e a data"]
  s1 --> fim((Fim))
  e1 --> fim
  classDef ator fill:#E6F1FB,stroke:#185FA5,color:#0C447C
  classDef sis fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
  classDef dec fill:#FAEEDA,stroke:#854F0B,color:#633806
  classDef err fill:#FCEBEB,stroke:#A32D2D,color:#791F1F
  class a1,a2,a3 ator
  class x1,s1 sis
  class d1 dec
  class e1 err
```

## 6. Definir membros do Conselho

Ator: Coordenador e Administrador. Imagem: [06-definir-membros-conselho.png](06-definir-membros-conselho.png)

```mermaid
flowchart TD
  ini(("Início")) --> a1["Ator acessa Criar Acessos / Contas"]
  a1 --> a2["Ator escolhe um orientador"]
  a2 --> a3["Ator seleciona Incluir ou Remover do Conselho"]
  a3 --> d1{"Ator é Coordenador ou Administrador?"}
  d1 -- Não --> e1["Sistema recusa: sem permissão"]
  d1 -- Sim --> d2{"A conta é de Orientador?"}
  d2 -- Não --> e2["Sistema recusa: somente orientadores participam do Conselho"]
  d2 -- Sim --> d3{"Incluir?"}
  d3 -- Sim --> s1["Sistema inclui o orientador no Conselho"]
  d3 -- Não --> s2["Sistema remove o orientador do Conselho e deixa de contar o voto dele"]
  s1 --> fim((Fim))
  s2 --> fim
  e1 --> fim
  e2 --> fim
  classDef ator fill:#E6F1FB,stroke:#185FA5,color:#0C447C
  classDef sis fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
  classDef dec fill:#FAEEDA,stroke:#854F0B,color:#633806
  classDef err fill:#FCEBEB,stroke:#A32D2D,color:#791F1F
  class a1,a2,a3 ator
  class s1,s2 sis
  class d1,d2,d3 dec
  class e1,e2 err
```

## 7. Votar no Conselho

Ator: Orientador membro do Conselho. Imagem: [07-votar-conselho.png](07-votar-conselho.png)

```mermaid
flowchart TD
  ini(("Início")) --> a1["Orientador entra com o próprio login e acessa Pareceres"]
  a1 --> a2["Orientador escolhe o projeto"]
  a2 --> a3["Orientador informa Aprovado ou Reprovado e o comentário"]
  a3 --> d1{"Orientador está no Conselho?"}
  d1 -- Não --> e1["Sistema recusa: solicitar inclusão à coordenação"]
  d1 -- Sim --> s1["Sistema grava o voto somente na conta do orientador logado"]
  s1 --> s2["Sistema recalcula o parecer do Conselho"]
  s2 --> d2{"Mais da metade dos membros aprovou?"}
  d2 -- Sim --> s3["Parecer do Conselho: Aprovado"]
  d2 -- Não --> d3{"Aprovação deixou de ser possível?"}
  d3 -- Sim --> s4["Parecer do Conselho: Reprovado"]
  d3 -- Não --> s5["Parecer do Conselho: Pendente"]
  s3 --> fim((Fim))
  s4 --> fim
  s5 --> fim
  e1 --> fim
  classDef ator fill:#E6F1FB,stroke:#185FA5,color:#0C447C
  classDef sis fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
  classDef dec fill:#FAEEDA,stroke:#854F0B,color:#633806
  classDef err fill:#FCEBEB,stroke:#A32D2D,color:#791F1F
  class a1,a2,a3 ator
  class s1,s2,s3,s4,s5 sis
  class d1,d2,d3 dec
  class e1 err
```

## 8. Escolher a exibição do nome (Meu perfil)

Ator: Aluno. Imagem: [08-exibicao-nome-perfil.png](08-exibicao-nome-perfil.png)

```mermaid
flowchart TD
  ini(("Início")) --> a1["Aluno acessa Meu perfil"]
  a1 --> s1["Sistema mostra nome completo e RA, ambos sem edição"]
  s1 --> a2["Aluno escolhe: nome completo ou primeiro nome e último sobrenome"]
  a2 --> a3["Aluno salva a preferência"]
  a3 --> d1{"Opção válida?"}
  d1 -- Não --> e1["Sistema recusa a alteração"]
  d1 -- Sim --> s2["Sistema grava somente a preferência de exibição"]
  s2 --> s3["Público e outros alunos passam a ver o nome conforme a preferência; gestão continua vendo o nome completo"]
  s3 --> fim((Fim))
  e1 --> fim
  classDef ator fill:#E6F1FB,stroke:#185FA5,color:#0C447C
  classDef sis fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
  classDef dec fill:#FAEEDA,stroke:#854F0B,color:#633806
  classDef err fill:#FCEBEB,stroke:#A32D2D,color:#791F1F
  class a1,a2,a3 ator
  class s1,s2,s3 sis
  class d1 dec
  class e1 err
```

## 9. Consultar projetos, histórico e filtros

Ator: Todos os atores. Imagem: [09-consultar-projetos-historico.png](09-consultar-projetos-historico.png)

```mermaid
flowchart TD
  ini(("Início")) --> a1["Ator acessa Consultar Projetos, Meus projetos ou Histórico"]
  a1 --> a2["Ator informa filtros: projeto, aluno, RA, situação e período"]
  a2 --> d1{"Ator tem perfil de gestão?"}
  d1 -- Não --> d2{"Ator é aluno?"}
  d2 -- Sim --> s1["Sistema considera os projetos publicados e os vinculados ao aluno"]
  d2 -- Não --> s2["Sistema considera apenas os projetos publicados"]
  d1 -- Sim --> s3["Sistema considera todos os projetos"]
  s1 --> d3{"Há algum filtro ou pesquisa ativa?"}
  s2 --> d3
  s3 --> d3
  d3 -- Não --> s4["Sistema oculta os projetos Finalizados da listagem principal"]
  d3 -- Sim --> s5["Sistema inclui os Finalizados no resultado"]
  s4 --> s6["Sistema ordena por data de criação, do mais recente ao mais antigo"]
  s5 --> s6
  s6 --> d4{"Ator tem perfil de gestão?"}
  d4 -- Sim --> s7["Sistema exibe nome completo e RA dos alunos"]
  d4 -- Não --> s8["Sistema omite o RA e exibe o nome conforme a preferência de cada aluno"]
  s7 --> fim((Fim))
  s8 --> fim
  classDef ator fill:#E6F1FB,stroke:#185FA5,color:#0C447C
  classDef sis fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
  classDef dec fill:#FAEEDA,stroke:#854F0B,color:#633806
  classDef err fill:#FCEBEB,stroke:#A32D2D,color:#791F1F
  class a1,a2 ator
  class s1,s2,s3,s4,s5,s6,s7,s8 sis
  class d1,d2,d3,d4 dec
```
