# ADR-009 — Stack frontend (bibliotecas específicas)

**Status:** accepted
**Data:** 2026-05-26

## Contexto

A escolha de React + Vite + TypeScript foi feita em [ADR-001](adr-001-stack-tecnologica.md). Faltam definir:

- Roteamento
- Estado de servidor
- Estilo
- Formulários e validação
- UI primitives acessíveis

Objetivos: simplicidade, ergonomia, baixo runtime cost, bom suporte a acessibilidade, fácil aprendizado para quem entrar no projeto depois.

## Decisão

| Categoria | Escolha | Notas |
|---|---|---|
| Roteamento | React Router 6 | Padrão de facto, sem reinvenção. |
| Estado de servidor | TanStack Query 5 | Cache, refetch, polling — match perfeito para parciais. |
| Estado UI local persistente | Zustand | Para "org atual" e "user" pós-bootstrap. Sem boilerplate. |
| Estilo | Tailwind CSS | Utilitários inline, sem CSS-in-JS, ergonomia em produção. |
| UI primitives | Headless UI | Dialog, Listbox, Menu acessíveis sem estilo opinado. |
| Formulários | React Hook Form + Zod | Validação tipada, performance, integração natural com TS. |
| Datas | date-fns (locale pt-BR) | Mais leve que dayjs; bem suportado. |
| Testes | Vitest + Testing Library | Mesma JIT do Vite; sem Jest config. |

## Por que essas escolhas

- **TanStack Query:** dispensa custom hooks complicados para cache/refetch. Polling de parciais é declarativo (`refetchInterval: 3000`).
- **Zustand:** menor superfície que Redux, sem ações/reducers — bom para o pouco estado global real (org atual, user atual).
- **Tailwind:** vence o trade-off entre custom CSS (lento de escrever) e MUI/Chakra (heavy, opinado). Print CSS para relatório fica natural.
- **Headless UI:** acessibilidade sem amarrar a um sistema de design. Combina bem com Tailwind (mesmo ecossistema, mesmo time).
- **React Hook Form + Zod:** schemas Zod reusáveis (mesma validação de regras como cédula = "exatamente N marcados") — pode até espelhar lógica de validação client/server.

## Consequências

### Positivas
- Time pequeno consegue ser produtivo rápido.
- Bundle leve (sem framework de UI completo).
- Acessibilidade endereçada por Headless UI.

### Negativas
- Sem sistema de design pronto — temos que construir os componentes base (Button, Input, etc.). Aceitável dado o volume de telas.

## Alternativas consideradas

### Material UI / Chakra UI
- Componentes prontos.
- Rejeitado: bundle pesado, customização sofrida quando se quer fugir do padrão.

### Redux Toolkit em vez de Zustand
- Mais padrão da indústria.
- Rejeitado: complexidade desnecessária para o escopo de estado real.

### TanStack Query + Jotai
- Substitui Zustand.
- Rejeitado por preferência de simplicidade — Zustand já basta.

### shadcn/ui
- Headless UI + Tailwind empacotados como componentes prontos copiados pro projeto.
- Considerado: pode entrar como "starter" de componentes em fase posterior. Por enquanto preferimos compor do zero sobre Headless UI direto.
