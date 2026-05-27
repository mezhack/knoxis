# Requisitos

Cada requisito é numerado para rastreabilidade entre specs, ADRs, contratos e testes.

- **RF** = Requisito Funcional
- **RNF** = Requisito Não-Funcional
- **RFu** = Requisito Futuro (fora do escopo da fase 1)

## Requisitos funcionais

### Multi-tenant e autenticação

**RF-001** — A plataforma deve suportar múltiplas organizações (igrejas) isoladas entre si. Uma organização nunca enxerga eleições, votantes, candidatos ou relatórios de outra.

**RF-002** — Um organizador deve poder se cadastrar com email e senha. Após cadastro, deve criar (ou ser convidado para) uma organização.

**RF-003** — Um organizador autenticado deve poder logar via email + senha. A sessão deve ser mantida por cookie httpOnly.

**RF-004** — Um organizador deve poder ter um dos seguintes papéis em uma organização: `owner`, `admin`, `viewer`. (Convites entre organizadores ficam para fase 2 — fase 1 entrega apenas o owner que criou.)

### Configuração de eleição

**RF-010** — Um organizador deve poder criar uma eleição definindo: nome, data prevista, descrição opcional.

**RF-011** — Em uma eleição, o organizador deve poder cadastrar um ou mais cargos. Cada cargo tem: nome (ex.: "Presbítero"), número de vagas (inteiro positivo).

**RF-012** — Em uma eleição, o organizador deve poder cadastrar candidatos por cargo. Um candidato pertence a exatamente um cargo (não há candidato concorrendo a dois cargos simultaneamente na mesma eleição).

**RF-013** — Em uma eleição, o organizador deve poder importar a lista de votantes via arquivo CSV contendo, no mínimo, colunas `cpf` e `nome`. CPFs duplicados devem ser rejeitados na importação (com relatório de linhas inválidas).

**RF-014** — Em uma eleição, o organizador deve poder configurar a regra do escrutínio final, escolhendo uma de:
- **Modo manual:** organizador marca um escrutínio específico como `is_final` antes ou durante.
- **Modo automático por máximo:** define um `max_escrutinios`; o sistema marca o último automaticamente.

**RF-015** — A eleição só pode ser iniciada (estado `em_andamento`) quando: tem pelo menos um cargo com pelo menos 1 vaga, número de candidatos do cargo ≥ número de vagas do cargo, lista de votantes não vazia, regra do escrutínio final definida.

### Escrutínios e votação

**RF-020** — Iniciar um escrutínio fixa, no momento da abertura: candidatos elegíveis, vagas remanescentes, lista de votantes. Alterações na eleição não afetam um escrutínio já aberto.

**RF-021** — Enquanto um escrutínio está aberto, eleitores devem poder acessar uma URL pública da eleição (sem login), informar seu CPF e, se válido e ainda não votou neste escrutínio, receber a cédula.

**RF-022** — A cédula deve apresentar todos os cargos do escrutínio atual em uma única tela, com seleção de exatamente `vagas_remanescentes` candidatos por cargo. Submissão com número diferente é rejeitada com mensagem clara.

**RF-023** — Após submissão, o sistema deve registrar o voto sem qualquer ligação persistida entre o eleitor (CPF/voter_id) e o conteúdo do voto. Ver [ADR-002](../03-decisoes/adr-002-voto-secreto-via-sessao.md).

**RF-024** — Uma sessão de cédula deve expirar em 10 minutos se não submetida. CPF não fica bloqueado por sessão expirada — pode tentar novamente.

**RF-025** — Um eleitor que já votou no escrutínio atual recebe mensagem clara de "voto já registrado neste escrutínio" e não pode votar novamente.

**RF-026** — O sistema deve registrar timestamp de submissão de cada voto (em granularidade de minuto ou hora — ver [ADR-002](../03-decisoes/adr-002-voto-secreto-via-sessao.md) para mitigação de correlação temporal).

### Encerramento e apuração

**RF-030** — O organizador deve poder encerrar manualmente um escrutínio. Encerramento é irreversível.

**RF-031** — Ao encerrar um escrutínio não-final, o sistema deve, por cargo: calcular o limiar de maioria simples (`floor(N/2) + 1` onde `N` = votantes do escrutínio); marcar como eleitos os candidatos que atingiram o limiar, respeitando o número de vagas (ordenando por votos desc); marcar candidatos remanescentes como elegíveis para o próximo escrutínio.

**RF-032** — Se mais candidatos do que vagas atingirem o limiar, eleger os `vagas` com mais votos. Os demais que atingiram limiar mas ficaram fora do corte **não** são eleitos e seguem para o próximo escrutínio (preservando contagem zerada para a nova rodada).

**RF-033** — Ao encerrar um escrutínio final, o sistema deve eleger os `vagas` candidatos com mais votos para cada cargo, **independentemente do limiar**. Empate na linha de corte: o sistema marca a situação como "empate pendente de resolução"; eleição não é encerrada até resolução manual pelo organizador.

**RF-034** — Quando todos os cargos tiverem todas as vagas preenchidas, a eleição transita para `encerrada` automaticamente.

**RF-035** — Se um escrutínio não-final encerra com vagas remanescentes, o organizador deve poder iniciar o próximo escrutínio. O sistema deve carregar automaticamente: candidatos remanescentes, vagas remanescentes, mesma lista de votantes.

### Parciais e relatórios

**RF-040** — Durante um escrutínio aberto, o organizador deve poder abrir uma rota dedicada de "parciais" em uma aba separada, com a contagem em tempo real de votos por candidato. Polling de no máximo 3 segundos. Esta rota só é acessível autenticado.

**RF-041** — Eleitores e a rota pública da eleição não devem expor parciais em nenhuma hipótese durante escrutínio aberto.

**RF-042** — Ao encerrar um escrutínio, a contagem total de votos por candidato deve ficar visível ao organizador, com destaque visual dos eleitos.

**RF-043** — O organizador deve poder acessar a aba de relatórios da eleição, com uma página impressível por escrutínio contendo: cabeçalho da eleição (nome, organização, data, número do escrutínio), por cargo a contagem de votos por candidato (ordenada desc), total de votantes do escrutínio, abstenção (votantes do escrutínio anterior − votantes deste, quando aplicável), candidatos eleitos no escrutínio.

**RF-044** — A página de relatório deve ter botão "Imprimir" que aciona o `window.print()` com CSS de impressão otimizado (sem menus, sem sidebars, layout limpo).

## Requisitos não-funcionais

### Segurança

**RNF-001** — Toda comunicação HTTPS. HTTP redireciona para HTTPS no Nginx.

**RNF-002** — Senhas de organizadores armazenadas com Argon2id (parâmetros conforme `django.contrib.auth.hashers.Argon2PasswordHasher`).

**RNF-003** — Cookies de sessão: `HttpOnly`, `Secure`, `SameSite=Lax`. CSRF habilitado para todas as mutações.

**RNF-004** — Rate limiting nas rotas: login (5 tentativas / 15min / IP), validação de CPF (10 tentativas / 5min / IP), submissão de voto (1 por sessão).

**RNF-005** — CPF nunca aparece em logs (mascarado como `***.***.***-XX`). Armazenado como hash HMAC-SHA256 determinístico (chave em variável de ambiente). Ver [ADR-007](../03-decisoes/adr-007-armazenamento-cpf.md).

**RNF-006** — Logs estruturados, sem PII desnecessária. Acessos a rotas de organizador são logados com user_id, ip, ação, timestamp.

### Auditabilidade

**RNF-010** — Toda transição de estado (eleição, escrutínio) gera registro em log de auditoria com user_id, ação, timestamp, dados antes/depois.

**RNF-011** — Apuração de eleitos é determinística e reproduzível: dada a tabela de votos e os parâmetros do escrutínio, recalcular sempre produz o mesmo resultado.

### Performance e capacidade

**RNF-020** — A plataforma deve suportar com folga: 500 eleitores por eleição, 10 escrutínios por eleição, 200 votos simultâneos sem degradação perceptível em VPS 2 vCPU / 4 GB RAM. (Valores conservadores; igrejas reais têm assembleias menores.)

**RNF-021** — Tempo de resposta P95 < 500 ms para rotas de votação em condições normais de carga.

### Disponibilidade e operação

**RNF-030** — Migrations idempotentes — rodar `migrate` duas vezes não erra e não altera estado a partir da segunda. Ver [ADR-004](../03-decisoes/adr-004-migrations-idempotentes.md).

**RNF-031** — Banco com backup automático diário (configuração de infra; documentar mas não implementar nesta fase).

**RNF-032** — Deploy reprodutível via `docker compose up` a partir de variáveis de ambiente documentadas.

### Acessibilidade e UX

**RNF-040** — Cabine do eleitor é **mobile-first**. A maioria dos votantes acessa pelo celular (geralmente o próprio, durante a assembleia), então o layout do celular não é "uma adaptação" do desktop — é o layout principal. O layout para desktop/tablet é uma elevação do mesmo conteúdo. Detalhamento de breakpoints e comportamentos em [docs/02-arquitetura/frontend.md](../02-arquitetura/frontend.md#responsividade).

**RNF-040a** — Breakpoints alvo da cabine do eleitor:
- Mobile pequeno: 320–374px (referência: iPhone SE 1ª geração) — deve funcionar, ainda que com alguma compactação.
- Mobile padrão: 375–767px — **alvo principal de design**. Todas as telas testadas explicitamente em 375x812 (iPhone 13/14) e 412x915 (Android comum).
- Tablet: 768–1023px — layout intermediário, conteúdo centralizado.
- Desktop: ≥1024px — conteúdo limitado em coluna central legível.

**RNF-040b** — Controles touch-friendly: área tocável mínima 44x44px (Apple HIG / WCAG 2.5.5 AAA). Espaçamento entre checkboxes/botões mínimo 8px. Sem dependência de hover para nenhuma interação.

**RNF-040c** — Tipografia da cabine: base mínima 16px no mobile (evita zoom automático do iOS em inputs). Hierarquia legível com contraste WCAG AA mínimo.

**RNF-040d** — A cédula em mobile deve apresentar um cargo por seção com rolagem natural, sem layouts de coluna lado-a-lado. Em tablet/desktop, pode haver até duas colunas se a quantidade de candidatos justificar.

**RNF-040e** — Inputs de CPF em mobile devem usar `inputmode="numeric"` para abrir teclado numérico e `autocomplete="off"` para evitar sugestões indevidas.

**RNF-041** — Cédula deve impedir submissão até o número correto de candidatos por cargo ser selecionado (feedback inline). Mensagens em português claro. Contador "X de Y selecionados" sempre visível por cargo, fixo no topo da seção em mobile.

**RNF-042** — Painel do organizador é **desktop-first**, mas precisa ser funcional em tablet (uso típico em assembleia: notebook do secretário + tablet auxiliar). Em celular, deve ser navegável mas não é o caso de uso primário — telas densas (relatório, lista de votantes) podem rolar horizontalmente.

**RNF-043** — Página de impressão do relatório deve, no `@media print`, normalizar para layout A4 retrato independentemente do dispositivo de origem (organizador pode mandar imprimir do próprio celular via AirPrint / Google Cloud Print).

## Requisitos futuros (fora da fase 1)

**RFu-001** — Lista de presença por CPF: organizador marca presentes antes/durante o escrutínio. Maioria simples passa a ser calculada sobre `presentes`, não sobre `votantes`. Ver [docs/07-futuro/funcionalidades-futuras.md](../07-futuro/funcionalidades-futuras.md).

**RFu-002** — 2FA TOTP para organizadores.

**RFu-003** — Convites de organizadores para uma organização existente (com aceite via email).

**RFu-004** — Faturamento, planos e limites por organização.

**RFu-005** — Personalização visual por organização (logo, cores) e PDF do relatório com identidade visual da igreja.

**RFu-006** — Exportação dos relatórios em PDF gerado server-side (mais robusto que `window.print`).

**RFu-007** — Trilha de auditoria exibível na UI (não só em log).
