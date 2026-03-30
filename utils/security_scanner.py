#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全扫描工具
定期检查系统的安全状态，包括敏感信息、依赖项漏洞等
"""

import os
import sys
import time
import json
import subprocess
import re
from datetime import datetime
from loguru import logger

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from db_manager import db_manager

class SecurityScanner:
    """安全扫描器"""
    
    def __init__(self):
        self.scan_interval = 3600  # 默认每小时扫描一次
        self.scan_history = []
    
    def start_scan(self):
        """开始安全扫描"""
        logger.info("🔒 开始安全扫描...")
        
        scan_results = {
            "timestamp": datetime.now().isoformat(),
            "scan_type": "full",
            "results": {
                "system_settings": self.scan_system_settings(),
                "database": self.scan_database(),
                "dependencies": self.scan_dependencies(),
                "file_permissions": self.scan_file_permissions(),
                "configuration": self.scan_configuration()
            }
        }
        
        self.scan_history.append(scan_results)
        
        # 记录安全扫描结果
        self.log_scan_results(scan_results)
        
        logger.info("🔒 安全扫描完成")
        return scan_results
    
    def scan_system_settings(self):
        """扫描系统设置中的敏感信息"""
        logger.info("🔍 扫描系统设置...")
        issues = []
        
        # 检查SMTP配置
        smtp_password = db_manager.get_system_setting('smtp_password')
        if smtp_password and len(smtp_password) > 0:
            issues.append({
                "type": "sensitive_info",
                "severity": "high",
                "description": "SMTP密码存储在系统设置中",
                "recommendation": "使用环境变量存储敏感信息"
            })
        
        # 检查QQ回复密钥
        qq_secret_key = db_manager.get_system_setting('qq_reply_secret_key')
        if qq_secret_key and len(qq_secret_key) > 0:
            issues.append({
                "type": "sensitive_info",
                "severity": "medium",
                "description": "QQ回复密钥存储在系统设置中",
                "recommendation": "使用环境变量存储敏感信息"
            })
        
        return {
            "status": "completed",
            "issues": issues
        }
    
    def scan_database(self):
        """扫描数据库中的安全问题"""
        logger.info("🔍 扫描数据库...")
        issues = []
        
        try:
            # 检查是否存在默认密码的admin用户
            with db_manager.lock:
                cursor = db_manager.conn.cursor()
                cursor.execute('SELECT username, password_hash FROM users WHERE username = ?', ('admin',))
                admin_user = cursor.fetchone()
                
                if admin_user:
                    # 检查是否使用默认密码
                    from passlib.context import CryptContext
                    pwd_context = CryptContext(schemes=['sha256_crypt'], deprecated='auto')
                    if pwd_context.verify('admin123', admin_user[1]):
                        issues.append({
                            "type": "default_password",
                            "severity": "critical",
                            "description": "管理员用户使用默认密码",
                            "recommendation": "立即修改管理员密码"
                        })
        except Exception as e:
            logger.error(f"数据库扫描失败: {e}")
        
        return {
            "status": "completed",
            "issues": issues
        }
    
    def scan_dependencies(self):
        """扫描依赖项的安全漏洞"""
        logger.info("🔍 扫描依赖项...")
        issues = []
        
        # 检查Python依赖项
        try:
            result = subprocess.run(
                ['pip', 'list', '--outdated'],
                capture_output=True,
                text=True
            )
            outdated_packages = result.stdout.strip().split('\n')[2:]  # 跳过标题行
            
            if outdated_packages:
                issues.append({
                    "type": "outdated_dependencies",
                    "severity": "medium",
                    "description": f"发现 {len(outdated_packages)} 个过时的依赖项",
                    "recommendation": "运行 pip install --upgrade 来更新依赖项"
                })
        except Exception as e:
            logger.error(f"依赖项扫描失败: {e}")
        
        return {
            "status": "completed",
            "issues": issues
        }
    
    def scan_file_permissions(self):
        """扫描文件权限设置"""
        logger.info("🔍 扫描文件权限...")
        issues = []
        
        # 检查数据目录权限
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        if os.path.exists(data_dir):
            stat_info = os.stat(data_dir)
            # 检查是否为 755 权限
            if oct(stat_info.st_mode)[-3:] != '755':
                issues.append({
                    "type": "file_permission",
                    "severity": "medium",
                    "description": f"数据目录权限不正确: {oct(stat_info.st_mode)[-3:]}",
                    "recommendation": "设置数据目录权限为 755"
                })
        
        # 检查配置文件权限
        config_files = [
            'global_config.yml',
            '.env'
        ]
        
        for config_file in config_files:
            config_path = os.path.join(os.path.dirname(__file__), '..', config_file)
            if os.path.exists(config_path):
                stat_info = os.stat(config_path)
                # 检查是否为 600 权限
                if oct(stat_info.st_mode)[-3:] != '600':
                    issues.append({
                        "type": "file_permission",
                        "severity": "medium",
                        "description": f"配置文件权限不正确: {config_file} - {oct(stat_info.st_mode)[-3:]}",
                        "recommendation": "设置配置文件权限为 600"
                    })
        
        return {
            "status": "completed",
            "issues": issues
        }
    
    def scan_configuration(self):
        """扫描配置文件中的安全问题"""
        logger.info("🔍 扫描配置...")
        issues = []
        
        # 检查加密密钥
        encryption_key = os.environ.get('ENCRYPTION_KEY')
        if not encryption_key:
            issues.append({
                "type": "encryption_key",
                "severity": "high",
                "description": "未设置加密密钥环境变量",
                "recommendation": "设置 ENCRYPTION_KEY 环境变量"
            })
        
        # 检查全局配置文件
        config_path = os.path.join(os.path.dirname(__file__), '..', 'global_config.yml')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
                # 检查是否包含硬编码的敏感信息
                if re.search(r'api_key\s*:\s*[^\s]+', config_content):
                    issues.append({
                        "type": "hardcoded_credentials",
                        "severity": "high",
                        "description": "配置文件中可能包含硬编码的API密钥",
                        "recommendation": "使用环境变量存储敏感信息"
                    })
        
        return {
            "status": "completed",
            "issues": issues
        }
    
    def log_scan_results(self, scan_results):
        """记录扫描结果"""
        # 计算严重程度
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        all_issues = []
        for category, result in scan_results['results'].items():
            all_issues.extend(result.get('issues', []))
        
        for issue in all_issues:
            severity = issue.get('severity', 'low')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # 记录到安全事件日志
        total_issues = sum(severity_counts.values())
        if total_issues > 0:
            description = f"安全扫描发现 {total_issues} 个问题: {severity_counts}"
            db_manager.log_security_event(
                event_type="security_scan",
                event_level="warning" if total_issues > 0 else "info",
                description=description
            )
        
        # 保存扫描结果到文件
        scan_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'security_scans')
        os.makedirs(scan_dir, exist_ok=True)
        
        scan_file = os.path.join(scan_dir, f"scan_{int(time.time())}.json")
        with open(scan_file, 'w', encoding='utf-8') as f:
            json.dump(scan_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"安全扫描结果已保存到: {scan_file}")
        
        # 清理旧文件，只保留最新的6个文件
        self._clean_old_scan_files(scan_dir, max_files=6)
    
    def _clean_old_scan_files(self, scan_dir, max_files=6):
        """清理旧的扫描文件，只保留最新的max_files个文件"""
        try:
            # 列出所有扫描文件
            scan_files = []
            for filename in os.listdir(scan_dir):
                if filename.startswith('scan_') and filename.endswith('.json'):
                    try:
                        # 提取时间戳
                        timestamp = int(filename.split('_')[1].split('.')[0])
                        file_path = os.path.join(scan_dir, filename)
                        if os.path.isfile(file_path):
                            scan_files.append((timestamp, file_path, filename))
                    except (IndexError, ValueError):
                        # 忽略文件名格式不正确的文件
                        continue
            
            # 按时间戳排序（最新的在前）
            scan_files.sort(key=lambda x: x[0], reverse=True)
            
            # 计算需要删除的文件
            files_to_delete = scan_files[max_files:]
            
            # 删除旧文件
            for timestamp, file_path, filename in files_to_delete:
                try:
                    os.remove(file_path)
                    logger.info(f"已清理旧的安全扫描文件: {filename}")
                except Exception as e:
                    logger.error(f"清理旧扫描文件失败: {filename} - {e}")
            
            logger.info(f"安全扫描文件清理完成，保留了{min(len(scan_files), max_files)}个最新文件")
        except Exception as e:
            logger.error(f"清理扫描文件时出错: {e}")
    
    def start_periodic_scan(self):
        """开始定期扫描"""
        logger.info(f"🔒 启动定期安全扫描，间隔: {self.scan_interval}秒")
        
        async def periodic_scan():
            while True:
                self.start_scan()
                await asyncio.sleep(self.scan_interval)
        
        import asyncio
        loop = asyncio.get_event_loop()
        loop.create_task(periodic_scan())

# 全局安全扫描器实例
security_scanner = SecurityScanner()

if __name__ == "__main__":
    # 运行安全扫描
    results = security_scanner.start_scan()
    print(json.dumps(results, ensure_ascii=False, indent=2))
