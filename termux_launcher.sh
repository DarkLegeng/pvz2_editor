#!/data/data/com.termux/files/usr/bin/bash

REPO_URL="https://github.com/DarkLegeng/pvz2_editor.git"
INSTALL_DIR="$HOME/pvz2_editor"
LEVELS_DIR="/sdcard/Download/PvZ2_Levels"
BACKUP_DIR="$HOME/pvz2_backups"
INSTALLER_SCRIPT="$HOME/installer.sh"
PYTHON_DEPS="requirements.txt"

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

check_termux() {
    [ ! -d "/data/data/com.termux/files/home" ] && error "Этот скрипт должен запускаться в Termux!"
}

fix_pkg_config() {
    info "Исправление конфигурации пакетов..."
    mkdir -p $PREFIX/etc/apt/apt.conf.d
    echo 'DPkg::options { "--force-confdef"; "--force-confnew"; }' > $PREFIX/etc/apt/apt.conf.d/99force-conf
    export DEBIAN_FRONTEND=noninteractive
}

install_dependencies() {
    info "Установка системных зависимостей..."
    pkg update -y && pkg upgrade -y
    
    # Установка основных пакетов
    for pkg in python tk x11-repo git wget openssl; do
        pkg install -y $pkg || error "Не удалось установить $pkg"
    done
    
    # Дополнительные зависимости для Tkinter
    pkg install -y python-tkinter || {
        warning "Прямая установка python-tkinter не удалась, пробуем альтернативный метод..."
        pip install tk || error "Не удалось установить tk через pip"
    }
    
    # Проверка установки Tkinter
    python -c "import tkinter" 2>/dev/null || {
        warning "Tkinter не установлен, пробуем переустановить Python..."
        pkg uninstall python -y
        pkg install -y python tk
        python -c "import tkinter" || error "Критическая ошибка: Tkinter не работает"
    }
}

setup_storage() {
    info "Настройка доступа к хранилищу..."
    termux-setup-storage
    mkdir -p "$LEVELS_DIR" || warning "Не удалось создать папку для уровней"
}

clone_or_update_repo() {
    info "Загрузка/обновление редактора..."
    if [ -d "$INSTALL_DIR" ]; then
        info "Обновление существующей копии..."
        cd "$INSTALL_DIR"
        git reset --hard
        git pull || error "Не удалось обновить репозиторий"
    else
        info "Клонирование репозитория..."
        git clone "$REPO_URL" "$INSTALL_DIR" || error "Не удалось клонировать репозиторий"
        cd "$INSTALL_DIR"
    fi
}

install_python_deps() {
    info "Установка Python-зависимостей..."
    pip install --upgrade pip || warning "Не удалось обновить pip"
    
    if [ -f "$PYTHON_DEPS" ]; then
        pip install -r "$PYTHON_DEPS" || error "Не удалось установить зависимости"
    else
        warning "Файл $PYTHON_DEPS не найден, устанавливаем основные пакеты..."
        pip install tk pillow || error "Не удалось установить основные пакеты"
    fi
}

fix_save_path() {
    info "Настройка пути сохранения..."
    sed -i "s|editor.save_level(filename)|editor.save_level(f\"$LEVELS_DIR/{filename}\")|g" level.py || \
    warning "Не удалось изменить путь сохранения"
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
    
    check_termux
    fix_pkg_config
    install_dependencies
    setup_storage
    clone_or_update_repo
    install_python_deps
    fix_save_path
    run_editor
}

main
