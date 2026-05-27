# ADR-008 — Multi-tenant via row-level (organization_id em todas as tabelas)

**Status:** accepted
**Data:** 2026-05-26

## Contexto

Knoxis é multi-tenant desde o dia zero. Cada igreja é uma organização isolada das demais. Há três estratégias clássicas de multi-tenancy:

1. **Database por tenant** — máximo isolamento, máxima sobrecarga operacional.
2. **Schema por tenant** — bom isolamento, migration por schema (multiplica trabalho).
3. **Row-level** — coluna `organization_id` em cada tabela; filtragem na aplicação.

## Decisão

**Row-level com `organization_id` em todas as tabelas de domínio.**

### Detalhes

- Cada modelo que pertence a uma organização declara `organization = ForeignKey(Organization, on_delete=PROTECT)`, com `db_index=True`.
- Mixin `TenantScopedViewSet` (DRF) sobrescreve `get_queryset()` para filtrar por `organization_id = request.current_organization.id`.
- Mixin sobrescreve `perform_create()` para injetar `organization` automaticamente, ignorando qualquer valor enviado pelo cliente.
- Modelos relacionados em cascata (ex.: `Candidate` pertence a `Election` pertence a `Organization`) recebem `organization_id` redundantemente para permitir filtragem direta (evitar joins implícitos em queries críticas).
- Constraints únicas que dependem da organização (ex.: `(organization_id, slug)`) declaradas explicitamente.

### Não usamos RLS (Row-Level Security) do Postgres

Considerado mas rejeitado nesta fase:
- Adiciona complexidade de setup (`SET app.current_org = ?` por conexão).
- Django ORM não tem suporte nativo elegante.
- Camada aplicacional do Django (mixin obrigatório) cobre o necessário com testes específicos.

Pode entrar em fase futura como camada extra de defense-in-depth — não substitui o mixin.

### Testes obrigatórios

- Todo viewset novo tem teste cross-tenant: cria org A e org B, autentica como A, tenta acessar recurso de B → expect 404 (e nunca 200).
- Teste de regressão consolidado que itera todos os viewsets registrados e verifica que herdam de `TenantScopedViewSet`.

## Consequências

### Positivas
- Setup operacional simples: um banco, um schema, uma migration roda para todos.
- Backup centralizado.
- Queries diretas sem mudança de connection ou schema.

### Negativas
- Vazamento cross-tenant é responsabilidade da aplicação. Bug em um viewset = vazamento. Mitigamos com mixin obrigatório, testes e revisão.
- Sem isolamento físico — em caso de pedido de exclusão LGPD de uma organização, precisamos cascade DELETE correto (testado).

## Alternativas consideradas

### Schema por tenant
- Mais isolamento.
- Rejeitado: complexidade de migrations multiplicada por N organizações; backup mais complicado; sem ganho real dada nossa expectativa de uso.

### Database por tenant
- Máximo isolamento.
- Rejeitado: overhead operacional enorme para escala esperada (centenas de tenants).

### RLS do Postgres como única camada
- Defense in depth elegante.
- Rejeitado isoladamente: ORM do Django + DRF não tem padrão estabelecido para isso; risco de configuração errada. Mantemos como opção complementar futura.
