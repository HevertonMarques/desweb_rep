# Matriz de rastreabilidade: Atores × Funcionalidades

Módulo 2: Controle (Registro). Cada linha corresponde a um caso de uso do [Diagrama de Caso de Uso](../caso-de-uso/caso-de-uso.md).

| Funcionalidade | Administrador | Coordenador | Orientador | Aluno | Acesso público |
|---|---|---|---|---|---|
| Carga massiva de projetos | ✔ |  |  |  |  |
| Carga massiva de professores | ✔ |  |  |  |  |
| CRUD de professor |  | ✔ |  |  |  |
| Consultar projetos |  | ✔ |  |  | ✔ |
| Registrar trabalho, grupo e membros (CRUD de trabalhos) |  |  | ✔ |  |  |
| Informar áreas de atuação, interdisciplinaridade e setor externo |  |  | ✔ |  |  |
| Realizar status (andamento): todos os status |  |  | ✔ |  |  |
| Realizar status (andamento): Cancelado, Pendente, Concluído |  |  |  | ✔ |  |
| Confirmar participação no grupo (time) |  |  |  | ✔ |  |

Arquivo para planilha: [matriz-rastreabilidade.csv](matriz-rastreabilidade.csv)

## Observações

- A matriz é coerente com o Diagrama de Caso de Uso: cada ✔ corresponde a uma associação entre ator e caso de uso.
- O ator Acesso público aparece apenas com consulta, conforme a tabela do módulo (acesso público: sim, consulta).
- Um professor pode acumular os perfis de Coordenador e Orientador.
