# Infraestrutura — Deploy Knoxis

## Pré-requisitos

- VPS com Ubuntu 22.04+ (recomendado: 2 vCPU, 4 GB RAM)
- Docker e Docker Compose instalados
- Domínio apontando para o servidor
- Certbot para TLS (Let's Encrypt)

## Variáveis de ambiente

Copiar `.env.example` e preencher:

```bash
cp backend/.env.example .env
# Editar .env com valores reais
openssl rand -hex 32   # para SECRET_KEY e CPF_HMAC_KEY
```

## Deploy inicial

```bash
# 1. Clonar o repo
git clone ... knoxis && cd knoxis

# 2. Configurar .env
cp backend/.env.example .env && nano .env

# 3. Ajustar nginx.conf (substituir SEU_DOMINIO)
nano infra/nginx.conf

# 4. Obter certificado TLS
certbot certonly --standalone -d seu-dominio.com.br

# 5. Subir containers
docker compose -f docker-compose.prod.yml up -d

# 6. Criar superusuário Django
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

## Atualização

```bash
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

## Backup

```bash
# Dump manual
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U knoxis knoxis > backup_$(date +%Y%m%d).sql

# Restore
docker compose -f docker-compose.prod.yml exec -T db \
  psql -U knoxis knoxis < backup_YYYYMMDD.sql
```

Recomendado: configurar cron diário no host para dump automático com retenção de 14 dias,
com envio para bucket S3-compatible (backblaze, cloudflare r2).

## Renovação TLS

O certbot renova automaticamente. Verificar com:

```bash
certbot renew --dry-run
```

Após renovação, reiniciar nginx:

```bash
docker compose -f docker-compose.prod.yml restart nginx
```
