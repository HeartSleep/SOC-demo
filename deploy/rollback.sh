#!/bin/bash

# Emergency Rollback Script
# Quickly rollback to previous deployment

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
ENVIRONMENT=${1:-staging}
CURRENT_ENV_FILE="/var/lib/soc-platform/current-env"
BACKUP_DIR="/var/lib/soc-platform/backups"
ROLLBACK_LOG="/var/log/soc-platform/rollback.log"

# Functions
log() {
    echo -e "${2}$1${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $ROLLBACK_LOG
}

get_current_env() {
    if [ -f "$CURRENT_ENV_FILE" ]; then
        cat $CURRENT_ENV_FILE
    else
        echo "blue"
    fi
}

get_previous_env() {
    current=$(get_current_env)
    if [ "$current" = "blue" ]; then
        echo "green"
    else
        echo "blue"
    fi
}

find_last_successful_deployment() {
    # Find the last successful deployment from logs
    if [ -f "/var/log/soc-platform/deployment.log" ]; then
        grep "Deployment successful" /var/log/soc-platform/deployment.log | \
            tail -2 | head -1 | \
            grep -oP 'SHA: \K[a-f0-9]+' || echo ""
    else
        echo ""
    fi
}

restore_from_backup() {
    local backup_name=$1
    local target_env=$2

    log "Restoring from backup: $backup_name to $target_env environment..." "$BLUE"

    # Check if backup exists
    if [ ! -f "$BACKUP_DIR/$backup_name.tar.gz" ]; then
        log "❌ Backup not found: $backup_name" "$RED"
        return 1
    fi

    # Extract backup
    tar -xzf "$BACKUP_DIR/$backup_name.tar.gz" -C /tmp/

    # Load docker images
    docker load < /tmp/$backup_name/backend.tar
    docker load < /tmp/$backup_name/frontend.tar

    # Deploy using the backup
    docker-compose -f /tmp/$backup_name/docker-compose.$target_env.yml up -d

    # Clean up temp files
    rm -rf /tmp/$backup_name

    log "✅ Restored from backup successfully" "$GREEN"
    return 0
}

quick_rollback() {
    log "========================================" "$YELLOW"
    log "   🔄 QUICK ROLLBACK - $ENVIRONMENT" "$YELLOW"
    log "========================================" "$YELLOW"

    CURRENT_ENV=$(get_current_env)
    PREVIOUS_ENV=$(get_previous_env)

    log "Current failed environment: $CURRENT_ENV" "$RED"
    log "Rolling back to: $PREVIOUS_ENV" "$GREEN"

    # Check if previous environment is still running
    if docker ps | grep -q "soc-backend-$PREVIOUS_ENV"; then
        log "Previous environment is still running, switching traffic..." "$GREEN"

        # Switch nginx to previous environment
        ./blue_green_deploy.sh switch-traffic $PREVIOUS_ENV

        # Stop current failed environment
        docker-compose -f "docker-compose.$CURRENT_ENV.yml" down || true

        # Update current environment file
        echo $PREVIOUS_ENV > $CURRENT_ENV_FILE

        log "✅ Quick rollback completed!" "$GREEN"
        return 0
    else
        log "Previous environment not running, attempting restore..." "$YELLOW"
        return 1
    fi
}

database_rollback() {
    local migration_version=$1

    log "Rolling back database migrations to version: $migration_version" "$YELLOW"

    # Connect to database and rollback
    cd /opt/soc-platform/backend
    source venv/bin/activate

    # Using Alembic for migrations
    alembic downgrade $migration_version

    log "✅ Database rolled back to version: $migration_version" "$GREEN"
}

full_rollback() {
    log "========================================" "$RED"
    log "   ⚠️  FULL ROLLBACK - $ENVIRONMENT" "$RED"
    log "========================================" "$RED"

    # Find last successful deployment
    LAST_SHA=$(find_last_successful_deployment)

    if [ -z "$LAST_SHA" ]; then
        log "❌ No previous successful deployment found!" "$RED"
        log "Manual intervention required!" "$RED"
        exit 1
    fi

    log "Last successful deployment SHA: $LAST_SHA" "$BLUE"

    # Stop all current containers
    log "Stopping all current containers..." "$YELLOW"
    docker-compose -f "docker-compose.blue.yml" down 2>/dev/null || true
    docker-compose -f "docker-compose.green.yml" down 2>/dev/null || true

    # Pull previous images
    log "Pulling previous images..." "$YELLOW"
    docker pull "ghcr.io/soc-platform-backend:$LAST_SHA"
    docker pull "ghcr.io/soc-platform-frontend:$LAST_SHA"

    # Tag as latest
    docker tag "ghcr.io/soc-platform-backend:$LAST_SHA" "ghcr.io/soc-platform-backend:latest"
    docker tag "ghcr.io/soc-platform-frontend:$LAST_SHA" "ghcr.io/soc-platform-frontend:latest"

    # Deploy blue environment with previous version
    TARGET_ENV="blue"

    cat > "docker-compose.$TARGET_ENV.yml" << EOF
version: '3.8'

services:
  backend-$TARGET_ENV:
    image: ghcr.io/soc-platform-backend:$LAST_SHA
    container_name: soc-backend-$TARGET_ENV
    environment:
      - ENVIRONMENT=$ENVIRONMENT
      - DATABASE_URL=\${DATABASE_URL}
      - REDIS_URL=\${REDIS_URL}
      - SECRET_KEY=\${SECRET_KEY}
      - JWT_SECRET_KEY=\${JWT_SECRET_KEY}
    ports:
      - "8001:8000"
    restart: unless-stopped

  frontend-$TARGET_ENV:
    image: ghcr.io/soc-platform-frontend:$LAST_SHA
    container_name: soc-frontend-$TARGET_ENV
    environment:
      - VITE_API_URL=http://localhost:8001
      - VITE_WS_URL=ws://localhost:8001
    ports:
      - "3001:80"
    depends_on:
      - backend-$TARGET_ENV
    restart: unless-stopped
EOF

    # Start the rollback deployment
    docker-compose -f "docker-compose.$TARGET_ENV.yml" up -d

    # Wait for health check
    log "Waiting for services to be healthy..." "$YELLOW"
    sleep 30

    # Check health
    if curl -f "http://localhost:8001/health" > /dev/null 2>&1; then
        log "✅ Rollback deployment healthy" "$GREEN"

        # Update nginx
        ./blue_green_deploy.sh switch-traffic $TARGET_ENV

        # Update current environment
        echo $TARGET_ENV > $CURRENT_ENV_FILE

        log "✅ Full rollback completed successfully!" "$GREEN"

        # Send notification
        if [ -n "$SLACK_WEBHOOK" ]; then
            curl -X POST $SLACK_WEBHOOK \
                -H 'Content-Type: application/json' \
                -d "{\"text\":\"⚠️ Emergency rollback completed for $ENVIRONMENT. Rolled back to SHA: $LAST_SHA\"}"
        fi
    else
        log "❌ Rollback deployment failed!" "$RED"
        log "CRITICAL: Manual intervention required immediately!" "$RED"

        # Send critical alert
        if [ -n "$PAGERDUTY_KEY" ]; then
            curl -X POST "https://events.pagerduty.com/v2/enqueue" \
                -H 'Content-Type: application/json' \
                -d "{
                    \"routing_key\": \"$PAGERDUTY_KEY\",
                    \"event_action\": \"trigger\",
                    \"payload\": {
                        \"summary\": \"CRITICAL: Rollback failed for $ENVIRONMENT\",
                        \"severity\": \"critical\",
                        \"source\": \"soc-platform\"
                    }
                }"
        fi

        exit 1
    fi
}

# Menu
show_menu() {
    echo ""
    echo "Select rollback type:"
    echo "  1) Quick rollback (switch to previous environment)"
    echo "  2) Full rollback (redeploy last successful version)"
    echo "  3) Database rollback only"
    echo "  4) Restore from backup"
    echo "  5) Emergency stop all"
    echo -n "Choice: "
}

emergency_stop() {
    log "⚠️ EMERGENCY STOP - Stopping all services!" "$RED"

    # Stop all SOC platform containers
    docker ps | grep soc- | awk '{print $1}' | xargs -r docker stop

    # Remove all SOC platform containers
    docker ps -a | grep soc- | awk '{print $1}' | xargs -r docker rm

    # Update nginx to maintenance page
    cat > /tmp/nginx-maintenance.conf << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        return 503;
        error_page 503 @maintenance;
    }

    location @maintenance {
        root /var/www/maintenance;
        rewrite ^.*$ /index.html break;
    }
}
EOF

    sudo mv /tmp/nginx-maintenance.conf /etc/nginx/sites-available/soc-platform
    sudo nginx -s reload

    log "All services stopped. Maintenance mode activated." "$YELLOW"
}

# Main
main() {
    # Create necessary directories
    mkdir -p /var/lib/soc-platform
    mkdir -p /var/log/soc-platform
    mkdir -p $BACKUP_DIR

    # Try quick rollback first
    if quick_rollback; then
        exit 0
    fi

    # If quick rollback fails, show menu
    show_menu
    read choice

    case $choice in
        1)
            quick_rollback || full_rollback
            ;;
        2)
            full_rollback
            ;;
        3)
            echo -n "Enter migration version to rollback to: "
            read version
            database_rollback $version
            ;;
        4)
            echo -n "Enter backup name: "
            read backup_name
            restore_from_backup $backup_name $(get_previous_env)
            ;;
        5)
            emergency_stop
            ;;
        *)
            log "Invalid choice" "$RED"
            exit 1
            ;;
    esac
}

# Handle interrupts
trap 'log "Rollback interrupted!" "$RED"; exit 1' INT TERM

# Run with urgency parameter for immediate action
if [ "$1" = "NOW" ] || [ "$1" = "EMERGENCY" ]; then
    log "🚨 EMERGENCY ROLLBACK INITIATED!" "$RED"
    quick_rollback || full_rollback
else
    main
fi