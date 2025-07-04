cat > termux_launcher.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash

# ==============================================
# PvZ 2 Level Editor Launcher
# Авто-дешифровка level.py
# ==============================================

# Конфигурация
REPO_URL="https://github.com/DarkLegeng/pvz2_editor.git"
INSTALL_DIR="$HOME/pvz2_editor"
LEVELS_DIR="/sdcard/Download/PvZ2_Levels"
GIT_CRYPT_KEY="-----BEGIN GIT-CRYPT KEY-----
ВАШ_КЛЮЧ_BASE64_ЗДЕСЬ
-----END GIT-CRYPT KEY-----"

# Цвета
RED='\e[1;31m'
GREEN='\e[1;32m'
NC='\e[0m'

# Функции
die() {
    echo -e "${RED}Ошибка: $1${NC}" >&2
    exit 1
}

# Установка
install() {
    echo -e "${GREEN}[1/3] Установка зависимостей...${NC}"
    pkg install -y git git-crypt python || die "Ошибка установки"

    echo -e "${GREEN}[2/3] Клонирование репозитория...${NC}"
    git clone "$REPO_URL" "$INSTALL_DIR" || die "Ошибка клонирования"
    cd "$INSTALL_DIR" || die "Не удалось перейти в папку"

    echo -e "${GREEN}[3/3] Дешифровка level.py...${NC}"
    echo "$GIT_CRYPT_KEY" > /tmp/gc-key
    git-crypt unlock /tmp/gc-key || die "Ошибка дешифровки"
    rm /tmp/gc-key
}

# Запуск
if [ -d "$INSTALL_DIR" ]; then
    cd "$INSTALL_DIR"
    git pull
    python level.py
else
    install
    cd "$INSTALL_DIR" && python level.py
fi
EOF
