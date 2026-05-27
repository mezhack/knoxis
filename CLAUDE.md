# Instruções do projeto Knoxis

Este arquivo complementa o CLAUDE.md global. Em caso de conflito, o global prevalece para regras de comportamento; este arquivo prevalece para padrões de stack e regras específicas deste projeto.

## Stack

- **Backend:** Python 3.12, Django 5.x, Django REST Framework
- **Frontend:** React 18 + Vite + TypeScript
- **Banco:** PostgreSQL 16
- **Auth:** Sessão Django em cookie httpOnly + Secure + SameSite=Lax, CSRF habilitado, Argon2id para hash de senha
- **Deploy:** VPS com Docker Compose (Nginx + Gunicorn + Postgres)

Decisões detalhadas em [docs/03-decisoes/](docs/03-decisoes/).

## Regras inegociáveis (além das globais)

### Migrations idempotentes
- Toda migration deve poder rodar duas vezes sem erro e sem alterar estado a partir da segunda execução.
- Usar `RunPython` com `reverse_code` definido e guardas explícitas para criação condicional de dados.
- Constraints, índices e checks: usar `IF NOT EXISTS` ou validação prévia. Detalhes em [ADR-004](docs/03-decisoes/adr-004-migrations-idempotentes.md).

### Voto secreto é invariante
- Não existe coluna, log, métrica ou cache que ligue `voter_id` ao conteúdo do voto após a submissão.
- A tabela `votes` nunca recebe `voter_id` ou `cpf`. A presença é registrada em tabela separada (`voter_attendance`).
- Toda nova feature precisa ser validada contra esse invariante antes do merge.

### Multi-tenant desde o dia zero
- Toda entidade de dado de eleição é escopada por `organization_id`.
- Queries do backend devem sempre filtrar por organização do usuário logado.
- Testes precisam cobrir vazamento cross-tenant.

### CPF é dado sensível
- CPF nunca aparece em logs (mascarar como `***.***.***-99`).
- Armazenado como hash HMAC determinístico para matching; opcionalmente armazenamos `cpf_last4` para exibição mascarada. Detalhes em [ADR-007](docs/03-decisoes/adr-007-armazenamento-cpf.md).

## Padrões de código

- Backend: PEP 8, `ruff` + `black`. Type hints em código de domínio.
- Frontend: ESLint + Prettier. Componentes funcionais com hooks. TanStack Query para estado de servidor.
- Sem comentários óbvios. Apenas quando o "porquê" não for evidente do código.
- Mensagens de commit em português, imperativo, sem `Co-Authored-By`.

## Fluxo de desenvolvimento

1. Antes de qualquer código: ler a fase atual em [docs/06-roadmap/fases.md](docs/06-roadmap/fases.md) e os requisitos relacionados.
2. Implementar a fase, com testes de aceitação derivados das specs.
3. Cada PR atualiza a documentação afetada no mesmo commit.
4. Nenhuma fase começa antes da anterior ser validada manualmente em ambiente local.

## Ordem de leitura recomendada para entender o domínio

1. [docs/01-especificacoes/glossario.md](docs/01-especificacoes/glossario.md)
2. [docs/01-especificacoes/regras-de-negocio.md](docs/01-especificacoes/regras-de-negocio.md)
3. [docs/01-especificacoes/requisitos.md](docs/01-especificacoes/requisitos.md)
4. [docs/04-modelo-de-dados/schema.md](docs/04-modelo-de-dados/schema.md)
