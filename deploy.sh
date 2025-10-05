#!/bin/bash

# Production Deployment Script for American Law Search
# This script deploys the application with nginx reverse proxy and SSL

set -e

echo "=================================================="
echo "  American Law Search - Production Deployment"
echo "=================================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root (sudo ./deploy.sh)"
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Docker if not present
install_docker() {
    if ! command_exists docker; then
        echo "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
        
        # Add current user to docker group if not root
        if [ "$SUDO_USER" ]; then
            usermod -aG docker "$SUDO_USER"
            echo "Added $SUDO_USER to docker group. Please log out and back in for changes to take effect."
        fi
    else
        echo "Docker is already installed."
    fi
}

# Install Docker Compose if not present
install_docker_compose() {
    if ! command_exists docker-compose; then
        echo "Installing Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    else
        echo "Docker Compose is already installed."
    fi
}

# Create necessary directories
create_directories() {
    echo "Creating necessary directories..."
    mkdir -p /var/www/certbot
    mkdir -p /etc/letsencrypt
}

# Check and create .env file
setup_environment() {
    if [ ! -f ".env" ]; then
        echo "Creating .env file from template..."
        cp .env.example .env
        echo ""
        echo "IMPORTANT: Please edit the .env file with your actual values:"
        echo "- OPENAI_API_KEY"
        echo "- HUGGING_FACE_USER_ACCESS_TOKEN"
        echo "- DOMAIN (if different from lexpublicus.com)"
        echo "- EMAIL (for SSL certificate)"
        echo ""
        read -p "Press Enter after you've updated the .env file..."
    else
        echo ".env file already exists."
    fi
}

# Setup SSL certificates
setup_ssl() {
    echo "Setting up SSL certificates..."
    
    # Source environment variables
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # Update setup-ssl.sh with actual values from .env
    if [ ! -z "$DOMAIN" ] && [ ! -z "$EMAIL" ]; then
        sed -i "s/DOMAIN=\"lexpublicus.com\"/DOMAIN=\"$DOMAIN\"/" setup-ssl.sh
        sed -i "s/EMAIL=\"admin@lexpublicus.com\"/EMAIL=\"$EMAIL\"/" setup-ssl.sh
    fi
    
    # Run SSL setup
    ./setup-ssl.sh
}

# Deploy application
deploy_application() {
    echo "Deploying application..."
    
    # Stop any existing containers
    docker-compose -f docker-compose.prod.yml down
    
    # Build and start the application
    docker-compose -f docker-compose.prod.yml up --build -d
    
    echo "Application deployed successfully!"
}

# Setup firewall
setup_firewall() {
    echo "Configuring firewall..."
    
    # Install ufw if not present
    if ! command_exists ufw; then
        #  apt-get update
        #  apt-get install -y ufw
        echo ""
    fi
    
    # Configure firewall rules
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    
    echo "Firewall configured."
}

# Main deployment process
main() {
    echo "Starting deployment process..."
    
    # Update system
    echo "Updating system packages..."
    # apt-get update
    # apt-get upgrade -y
    
    # Install required software
    install_docker
    install_docker_compose
    
    # Create directories
    create_directories
    
    # Setup environment
    setup_environment
    
    # Setup SSL certificates
    setup_ssl
    
    # Configure firewall
    setup_firewall
    
    # Deploy application
    deploy_application
    
    echo ""
    echo "=================================================="
    echo "  Deployment Complete!"
    echo "=================================================="
    echo ""
    echo "Your application is now running with:"
    echo "- Nginx reverse proxy"
    echo "- SSL/HTTPS encryption"
    echo "- Automatic certificate renewal"
    echo ""
    echo "You can access your site at: https://$DOMAIN"
    echo ""
    echo "To view logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo "To restart: docker-compose -f docker-compose.prod.yml restart"
    echo "To stop: docker-compose -f docker-compose.prod.yml down"
    echo ""
}

# Run main function
main "$@"