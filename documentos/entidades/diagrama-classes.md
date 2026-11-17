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
    +boolean membroConselho
    +registrarProjeto()
    +informarAreas()
    +alterarStatus()
    +votarConselho()
    +registrarParecerEtica()
    +definirMembroConselho()
  }
  class Aluno {
    +int id
    +String ra
    +String nome
    +String email
    +ExibicaoNome exibicaoNome
    +confirmarParticipacao()
    +alterarStatus()
    +escolherExibicaoNome()
    +consultarMeusProjetos()
  }
  class Projeto {
    +int id
    +String titulo
    +String areasAtuacao
    +String interdisciplinaridade
    +String setorExterno
    +StatusProjeto status
    +boolean publicado
    +DateTime criadoEm
    +alterarStatus()
    +publicar()
  }
  class Grupo {
    +int id
    +String nome
    +adicionarMembro()
  }
  class Participacao {
    +StatusParticipacao status
    +String justificativaRecusa
    +confirmar()
    +recusar()
  }
  class ParecerEtica {
    +StatusParecer status
    +String observacao
    +String registradoPor
    +DateTime atualizadoEm
    +registrar()
  }
  class VotoConselho {
    +StatusParecer status
    +String comentario
    +DateTime atualizadoEm
    +votar()
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
  class StatusParticipacao {
    <<enumeration>>
    PENDENTE
    CONFIRMADO
    RECUSADO
  }
  class StatusParecer {
    <<enumeration>>
    PENDENTE
    APROVADO
    REPROVADO
  }
  class ExibicaoNome {
    <<enumeration>>
    COMPLETO
    ABREVIADO
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
  Projeto "1" *-- "1" ParecerEtica : tem
  Projeto "1" *-- "0..*" VotoConselho : recebe
  VotoConselho "0..*" --> "1" Professor : emitido por membro do Conselho
  Projeto ..> StatusProjeto
  Participacao ..> StatusParticipacao
  ParecerEtica ..> StatusParecer
  VotoConselho ..> StatusParecer
  Aluno ..> ExibicaoNome
  Professor ..> Perfil
```

## Entidades

| Entidade | Papel no módulo |
|---|---|
| Projeto | Trabalho extensionista registrado pelo orientador, com áreas de atuação, interdisciplinaridade, setor externo, status, publicação e data de criação |
| Professor | Orientador, Coordenador ou Administrador; o atributo perfil indica qual. Orientadores incluídos no Conselho (membroConselho) votam nos projetos |
| Grupo | Time vinculado ao projeto |
| Aluno | Membro de time. Escolhe como o nome é exibido (exibicaoNome); o RA não pode ser alterado |
| Participacao | Vínculo entre aluno e grupo, com o status (pendente, confirmado ou recusado) e a justificativa de recusa. É preservado mesmo depois de o projeto ser finalizado |
| ParecerEtica | Decisão de Ética sobre o projeto, registrada por Coordenador ou Administrador após avaliação feita fora do sistema |
| VotoConselho | Voto individual de um orientador membro do Conselho sobre um projeto, com comentário. Cada orientador só registra o próprio voto |

## Regras de negócio relacionadas

- O parecer do Conselho é calculado a partir dos votos: **Aprovado** quando mais da metade dos membros aprova, **Reprovado** quando a aprovação deixa de ser possível e **Pendente** nos demais casos.
- O projeto só pode ir para Desenvolvimento com Ética e Conselho aprovados.
- A exibição do nome vale para o público e para outros alunos. Orientadores, Coordenadores e Administradores sempre veem o nome completo e o RA; público e alunos nunca veem o RA.
- Projetos finalizados não são apagados: saem da listagem principal e continuam na pesquisa e no histórico.

## Observação

Os atributos refletem o sistema atual e poderão ser refinados nas próximas etapas.
