#!/data/data/com.termux/files/usr/bin/bash

REPO_URL="https://github.com/DarkLegeng/pvz2_editor.git"
INSTALL_DIR="$HOME/pvz2_editor"
LEVELS_DIR="/sdcard/Download/PvZ2_Levels"
BACKUP_DIR="$HOME/pvz2_backups"
INSTALLER_SCRIPT="$HOME/installer.sh"

GREEN='\e[1;32m'
RED='\e[1;31m'
YELLOW='\e[1;33m'
BLUE='\e[1;34m'
NC='\e[0m'

error() { 
    echo -e "${RED}✖ Ошибка: $1${NC}" >&2
    [ "$2" == "noexit" ] || exit 1
}

info() {
    echo -e "${GREEN}ℹ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

debug() {
    echo -e "${BLUE}🐛 $1${NC}"
}

[ ! -d "/data/data/com.termux/files/home" ] && error "Этот скрипт должен запускаться в Termux!"

auto_fix_configs() {
    info "Настройка системы для автоматического разрешения конфликтов..."
    mkdir -p /data/data/com.termux/files/usr/etc/apt/apt.conf.d
    echo 'DPkg::options { "--force-confdef"; "--force-confnew"; }' > /data/data/com.termux/files/usr/etc/apt/apt.conf.d/99force-conf
    export DEBIAN_FRONTEND=noninteractive
}

fix_openssl_issue() {
    info "Попытка исправить проблему с OpenSSL..."
    
    mkdir -p "$BACKUP_DIR"
    if [ -f "/data/data/com.termux/files/usr/etc/tls/openssl.cnf" ]; then
        cp "/data/data/com.termux/files/usr/etc/tls/openssl.cnf" "$BACKUP_DIR/openssl.cnf.backup"
    fi
    
    yes | pkg install openssl --reinstall 2>/dev/null || {
        warning "Не удалось автоматически исправить OpenSSL, попробую ручной метод..."
        pkg uninstall openssl -y
        pkg clean
        pkg update -y
        yes | pkg install openssl -y || error "Критическая ошибка: не удалось установить OpenSSL"
    }
}

create_backup() {
    info "Создаем резервную копию текущей установки..."
    mkdir -p "$BACKUP_DIR"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    tar -czf "$BACKUP_DIR/pvz2_editor_backup_$timestamp.tar.gz" -C "$INSTALL_DIR" . 2>/dev/null
}

check_updates() {
    info "Проверка обновлений..."
    if [ -f "$INSTALLER_SCRIPT" ]; then
        rm -f "$INSTALLER_SCRIPT"
    fi
    
    if ! curl -sL https://raw.githubusercontent.com/DarkLegeng/pvz2_editor/main/termux_launcher.sh > "$INSTALLER_SCRIPT"; then
        error "Не удалось загрузить обновлённый скрипт"
    fi
    
    chmod +x "$INSTALLER_SCRIPT"
    info "Обновлённый скрипт сохранён как $INSTALLER_SCRIPT"
}

main_install() {
    auto_fix_configs
    
    info "1. Обновление пакетов Termux..."
    yes | pkg update -y && yes | pkg upgrade -y || {
        warning "Обновление пакетов завершилось с предупреждениями, проверяем OpenSSL..."
        fix_openssl_issue
        yes | pkg upgrade -y || error "Не удалось обновить пакеты"
    }
    
    info "2. Установка системных зависимостей..."
    yes | pkg install -y python git || error "Не удалось установить зависимости"
    
    info "3. Настройка доступа к хранилищу..."
    termux-setup-storage
    mkdir -p "$LEVELS_DIR" || warning "Не удалось создать папку для уровней"
    
    info "4. Загрузка/обновление редактора..."
    if [ -d "$INSTALL_DIR" ]; then
        create_backup
        cd "$INSTALL_DIR"
        git reset --hard || warning "Не удалось сбросить изменения"
        git pull || error "Не удалось обновить репозиторий"
    else
        git clone "$REPO_URL" "$INSTALL_DIR" || error "Не удалось клонировать репозиторий"
        cd "$INSTALL_DIR"
    fi
    
    info "5. Установка Python-зависимостей..."
    yes | pip install --upgrade pip || warning "Не удалось обновить pip"
    yes | pip install -r requirements.txt || error "Не удалось установить зависимости"
    
    info "6. Настройка системы сохранения..."
    if grep -q "editor.save_level(filename)" level.py; then
        sed -i "s|editor.save_level(filename)|editor.save_level(f\"$LEVELS_DIR/{filename}\")|g" level.py || \
        warning "Не удалось изменить путь сохранения"
    else
        debug "Путь сохранения уже настроен"
    fi
    
    chmod +x level.py termux_launcher.sh
}

run_editor() {
    info "🚀 Запуск PvZ 2 Level Editor..."
    echo -e "${GREEN}========================================${NC}"
    python level.py
    
    echo -e "${GREEN}========================================${NC}"
    info "Уровни сохраняются в: ${YELLOW}$LEVELS_DIR${NC}"
    info "Для повторного запуска вводите: ${YELLOW}python3 level.py${NC}"
    info "Для обновления редактора запустите этот скрипт снова"
    echo -e "${GREEN}========================================${NC}"
}

main() {
    clear
    echo -e "${GREEN}╔══════════════════════════════════════╗"
    echo -e "║    PvZ 2 Level Editor Installer      ║"
    echo -e "╚══════════════════════════════════════╝${NC}"
    
    if [ "$0" = "bash" ]; then
        check_updates
        exec bash "$INSTALLER_SCRIPT"
    fi
    
    main_install
    run_editor
}

main
