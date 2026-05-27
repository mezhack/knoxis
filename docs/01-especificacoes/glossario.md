# Glossário

Termos do domínio eclesiástico e do sistema. Leia antes dos demais documentos.

## Domínio eclesiástico

**Igreja Presbiteriana do Brasil (IPB)**
Denominação cristã reformada, organizada em forma presbiteriana de governo. O caso de uso inicial do Knoxis é a eleição interna na IPB local.

**Presbítero**
Oficial eclesiástico eleito pela igreja para compor o Conselho, órgão de governo da igreja local. Cargo eletivo.

**Diácono**
Oficial eclesiástico eleito pela igreja para a Junta Diaconal, responsável por serviço, assistência e administração de recursos. Cargo eletivo.

**Cargo**
No contexto da plataforma, "presbítero" ou "diácono" são os cargos típicos. O sistema é genérico o suficiente para permitir outros nomes de cargo configurados pelo organizador.

**Vaga**
Posição a ser preenchida em uma eleição para um cargo específico. Definida pelo Conselho/edital antes da eleição.

**Candidato**
Membro indicado para concorrer a um cargo. Pode haver mais candidatos que vagas (o esperado).

**Membro comungante**
Membro da igreja com direito a voto em assembleia. A lista de votantes do Knoxis corresponde ao rol de comungantes aptos.

**Cédula**
Documento (físico ou digital) onde o eleitor registra seus votos. No Knoxis, a cédula é digital e contém **todos os cargos da eleição** em um único formulário.

**Escrutínio**
Cada rodada de votação. Uma eleição pode ter múltiplos escrutínios até preencher todas as vagas. Numerados a partir de 1.

**Maioria simples**
Regra de elegibilidade: candidato eleito quando recebe pelo menos `floor(N/2) + 1` votos, onde `N` é o número de votantes do escrutínio.

**Escrutínio final**
Escrutínio marcado pelo organizador como o último permitido pelo edital. Nele, os mais votados ocupam as vagas remanescentes **mesmo sem atingir maioria simples**.

**Abstenção**
Diferença entre o número de votantes do escrutínio anterior e o atual. Membro que votou na rodada 1 mas não voltou na rodada 2 conta como abstenção da rodada 2.

**Ata da assembleia**
Documento formal que registra os atos da assembleia da igreja, incluindo o resultado das eleições. O relatório do Knoxis serve como anexo a essa ata.

## Domínio do sistema

**Organização**
Tenant da plataforma. Tipicamente uma igreja local. Tem um ou mais organizadores vinculados.

**Organizador**
Usuário com login na plataforma, vinculado a uma ou mais organizações, autorizado a configurar e conduzir eleições naquela organização. Papéis possíveis: `owner`, `admin`, `viewer`.

**Eleição**
Entidade que agrupa cargos, candidatos, votantes e escrutínios. Pertence a uma organização. Tem ciclo de vida: `rascunho` → `pronta` → `em_andamento` → `encerrada`.

**Sessão de cédula**
Sessão temporária criada quando o eleitor valida o CPF. Permite submeter a cédula uma única vez no escrutínio aberto. Curta duração (proposta: 10 min).

**Parciais**
Contagem de votos em tempo real durante o escrutínio aberto. Visível apenas ao organizador autenticado, em rota separada (aba dedicada).

**Relatório de escrutínio**
Visualização impressível com: contagem de votos por candidato, total de votantes, abstenções relativas ao escrutínio anterior, eleitos do escrutínio, candidatos remanescentes.

**Regra do último escrutínio**
Configuração que define como o último escrutínio funciona: por número máximo (`max_escrutinios`) ou manualmente marcado pelo organizador (`is_final = true`). Em escrutínio final, vence quem tem mais votos; empate na linha de corte requer resolução manual do organizador.
