# Visão geral

## Problema

Eleições internas em igrejas presbiterianas (e denominações semelhantes) seguem ritos específicos que não são bem atendidos por ferramentas genéricas (Google Forms, urnas eletrônicas comerciais, papel):

- A cédula tradicional contém múltiplos cargos com múltiplas vagas cada, e cada eleitor marca exatamente o número de vagas disponível por cargo.
- A regra de eleição é **maioria simples dos presentes/votantes** (50% + 1), o que comumente exige múltiplos escrutínios.
- O edital de cada eleição varia: número de vagas muda; número máximo de escrutínios muda; regra do último escrutínio muda (pode encerrar por "mais votados", sem exigir maioria).
- Voto é secreto, mas precisa ser validado por identificação do eleitor (CPF batido contra rol de membros comungantes da igreja).
- Apuração precisa ser auditável: o resultado de cada escrutínio é anexado à ata da assembleia.

Hoje, igrejas fazem isso em papel (lento, sujeito a erros de contagem) ou improvisam em planilhas (frágil, sem voto secreto real, sem controle de duplo voto).

## Visão do produto

**Knoxis** é uma plataforma SaaS multi-igreja onde um organizador (presbítero responsável, secretário do conselho, etc.) configura uma eleição, importa o rol de membros aptos a votar e conduz a votação em múltiplos escrutínios até que todas as vagas sejam preenchidas — com relatórios prontos para a ata.

Nome em homenagem a **John Knox**, reformador escocês e referência fundadora do presbiterianismo.

## Casos de uso primários

1. **Configurar eleição:** organizador define cargos, vagas por cargo, lista de candidatos por cargo, lista de votantes (CPF + nome) e regra do último escrutínio.
2. **Conduzir escrutínio:** abre votação, eleitores entram com CPF, recebem cédula, votam, sistema acumula. Organizador acompanha parciais em aba separada (privada).
3. **Encerrar escrutínio e apurar:** sistema calcula eleitos por maioria simples sobre votantes do escrutínio, destaca vencedores e candidatos remanescentes.
4. **Iniciar próximo escrutínio:** mesmas vagas restantes, candidatos restantes, sem necessidade de reconfiguração manual.
5. **Encerrar eleição:** todas as vagas preenchidas (por maioria nos escrutínios intermediários ou por "mais votados" no escrutínio final).
6. **Gerar relatório:** versão impressível, escrutínio a escrutínio, com contagem de votos por candidato, total de votantes e abstenções, para anexar à ata.

## Atores

- **Organizador (admin de organização):** usuário da igreja que configura e conduz eleições. Tem login.
- **Eleitor:** membro da igreja com CPF na lista. Não tem login; identifica-se pelo CPF no momento do voto.
- **Super admin da plataforma (futuro):** Anthropic-style, gerencia organizações. Inicialmente apenas via Django admin com superuser local.

## Escopo da fase 1 (esta documentação)

Inclui:
- Autenticação de organizadores (cadastro + login)
- Multi-tenant (cada organização tem suas eleições e listas isoladas)
- CRUD de eleição: cargos, vagas, candidatos, lista de votantes
- Fluxo de votação por CPF, voto secreto via sessão de cédula
- Escrutínios sucessivos com regra de maioria simples
- Configuração do escrutínio final (modo "mais votados")
- Parciais em tempo real (aba separada, apenas admin)
- Resultados pós-escrutínio com vencedores destacados
- Relatórios impressíveis por escrutínio

Não inclui (vai para o backlog futuro — ver [funcionalidades-futuras.md](07-futuro/funcionalidades-futuras.md)):
- Lista de presença por CPF
- Cálculo de maioria baseado em presentes (em vez de votantes)
- 2FA para organizadores
- Faturamento / planos / limites por organização
- Aplicativo do eleitor com QR code de identificação
- Personalização visual (logo/cores) por organização

## Não-objetivos

- **Não é uma urna eletrônica certificada.** O sistema atende ao rito eclesiástico, não substitui processos políticos legais.
- **Não é uma plataforma de pesquisa.** A cédula tem estrutura fixa: dois (ou mais) cargos, com N vagas cada, marca-se exatamente N por cargo.
- **Não armazena CPF em claro.** Usamos hash determinístico para matching (ver [ADR-007](03-decisoes/adr-007-armazenamento-cpf.md)).

## Princípios de design

- **SDD:** especificações primeiro; implementação deriva da spec.
- **Fases testáveis individualmente:** cada fase termina com um sistema funcional ponta-a-ponta dentro de seu escopo.
- **Zero regressão:** cada fase preserva os contratos da anterior.
- **Migrations idempotentes:** rodar duas vezes não quebra nada.
- **Voto secreto verificável:** o modelo de dados torna impossível ligar eleitor a voto.
