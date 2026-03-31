#!/bin/bash

# ============================================
# 闲鱼自动回复系统 - 自动更新脚本
# ============================================

# 检测终端是否支持彩色输出
check_color_support() {
    if [ -t 1 ] && command -v tput &> /dev/null; then
        if [ $(tput colors) -ge 8 ]; then
            return 0
        fi
    fi
    return 1
}

# 颜色定义
if check_color_support; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    # 禁用颜色
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# 项目目录
# 优先使用环境变量，其次使用脚本所在目录
if [ -n "$PROJECT_DIR" ]; then
    # 使用环境变量
    PROJECT_DIR="$PROJECT_DIR"
elif [ -f "$(dirname "$0")/docker-compose-cn.yml" ]; then
    # 使用脚本所在目录
    PROJECT_DIR="$(dirname "$0")"
else
    # 兼容旧版本，使用默认路径
    PROJECT_DIR="/home/xianyu/xianyu-auto-bot"
fi
DOCKER_COMPOSE_FILE="docker-compose-cn.yml"

echo -e "${BLUE}项目目录: $PROJECT_DIR${NC}"

# 检查并生成 .env 文件
check_env_file() {
    ENV_FILE="$PROJECT_DIR/.env"
    
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}检测到 .env 文件不存在，正在自动生成...${NC}"
        
        # 生成随机密钥
        ENCRYPTION_KEY=$(openssl rand -hex 32)
        JWT_SECRET_KEY=$(openssl rand -hex 32)
        
        # 生成 .env 文件内容
        cat > "$ENV_FILE" << EOF
# ========== 必须配置 ==========
ENCRYPTION_KEY=$ENCRYPTION_KEY
JWT_SECRET_KEY=$JWT_SECRET_KEY

# ========== 建议修改 ==========
# SQL_LOG_ENABLED=false
TOKEN_EXPIRE_TIME=86400
# WEB_PORT=8080
MEMORY_LIMIT=2048
EOF
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✓ .env 文件生成成功${NC}"
            echo -e "${BLUE}  - ENCRYPTION_KEY: $ENCRYPTION_KEY${NC}"
            echo -e "${BLUE}  - JWT_SECRET_KEY: $JWT_SECRET_KEY${NC}"
        else
            echo -e "${RED}  ✗ .env 文件生成失败${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}  ✓ .env 文件已存在${NC}"
    fi
}


# 检测 Docker 命令
detect_docker() {
    if command -v docker &> /dev/null; then
        # 检查是否支持 docker compose (新写法)
        if docker compose version &> /dev/null; then
            DOCKER_CMD="docker compose"
        # 检查 docker-compose (旧写法)
        elif command -v docker-compose &> /dev/null; then
            DOCKER_CMD="docker-compose"
        else
            echo -e "${RED}错误：未找到可用的 Docker 命令${NC}"
            exit 1
        fi
    else
        echo -e "${RED}错误：未安装 Docker${NC}"
        exit 1
    fi
    echo -e "${BLUE}使用 Docker 命令: $DOCKER_CMD${NC}"
}

# 检测是否已有实例在运行
# 检测是否小皮环境并提示设置全局环境
setup_xp_env() {
    if [ -f "/xp/server/docker/docker" ]; then
        # 检查是否已经设置了全局环境
        if ! command -v docker &> /dev/null || ! command -v pgrep &> /dev/null; then
            echo -e "${YELLOW}检测到小皮环境${NC}"
            echo -e "${BLUE}小皮环境需要设置全局环境变量才能正常使用${NC}"
            echo ""
            read -p "是否设置小皮环境为全局环境? (Y/N): " choice
            case "$choice" in
                [Yy]|[Yy][Ee][Ss])
                    echo -e "${YELLOW}正在设置小皮环境为全局环境...${NC}"
                    
                    # 小皮环境路径
                    XP_DOCKER_DIR="/xp/server/docker"
                    XP_PATHS="$XP_DOCKER_DIR:$XP_DOCKER_DIR/compose:$XP_DOCKER_DIR/containerd"
                    
                    # 添加到当前会话
                    export PATH="$XP_PATHS:$PATH"
                    
                    # 添加到 ~/.bashrc
                    if [ -f "$HOME/.bashrc" ]; then
                        # 检查是否已存在
                        if ! grep -q "$XP_DOCKER_DIR" "$HOME/.bashrc" 2>/dev/null; then
                            echo "" >> "$HOME/.bashrc"
                            echo "# 小皮环境 Docker 配置" >> "$HOME/.bashrc"
                            echo "export PATH=\"$XP_PATHS:\$PATH\"" >> "$HOME/.bashrc"
                            echo -e "${GREEN}  ✓ 已添加到 ~/.bashrc${NC}"
                        else
                            echo -e "${GREEN}  ✓ ~/.bashrc 中已存在配置${NC}"
                        fi
                    fi
                    
                    # 添加到 ~/.profile
                    if [ -f "$HOME/.profile" ]; then
                        if ! grep -q "$XP_DOCKER_DIR" "$HOME/.profile" 2>/dev/null; then
                            echo "" >> "$HOME/.profile"
                            echo "# 小皮环境 Docker 配置" >> "$HOME/.profile"
                            echo "export PATH=\"$XP_PATHS:\$PATH\"" >> "$HOME/.profile"
                            echo -e "${GREEN}  ✓ 已添加到 ~/.profile${NC}"
                        fi
                    fi
                    
                    echo -e "${GREEN}  ✓ 小皮环境已设置为全局环境${NC}"
                    echo -e "${GREEN}  ✓ 当前会话已实时生效${NC}"
                    echo ""
                    ;;
                *)
                    echo -e "${YELLOW}跳过设置，使用小皮环境本地命令${NC}"
                    echo ""
                    ;;
            esac
        fi
    fi
}

check_running() {
    SCRIPT_NAME=$(basename "$0")
    
    # 检测小皮环境，设置对应的命令路径
    if [ -f "/xp/server/docker/docker" ]; then
        # 小皮环境
        PGREP_CMD="/xp/server/docker/pgrep"
        KILL_CMD="/xp/server/docker/kill"
        # 如果小皮环境没有 pgrep，使用系统默认
        if [ ! -f "$PGREP_CMD" ]; then
            PGREP_CMD="pgrep"
            KILL_CMD="kill"
        fi
    else
        # 普通 Linux 环境
        PGREP_CMD="pgrep"
        KILL_CMD="kill"
    fi
    
    # 获取其他运行中的脚本进程（排除当前进程）
    # 匹配包含脚本名称的 bash 进程
    OTHER_PIDS=$($PGREP_CMD -f "bash.*$SCRIPT_NAME" 2>/dev/null | grep -v $$ | grep -v "grep" || true)
    # 如果没有匹配到，尝试直接匹配脚本名称
    if [ -z "$OTHER_PIDS" ]; then
        OTHER_PIDS=$($PGREP_CMD -f "$SCRIPT_NAME" 2>/dev/null | grep -v $$ | grep -v "grep" || true)
    fi
    
    if [ -n "$OTHER_PIDS" ]; then
        echo -e "${YELLOW}检测到另一个更新脚本正在运行中${NC}"
        echo -e "${BLUE}运行中的进程 ID: $OTHER_PIDS${NC}"
        echo ""
        read -p "是否停止正在运行的实例? (Y/N): " choice
        case "$choice" in
            [Yy]|[Yy][Ee][Ss])
                echo -e "${YELLOW}正在停止运行中的实例...${NC}"
                echo "$OTHER_PIDS" | xargs -r $KILL_CMD -TERM 2>/dev/null || true
                sleep 2
                # 再次检查是否还在运行
                STILL_RUNNING=$($PGREP_CMD -f "bash.*$SCRIPT_NAME" 2>/dev/null | grep -v $$ | grep -v "grep" || true)
                if [ -z "$STILL_RUNNING" ]; then
                    STILL_RUNNING=$($PGREP_CMD -f "$SCRIPT_NAME" 2>/dev/null | grep -v $$ | grep -v "grep" || true)
                fi
                if [ -n "$STILL_RUNNING" ]; then
                    echo -e "${YELLOW}强制终止...${NC}"
                    echo "$OTHER_PIDS" | xargs -r $KILL_CMD -KILL 2>/dev/null || true
                    sleep 1
                fi
                echo -e "${GREEN}  ✓ 已停止运行中的实例${NC}"
                echo ""
                ;;
            *)
                echo -e "${YELLOW}取消操作，退出脚本${NC}"
                exit 0
                ;;
        esac
    fi
}

# 显示菜单并让用户选择
show_menu() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}   闲鱼自动回复系统 - 自动更新脚本${NC}"
    echo -e "${BLUE}===========================================${NC}"
    echo ""
    echo "请选择要执行的操作:"
    echo ""
    echo "  1) 常规更新           - 拉取代码并重建容器"
    echo "  2) 强制更新           - 丢弃本地修改，强制更新"
    echo "  3) 备份并更新         - 先备份数据，再更新"
    echo "  4) 仅拉取代码         - 不重建容器"
    echo "  5) 查看帮助           - 显示命令行参数说明"
    echo "  0) 退出               - 取消操作"
    echo ""
    read -p "请输入数字 [0-5]: " choice
    echo ""
    
    case "$choice" in
        1)
            return 0
            ;;
        2)
            FORCE_UPDATE=true
            return 0
            ;;
        3)
            BACKUP_BEFORE_UPDATE=true
            return 0
            ;;
        4)
            NO_BUILD=true
            return 0
            ;;
        5)
            show_help_details
            exit 0
            ;;
        0)
            echo -e "${YELLOW}已取消操作${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效的选择，请重新运行脚本${NC}"
            exit 1
            ;;
    esac
}

# 显示详细帮助信息
show_help_details() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}   闲鱼自动回复系统 - 命令行参数说明${NC}"
    echo -e "${BLUE}===========================================${NC}"
    echo ""
    echo "用法: ./update.sh [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help       显示此帮助信息"
    echo "  -f, --force      强制更新（丢弃本地修改）"
    echo "  -b, --backup     更新前备份数据"
    echo "  --no-build       拉取代码但不重建容器"
    echo ""
    echo "示例:"
    echo "  ./update.sh              # 常规更新"
    echo "  ./update.sh -f           # 强制更新（丢弃本地修改）"
    echo "  ./update.sh -b           # 更新前备份数据"
    echo ""
}

# 显示帮助信息（兼容旧版本）
show_help() {
    show_help_details
}

# 备份数据
backup_data() {
    echo -e "${YELLOW}[1/5] 正在备份数据...${NC}"
    BACKUP_DIR="$PROJECT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
    
    # 创建备份目录并检查权限
    if mkdir -p "$BACKUP_DIR" 2>/dev/null; then
        echo -e "${GREEN}  ✓ 备份目录创建成功: $BACKUP_DIR${NC}"
    else
        echo -e "${RED}  ✗ 备份目录创建失败，可能权限不足${NC}"
        echo -e "${YELLOW}提示：请检查 $PROJECT_DIR/backups 目录权限${NC}"
        return 1
    fi

    # 备份数据库文件
    if [ -d "$PROJECT_DIR/data" ]; then
        if cp -r "$PROJECT_DIR/data" "$BACKUP_DIR/" 2>/dev/null; then
            echo -e "${GREEN}  ✓ 数据目录已备份${NC}"
        else
            echo -e "${YELLOW}  ⚠ 数据目录备份失败，可能权限不足${NC}"
        fi
    fi

    # 备份配置文件
    if [ -f "$PROJECT_DIR/.env" ]; then
        if cp "$PROJECT_DIR/.env" "$BACKUP_DIR/" 2>/dev/null; then
            echo -e "${GREEN}  ✓ 环境配置文件已备份${NC}"
        else
            echo -e "${YELLOW}  ⚠ 环境配置文件备份失败，可能权限不足${NC}"
        fi
    fi

    # 备份 docker-compose 文件
    if [ -f "$PROJECT_DIR/$DOCKER_COMPOSE_FILE" ]; then
        if cp "$PROJECT_DIR/$DOCKER_COMPOSE_FILE" "$BACKUP_DIR/" 2>/dev/null; then
            echo -e "${GREEN}  ✓ Docker Compose 文件已备份${NC}"
        else
            echo -e "${YELLOW}  ⚠ Docker Compose 文件备份失败，可能权限不足${NC}"
        fi
    fi
}

# 拉取最新代码
pull_code() {
    echo -e "${YELLOW}[2/5] 正在拉取最新代码...${NC}"
    cd "$PROJECT_DIR" || exit 1

    # 检查是否有本地修改
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}检测到本地有修改的文件${NC}"
        if [ "$FORCE_UPDATE" = true ]; then
            echo -e "${YELLOW}强制更新模式：正在丢弃本地修改...${NC}"
            git stash
            git reset --hard HEAD
        else
            echo -e "${YELLOW}正在尝试自动合并...${NC}"
        fi
    fi

    # 拉取代码
    git fetch origin
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})

    if [ "$LOCAL" = "$REMOTE" ]; then
        echo -e "${GREEN}  ✓ 当前已经是最新版本，无需更新${NC}"
        if [ "$NO_BUILD" = true ]; then
            exit 0
        fi
    else
        echo -e "${BLUE}  → 正在拉取最新代码...${NC}"
        git pull origin main
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✓ 代码更新成功${NC}"
        else
            echo -e "${RED}  ✗ 代码更新失败${NC}"
            echo -e "${YELLOW}提示：可以使用 -f 参数强制更新，或手动解决冲突${NC}"
            exit 1
        fi
    fi
}

# 重建并启动容器
rebuild_container() {
    echo -e "${YELLOW}[3/5] 正在重建 Docker 容器...${NC}"
    cd "$PROJECT_DIR" || exit 1

    # 停止现有容器
    echo -e "${BLUE}  → 停止现有容器...${NC}"
    $DOCKER_CMD -f "$DOCKER_COMPOSE_FILE" down

    # 拉取最新镜像
    echo -e "${BLUE}  → 拉取最新镜像...${NC}"
    $DOCKER_CMD -f "$DOCKER_COMPOSE_FILE" pull

    # 重建并启动
    echo -e "${BLUE}  → 重建并启动容器...${NC}"
    $DOCKER_CMD -f "$DOCKER_COMPOSE_FILE" up -d --build

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓ 容器重建成功${NC}"
    else
        echo -e "${RED}  ✗ 容器重建失败${NC}"
        exit 1
    fi
}

# 检查服务状态
check_status() {
    echo -e "${YELLOW}[4/5] 正在检查服务状态...${NC}"
    cd "$PROJECT_DIR" || exit 1

    sleep 3

    # 检查容器状态
    CONTAINER_STATUS=$($DOCKER_CMD -f "$DOCKER_COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}")
    echo -e "${BLUE}容器状态:${NC}"
    echo "$CONTAINER_STATUS"

    # 检查是否有容器在运行
    RUNNING_COUNT=$($DOCKER_CMD -f "$DOCKER_COMPOSE_FILE" ps -q | wc -l)
    if [ "$RUNNING_COUNT" -gt 0 ]; then
        echo -e "${GREEN}  ✓ 服务运行正常${NC}"
    else
        echo -e "${RED}  ✗ 服务未正常运行，请检查日志${NC}"
        echo -e "${YELLOW}查看日志命令: $DOCKER_CMD -f $DOCKER_COMPOSE_FILE logs${NC}"
    fi
}

# 清理旧备份
cleanup_old_backups() {
    echo -e "${YELLOW}[5/5] 清理旧备份...${NC}"
    BACKUP_DIR="$PROJECT_DIR/backups"

    if [ -d "$BACKUP_DIR" ]; then
        # 保留最近 10 个备份，使用更安全的方式
        cd "$BACKUP_DIR" || return
        
        # 计算总备份数
        TOTAL_COUNT=$(find . -type d -name "[0-9]*" | wc -l)
        if [ "$TOTAL_COUNT" -gt 10 ]; then
            # 使用 find 命令查找并删除旧备份
            find . -type d -name "[0-9]*" -printf "%T@ %p\n" | sort -n | head -n $((TOTAL_COUNT - 10)) | cut -d' ' -f2- | xargs -r rm -rf 2>/dev/null
        fi
        
        BACKUP_COUNT=$(find . -type d -name "[0-9]*" | wc -l)
        echo -e "${GREEN}  ✓ 已清理旧备份，当前保留 $BACKUP_COUNT 个备份${NC}"
    fi
}

# 主函数
main() {
    # 默认参数
    FORCE_UPDATE=false
    BACKUP_BEFORE_UPDATE=false
    NO_BUILD=false

    # 解析参数
    PARAM_COUNT=$#
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -f|--force)
                FORCE_UPDATE=true
                shift
                ;;
            -b|--backup)
                BACKUP_BEFORE_UPDATE=true
                shift
                ;;
            --no-build)
                NO_BUILD=true
                shift
                ;;
            *)
                echo -e "${RED}未知选项: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done

    # 如果没有参数，显示交互式菜单
    if [ "$PARAM_COUNT" -eq 0 ]; then
        show_menu
    fi

    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}   闲鱼自动回复系统 - 自动更新脚本${NC}"
    echo -e "${BLUE}===========================================${NC}"
    echo ""

    # 检测小皮环境并提示设置全局环境
    setup_xp_env

    # 检测是否已有实例在运行
    check_running

    # 检测 Docker 命令
    detect_docker

    # 检查项目目录
    if [ ! -d "$PROJECT_DIR" ]; then
        echo -e "${RED}错误：项目目录不存在: $PROJECT_DIR${NC}"
        exit 1
    fi

    # 检查并生成 .env 文件
    check_env_file

    # 执行更新流程
    if [ "$BACKUP_BEFORE_UPDATE" = true ]; then
        backup_data
    fi

    pull_code

    if [ "$NO_BUILD" = false ]; then
        rebuild_container
        check_status
        if [ "$BACKUP_BEFORE_UPDATE" = true ]; then
            cleanup_old_backups
        fi
    fi

    echo ""
    echo -e "${GREEN}===========================================${NC}"
    echo -e "${GREEN}   更新流程执行完毕！${NC}"
    echo -e "${GREEN}===========================================${NC}"
}

# 执行主函数
main "$@"
