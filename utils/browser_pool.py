"""
浏览器实例池管理器
按账号复用浏览器实例，最多3个实例自动管理
"""

import asyncio
import time
from typing import Dict, Optional
from loguru import logger
from utils.order_detail_fetcher import OrderDetailFetcher


class BrowserPool:
    """浏览器实例池管理器"""
    
    def __init__(self, max_instances: int = 3):
        """初始化浏览器实例池
        
        Args:
            max_instances: 最大浏览器实例数
        """
        self.max_instances = max_instances
        self.instances: Dict[str, Dict] = {}  # {cookie_id: {'instance': OrderDetailFetcher, 'last_used': float}}
        self.lock = asyncio.Lock()
        self.cleanup_task = None
        
    async def start(self):
        """启动浏览器实例池"""
        # 启动定期清理任务
        self.cleanup_task = asyncio.create_task(self._cleanup_inactive_instances())
        logger.info(f"浏览器实例池已启动，最大实例数: {self.max_instances}")
    
    async def stop(self):
        """停止浏览器实例池"""
        # 取消清理任务
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # 关闭所有浏览器实例
        async with self.lock:
            for cookie_id, instance_info in list(self.instances.items()):
                instance = instance_info['instance']
                try:
                    await instance.close_browser()
                    logger.info(f"关闭浏览器实例: {cookie_id}")
                except Exception as e:
                    logger.error(f"关闭浏览器实例失败: {cookie_id} - {e}")
            self.instances.clear()
        
        logger.info("浏览器实例池已停止")
    
    async def get_instance(self, cookie_id: str, cookie_string: str, headless: bool = True) -> OrderDetailFetcher:
        """获取浏览器实例
        
        Args:
            cookie_id: 账号ID
            cookie_string: Cookie字符串
            headless: 是否以无头模式运行
            
        Returns:
            OrderDetailFetcher: 浏览器实例
        """
        async with self.lock:
            # 检查是否已有实例
            if cookie_id in self.instances:
                instance_info = self.instances[cookie_id]
                instance = instance_info['instance']
                # 更新最后使用时间
                instance_info['last_used'] = time.time()
                logger.info(f"复用浏览器实例: {cookie_id}")
                return instance
            
            # 检查实例数是否达到上限
            if len(self.instances) >= self.max_instances:
                # 清理最不活跃的实例
                await self._cleanup_oldest_instance()
            
            # 创建新实例
            instance = OrderDetailFetcher(cookie_string)
            try:
                await instance.init_browser(headless=headless)
                self.instances[cookie_id] = {
                    'instance': instance,
                    'last_used': time.time()
                }
                logger.info(f"创建新浏览器实例: {cookie_id}，当前实例数: {len(self.instances)}/{self.max_instances}")
                return instance
            except Exception as e:
                logger.error(f"创建浏览器实例失败: {cookie_id} - {e}")
                # 清理失败的实例
                try:
                    await instance.close_browser()
                except:
                    pass
                raise
    
    async def _cleanup_inactive_instances(self):
        """定期清理不活跃的实例"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                await self._cleanup_expired_instances()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理不活跃实例失败: {e}")
    
    async def _cleanup_expired_instances(self):
        """清理过期的实例"""
        async with self.lock:
            current_time = time.time()
            expired_instances = []
            
            # 找出超过30分钟未使用的实例
            for cookie_id, instance_info in self.instances.items():
                if current_time - instance_info['last_used'] > 1800:  # 30分钟
                    expired_instances.append(cookie_id)
            
            # 清理过期实例
            for cookie_id in expired_instances:
                instance_info = self.instances.pop(cookie_id)
                instance = instance_info['instance']
                try:
                    await instance.close_browser()
                    logger.info(f"清理过期浏览器实例: {cookie_id}")
                except Exception as e:
                    logger.error(f"清理过期浏览器实例失败: {cookie_id} - {e}")
    
    async def _cleanup_oldest_instance(self):
        """清理最不活跃的实例"""
        if not self.instances:
            return
        
        # 找出最不活跃的实例
        oldest_cookie_id = min(self.instances, key=lambda x: self.instances[x]['last_used'])
        instance_info = self.instances.pop(oldest_cookie_id)
        instance = instance_info['instance']
        
        try:
            await instance.close_browser()
            logger.info(f"清理最不活跃的浏览器实例: {oldest_cookie_id}")
        except Exception as e:
            logger.error(f"清理最不活跃的浏览器实例失败: {oldest_cookie_id} - {e}")
    
    def get_instance_count(self) -> int:
        """获取当前实例数"""
        return len(self.instances)


# 创建全局浏览器实例池
browser_pool = BrowserPool(max_instances=3)


async def init_browser_pool():
    """初始化浏览器实例池"""
    await browser_pool.start()


async def close_browser_pool():
    """关闭浏览器实例池"""
    await browser_pool.stop()
