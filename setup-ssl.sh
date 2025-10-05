#!/bin/bash

# SSL Certificate Setup Script for Let's Encrypt
# This script sets up SSL certificates for lexpublicus.com

set -e

DOMAIN="lexpublicus.com"
EMAIL="admin@lexpublicus.com"  # Change this to your email
WEBROOT="/var/www/certbot"

echo "Setting up SSL certificates for $DOMAIN..."

# Create webroot directory for Let's Encrypt challenges
mkdir -p $WEBROOT

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Stop nginx if running to avoid port conflicts during initial setup
if systemctl is-active --quiet nginx; then
    echo "Stopping nginx for initial certificate generation..."
    systemctl stop nginx
fi

# Generate initial certificate using standalone mode
echo "Generating initial SSL certificate..."
certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --domains $DOMAIN \
    --domains www.$DOMAIN

# Create renewal hook script
cat > /etc/letsencrypt/renewal-hooks/deploy/01-reload-nginx.sh << 'EOF'
#!/bin/bash
systemctl reload nginx
EOF

chmod +x /etc/letsencrypt/renewal-hooks/deploy/01-reload-nginx.sh

# Set up automatic renewal with cron
echo "Setting up automatic certificate renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

echo "SSL certificate setup completed!"
echo "Certificate location: /etc/letsencrypt/live/$DOMAIN/"
echo "Auto-renewal configured via cron job."
echo ""
echo "Next steps:"
echo "1. Update nginx configuration with your domain name"
echo "2. Start nginx: systemctl start nginx"
echo "3. Enable nginx: systemctl enable nginx"