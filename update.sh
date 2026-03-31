#!/bin/bash

# ============================================
# 闲鱼自动回复系统 - 自动更新脚本
# ============================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目目录
PROJECT_DIR="/home/xianyu/xianyu-auto-bot"
DOCKER_COMPOSE_FILE="docker-compose-cn.yml"

# 检测 Docker 命令
 detect_docker() {
    if command -v docker &> /dev/null; then
        # 检查是否支持 docker compose (新写法)
        if docker compose version &> /dev/null; then
            DOCKER_CMD="docker compose"
        # 检查 docker-compose (旧写法)
        elif command -v docker-compose &> /dev/null; then
            DOCKER_CMD="docker-compose"
        # 检查小皮环境的 Docker
        elif [ -f "/xp/server/docker/docker" ]; then
            if /xp/server/docker/docker compose version &> /dev/null; then
                DOCKER_CMD="/xp/server/docker/docker compose"
            else
                DOCKER_CMD="/xp/server/docker/docker-compose"
            fi
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

# 显示帮助信息
show_help() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}   闲鱼自动回复系统 - 自动更新脚本${NC}"
    echo -e "${BLUE}===========================================${NC}"
    echo ""
    echo "用法: ./update.sh [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help       显示帮助信息"
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

# 备份数据
backup_data() {
    echo -e "${YELLOW}[1/5] 正在备份数据...${NC}"
    BACKUP_DIR="$PROJECT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # 备份数据库文件
    if [ -d "$PROJECT_DIR/data" ]; then
        cp -r "$PROJECT_DIR/data" "$BACKUP_DIR/" 2>/dev/null
        echo -e "${GREEN}  ✓ 数据目录已备份到: $BACKUP_DIR${NC}"
    fi

    # 备份配置文件
    if [ -f "$PROJECT_DIR/.env" ]; then
        cp "$PROJECT_DIR/.env" "$BACKUP_DIR/" 2>/dev/null
        echo -e "${GREEN}  ✓ 环境配置文件已备份${NC}"
    fi

    # 备份 docker-compose 文件
    if [ -f "$PROJECT_DIR/$DOCKER_COMPOSE_FILE" ]; then
        cp "$PROJECT_DIR/$DOCKER_COMPOSE_FILE" "$BACKUP_DIR/" 2>/dev/null
        echo -e "${GREEN}  ✓ Docker Compose 文件已备份${NC}"
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
        git pull origin main
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✓ 代码更新成功${NC}"
        else
            echo -e "${RED}  ✗ 代码更新失败${NC}"
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
        # 保留最近 10 个备份
        cd "$BACKUP_DIR" || return
        ls -t | tail -n +11 | xargs -r rm -rf
        BACKUP_COUNT=$(ls -1 | wc -l)
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

    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}   闲鱼自动回复系统 - 自动更新脚本${NC}"
    echo -e "${BLUE}===========================================${NC}"
    echo ""

    # 检测 Docker 命令
    detect_docker

    # 检查项目目录
    if [ ! -d "$PROJECT_DIR" ]; then
        echo -e "${RED}错误：项目目录不存在: $PROJECT_DIR${NC}"
        exit 1
    fi

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
