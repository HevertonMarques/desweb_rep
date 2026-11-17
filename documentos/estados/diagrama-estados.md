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
  Liberado --> Avaliado : coordenação registra
  Cancelado --> [*]
  Finalizado --> [*]
  Avaliado --> [*]
```

## Estados finais

Cancelado, Finalizado e Avaliado. Nenhum deles aceita nova mudança de estado.

## Quem realiza cada estado

| Estado | Orientador responsável, Coordenador e Administrador | Aluno confirmado no grupo | Condição |
|---|---|---|---|
| Novo | Automático | Automático | Criação do projeto |
| Pendente | Sim | Sim | A partir de Novo ou Desenvolvimento |
| Desenvolvimento | Sim | Não | Pareceres de Ética **e** do Conselho aprovados |
| Cancelado | Sim | Sim | A partir de Novo ou Desenvolvimento |
| Concluído | Sim | Sim | A partir de Desenvolvimento |
| Finalizado | Sim | Não | A partir de Concluído |
| Liberado apresentação | Sim | Não | A partir de Concluído |
| Avaliado | Somente Coordenador e Administrador | Não | A partir de Liberado apresentação, após a avaliação na mostra |

## Regras

- O orientador só altera os projetos em que consta como responsável; Coordenador e Administrador alteram todos.
- O aluno só altera o estado dos projetos em que sua participação está **confirmada**, e apenas para Pendente, Cancelado ou Concluído.
- Qualquer mudança para Desenvolvimento, inclusive o retorno a partir de Concluído, exige os pareceres de Ética e do Conselho aprovados ([atividades 05 a 07](../atividades/diagramas-atividade.md)).
- Projetos Finalizados saem da listagem principal, mas continuam disponíveis na pesquisa e no histórico. Nenhum projeto é apagado ao mudar de estado.
- Projetos antigos no estado "Em andamento" foram convertidos para Desenvolvimento.
