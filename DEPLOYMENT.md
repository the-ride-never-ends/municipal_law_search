# American Law Search - Production Deployment Guide

## Overview
This guide will help you deploy the American Law Search application with nginx reverse proxy and SSL/HTTPS support.

## Files Created

### Configuration Files
- `nginx/nginx.conf` - Nginx reverse proxy configuration with SSL support
- `docker-compose.prod.yml` - Production Docker Compose configuration
- `.env.example` - Environment variables template

### Scripts
- `deploy.sh` - Full production deployment script
- `setup-ssl.sh` - SSL certificate setup with Let's Encrypt
- `update.sh` - Quick update script for application changes

## Prerequisites

1. **Domain Name**: Ensure your domain (e.g., lexpublicus.com) points to your server's IP address
2. **Server Requirements**: 
   - Ubuntu/Debian Linux server
   - Root access or sudo privileges
   - Ports 80 and 443 open for HTTP/HTTPS traffic

## Quick Deployment

### Step 1: Prepare Environment
```bash
# Copy and edit the environment file
cp .env.example .env
nano .env
```

Update the following values in `.env`:
- `OPENAI_API_KEY` - Your OpenAI API key
- `HUGGING_FACE_USER_ACCESS_TOKEN` - Your Hugging Face token
- `DOMAIN` - Your domain name (e.g., lexpublicus.com)
- `EMAIL` - Your email for SSL certificate notifications

### Step 2: Run Deployment
```bash
# Run the deployment script as root
sudo ./deploy.sh
```

This script will:
- Install Docker and Docker Compose
- Set up SSL certificates with Let's Encrypt
- Configure nginx reverse proxy
- Deploy the application
- Configure firewall settings

### Step 3: Verify Deployment
Visit your domain in a browser:
- `https://yourdomain.com` - Should show your application with SSL

## Manual Deployment Steps

If you prefer to deploy manually:

### 1. Install Dependencies
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Setup SSL Certificates
```bash
# Run SSL setup script
sudo ./setup-ssl.sh
```

### 3. Deploy Application
```bash
# Create .env file
cp .env.example .env
# Edit .env with your values

# Start the application
docker-compose -f docker-compose.prod.yml up -d --build
```

## Management Commands

### View Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### Restart Application
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Stop Application
```bash
docker-compose -f docker-compose.prod.yml down
```

### Update Application
```bash
./update.sh
```

## SSL Certificate Management

### Automatic Renewal
SSL certificates are automatically renewed via cron job. The deployment script sets this up automatically.

### Manual Renewal
```bash
sudo certbot renew
sudo systemctl reload nginx
```

### Check Certificate Status
```bash
sudo certbot certificates
```

## Security Features

The deployment includes several security features:

1. **SSL/TLS Encryption**: HTTPS with Let's Encrypt certificates
2. **Security Headers**: HSTS, X-Frame-Options, Content Security Policy
3. **Rate Limiting**: API rate limiting to prevent abuse
4. **Firewall**: UFW firewall configured to allow only necessary ports
5. **Secure SSL Configuration**: Modern TLS protocols and ciphers

## Troubleshooting

### Application not accessible
1. Check if containers are running: `docker ps`
2. Check logs: `docker-compose -f docker-compose.prod.yml logs`
3. Verify domain DNS points to your server
4. Check firewall: `sudo ufw status`

### SSL certificate issues
1. Check certificate status: `sudo certbot certificates`
2. Verify domain ownership
3. Check DNS propagation: `nslookup yourdomain.com`
4. Review certbot logs: `sudo tail -f /var/log/letsencrypt/letsencrypt.log`

### Nginx issues
1. Test nginx configuration: `sudo nginx -t`
2. Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. Restart nginx: `sudo systemctl restart nginx`

## Monitoring

### Health Check
The application includes a health check endpoint: `https://yourdomain.com/health`

### Log Monitoring
```bash
# Application logs
docker-compose -f docker-compose.prod.yml logs -f app

# Nginx logs
docker-compose -f docker-compose.prod.yml logs -f nginx
```

## Backup Recommendations

1. **Database**: Regular backups of the `data/` directory
2. **SSL Certificates**: Backup `/etc/letsencrypt/`
3. **Configuration**: Backup nginx configuration and environment files

## Performance Optimization

The nginx configuration includes:
- Gzip compression
- Static file caching
- Connection keep-alive
- Worker process optimization

For high-traffic sites, consider:
- Adding a CDN
- Database optimization
- Load balancing
- Monitoring setup

## Support

For issues related to:
- **Application**: Check application logs and documentation
- **SSL**: Refer to Let's Encrypt documentation
- **Nginx**: Check nginx documentation and logs
- **Docker**: Review Docker and Docker Compose documentation