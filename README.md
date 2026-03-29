# 🐟 闲鱼自动回复系统
基于 [zhinianboke/xianyu-auto-reply](https://github.com/zhinianboke/xianyu-auto-reply) 二次开发 · 全新 UI · 持续更新
## 📋 项目概述

一个功能完整的闲鱼自动回复和管理系统，采用现代化的技术架构，支持多用户、多账号管理，具备智能回复、自动发货、自动确认发货、商品管理等企业级功能。系统基于Python异步编程，使用FastAPI提供RESTful API，SQLite数据库存储，支持Docker一键部署。

> **⚠️ 重要提示：本项目仅供学习研究使用，严禁商业用途！使用前请仔细阅读[版权声明](#️-版权声明与使用条款)。**

## 🏗️ 技术架构

### 核心技术栈

- **后端框架**: FastAPI + Python 3.11+ 异步编程
- **数据库**: SQLite 3 + 多用户数据隔离 + 自动迁移
- **前端**: React 18 + TypeScript + Vite + Tailwind CSS + 响应式设计
- **通信协议**: WebSocket + RESTful API + 实时通信
- **部署方式**: Docker + Docker Compose + 一键部署
- **日志系统**: Loguru + 文件轮转 + 实时收集
- **安全认证**: JWT + 图形验证码 + 邮箱验证 + 权限控制

### 系统架构特点

- **微服务设计**: 模块化架构，易于维护和扩展
- **异步处理**: 基于asyncio的高性能异步处理
- **多用户隔离**: 完全的数据隔离和权限控制
- **容器化部署**: Docker容器化，支持一键部署
- **实时监控**: WebSocket实时通信和状态监控
- **自动化运维**: 自动重连、异常恢复、日志轮转

## ✨ 核心特性

### 🔐 多用户系统

- **用户注册登录** - 支持邮箱验证码注册，图形验证码保护
- **数据完全隔离** - 每个用户的数据独立存储，互不干扰
- **权限管理** - 严格的用户权限控制和JWT认证
- **安全保护** - 防暴力破解、会话管理、安全日志
- **授权期限管理** - 核心滑块验证模块包含授权期限验证，确保合规使用

### 📱 多账号管理

- **无限账号支持** - 每个用户可管理多个闲鱼账号
- **独立运行** - 每个账号独立监控，互不影响
- **实时状态** - 账号连接状态实时监控
- **批量操作** - 支持批量启动、停止账号任务

### 🤖 智能回复系统

- **关键词匹配** - 支持精确关键词匹配回复
- **指定商品回复** - 支持为特定商品设置专门的回复内容，优先级最高
- **商品专用关键词** - 支持为特定商品设置专用关键词回复
- **通用关键词** - 支持全局通用关键词，适用于所有商品
- **批量导入导出** - 支持Excel格式的关键词批量导入导出
- **AI智能回复** - 集成OpenAI API，支持上下文理解
- **变量替换** - 回复内容支持动态变量（用户名、商品信息、商品ID等）
- **优先级策略** - 指定商品回复 > 商品专用关键词 > 通用关键词 > 默认回复 > AI回复

### 🚚 自动发货功能

- **智能匹配** - 基于商品信息自动匹配发货规则
- **多规格支持** - 支持同一商品的不同规格自动匹配对应卡券
- **精确匹配+兜底机制** - 优先精确匹配规格，失败时自动降级到普通卡券
- **延时发货** - 支持设置发货延时时间（0-3600秒）
- **多种触发** - 支持付款消息、小刀消息等多种触发条件
- **防重复发货** - 智能防重复机制，避免重复发货
- **多种发货方式** - 支持固定文字、批量数据、API调用、图片发货等方式
- **图片发货** - 支持上传图片并自动发送给买家，图片自动上传到CDN
- **自动确认发货** - 检测到付款后自动调用闲鱼API确认发货，支持锁机制防并发
- **防重复确认** - 智能防重复确认机制，避免重复API调用
- **订单详情缓存** - 订单详情获取支持数据库缓存，大幅提升性能
- **发货统计** - 完整的发货记录和统计功能

### 🛍️ 商品管理

- **自动收集** - 消息触发时自动收集商品信息
- **API获取** - 通过闲鱼API获取完整商品详情
- **多规格支持** - 支持多规格商品的规格信息管理
- **批量管理** - 支持批量查看、编辑、切换多规格状态
- **智能去重** - 自动去重，避免重复存储

### 🔍 商品搜索功能

- **真实数据获取** - 基于Playwright技术获取真实闲鱼商品数据
- **智能排序** - 按"人想要"数量自动倒序排列
- **多页搜索** - 支持一次性获取多页商品数据
- **前端分页** - 灵活的前端分页显示
- **商品详情** - 支持查看完整商品详情信息

### 📊 系统监控

- **实时日志** - 完整的操作日志记录和查看
- **性能监控** - 系统资源使用情况监控
- **健康检查** - 服务状态健康检查

### 📁 数据管理

- **Excel导入导出** - 支持关键词数据的Excel格式导入导出
- **模板生成** - 自动生成包含示例数据的导入模板
- **批量操作** - 支持批量添加、更新关键词数据
- **数据验证** - 导入时自动验证数据格式和重复性
- **多规格卡券管理** - 支持创建和管理多规格卡券
- **发货规则管理** - 支持多规格发货规则的创建和管理
- **数据备份** - 自动数据备份和恢复
- **一键部署** - 提供预构建Docker镜像，无需编译即可快速部署

## 📁 项目结构

<details>
<summary>点击展开查看详细项目结构</summary>

```
xianyu-auto-reply/
├── 📄 核心文件
│   ├── Start.py                    # 项目启动入口，初始化所有服务
│   ├── XianyuAutoAsync.py         # 闲鱼WebSocket连接和消息处理核心
│   ├── reply_server.py            # FastAPI Web服务器和完整API接口
│   ├── db_manager.py              # SQLite数据库管理，支持多用户数据隔离
│   ├── cookie_manager.py          # 多账号Cookie管理和任务调度
│   ├── ai_reply_engine.py         # AI智能回复引擎，支持多种AI模型
│   ├── order_status_handler.py    # 订单状态处理和更新模块
│   ├── file_log_collector.py      # 实时日志收集和管理系统
│   ├── config.py                  # 全局配置文件管理器
│   ├── usage_statistics.py        # 用户统计和数据分析模块
│   ├── simple_stats_server.py     # 简单统计服务器（可选）
│   ├── secure_confirm_ultra.py    # 自动确认发货模块（多层加密保护）
│   ├── secure_confirm_decrypted.py # 自动确认发货模块（解密版本）
│   ├── secure_freeshipping_ultra.py # 自动免拼发货模块（多层加密保护）
│   └── secure_freeshipping_decrypted.py # 自动免拼发货模块（解密版本）
├── 🛠️ 工具模块
│   └── utils/
│       ├── xianyu_utils.py        # 闲鱼API工具函数（加密、签名、解析）
│       ├── message_utils.py       # 消息格式化和处理工具
│       ├── ws_utils.py            # WebSocket客户端封装
│       ├── image_utils.py         # 图片处理和管理工具
│       ├── image_uploader.py      # 图片上传到闲鱼CDN
│       ├── image_utils.py         # 图片处理工具（压缩、格式转换）
│       ├── item_search.py         # 商品搜索功能（基于Playwright，无头模式）
│       ├── order_detail_fetcher.py # 订单详情获取工具
│       └── qr_login.py            # 二维码登录功能
├── 🌐 前端界面
│   ├── frontend/                  # React + TypeScript + Vite 前端项目
│   │   ├── public/                # 静态资源
│   │   │   ├── static/            # 图片等静态文件
│   │   │   └── favicon.svg        # 网站图标
│   │   ├── src/                   # 源代码
│   │   │   ├── api/               # API调用接口
│   │   │   ├── components/        # 通用组件
│   │   │   ├── pages/             # 页面组件
│   │   │   ├── store/             # 状态管理
│   │   │   ├── styles/            # 样式文件
│   │   │   ├── types/             # TypeScript类型定义
│   │   │   ├── utils/             # 工具函数
│   │   │   ├── App.tsx            # 应用主组件
│   │   │   └── main.tsx           # 应用入口
│   │   ├── package.json           # 前端依赖配置
│   │   ├── tailwind.config.js     # Tailwind CSS配置
│   │   └── vite.config.ts         # Vite配置
│   └── static/                    # 前端构建输出目录
│       ├── assets/                # 构建后的静态资源
│       ├── static/                # 静态文件
│       ├── favicon.svg            # 网站图标
│       └── index.html             # 构建后的主页面
├── 🐳 Docker部署
│   ├── Dockerfile                 # Docker镜像构建文件（优化版）
│   ├── Dockerfile-cn             # 国内优化版Docker镜像构建文件
│   ├── docker-compose.yml        # Docker Compose一键部署配置
│   ├── docker-compose-cn.yml     # 国内优化版Docker Compose配置
│   ├── docker-deploy.sh          # Docker部署管理脚本（Linux/macOS）
│   ├── docker-deploy.bat         # Docker部署管理脚本（Windows）
│   ├── entrypoint.sh              # Docker容器启动脚本
│   └── .dockerignore             # Docker构建忽略文件
├── 🌐 Nginx配置
│   └── nginx/
│       ├── nginx.conf            # Nginx反向代理配置
│       └── ssl/                  # SSL证书目录
├── 📋 配置文件
│   ├── global_config.yml         # 全局配置文件（WebSocket、API等）
│   ├── requirements.txt          # Python依赖包列表（精简版，无内置模块）
│   ├── .gitignore                # Git忽略文件配置（完整版）
│   └── README.md                 # 项目说明文档（本文件）
└── 📊 数据目录（运行时创建）
    ├── data/                     # 数据目录（Docker挂载，自动创建）
    │   ├── xianyu_data.db        # SQLite主数据库文件
    │   ├── user_stats.db         # 用户统计数据库
    │   └── xianyu_data_backup_*.db # 数据库备份文件
    ├── logs/                     # 按日期分割的日志文件
    └── backups/                  # 其他备份文件
```

</details>

## 🆕 最新更新

### 2026年3月30日更新

**🐛 Bug修复**

- ✅ 修复Token刷新重试机制：实现6次失败后自动停止所有任务，防止账号被封
- ✅ 修复SQLite时间格式解析：解决负数等待时间问题
- ✅ 修复邮件通知渠道测试功能：兼容recipient_email和email字段，支持渠道独立SMTP配置
- ✅ 修复系统设置邮件测试接口：添加await关键字调用异步函数
- ✅ 修复CSRF中间件：对带Authorization header的API请求跳过检查
- ✅ 修复SMTP连接意外关闭：根据端口自动判断SSL（465）/STARTTLS（587）
- ✅ 修复验证码冷却期：添加发送邮件验证码后60秒冷却期检查
- ✅ 修复极验验证422错误：修复字段名validate_code → validate
- ✅ 修复登录接口500错误：添加完整的try-except错误处理
- ✅ 修复GeetestValidateRequest字段名警告：使用Field(alias="validate")避免与BaseModel冲突
- ✅ 修复数据管理页面表头显示英文：添加完整的中文列名映射
- ✅ 修复刷新Token状态显示：添加token_status、token_message、last_token_refresh字段
- ✅ 修复cookie_manager未保存live实例引用：添加live_instances字典和get_live_instance方法

**✨ 新增功能**

- ✅ 添加邮件通知渠道测试接口：支持独立SMTP配置测试
- ✅ 添加系统设置邮件测试接口
- ✅ 添加商品擦亮功能API接口：在售商品列表、一键擦亮、定时擦亮、取消定时擦亮、擦亮历史
- ✅ 添加通知渠道测试接口
- ✅ 完善AI滑块自主学习功能：自动记录、轨迹分析、参数优化、策略推荐
- ✅ 完善扫码登录获取最新token功能
- ✅ 完善自动登录获取最新token功能

**📊 功能优化**

- ✅ 优化Token状态显示：实时获取live实例的Token状态
- ✅ 优化数据管理：添加完整的中文列名映射
- ✅ 优化cookie_manager：添加live实例保存和获取功能

### 2026年3月更新

**🌟 前端全新升级**

- ✅ 重构前端为 React 18 + TypeScript + Vite + Tailwind CSS
- ✅ 全新现代化 UI 设计，响应式布局支持多设备
- ✅ 优化前端性能，提升加载速度和用户体验
- ✅ 完善的 TypeScript 类型定义，提高代码可维护性
- ✅ 集成 Zustand 状态管理，简化状态管理逻辑
- ✅ 使用 React Query 优化 API 调用和缓存策略

**🔧 后端功能增强**

- ✅ 优化数据库查询性能，减少响应时间
- ✅ 增强错误处理和日志记录，提高系统稳定性
- ✅ 完善的 API 文档，便于前端集成和调试
- ✅ 优化 WebSocket 连接管理，减少资源消耗

**🛠️ 部署与配置优化**

- ✅ 简化 Docker 部署流程，支持一键启动
- ✅ 优化环境变量配置，提高安全性
- ✅ 完善的部署文档和故障排查指南

### 2025年1月更新

**🔥 性能与安全增强**

- ✅ 新增 Nuitka 二进制编译支持，核心模块可编译为 .pyd/.so 提升性能和安全性
- ✅ 滑块验证模块增加授权期限验证机制，确保合规使用
- ✅ Docker 构建优化，自动编译二进制模块，提升容器启动效率
- ✅ 完善的错误处理和重试机制，提升系统稳定性
- ✅ 修复滑块验证模块内存泄漏问题，浏览器资源正确释放

**📦 数据管理优化**

- ✅ 数据库文件统一迁移到 `data/` 目录，更好的组织和管理
- ✅ 启动时自动检测并迁移旧数据库文件，无需手动操作
- ✅ 备份文件自动整理到数据目录，便于集中管理
- ✅ Docker挂载更简洁，一个data目录包含所有数据

**🛠️ 配置文件优化**

- ✅ 完善 `.gitignore`，新增编译产物、浏览器缓存等规则
- ✅ 完善 `.dockerignore`，优化Docker构建速度和镜像体积
- ✅ 增强 `entrypoint.sh`，添加环境验证和详细启动日志
- ✅ 清理测试文件和临时文件，保持代码库整洁

**📦 依赖管理**

- ✅ `requirements.txt` 优化，移除Python内置模块，按功能分类
- ✅ 添加 Nuitka 编译工具链（可选）
- ✅ 详细的依赖说明和安装指南

**🐛 Bug修复**

- ✅ 修复浏览器资源泄漏问题，Docker容器RAM使用稳定
- ✅ 优化历史记录存储，减少90%磁盘和内存占用
- ✅ 添加析构函数确保资源释放

**🏗️ 多架构支持**

- ✅ Docker镜像支持AMD64和ARM64双架构
- ✅ GitHub Actions自动构建并推送到双镜像仓库
- ✅ 支持Oracle Cloud、AWS Graviton等ARM服务器
- ✅ Docker自动选择匹配的架构，无需手动指定
- ✅ 国内外双镜像源，确保下载速度

## 🚀 使用方法

### 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/ww125cn/xianyu-auto-bot.git
cd xianyu-auto-bot

# 2. 安装依赖
pip install -r requirements.txt
#python -m playwright install chromium 

# 3. 构建前端
cd frontend
npm install
npm run build

# 4 配置环境
生成 64 位随机 hex 字符串作为加密密钥
python -c "import secrets; print(secrets.token_hex(32))"

$env:SQL_LOG_ENABLED = "false"
$env:ENCRYPTION_KEY = "36737d97d7d6611500703a6ba634ca476a9d52a00fdbd94071aa5d974e4c9e5e"
# 5. 启动服务（返回项目根目录）
cd ..

python Start.py

# 5. 访问应用
# 浏览器打开 http://localhost:8080
```

### 🔐 默认登录信息

```
用户名: admin
密码: admin123
```

⚠️ **安全提示：首次登录后请立即修改默认密码！**

**说明：**

- `npm run build` 会将前端打包到 `static/` 目录
- `Start.py` 启动后端服务（端口 8080），同时提供前端静态文件
- 前端已构建，无需单独运行前端开发服务器

### 前端开发模式

如需修改前端代码（支持热更新）：

```bash
# 终端1：启动后端
$env:SQL_LOG_ENABLED = "false"
$env:ENCRYPTION_KEY = "36737d97d7d6611500703a6ba634ca476a9d52a00fdbd94071aa5d974e4c9e5e"
python Start.py

# 终端2：启动前端开发服务器
cd frontend
npm run dev

# 访问 http://localhost:3000
```
