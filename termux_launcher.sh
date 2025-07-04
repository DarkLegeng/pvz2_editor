#!/data/data/com.termux/files/usr/bin/bash

# Конфигурация
REPO_URL="https://github.com/DarkLegeng/pvz2_editor.git"
INSTALL_DIR="$HOME/pvz2_editor"
LEVELS_DIR="/sdcard/Download/PvZ2_Levels"
BACKUP_DIR="$HOME/pvz2_backups"
PYTHON_DEPS="requirements.txt"

# Цвета для вывода
GREEN='\e[1;32m'
RED='\e[1;31m'
YELLOW='\e[1;33m'
NC='\e[0m'

# Функции для вывода сообщений
error() {
    echo -e "${RED}✖ Ошибка: $1${NC}" >&2
    exit 1
}

info() {
    echo -e "${GREEN}ℹ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Проверка запуска в Termux
check_termux() {
    if [ ! -d "/data/data/com.termux/files/home" ]; then
        error "Этот скрипт должен запускаться в Termux!"
    fi
}

# Установка зависимостей
install_dependencies() {
    info "Обновление пакетов..."
    pkg update -y && pkg upgrade -y || warning "Не удалось обновить пакеты"

    info "Установка Python и Git..."
    pkg install -y python git || error "Не удалось установить Python"

    info "Установка консольных инструментов..."
    pkg install -y dialog || warning "Не удалось установить dialog (опционально)"

    info "Установка Python-библиотек..."
    pip install --upgrade pip || warning "Не удалось обновить pip"
    pip install inquirerpy || warning "Не удалось установить inquirerpy (будет простой ввод)"
}

# Настройка хранилища
setup_storage() {
    info "Запрос разрешений на хранилище..."
    termux-setup-storage
    sleep 2  # Даем время для обработки разрешения

    info "Создание папки для уровней..."
    mkdir -p "$LEVELS_DIR" || warning "Не удалось создать $LEVELS_DIR"
}

# Клонирование или обновление репозитория
clone_repo() {
    if [ -d "$INSTALL_DIR" ]; then
        info "Обновление существующей копии..."
        cd "$INSTALL_DIR" || error "Не удалось перейти в $INSTALL_DIR"
        git reset --hard
        git pull || error "Не удалось обновить репозиторий"
    else
        info "Клонирование репозитория..."
        git clone "$REPO_URL" "$INSTALL_DIR" || error "Не удалось клонировать репозиторий"
        cd "$INSTALL_DIR" || error "Не удалось перейти в $INSTALL_DIR"
    fi
}

# Патчинг для работы в Termux
patch_for_termux() {
    info "Адаптация кода для Termux..."

    # Удаление Tkinter
    sed -i '/import tkinter/d' level.py
    sed -i '/from tkinter import/d' level.py

    # Замена GUI-функций на консольные аналоги
    sed -i 's/messagebox.showwarning(/print("⚠ Предупреждение: /g' level.py
    sed -i 's/messagebox.showerror(/print("✖ Ошибка: /g' level.py
    sed -i 's/simpledialog.askstring(/input(/g' level.py
    sed -i 's/simpledialog.askinteger(/int(input(/g' level.py

    # Изменение пути сохранения
    sed -i "s|editor.save_level(filename)|editor.save_level('$LEVELS_DIR/' + filename)|g" level.py

    # Упрощение выбора опций
    sed -i 's/select_from_list(/print("Варианты:"); [print(f"{i}. {opt[1]}") for i, opt in enumerate(options, 1)]; input("Выберите номер: ")/g' level.py

    info "Код адаптирован для консольного режима"
}

# Запуск редактора
run_editor() {
    info "Запуск редактора уровней..."
    cd "$INSTALL_DIR" || error "Не удалось перейти в $INSTALL_DIR"
    python level.py

    echo -e "\n${GREEN}=== Готово! ===${NC}"
    echo "Уровни сохранены в: $LEVELS_DIR"
    echo "Для повторного запуска:"
    echo "cd $INSTALL_DIR && python level.py"
}

# Основная функция
main() {
    clear
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════╗"
    echo "║    PvZ 2 Level Editor для Termux     ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "${NC}"
    
    check_termux
    install_dependencies
    setup_storage
    clone_repo
    patch_for_termux
    run_editor
}

# Запуск
main
