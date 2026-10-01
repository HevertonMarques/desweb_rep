# Diagrama de Classes: Módulo 2 Controle (Registro)

Imagem: [diagrama-classes.png](diagrama-classes.png)

```mermaid
classDiagram
  direction LR
  class Professor {
    +int id
    +String nome
    +String email
    +Perfil perfil
    +registrarProjeto()
    +informarAreas()
    +alterarStatus()
  }
  class Aluno {
    +int id
    +String ra
    +String nome
    +String email
    +confirmarParticipacao()
    +alterarStatus()
  }
  class Projeto {
    +int id
    +String titulo
    +String areasAtuacao
    +String interdisciplinaridade
    +String setorExterno
    +StatusProjeto status
    +alterarStatus()
  }
  class Grupo {
    +int id
    +String nome
    +adicionarMembro()
  }
  class Participacao {
    +boolean confirmada
    +confirmar()
  }
  class StatusProjeto {
    <<enumeration>>
    NOVO
    PENDENTE
    DESENVOLVIMENTO
    CANCELADO
    CONCLUIDO
    FINALIZADO
    LIBERADO_APRESENTACAO
    AVALIADO
  }
  class Perfil {
    <<enumeration>>
    ADMINISTRADOR
    COORDENADOR
    ORIENTADOR
  }
  Professor "1" --> "0..*" Projeto : orienta
  Projeto "1" *-- "1" Grupo : possui
  Grupo "1" *-- "1..*" Participacao : composto por
  Participacao "0..*" --> "1" Aluno : refere-se a
  Projeto ..> StatusProjeto
  Professor ..> Perfil
```

## Entidades

| Entidade | Papel no módulo |
|---|---|
| Projeto | Trabalho extensionista registrado pelo orientador, com áreas de atuação, interdisciplinaridade, setor externo e status |
| Professor | Orientador do projeto; o atributo perfil indica Administrador, Coordenador ou Orientador |
| Grupo | Time vinculado ao projeto |
| Aluno | Membro de time |
| Participacao | Vínculo entre aluno e grupo, com a confirmação de participação |

## Observação

Os atributos são uma primeira proposta e poderão ser refinados nas próximas etapas.
