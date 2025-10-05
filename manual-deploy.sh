#!/bin/bash

# Manual deployment script when Docker has issues
# This script runs the application directly on the host

set -e

echo "=================================================="
echo "  American Law Search - Manual Deployment"
echo "=================================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root (sudo ./manual-deploy.sh)"
    exit 1
fi

# Install required system packages
echo "Installing system dependencies..."
apt update

# Try to fix broken packages first
dpkg --configure -a || true
apt --fix-broken install -y || true

# Install essential packages
apt install -y python3-pip python3-venv python3-dev build-essential curl

# Install pip for the system Python
curl -fsSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py --force-reinstall
rm get-pip.py

# Create application directory and user
useradd -r -s /bin/false lexpublicus || true
mkdir -p /opt/lexpublicus
cp -r /var/www/lexpublicus.com/* /opt/lexpublicus/
chown -R lexpublicus:lexpublicus /opt/lexpublicus

# Install Python dependencies
cd /opt/lexpublicus
sudo -u lexpublicus python3 -m pip install --user -r requirements.txt

# Create systemd service for the application
cat > /etc/systemd/system/lexpublicus.service << 'EOF'
[Unit]
Description=American Law Search Application
After=network.target

[Service]
Type=simple
User=lexpublicus
WorkingDirectory=/opt/lexpublicus/app
Environment=PATH=/home/lexpublicus/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/opt/lexpublicus/app
ExecStart=/usr/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Load environment variables
if [ -f "/var/www/lexpublicus.com/.env" ]; then
    while IFS= read -r line; do
        if [[ $line && ! $line =~ ^#.* ]]; then
            echo "Environment=$line" >> /etc/systemd/system/lexpublicus.service
        fi
    done < "/var/www/lexpublicus.com/.env"
fi

# Create nginx configuration for non-SSL (we'll add SSL after testing)
cat > /etc/nginx/sites-available/lexpublicus << 'EOF'
server {
    listen 80;
    server_name lexpublicus.com www.lexpublicus.com;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    location / {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/lexpublicus /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Start services
systemctl daemon-reload
systemctl enable lexpublicus
systemctl start lexpublicus
systemctl enable nginx
systemctl start nginx

echo ""
echo "=================================================="
echo "  Manual Deployment Complete!"
echo "=================================================="
echo ""
echo "Application is running on:"
echo "- HTTP: http://$(curl -s ifconfig.me)"
echo "- Local: http://localhost"
echo ""
echo "To check logs:"
echo "- App logs: journalctl -fu lexpublicus"
echo "- Nginx logs: tail -f /var/log/nginx/error.log"
echo ""
echo "To add HTTPS later:"
echo "1. Run: sudo ./setup-ssl.sh"
echo "2. Update nginx config to use SSL"
echo ""