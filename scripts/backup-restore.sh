#!/bin/bash

# Bwenge OS Backup and Restore System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
BACKUP_DIR=${BACKUP_DIR:-"./backups"}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ENVIRONMENT=${ENVIRONMENT:-"development"}

# Database configuration
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-"5432"}
DB_NAME=${DB_NAME:-"bwenge"}
DB_USER=${DB_USER:-"bwenge"}
DB_PASSWORD=${DB_PASSWORD:-"bwenge_dev"}

# Redis configuration
REDIS_HOST=${REDIS_HOST:-"localhost"}
REDIS_PORT=${REDIS_PORT:-"6379"}

# Weaviate configuration
WEAVIATE_URL=${WEAVIATE_URL:-"http://localhost:8080"}

show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  backup          Create full system backup"
    echo "  restore         Restore from backup"
    echo "  list            List available backups"
    echo "  cleanup         Clean old backups"
    echo "  db-backup       Backup only database"
    echo "  db-restore      Restore only database"
    echo "  files-backup    Backup only files"
    echo "  files-restore   Restore only files"
    echo ""
    echo "Options:"
    echo "  --backup-name   Specify backup name for restore"
    echo "  --keep-days     Days to keep backups (default: 30)"
    echo "  --environment   Environment (development/staging/production)"
    echo ""
    echo "Examples:"
    echo "  $0 backup"
    echo "  $0 restore --backup-name backup_20231201_120000"
    echo "  $0 cleanup --keep-days 7"
}

create_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    print_success "Backup directory created: $BACKUP_DIR"
}

backup_database() {
    local backup_name=${1:-"db_backup_$TIMESTAMP"}
    local backup_file="$BACKUP_DIR/${backup_name}.sql"
    
    print_status "Backing up PostgreSQL database..."
    
    if command -v docker-compose &> /dev/null && docker-compose ps postgres | grep -q Up; then
        # Use docker-compose if available
        docker-compose exec -T postgres pg_dump -U "$DB_USER" "$DB_NAME" > "$backup_file"
    else
        # Use direct connection
        PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" > "$backup_file"
    fi
    
    if [ -f "$backup_file" ] && [ -s "$backup_file" ]; then
        gzip "$backup_file"
        print_success "Database backup created: ${backup_file}.gz"
        return 0
    else
        print_error "Database backup failed"
        return 1
    fi
}

restore_database() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        return 1
    fi
    
    print_status "Restoring PostgreSQL database from: $backup_file"
    
    # Decompress if needed
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" > "${backup_file%.gz}"
        backup_file="${backup_file%.gz}"
    fi
    
    if command -v docker-compose &> /dev/null && docker-compose ps postgres | grep -q Up; then
        # Use docker-compose if available
        docker-compose exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" < "$backup_file"
    else
        # Use direct connection
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < "$backup_file"
    fi
    
    print_success "Database restored successfully"
}

backup_redis() {
    local backup_name=${1:-"redis_backup_$TIMESTAMP"}
    local backup_file="$BACKUP_DIR/${backup_name}.rdb"
    
    print_status "Backing up Redis data..."
    
    if command -v docker-compose &> /dev/null && docker-compose ps redis | grep -q Up; then
        # Use docker-compose if available
        docker-compose exec redis redis-cli BGSAVE
        sleep 5  # Wait for background save to complete
        docker-compose exec redis cat /data/dump.rdb > "$backup_file"
    else
        # Use direct connection
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" BGSAVE
        sleep 5
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --rdb "$backup_file"
    fi
    
    if [ -f "$backup_file" ] && [ -s "$backup_file" ]; then
        gzip "$backup_file"
        print_success "Redis backup created: ${backup_file}.gz"
        return 0
    else
        print_error "Redis backup failed"
        return 1
    fi
}

backup_weaviate() {
    local backup_name=${1:-"weaviate_backup_$TIMESTAMP"}
    local backup_file="$BACKUP_DIR/${backup_name}.json"
    
    print_status "Backing up Weaviate data..."
    
    # Export all objects from Weaviate
    curl -s "$WEAVIATE_URL/v1/objects" | jq '.' > "$backup_file"
    
    if [ -f "$backup_file" ] && [ -s "$backup_file" ]; then
        gzip "$backup_file"
        print_success "Weaviate backup created: ${backup_file}.gz"
        return 0
    else
        print_error "Weaviate backup failed"
        return 1
    fi
}

backup_files() {
    local backup_name=${1:-"files_backup_$TIMESTAMP"}
    local backup_file="$BACKUP_DIR/${backup_name}.tar.gz"
    
    print_status "Backing up uploaded files and assets..."
    
    # Create tar archive of uploads and assets
    tar -czf "$backup_file" \
        --exclude="*.tmp" \
        --exclude="*.log" \
        uploads/ assets/ 2>/dev/null || true
    
    if [ -f "$backup_file" ] && [ -s "$backup_file" ]; then
        print_success "Files backup created: $backup_file"
        return 0
    else
        print_error "Files backup failed"
        return 1
    fi
}

restore_files() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        return 1
    fi
    
    print_status "Restoring files from: $backup_file"
    
    # Extract tar archive
    tar -xzf "$backup_file"
    
    print_success "Files restored successfully"
}

create_full_backup() {
    local backup_name="full_backup_$TIMESTAMP"
    
    print_status "Creating full system backup: $backup_name"
    
    create_backup_dir
    
    # Create backup manifest
    local manifest_file="$BACKUP_DIR/${backup_name}_manifest.json"
    cat > "$manifest_file" << EOF
{
    "backup_name": "$backup_name",
    "timestamp": "$TIMESTAMP",
    "environment": "$ENVIRONMENT",
    "components": {
        "database": "${backup_name}_db.sql.gz",
        "redis": "${backup_name}_redis.rdb.gz",
        "weaviate": "${backup_name}_weaviate.json.gz",
        "files": "${backup_name}_files.tar.gz"
    },
    "version": "1.0"
}
EOF
    
    # Backup each component
    local success=true
    
    if ! backup_database "${backup_name}_db"; then
        success=false
    fi
    
    if ! backup_redis "${backup_name}_redis"; then
        success=false
    fi
    
    if ! backup_weaviate "${backup_name}_weaviate"; then
        success=false
    fi
    
    if ! backup_files "${backup_name}_files"; then
        success=false
    fi
    
    if [ "$success" = true ]; then
        print_success "Full backup completed: $backup_name"
        print_status "Backup manifest: $manifest_file"
    else
        print_error "Some backup components failed"
        return 1
    fi
}

restore_full_backup() {
    local backup_name="$1"
    
    if [ -z "$backup_name" ]; then
        print_error "Backup name is required for restore"
        return 1
    fi
    
    local manifest_file="$BACKUP_DIR/${backup_name}_manifest.json"
    
    if [ ! -f "$manifest_file" ]; then
        print_error "Backup manifest not found: $manifest_file"
        return 1
    fi
    
    print_status "Restoring from backup: $backup_name"
    
    # Read manifest
    local db_file=$(jq -r '.components.database' "$manifest_file")
    local redis_file=$(jq -r '.components.redis' "$manifest_file")
    local weaviate_file=$(jq -r '.components.weaviate' "$manifest_file")
    local files_file=$(jq -r '.components.files' "$manifest_file")
    
    # Restore each component
    print_warning "This will overwrite existing data. Continue? (y/N)"
    read -r confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        print_status "Restore cancelled"
        return 0
    fi
    
    # Stop services during restore
    if command -v docker-compose &> /dev/null; then
        print_status "Stopping services..."
        docker-compose stop api-gateway auth-service ingest-service persona-service chat-service 3d-service analytics-service payments-service
    fi
    
    # Restore database
    if [ -f "$BACKUP_DIR/$db_file" ]; then
        restore_database "$BACKUP_DIR/$db_file"
    fi
    
    # Restore files
    if [ -f "$BACKUP_DIR/$files_file" ]; then
        restore_files "$BACKUP_DIR/$files_file"
    fi
    
    # Restart services
    if command -v docker-compose &> /dev/null; then
        print_status "Starting services..."
        docker-compose up -d
    fi
    
    print_success "Full restore completed"
}

list_backups() {
    print_status "Available backups in $BACKUP_DIR:"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        print_warning "Backup directory does not exist"
        return 0
    fi
    
    echo ""
    echo "Full Backups:"
    for manifest in "$BACKUP_DIR"/*_manifest.json; do
        if [ -f "$manifest" ]; then
            local backup_name=$(jq -r '.backup_name' "$manifest")
            local timestamp=$(jq -r '.timestamp' "$manifest")
            local environment=$(jq -r '.environment' "$manifest")
            echo "  - $backup_name ($environment) - $timestamp"
        fi
    done
    
    echo ""
    echo "Individual Backups:"
    ls -la "$BACKUP_DIR"/*.sql.gz "$BACKUP_DIR"/*.rdb.gz "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "  No individual backups found"
}

cleanup_backups() {
    local keep_days=${1:-30}
    
    print_status "Cleaning up backups older than $keep_days days..."
    
    if [ ! -d "$BACKUP_DIR" ]; then
        print_warning "Backup directory does not exist"
        return 0
    fi
    
    # Find and delete old backups
    local deleted_count=0
    
    find "$BACKUP_DIR" -name "*.gz" -o -name "*.json" -type f -mtime +$keep_days | while read -r file; do
        rm -f "$file"
        print_status "Deleted: $(basename "$file")"
        ((deleted_count++))
    done
    
    print_success "Cleanup completed. Deleted $deleted_count files."
}

# Main script logic
case "${1:-}" in
    "backup")
        create_full_backup
        ;;
    "restore")
        shift
        backup_name=""
        while [[ $# -gt 0 ]]; do
            case $1 in
                --backup-name)
                    backup_name="$2"
                    shift 2
                    ;;
                *)
                    print_error "Unknown option: $1"
                    show_usage
                    exit 1
                    ;;
            esac
        done
        restore_full_backup "$backup_name"
        ;;
    "list")
        list_backups
        ;;
    "cleanup")
        shift
        keep_days=30
        while [[ $# -gt 0 ]]; do
            case $1 in
                --keep-days)
                    keep_days="$2"
                    shift 2
                    ;;
                *)
                    print_error "Unknown option: $1"
                    show_usage
                    exit 1
                    ;;
            esac
        done
        cleanup_backups "$keep_days"
        ;;
    "db-backup")
        create_backup_dir
        backup_database
        ;;
    "db-restore")
        if [ -z "$2" ]; then
            print_error "Backup file path is required"
            exit 1
        fi
        restore_database "$2"
        ;;
    "files-backup")
        create_backup_dir
        backup_files
        ;;
    "files-restore")
        if [ -z "$2" ]; then
            print_error "Backup file path is required"
            exit 1
        fi
        restore_files "$2"
        ;;
    *)
        show_usage
        exit 1
        ;;
esac