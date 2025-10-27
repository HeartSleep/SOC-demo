#!/bin/bash

################################################################################
# SOC Platform Production Deployment Script
# Complete setup for production environment with security tools
################################################################################

set -e  # Exit on error
set -o pipefail  # Exit on pipe failure

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PLATFORM_NAME="SOC Security Platform"
INSTALL_DIR="/opt/soc-platform"
DATA_DIR="/var/data/soc-platform"
LOG_DIR="/var/log/soc-platform"
BACKUP_DIR="/var/backups/soc-platform"
USER="soc-admin"
GROUP="soc-admin"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
            PACKAGE_MANAGER="apt-get"
        elif [ -f /etc/redhat-release ]; then
            OS="rhel"
            PACKAGE_MANAGER="yum"
        else
            OS="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PACKAGE_MANAGER="brew"
    else
        OS="unknown"
    fi

    if [ "$OS" == "unknown" ]; then
        print_error "Unsupported operating system"
        exit 1
    fi

    print_success "Detected OS: $OS"
}

# Install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."

    if [ "$OS" == "debian" ]; then
        apt-get update
        apt-get install -y \
            build-essential \
            python3-dev \
            python3-pip \
            python3-venv \
            postgresql \
            postgresql-contrib \
            redis-server \
            nginx \
            git \
            curl \
            wget \
            nmap \
            nikto \
            sqlmap \
            dirb \
            gobuster \
            hydra \
            john \
            hashcat \
            metasploit-framework \
            wireshark \
            tcpdump \
            aircrack-ng \
            net-tools \
            dnsutils \
            whois \
            sslscan \
            sslyze \
            testssl.sh \
            masscan \
            zmap \
            supervisor \
            ufw \
            fail2ban \
            logrotate \
            certbot \
            python3-certbot-nginx

    elif [ "$OS" == "rhel" ]; then
        yum install -y epel-release
        yum install -y \
            gcc \
            python3-devel \
            python3-pip \
            postgresql-server \
            postgresql-contrib \
            redis \
            nginx \
            git \
            curl \
            wget \
            nmap \
            supervisor \
            firewalld \
            fail2ban \
            logrotate \
            certbot \
            python3-certbot-nginx
    fi

    print_success "System dependencies installed"
}

# Install security tools
install_security_tools() {
    print_status "Installing security scanning tools..."

    # Install Nuclei
    print_status "Installing Nuclei..."
    if ! command -v nuclei &> /dev/null; then
        wget -q https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip
        unzip -q nuclei_linux_amd64.zip
        mv nuclei /usr/local/bin/
        chmod +x /usr/local/bin/nuclei
        rm nuclei_linux_amd64.zip

        # Download templates
        nuclei -update-templates
    fi
    print_success "Nuclei installed"

    # Install OWASP ZAP
    print_status "Installing OWASP ZAP..."
    if [ ! -d "/opt/zaproxy" ]; then
        wget -q https://github.com/zaproxy/zaproxy/releases/download/v2.14.0/ZAP_2.14.0_Linux.tar.gz
        tar -xzf ZAP_2.14.0_Linux.tar.gz -C /opt/
        rm ZAP_2.14.0_Linux.tar.gz
        ln -sf /opt/ZAP_2.14.0/zap.sh /usr/local/bin/zap
    fi
    print_success "OWASP ZAP installed"

    # Install Amass
    print_status "Installing Amass..."
    if ! command -v amass &> /dev/null; then
        wget -q https://github.com/OWASP/Amass/releases/latest/download/amass_linux_amd64.zip
        unzip -q amass_linux_amd64.zip
        mv amass_linux_amd64/amass /usr/local/bin/
        rm -rf amass_linux_amd64*
    fi
    print_success "Amass installed"

    # Install Subfinder
    print_status "Installing Subfinder..."
    if ! command -v subfinder &> /dev/null; then
        wget -q https://github.com/projectdiscovery/subfinder/releases/latest/download/subfinder_linux_amd64.zip
        unzip -q subfinder_linux_amd64.zip
        mv subfinder /usr/local/bin/
        chmod +x /usr/local/bin/subfinder
        rm subfinder_linux_amd64.zip
    fi
    print_success "Subfinder installed"

    # Install httpx
    print_status "Installing httpx..."
    if ! command -v httpx &> /dev/null; then
        wget -q https://github.com/projectdiscovery/httpx/releases/latest/download/httpx_linux_amd64.zip
        unzip -q httpx_linux_amd64.zip
        mv httpx /usr/local/bin/
        chmod +x /usr/local/bin/httpx
        rm httpx_linux_amd64.zip
    fi
    print_success "httpx installed"

    print_success "All security tools installed"
}

# Setup PostgreSQL
setup_postgresql() {
    print_status "Setting up PostgreSQL..."

    # Initialize PostgreSQL if needed
    if [ "$OS" == "rhel" ]; then
        postgresql-setup initdb
    fi

    # Start PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql

    # Generate secure password
    DB_PASSWORD=$(openssl rand -base64 32)

    # Create database and user
    sudo -u postgres psql <<EOF
CREATE USER soc_prod_user WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE soc_platform_prod OWNER soc_prod_user;
GRANT ALL PRIVILEGES ON DATABASE soc_platform_prod TO soc_prod_user;
ALTER USER soc_prod_user CREATEDB;
EOF

    # Configure PostgreSQL for production
    PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+\.\d+')
    PG_CONFIG="/etc/postgresql/$PG_VERSION/main/postgresql.conf"

    if [ -f "$PG_CONFIG" ]; then
        # Backup original config
        cp "$PG_CONFIG" "${PG_CONFIG}.backup"

        # Update configuration
        cat >> "$PG_CONFIG" <<EOF

# SOC Platform Production Settings
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 1310kB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 4
max_parallel_workers_per_gather = 2
max_parallel_workers = 4
max_parallel_maintenance_workers = 2
EOF
    fi

    # Configure pg_hba.conf for security
    PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"
    if [ -f "$PG_HBA" ]; then
        cp "$PG_HBA" "${PG_HBA}.backup"

        # Update authentication
        sed -i 's/local   all             all                                     peer/local   all             all                                     md5/' "$PG_HBA"
    fi

    # Restart PostgreSQL
    systemctl restart postgresql

    # Save database password
    echo "DATABASE_URL=postgresql+asyncpg://soc_prod_user:${DB_PASSWORD}@localhost:5432/soc_platform_prod" >> "$INSTALL_DIR/.env.production"

    print_success "PostgreSQL configured"
}

# Setup Redis
setup_redis() {
    print_status "Setting up Redis..."

    # Generate secure password
    REDIS_PASSWORD=$(openssl rand -base64 32)

    # Configure Redis
    REDIS_CONFIG="/etc/redis/redis.conf"
    if [ ! -f "$REDIS_CONFIG" ]; then
        REDIS_CONFIG="/etc/redis.conf"
    fi

    if [ -f "$REDIS_CONFIG" ]; then
        # Backup original config
        cp "$REDIS_CONFIG" "${REDIS_CONFIG}.backup"

        # Update configuration
        sed -i "s/# requirepass foobared/requirepass $REDIS_PASSWORD/" "$REDIS_CONFIG"
        sed -i "s/# maxclients 10000/maxclients 10000/" "$REDIS_CONFIG"
        sed -i "s/# maxmemory <bytes>/maxmemory 2gb/" "$REDIS_CONFIG"
        sed -i "s/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/" "$REDIS_CONFIG"

        # Enable persistence
        sed -i "s/save 900 1/save 900 1\nsave 300 10\nsave 60 10000/" "$REDIS_CONFIG"
        sed -i "s/# appendonly no/appendonly yes/" "$REDIS_CONFIG"
    fi

    # Start Redis
    systemctl start redis
    systemctl enable redis

    # Save Redis password
    echo "REDIS_PASSWORD=${REDIS_PASSWORD}" >> "$INSTALL_DIR/.env.production"
    echo "REDIS_URL=redis://:${REDIS_PASSWORD}@localhost:6379/0" >> "$INSTALL_DIR/.env.production"

    print_success "Redis configured"
}

# Create application user
create_app_user() {
    print_status "Creating application user..."

    if ! id "$USER" &>/dev/null; then
        useradd -m -s /bin/bash "$USER"
        usermod -aG sudo "$USER"
    fi

    print_success "Application user created"
}

# Setup application directories
setup_directories() {
    print_status "Setting up application directories..."

    # Create directories
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DATA_DIR"/{uploads,scan-results,quarantine,backups}
    mkdir -p "$LOG_DIR"/{app,nginx,audit}
    mkdir -p "$BACKUP_DIR"/{database,files,configs}

    # Set permissions
    chown -R "$USER:$GROUP" "$INSTALL_DIR"
    chown -R "$USER:$GROUP" "$DATA_DIR"
    chown -R "$USER:$GROUP" "$LOG_DIR"
    chown -R "$USER:$GROUP" "$BACKUP_DIR"

    chmod 750 "$INSTALL_DIR"
    chmod 750 "$DATA_DIR"
    chmod 750 "$LOG_DIR"
    chmod 750 "$BACKUP_DIR"

    print_success "Directories created"
}

# Clone application
clone_application() {
    print_status "Cloning application code..."

    # Clone from repository (replace with actual repo)
    if [ -d "$INSTALL_DIR/.git" ]; then
        cd "$INSTALL_DIR"
        git pull origin main
    else
        # Copy from current directory for now
        cp -r . "$INSTALL_DIR/"
    fi

    chown -R "$USER:$GROUP" "$INSTALL_DIR"

    print_success "Application code deployed"
}

# Setup Python environment
setup_python_env() {
    print_status "Setting up Python environment..."

    cd "$INSTALL_DIR/backend"

    # Create virtual environment
    sudo -u "$USER" python3 -m venv venv

    # Upgrade pip
    sudo -u "$USER" venv/bin/pip install --upgrade pip

    # Install Python dependencies
    sudo -u "$USER" venv/bin/pip install -r requirements.txt

    # Install additional production dependencies
    sudo -u "$USER" venv/bin/pip install \
        gunicorn \
        uvloop \
        httptools \
        python-multipart \
        email-validator \
        python-jose[cryptography] \
        passlib[bcrypt] \
        python-multipart \
        celery[redis] \
        flower \
        prometheus-client \
        sentry-sdk \
        python-nmap \
        zapv2 \
        beautifulsoup4 \
        cryptography

    print_success "Python environment configured"
}

# Setup Node.js environment
setup_nodejs_env() {
    print_status "Setting up Node.js environment..."

    # Install Node.js if not present
    if ! command -v node &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt-get install -y nodejs
    fi

    cd "$INSTALL_DIR/frontend"

    # Install dependencies
    sudo -u "$USER" npm ci --production

    # Build frontend
    sudo -u "$USER" npm run build

    print_success "Node.js environment configured"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."

    cd "$INSTALL_DIR/backend"

    # Initialize Alembic if needed
    if [ ! -d "alembic/versions" ]; then
        sudo -u "$USER" venv/bin/alembic init alembic
    fi

    # Run migrations
    sudo -u "$USER" venv/bin/alembic upgrade head

    print_success "Database migrations completed"
}

# Configure Nginx
configure_nginx() {
    print_status "Configuring Nginx..."

    # Create Nginx configuration
    cat > "/etc/nginx/sites-available/soc-platform" <<'EOF'
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;
limit_conn_zone $binary_remote_addr zone=addr:10m;

# Upstream backend
upstream soc_backend {
    least_conn;
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s backup;
    keepalive 32;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name soc-platform.com www.soc-platform.com;
    return 301 https://$server_name$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name soc-platform.com www.soc-platform.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/soc-platform.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/soc-platform.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' wss:;" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # Rate limiting
    limit_req zone=general burst=20 nodelay;
    limit_conn addr 100;

    # Logging
    access_log /var/log/soc-platform/nginx/access.log combined;
    error_log /var/log/soc-platform/nginx/error.log warn;

    # Root directory
    root /opt/soc-platform/frontend/dist;
    index index.html;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml+rss application/rss+xml application/atom+xml image/svg+xml text/javascript application/x-javascript application/x-font-ttf application/vnd.ms-fontobject font/opentype;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    # API routes
    location /api {
        limit_req zone=api burst=50 nodelay;

        proxy_pass http://soc_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket route
    location /ws {
        proxy_pass http://soc_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://soc_backend/health;
        access_log off;
    }

    # Block access to sensitive files
    location ~ /\.(env|git|svn|htaccess|htpasswd) {
        deny all;
        return 404;
    }

    # Client body size
    client_max_body_size 50M;
    client_body_buffer_size 1M;

    # Timeouts
    send_timeout 60s;
    keepalive_timeout 65;
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/soc-platform /etc/nginx/sites-enabled/

    # Test configuration
    nginx -t

    # Restart Nginx
    systemctl restart nginx
    systemctl enable nginx

    print_success "Nginx configured"
}

# Setup SSL certificate
setup_ssl() {
    print_status "Setting up SSL certificate..."

    # Get domain from user
    read -p "Enter your domain name (e.g., soc-platform.com): " DOMAIN

    if [ -n "$DOMAIN" ]; then
        # Obtain certificate
        certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN"

        # Setup auto-renewal
        echo "0 0 * * * root certbot renew --quiet" > /etc/cron.d/certbot-renew

        print_success "SSL certificate configured"
    else
        print_warning "SSL certificate setup skipped"
    fi
}

# Configure firewall
configure_firewall() {
    print_status "Configuring firewall..."

    if [ "$OS" == "debian" ]; then
        # UFW configuration
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow 22/tcp   # SSH
        ufw allow 80/tcp   # HTTP
        ufw allow 443/tcp  # HTTPS
        ufw allow 8000/tcp # Backend (internal only)
        ufw --force enable
    elif [ "$OS" == "rhel" ]; then
        # Firewalld configuration
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
    fi

    print_success "Firewall configured"
}

# Configure fail2ban
configure_fail2ban() {
    print_status "Configuring Fail2ban..."

    # Create jail configuration
    cat > "/etc/fail2ban/jail.local" <<EOF
[DEFAULT]
ignoreip = 127.0.0.1/8 ::1
bantime  = 3600
findtime  = 600
maxretry = 5

[sshd]
enabled = true
port    = ssh
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter  = nginx-http-auth
port    = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter  = nginx-limit-req
port    = http,https
logpath = /var/log/nginx/error.log

[soc-platform]
enabled = true
filter  = soc-platform
port    = http,https
logpath = /var/log/soc-platform/app/security.log
maxretry = 3
bantime  = 7200
EOF

    # Create custom filter for SOC platform
    cat > "/etc/fail2ban/filter.d/soc-platform.conf" <<EOF
[Definition]
failregex = ^.* Failed login attempt from <HOST>.*$
            ^.* Suspicious activity detected from <HOST>.*$
            ^.* Multiple failed API calls from <HOST>.*$
ignoreregex =
EOF

    # Restart fail2ban
    systemctl restart fail2ban
    systemctl enable fail2ban

    print_success "Fail2ban configured"
}

# Setup systemd services
setup_systemd_services() {
    print_status "Setting up systemd services..."

    # Backend service
    cat > "/etc/systemd/system/soc-backend.service" <<EOF
[Unit]
Description=SOC Platform Backend
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=$USER
Group=$GROUP
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=$INSTALL_DIR/backend/venv/bin"
ExecStart=$INSTALL_DIR/backend/venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 60 \
    --access-logfile /var/log/soc-platform/app/access.log \
    --error-logfile /var/log/soc-platform/app/error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Celery worker service
    cat > "/etc/systemd/system/soc-celery.service" <<EOF
[Unit]
Description=SOC Platform Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=$USER
Group=$GROUP
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=$INSTALL_DIR/backend/venv/bin"
ExecStart=$INSTALL_DIR/backend/venv/bin/celery -A app.core.celery.celery_app worker \
    --loglevel=info \
    --logfile=/var/log/soc-platform/app/celery.log \
    --concurrency=4
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    # Celery beat service
    cat > "/etc/systemd/system/soc-celery-beat.service" <<EOF
[Unit]
Description=SOC Platform Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=$USER
Group=$GROUP
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=$INSTALL_DIR/backend/venv/bin"
ExecStart=$INSTALL_DIR/backend/venv/bin/celery -A app.core.celery.celery_app beat \
    --loglevel=info \
    --logfile=/var/log/soc-platform/app/celery-beat.log
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload

    # Enable services
    systemctl enable soc-backend
    systemctl enable soc-celery
    systemctl enable soc-celery-beat

    print_success "Systemd services configured"
}

# Setup log rotation
setup_log_rotation() {
    print_status "Setting up log rotation..."

    cat > "/etc/logrotate.d/soc-platform" <<EOF
/var/log/soc-platform/*/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 $USER $GROUP
    sharedscripts
    postrotate
        systemctl reload soc-backend >/dev/null 2>&1 || true
    endscript
}
EOF

    print_success "Log rotation configured"
}

# Setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring..."

    # Install Prometheus Node Exporter
    wget -q https://github.com/prometheus/node_exporter/releases/latest/download/node_exporter-1.6.1.linux-amd64.tar.gz
    tar xzf node_exporter-*.tar.gz
    mv node_exporter-*/node_exporter /usr/local/bin/
    rm -rf node_exporter-*

    # Create systemd service for node exporter
    cat > "/etc/systemd/system/node_exporter.service" <<EOF
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
Type=simple
User=nobody
Group=nogroup
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl start node_exporter
    systemctl enable node_exporter

    print_success "Monitoring configured"
}

# Generate production config
generate_production_config() {
    print_status "Generating production configuration..."

    cd "$INSTALL_DIR/scripts"
    python3 generate_production_config.py

    print_success "Production configuration generated"
}

# Final setup
final_setup() {
    print_status "Performing final setup..."

    # Set proper permissions
    chmod 600 "$INSTALL_DIR/.env.production"
    chmod 600 "$INSTALL_DIR/secrets.json"

    # Start services
    systemctl start soc-backend
    systemctl start soc-celery
    systemctl start soc-celery-beat

    print_success "Services started"

    # Create initial admin user
    cd "$INSTALL_DIR/backend"
    sudo -u "$USER" venv/bin/python <<EOF
from app.core.database import get_db
from app.models.user import User
from app.core.security import get_password_hash
import asyncio

async def create_admin():
    db = await anext(get_db())
    admin = User(
        username="admin",
        email="admin@soc-platform.com",
        password_hash=get_password_hash("ChangeMeNow123!"),
        role="admin",
        is_active=True,
        is_verified=True
    )
    db.add(admin)
    await db.commit()
    print("Admin user created")

asyncio.run(create_admin())
EOF

    print_success "Initial admin user created (username: admin, password: ChangeMeNow123!)"
}

# Main installation flow
main() {
    echo "================================================"
    echo "     $PLATFORM_NAME Production Deployment"
    echo "================================================"
    echo ""

    check_root
    detect_os
    install_system_deps
    install_security_tools
    create_app_user
    setup_directories
    clone_application
    setup_postgresql
    setup_redis
    setup_python_env
    setup_nodejs_env
    generate_production_config
    run_migrations
    configure_nginx
    setup_ssl
    configure_firewall
    configure_fail2ban
    setup_systemd_services
    setup_log_rotation
    setup_monitoring
    final_setup

    echo ""
    echo "================================================"
    echo "     Installation Complete!"
    echo "================================================"
    echo ""
    print_success "Platform URL: https://soc-platform.com"
    print_success "Admin Login: admin / ChangeMeNow123!"
    print_warning "Please change the admin password immediately!"
    echo ""
    echo "Next steps:"
    echo "1. Change admin password"
    echo "2. Configure email settings in .env.production"
    echo "3. Set up backup automation"
    echo "4. Configure external integrations (Shodan, VirusTotal, etc.)"
    echo "5. Review and adjust security settings"
    echo ""
    echo "Services status:"
    systemctl status soc-backend --no-pager
    systemctl status soc-celery --no-pager
    systemctl status nginx --no-pager
    systemctl status postgresql --no-pager
    systemctl status redis --no-pager
}

# Run main function
main "$@"