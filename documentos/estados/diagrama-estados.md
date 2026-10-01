# Diagrama de Estados: Projeto (Módulo 2 Controle)

Imagem: [diagrama-estados.png](diagrama-estados.png)

```mermaid
stateDiagram-v2
  direction TB
  state "Concluído" as Concluido
  state "Liberado apresentação" as Liberado
  [*] --> Novo : criação automática
  Novo --> Pendente
  Novo --> Desenvolvimento
  Novo --> Cancelado
  Pendente --> Desenvolvimento
  Desenvolvimento --> Pendente
  Desenvolvimento --> Cancelado
  Desenvolvimento --> Concluido
  Concluido --> Desenvolvimento
  Concluido --> Finalizado
  Concluido --> Liberado
  Liberado --> Avaliado : automático
  Cancelado --> [*]
  Finalizado --> [*]
  Avaliado --> [*]
```

## Estados finais

Cancelado, Finalizado e Avaliado.

## Quem realiza cada status

| Status | Quem realiza |
|---|---|
| Novo | Automático (criação do projeto) |
| Pendente | Orientador ou Aluno |
| Desenvolvimento | Orientador |
| Cancelado | Orientador ou Aluno |
| Concluído | Orientador ou Aluno |
| Finalizado | Orientador |
| Liberado apresentação | Orientador |
| Avaliado | Automático (após a avaliação na mostra) |

O orientador realiza todos os status; o aluno realiza apenas Cancelado, Pendente e Concluído.
