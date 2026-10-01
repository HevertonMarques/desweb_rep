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

Ator: Orientador e Aluno. Imagem: [02-realizar-status-andamento.png](02-realizar-status-andamento.png)

```mermaid
flowchart TD
  ini(("Início")) --> a1["Ator abre o projeto"]
  a1 --> a2["Ator seleciona o novo status"]
  a2 --> d1{"Ator é aluno?"}
  d1 -- Sim --> d2{"Aluno é membro confirmado do grupo?"}
  d2 -- Não --> e1["Sistema recusa: participação não confirmada"]
  d2 -- Sim --> d3{"Status é Cancelado, Pendente ou Concluído?"}
  d3 -- Não --> e2["Sistema recusa: status não permitido ao aluno"]
  d3 -- Sim --> d4{"Transição válida a partir do status atual?"}
  d1 -- "Não (orientador)" --> d4
  d4 -- Não --> e3["Sistema recusa: transição inválida"]
  d4 -- Sim --> s1["Sistema atualiza o status do projeto"]
  s1 --> fim((Fim))
  e1 --> fim
  e2 --> fim
  e3 --> fim
  classDef ator fill:#E6F1FB,stroke:#185FA5,color:#0C447C
  classDef sis fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
  classDef dec fill:#FAEEDA,stroke:#854F0B,color:#633806
  classDef err fill:#FCEBEB,stroke:#A32D2D,color:#791F1F
  class a1,a2 ator
  class s1 sis
  class d1,d2,d3,d4 dec
  class e1,e2,e3 err
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

