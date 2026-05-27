# Funcionalidades futuras (fase 2+)

Itens deliberadamente fora do escopo da fase 1. Cada um tem ID `RFu-XXX` referenciado nos requisitos, ADRs e roadmap.

---

## RFu-001 — Lista de presença por CPF

**O que é:** organizador marca, antes ou durante o escrutínio, quais membros estão **presentes** na assembleia (identificando por CPF na lista). O cálculo de maioria simples passa a ser sobre **presentes**, e não sobre **votantes**.

**Por que importa:** o rito presbiteriano clássico define maioria sobre "presentes". Hoje (fase 1) usamos votantes como proxy — funciona para casos comuns, mas tecnicamente diverge da norma quando alguém presente decide não votar (voto em branco/abstenção tradicional).

**Impacto nas regras de negócio:**
- RN-1 muda: `N = presentes do escrutínio` em vez de `votantes do escrutínio`.
- RN-4 (abstenção) refina: abstenção do escrutínio = `max(0, presentes - votantes)`.
- Relatório passa a mostrar: presentes, votantes, abstenções, brancos/nulos (se decidirmos diferenciar).

**Modelagem proposta:**
- Nova tabela `voter_presence(escrutinio_id, voter_id, marked_at, unmarked_at)` — append-only para auditoria.
- Endpoints admin para marcar/desmarcar presença em lote (CPF entrada, lista).
- Frontend: tela dedicada de "lista de presença" com busca rápida por CPF/nome.

**Compatibilidade:**
- Eleições criadas na fase 1 (sem presença) continuam usando cálculo por votantes — flag por eleição: `attendance_mode = 'voters' | 'presents'`.
- Default em eleições novas: `presents`. Eleições antigas mantêm `voters` (zero regressão).

**Dependências:** nenhuma técnica obrigatória; depende de o organizador querer e ter logística de marcação.

---

## RFu-002 — 2FA TOTP para organizadores

**O que é:** segundo fator via app autenticador (Google Authenticator, Authy, etc.) no login do organizador.

**Por que importa:** plataforma exposta à internet, contas controlam eleições reais. 2FA mitiga roubo de senha.

**Implementação proposta:**
- `django-otp` ou `django-two-factor-auth`.
- Optional na fase de rollout; tornar obrigatório por organização (config) ou globalmente em fase posterior.
- Recovery codes gerados no setup.

**Impacto:** mínimo — só adiciona um passo no login. Sem mudança de modelo de dados estrutural (tabelas próprias do plugin).

---

## RFu-003 — Convites de organizadores

**O que é:** owner de uma organização convida outros usuários (por email) para serem `admin` ou `viewer`. Convidado aceita e ganha o papel.

**Por que importa:** assembleias têm vários assistentes (secretário, mesários). Centralizar tudo no owner é fricção.

**Implementação proposta:**
- Tabela `organization_invitations(organization, email, role, token, expires_at, accepted_at)`.
- Email de convite com link assinado.
- Tela admin "membros da organização" com adição/remoção.

**Depende de:** SMTP funcional configurado.

---

## RFu-004 — Faturamento, planos, limites

**O que é:** monetização da plataforma. Plano gratuito limitado, plano pago com mais eleições / votantes / armazenamento.

**Por que importa:** sustentabilidade do produto.

**Implementação proposta:**
- Integração com Stripe ou similar.
- Modelo `subscription`, `plan`, limites enforced no backend (counters por organização).
- Página de billing.

**Considerações:** entra somente quando houver demanda real e o produto tiver atingido o ajuste com o caso de uso da igreja inicial.

---

## RFu-005 — Personalização visual por organização

**O que é:** organização configura logo da igreja, cores da identidade visual; cabine do eleitor e relatórios usam essa identidade.

**Por que importa:** ata e impressões com identidade da igreja é valor percebido alto.

**Implementação proposta:**
- Upload de logo (PNG/SVG) em `media/`.
- Configuração de cor primária (variável CSS).
- Frontend lê config da organização no bootstrap.

**Considerações:** validar tamanho/segurança do upload; SVG é vetor de XSS se servido com tipo errado — usar Content-Disposition: attachment ou converter para PNG.

---

## RFu-006 — Relatório em PDF gerado server-side

**O que é:** botão "Baixar PDF" no relatório do escrutínio, com PDF renderizado no servidor (não dependendo de `window.print` do navegador).

**Por que importa:** PDF é mais robusto para anexar à ata em formato eletrônico. Não depende do navegador do organizador.

**Implementação proposta:**
- WeasyPrint (HTML+CSS → PDF) ou ReportLab.
- Reaproveita o template HTML já usado para impressão.
- Marcar com cabeçalho/rodapé padronizado e assinatura digital (em fase ainda mais futura).

---

## RFu-007 — Trilha de auditoria visível na UI

**O que é:** página onde owner consulta o log de ações da organização (`audit_log`).

**Por que importa:** transparência interna; investigação de "quem mudou o quê".

**Implementação proposta:**
- Endpoint `GET /admin/audit_log?filters=...` paginado.
- Frontend simples: tabela com ação, usuário, target, timestamp, payload colapsável.

---

## Backlog técnico (sem RFu)

Itens menores que ganham issue quando virem prioridade:

- Recuperação de senha por email self-service (fluxo padrão do Django + template em pt-BR).
- Internacionalização (i18n) — adicionar `en`, `pt-PT` se houver demanda.
- App mobile com QR code de identidade (eleitor mostra QR ao mesário em vez de digitar CPF).
- Modo "kiosk" para tablet compartilhado em cabine física (login automático, foco no formulário, sem navegação).
- Export CSV dos relatórios (além da impressão).
- Notificações por email/whatsapp para o organizador quando escrutínio é encerrado / eleição termina.
- Suporte a múltiplos tipos de eleição (não-presbiteriano: igrejas batistas, conselhos comunitários, etc.) com regras parametrizáveis.
- Tightening de CSP (remover `'unsafe-inline'` em styles via nonce).
- Migração de rate limit para Redis caso a plataforma escale horizontalmente.
- RLS do Postgres como defense-in-depth multi-tenant.
- Pen-test externo formal antes do "v1.0" público.
