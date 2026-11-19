# [Controle HRV]

Projeto Extensionista 2026 sem. 2: Módulo 2, Controle (Registro).

Sistema web para registrar e controlar os projetos extensionistas desenvolvidos durante o semestre letivo, usado pelo coordenador, pelos professores orientadores e pelos alunos.

## Equipe

| RA | Nome | Responsabilidade (NEG/DEV) |
|---|---|---|
| [33711] | [Heverton Marques Oliveira] | [NEG] |
| [34001] | [Victor Augusto da Silva Hollanda] | [DEV] |
| [33772] | [Raul Domingues da Silva Honorio] | [NEG] |

Grupo: [4]. Orientador: [André Marcos].

## Documentação

A modelagem da Etapa 1 está na pasta [documentos](documentos/README.md): caso de uso, atividades, classes, estados e matriz de rastreabilidade.

## Nomes e orientadores

- Cada pessoa escolhe em **Meu perfil** como o próprio nome aparece (completo, ou primeiro nome e último sobrenome). A escolha vale para todos os perfis nas telas de consulta, inclusive para a própria pessoa.
- O nome completo e o RA só aparecem para a gestão nos formulários de criar e editar projeto, na exportação CSV e em Gerenciar Contas. Público e alunos nunca recebem o RA.
- Cada projeto pode ter **um ou mais orientadores/coorientadores**, selecionados por checklist entre as contas de Orientador e Coordenador cadastradas. Todos os orientadores vinculados ao projeto possuem permissão para editá-lo, publicá-lo e alterar seus estados permitidos. Na carga massiva de projetos em JSON, pode-se informar `"orientadores": ["Nome 1", "Nome 2"]` ou `"orientador_nome": "Nome 1, Nome 2"`, sempre correspondendo aos nomes completos das contas cadastradas (caso contrário o projeto é ignorado).

## Configuração local (segredos.py)

O arquivo `segredos.py` não vai para o GitHub (veja `.gitignore`) e fica na mesma pasta do `app.py`:

```python
SECRET_KEY = "uma-chave-longa-e-aleatoria"
ADMIN_SENHA_INICIAL = "senha-do-primeiro-acesso"   # opcional
```

`ADMIN_SENHA_INICIAL` só é usada quando o banco ainda não existe e o Administrador é criado. Sem ela, o sistema gera uma senha aleatória e a mostra uma única vez no log do servidor. Um banco já existente não é alterado. A senha do Administrador não fica no código-fonte.

Todas as senhas ficam no banco apenas como hash (PBKDF2-SHA256 com sal individual); ninguém, nem o Administrador, consegue ver a senha de outra pessoa. Quem esquece a senha tem a conta redefinida pelo Administrador para a provisória. Senhas antigas em texto puro são convertidas sozinhas na primeira vez em que o site abre com esta versão, e essa conversão não tem volta: antes de atualizar, faça uma cópia do arquivo `.db`.

## Cronograma

| Etapa | Entrega | Prazo |
|---|---|---|
| 1 | Análise e modelagem | 24/set |
| 2 | Primeira versão do protótipo | 29/out |
| 3 | MVP e testes | 26/nov |

## Licença e Atribuição

Este repositório contém o código de programação e os materiais do trabalho acadêmico associado, ambos licenciados sob a **Licença MIT**.

- **Uso livre:** é permitido copiar, modificar, distribuir e utilizar o código comercialmente.
- **Exigência de créditos:** é obrigatório manter o aviso de direitos autorais e a licença em todas as cópias ou partes substanciais do software.
- **Sem garantias:** o código é fornecido "como está", sem garantias de qualquer tipo.

Termos completos no arquivo [LICENSE](LICENSE).
