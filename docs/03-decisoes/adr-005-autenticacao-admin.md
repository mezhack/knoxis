# ADR-005 — Autenticação de organizador

**Status:** accepted
**Data:** 2026-05-26

## Contexto

A plataforma roda em VPS exposta à internet pública. Organizadores são leigos em segurança — não devem precisar entender chaves, tokens, etc. A interface de uso típica é desktop com sessão longa durante uma assembleia. O ataque mais comum esperado é força bruta a partir de bots.

## Decisão

**Autenticação por email + senha. Senha hasheada com Argon2id (config padrão do Django). Sessão de servidor (`django.contrib.sessions`) com cookie de sessão `HttpOnly`, `Secure`, `SameSite=Lax`. CSRF token obrigatório em todas as mutações. Bloqueio de força bruta com `django-axes`.**

### Detalhes

- **Hash:** `django.contrib.auth.hashers.Argon2PasswordHasher` em primeiro lugar em `PASSWORD_HASHERS`.
- **Política de senha:** mínimo 12 caracteres. Validators do Django ativos: `MinimumLengthValidator(12)`, `UserAttributeSimilarityValidator`, `CommonPasswordValidator`, `NumericPasswordValidator`. Sem regra "tem que ter símbolo especial" (anti-padrão).
- **Cookie de sessão:**
  - `SESSION_COOKIE_HTTPONLY = True`
  - `SESSION_COOKIE_SECURE = True`
  - `SESSION_COOKIE_SAMESITE = 'Lax'`
  - `SESSION_COOKIE_AGE = 60*60*8` (8h)
  - `SESSION_EXPIRE_AT_BROWSER_CLOSE = False` (intencional — assembleias longas)
- **CSRF:**
  - `CSRF_COOKIE_HTTPONLY = False` (precisa ser lido pelo JS — esse é o cookie de double-submit; o de sessão é HttpOnly).
  - `CSRF_COOKIE_SECURE = True`
  - `CSRF_COOKIE_SAMESITE = 'Lax'`
  - Frontend lê `csrftoken` cookie e envia em `X-CSRFToken` header.
- **Brute force:**
  - `django-axes` configurado:
    - `AXES_FAILURE_LIMIT = 5`
    - `AXES_COOLOFF_TIME = 0.5` (em horas — 30 min)
    - Tracking por `username + ip` (não só IP, para não permitir DoS de conta).
- **Recuperação de senha:** envio de link com token assinado (Django built-in), expiração de 1h. Email via SMTP configurado. **Fase 2** — na fase 1, recuperação é manual pelo super-admin via Django admin.

### Por que não JWT?

- JWT em SPA tipicamente vive em localStorage → vetor XSS direto.
- JWT em cookie httpOnly perde a única vantagem percebida (stateless), e ainda requer construir refresh token, blacklist, etc.
- Sessão em cookie httpOnly é mais simples, mais segura, e já vem pronta no Django.
- Trade-off: sessão exige banco. Custo desprezível dado o volume.

### Por que não 2FA na fase 1?

- Atrito de cadastro para organizadores leigos.
- Cobertura técnica é razoável sem 2FA dado: Argon2 + brute-force lockout + sessão httpOnly + HTTPS + CSP.
- 2FA TOTP entra como RFu-002.

## Consequências

### Positivas
- Stack simples, conhecida, segura.
- Recuperação total de credenciais via Django admin se algo der errado.
- Bloqueio efetivo de bots de força bruta.

### Negativas
- Sessão tem state em banco (mas Django gerencia automaticamente).
- Sem 2FA na fase 1 — risco residual aceito.

## Alternativas consideradas

### JWT em localStorage
- Rejeitado: XSS = roubo de token.

### JWT em cookie httpOnly
- Rejeitado: complexidade extra sem ganho real vs sessão Django.

### Magic link (email-only login)
- Rejeitado: organizador precisa estar com email aberto na assembleia. Atrito alto.

### OAuth (Google, etc.)
- Rejeitado nesta fase: maioria das igrejas usa conta institucional informal; obrigar a vincular Google é fricção. Pode entrar em fase futura como opção adicional.
