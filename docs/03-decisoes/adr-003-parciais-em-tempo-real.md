# ADR-003 — Parciais em tempo real via polling

**Status:** accepted
**Data:** 2026-05-26

## Contexto

O organizador precisa acompanhar a contagem parcial em tempo real durante o escrutínio aberto, em uma aba dedicada (não vazada para o eleitor). Latência aceitável: alguns segundos. Volume esperado: centenas de votos por escrutínio, raramente milhares.

Opções avaliadas:
- WebSocket (Django Channels)
- Server-Sent Events (SSE)
- HTTP polling de baixo intervalo

## Decisão

**HTTP polling a cada 3 segundos**, do frontend do organizador para a rota `/api/v1/admin/escrutinios/{id}/parciais`.

Otimizações:
- Resposta inclui `ETag` baseado em `(escrutinio.id, escrutinio.status, COUNT(votes WHERE escrutinio_id = ?))`. Cliente envia `If-None-Match`; servidor responde `304 Not Modified` quando nada mudou.
- Query única agregada (`SELECT candidate_id, COUNT(*) ... GROUP BY ...`) com índice em `votes(escrutinio_id, candidate_id)`.
- Polling para automaticamente quando o escrutínio sai de `aberto`.

## Justificativa

- **Simplicidade:** sem dependência de Channels, Redis, broker, infra extra. Sem ASGI/WSGI híbrido.
- **Volume modesto:** ~20 organizadores simultâneos no pior caso (uma igreja grande, vários assistentes), 1 request a cada 3s = 7 req/s no pico. Trivial.
- **Compatibilidade total** com Gunicorn WSGI padrão.
- **Funciona atrás de qualquer proxy**, qualquer cliente. Sem upgrade de protocolo.

## Consequências

### Positivas
- Stack permanece WSGI puro. Deploy simples.
- Sem dependência de Redis na fase inicial (ver ADR-006).
- ETag elimina payload repetido — custo real é apenas a query agregada quando há mudança.

### Negativas
- Latência mínima ~1.5s (média do intervalo).
- Sem push real — se quiser empurrar "escrutínio encerrado" pro frontend, depende do próximo poll.

### Trade-off
- Caso futuro: tela pública projetada exibindo resultados pós-escrutínio para a assembleia. Polling ainda serve. Se um dia for necessário pushar (ex.: notificação ao eleitor de "escrutínio aberto"), reavaliamos com Channels.

## Alternativas consideradas

### Django Channels (WebSocket)
- Push instantâneo.
- Rejeitado: requer ASGI, Daphne/Uvicorn, geralmente Redis como channel layer. Overhead alto para o ganho real.

### SSE com `StreamingHttpResponse`
- Mais simples que WebSocket, ainda push.
- Rejeitado: conexões longas atrapalham Gunicorn (workers ocupados). Funcionaria com workers async, mas adiciona complexidade.

### Polling a 1s
- Mais responsivo.
- Rejeitado: 3s é suficiente para uso humano; menor intervalo aumenta carga sem benefício prático.
