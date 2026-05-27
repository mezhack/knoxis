# Frontend

## Stack

- React 18
- TypeScript 5
- Vite 5 (dev + build)
- React Router 6
- TanStack Query 5 (estado de servidor, cache, polling)
- Zustand (estado de UI local que precisa persistir entre rotas)
- Tailwind CSS (utilitários — sem framework de componente pesado)
- Headless UI (componentes acessíveis primitivos: dialog, listbox)
- React Hook Form + Zod para formulários e validação
- date-fns para datas em pt-BR

## Estrutura

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── router.tsx
│   ├── lib/
│   │   ├── api.ts             # fetch wrapper com cookies + tratamento de erro
│   │   ├── cpf.ts             # formatação/validação client-side
│   │   └── format.ts          # datas, números pt-BR
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   └── useOrganization.ts
│   ├── modules/
│   │   ├── admin/             # painel do organizador
│   │   │   ├── pages/
│   │   │   │   ├── LoginPage.tsx
│   │   │   │   ├── SignupPage.tsx
│   │   │   │   ├── ElectionListPage.tsx
│   │   │   │   ├── ElectionFormPage.tsx
│   │   │   │   ├── ElectionDashboardPage.tsx
│   │   │   │   ├── EscrutinioParciaisPage.tsx
│   │   │   │   ├── EscrutinioResultadoPage.tsx
│   │   │   │   └── RelatorioImpressoPage.tsx
│   │   │   └── components/
│   │   └── voter/             # cabine do eleitor (pública)
│   │       ├── pages/
│   │       │   ├── ElectionEntryPage.tsx     # informa CPF
│   │       │   ├── BallotPage.tsx            # cédula
│   │       │   └── ConfirmationPage.tsx
│   │       └── components/
│   └── styles/
│       └── print.css          # CSS de impressão de relatório
└── public/
```

## Convenções

- Componentes funcionais com hooks. Sem class components.
- Nomes em inglês para código (variáveis, componentes, props). Strings de UI em português.
- Componentes de página em `pages/`, componentes reutilizáveis em `components/`.
- Hooks customizados prefixados com `use*`.
- Tipos em arquivo próximo ao uso; tipos compartilhados em `src/lib/types.ts`.

## Estado

- **Servidor:** TanStack Query. Toda chamada à API passa por hooks `useQuery` / `useMutation` com chaves consistentes (`['elections', orgId]`, `['escrutinio', escrutinioId, 'parciais']`).
- **UI persistente entre rotas:** Zustand store para "organização atual selecionada" e "usuário logado" (após bootstrap).
- **Local de formulário:** React Hook Form (não escala para estado global, intencionalmente).

## Autenticação

- App admin faz bootstrap em `App.tsx` com `GET /api/v1/admin/me`.
- Se 401, redireciona para `/login`.
- Logout: `POST /api/v1/admin/auth/logout` + redirect.
- CSRF token: obtido via `GET /api/v1/csrf` no bootstrap; lib `api.ts` inclui automaticamente em mutações.
- Cabine do eleitor não tem login — sessão é apenas o cookie de `ballot_session` definido após validar CPF.

## Polling de parciais

Hook `useEscrutinioParciais(escrutinioId)`:

```ts
return useQuery({
  queryKey: ['escrutinio', escrutinioId, 'parciais'],
  queryFn: () => api.get(`/admin/escrutinios/${escrutinioId}/parciais`),
  refetchInterval: 3000,
  enabled: escrutinioStatus === 'aberto',
});
```

Para o eleitor (cabine), parciais nunca são chamadas — a página de espera/confirmação não tem endpoint correspondente público.

## Impressão de relatório

- Página `RelatorioImpressoPage.tsx` aplica `<style>` global incluído de `styles/print.css`.
- `@media print` esconde headers/sidebars do app e expande a área de relatório.
- Botão "Imprimir" chama `window.print()`.
- Mantemos render server-side de PDF como item futuro (RFu-006).

## Responsividade

A plataforma tem dois "públicos" com prioridades opostas:

| App | Prioridade de design | Justificativa |
|---|---|---|
| Cabine do eleitor | **Mobile-first** | Maioria dos votantes usa o próprio celular durante a assembleia. |
| Painel do organizador | **Desktop-first** (funcional em tablet, navegável em mobile) | Operador trabalha com notebook na mesa de apoio. |

### Breakpoints (Tailwind)

Usamos os breakpoints padrão do Tailwind, com este mapeamento de intenção:

| Tailwind | min-width | Categoria | Cabine do eleitor | Painel do organizador |
|---|---|---|---|---|
| (default) | 0px | Mobile pequeno | Funcional, compacto | Funcional, conteúdo rolável |
| `sm:` | 640px | Mobile grande | Padrão de design | Funcional |
| `md:` | 768px | Tablet | Conteúdo centrado, ~ 600px de largura | Layout em duas zonas (nav lateral colapsável) |
| `lg:` | 1024px | Desktop | Conteúdo centralizado em coluna ≤ 720px | Layout final com sidebar persistente |
| `xl:` | 1280px | Desktop largo | Idem `lg:` | Aproveita largura extra para tabelas |

> Tudo abaixo de `sm` ainda precisa funcionar. Testes manuais em 320px (iPhone SE 1ª geração) confirmam que o conteúdo principal renderiza sem overflow horizontal indesejado.

### Padrões de UI para mobile (cabine do eleitor)

- **Fonte base 16px no `html`.** Inputs herdam — evita zoom automático do iOS em foco.
- **Área tocável mínima 44x44px** em qualquer elemento interativo (checkbox custom com `label` clicável, botões com `min-h-11`).
- **Espaçamento vertical generoso** entre candidatos (≥ 12px) — toque preciso com polegar.
- **Contador "fixo no topo"** por cargo: `position: sticky; top: 0;` dentro da seção do cargo, com fundo opaco. Eleitor rola a lista sem perder de vista quantos faltam marcar.
- **Header minimalista**: apenas nome da igreja + nome da eleição + número do escrutínio em fonte pequena no topo. Sem menus, sem links extras.
- **Botão "Confirmar voto"** sempre acessível: posição `sticky bottom-0` em mobile, com sombra superior para destacar.
- **Tela de revisão** (antes de submeter) com cargos colapsáveis individualmente.
- **Inputs de CPF**: `inputmode="numeric"`, `autocomplete="off"`, máscara `000.000.000-00` aplicada via JS (não via input type=number — ruim no iOS).
- **Sem modais sobrepostos** em mobile: confirmação dupla é uma tela cheia que volta para a anterior, não um dialog.

### Padrões de UI para mobile (painel do organizador)

- Acesso navegável mas não otimizado. Lista de eleições, parciais e detalhe de escrutínio precisam funcionar — telas densas (lista de votantes paginada, relatório completo) podem ter rolagem horizontal.
- Tabelas usam `overflow-x-auto` para deslizar horizontalmente quando faltar largura.
- Botões críticos (encerrar escrutínio, resolver empate) recebem confirmação extra em mobile para evitar toque acidental — modal de confirmação com botões "Cancelar" e "Confirmar" bem espaçados.

### Padrões de tablet (768–1023px)

- Cabine: igual mobile mas com conteúdo centrado em `max-w-screen-sm` (~ 640px).
- Organizador: nav lateral colapsada (hamburger), conteúdo principal em uma coluna.

### Padrões de desktop (≥1024px)

- Cabine: idêntica ao tablet — não faz sentido espalhar uma cédula em 1920px. Mantemos coluna central confortável (`max-w-screen-md` ~ 768px).
- Organizador: nav lateral persistente, header com info de organização/usuário, tabelas em largura plena.

### Verificação obrigatória por fase

A cada PR que toque UI da cabine do eleitor:
1. Screenshot em 375x812 (mobile padrão).
2. Screenshot em 768x1024 (tablet).
3. Screenshot em 1440x900 (desktop).
4. Verificar manualmente em 320x568 (iPhone SE 1ª geração) — pelo menos uma vez por fase.

Em PRs do painel do organizador: screenshots em 375x812 (navegável), 768x1024 (funcional), 1440x900 (alvo principal).

### Não usamos

- Bibliotecas de "framework mobile" (Ionic, Capacitor). Knoxis é web — PWA pode entrar no backlog, app nativo só se houver demanda real (RFu).
- Detecção de user-agent para alternar layouts. Tudo é responsivo via CSS / media queries / breakpoints Tailwind.

## Acessibilidade

- Foco visível, labels associadas a inputs, navegação por teclado.
- Cores com contraste WCAG AA.
- Cédula: ARIA `aria-labelledby` e `aria-describedby` por cargo, contador acessível ("3 de 4 selecionados").
- Mensagens de erro vinculadas por `aria-describedby`.
- Targets touch ≥ 44x44px (WCAG 2.5.5 nível AAA — adotamos como mínimo na cabine).
- Inputs com `aria-required`, mensagens de erro com `role="alert"` para serem anunciadas por leitores de tela.

## Build e deploy

- `vite build` gera `dist/` estático.
- Nginx serve `dist/` na raiz; fallback `try_files $uri /index.html` para SPA.
- Hash em filename para cache busting; `index.html` com `no-cache`.
