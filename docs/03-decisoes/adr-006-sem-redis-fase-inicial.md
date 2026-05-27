# ADR-006 — Sem Redis na fase inicial

**Status:** accepted
**Data:** 2026-05-26

## Contexto

O usuário sinalizou abertura para Redis se necessário, mas pediu para evitá-lo se não fizer falta. Casos típicos que justificariam Redis em um Django: cache de view/template, channel layer para WebSocket, broker de Celery, rate limiting distribuído, session store.

## Decisão

**Fase 1 não usa Redis.** Justificativa caso a caso:

- **Cache de view:** parciais usam ETag + query agregada com índice. Sem necessidade.
- **WebSocket:** decidido em [ADR-003](adr-003-parciais-em-tempo-real.md) por polling.
- **Celery:** sem background jobs na fase 1. Importação de CSV roda síncrona (centenas de linhas, segundos). Envio de email de recuperação pode usar `django-anymail` síncrono com SMTP.
- **Rate limiting:** `django-ratelimit` com backend de cache local; em deploy single-instance funciona. Caso futuro precise multi-instance, migrar para backend Redis então.
- **Session store:** banco (default Django). Volume desprezível.

## Quando reavaliar

Cenários que devem disparar reconsideração:

1. Necessidade real de push (notificações in-app) → Channels + Redis.
2. Background jobs (geração de PDF pesado, envio de muitos emails, processamento de imagens) → Celery + Redis/RabbitMQ.
3. Múltiplas instâncias do backend atrás de load balancer → rate limit e cache compartilhados → Redis.
4. Performance de session store virou gargalo (improvável dado o volume).

## Consequências

### Positivas
- Stack mais simples: 3 containers (nginx, django, postgres) em vez de 4+.
- Menos custo de infra em VPS pequena.
- Menos superfície de ataque.

### Negativas
- Push em tempo real, se quisermos no futuro, exige introduzir Redis. Sem dívida arquitetural — Channels é additivo.
- Rate limit é por instância — em deploy single-instance é correto, mas escalar horizontalmente exige migrar.

## Alternativas consideradas

### Adicionar Redis "por garantia"
- Rejeitado: YAGNI. Pode ser plugado depois sem refactor estrutural.

### Memcached
- Mais leve que Redis.
- Rejeitado pelo mesmo motivo: nada exige cache distribuído nesta fase.
