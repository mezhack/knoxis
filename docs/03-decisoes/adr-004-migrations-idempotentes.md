# ADR-004 — Migrations idempotentes obrigatórias

**Status:** accepted
**Data:** 2026-05-26

## Contexto

Migrations precisam ser seguras de rodar múltiplas vezes — em ambientes de dev com reset frequente, em deploys que reiniciam containers, em situações de recuperação onde o estado parcial precisa ser reconciliado. Django migrations já são bem-comportadas, mas migrations customizadas (data migrations via `RunPython`) e operações específicas (índices condicionais, constraints, dados seed) frequentemente quebram em segunda execução.

## Decisão

Toda migration **deve poder rodar duas vezes consecutivas sem erro e sem alterar estado a partir da segunda execução**. Isso é verificado em CI.

### Regras por tipo de operação

#### Schema (criar/alterar tabela, coluna)
- Operações nativas do Django (`migrations.CreateModel`, `AddField`, etc.) já são idempotentes em conjunto com o `django_migrations` table — Django pula migrations já aplicadas. ✅
- **Operações SQL cruas via `RunSQL` exigem cuidado:**
  - `CREATE INDEX` → usar `CREATE INDEX IF NOT EXISTS`.
  - `CREATE TYPE` (enum) → guardar com `DO $$ BEGIN ... EXCEPTION WHEN duplicate_object THEN null; END $$;`.
  - `ALTER TABLE ... ADD CONSTRAINT` → `DROP IF EXISTS` antes, ou usar `DO` block com checagem em `information_schema`.
  - Sempre fornecer `reverse_sql`, mesmo que seja `migrations.RunSQL.noop`.

#### Dados (RunPython)
- Sempre fornecer `reverse_code` (mesmo que `noop`).
- Inserções: usar `get_or_create` ou `update_or_create`, nunca `create` direto.
- Atualizações em bulk: verificar pré-condições com filter antes (`if not Model.objects.filter(...).exists(): ...`).
- Não depender da ordem de outras migrations além das declaradas em `dependencies`.

#### Dados sensíveis a estado pré-existente
- Quando a migration depende de algo já existir (ex.: "para cada Election sem default_x, setar X"), envolver em filter que naturalmente vira no-op na segunda execução: `Election.objects.filter(default_x__isnull=True).update(default_x=valor)`.

### Verificação em CI

Job de teste obrigatório:

1. `python manage.py migrate` (aplica tudo)
2. `python manage.py migrate` (roda de novo)
3. Verificar que o segundo retornou "No migrations to apply".

Adicionalmente, para cada migration nova, rodar:

1. Subir banco vazio + migrate
2. Snapshot do schema (`pg_dump --schema-only`)
3. Migrate de novo
4. Snapshot do schema novamente
5. `diff` deve ser vazio.

### Documentação por migration

Migrations não-triviais (`RunPython`, `RunSQL`) recebem docstring no topo:

```python
class Migration(migrations.Migration):
    """
    Seeds default 'Presbítero' and 'Diácono' positions on existing elections.
    Idempotent: uses get_or_create per (election, name).
    """
```

## Consequências

### Positivas
- Deploy seguro mesmo em reinícios e racing conditions.
- Recuperação de falhas parciais sem intervenção manual.
- Test de migrations pega bugs cedo.

### Negativas
- Migrations levam um pouco mais de código (checks adicionais).
- Tempo extra em CI.

## Alternativas consideradas

### Confiar no Django migration tracker
- O `django_migrations` table já evita reaplicação. Suficiente para schema padrão, mas falha em `RunSQL` cru e em data migrations sem guardas.
- Rejeitado isoladamente — usamos em conjunto com as regras acima.

### Usar Alembic
- Mais granular, mas duplica o sistema de migrations (Django ORM + Alembic seria caótico).
- Rejeitado.

### Idempotência opcional
- "Marcamos migrations sensíveis."
- Rejeitado: requer disciplina humana frágil. Regra simples (todas idempotentes) é mais segura.
