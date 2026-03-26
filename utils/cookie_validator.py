"""
Cookie有效性检查工具
用于定期检查账号Cookie是否失效
包含防封号机制：随机延迟、顺序检查、模拟正常用户行为
"""

import asyncio
import time
import random
from typing import Dict, Optional, Callable
from loguru import logger
import aiohttp
from aiohttp import ClientConnectorError, ClientError


class CookieValidator:
    """Cookie有效性检查器"""
    
    # 用户代理列表，模拟不同浏览器
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ]
    
    def __init__(self, check_interval: int = 7200, min_delay: int = 30, max_delay: int = 120):  # 默认每2小时检查一次
        """
        初始化Cookie验证器
        
        Args:
            check_interval: 检查间隔（秒），默认2小时
            min_delay: 检查间隔最小延迟（秒），默认30秒
            max_delay: 检查间隔最大延迟（秒），默认120秒
        """
        self.check_interval = check_interval
        self.min_delay = min_delay
        self.max_delay = max_delay
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._callbacks: list[Callable[[str, bool, str], None]] = []  # 状态变更回调函数列表
        self._semaphore = asyncio.Semaphore(1)  # 限制同时只检查一个账号
        
    def add_status_change_callback(self, callback: Callable[[str, bool, str], None]):
        """
        添加Cookie状态变更回调函数
        
        Args:
            callback: 回调函数，参数为 (cookie_id, is_valid, message)
        """
        self._callbacks.append(callback)
        
    def remove_status_change_callback(self, callback: Callable[[str, bool, str], None]):
        """移除Cookie状态变更回调函数"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    async def _notify_status_change(self, cookie_id: str, is_valid: bool, message: str):
        """通知所有回调函数状态变更"""
        for callback in self._callbacks:
            try:
                callback(cookie_id, is_valid, message)
            except Exception as e:
                logger.error(f"通知Cookie状态变更回调失败: {e}")
    
    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.USER_AGENTS)
    
    async def _random_delay(self):
        """随机延迟，模拟人类行为"""
        delay = random.randint(self.min_delay, self.max_delay)
        logger.debug(f"随机延迟 {delay} 秒")
        await asyncio.sleep(delay)
    
    async def validate_cookie(self, cookie_id: str, cookie_string: str, use_delay: bool = True) -> tuple[bool, str]:
        """
        验证单个Cookie的有效性
        
        Args:
            cookie_id: Cookie ID
            cookie_string: Cookie字符串
            use_delay: 是否使用随机延迟（默认True）
            
        Returns:
            (是否有效, 消息)
        """
        # 使用信号量限制并发，确保同时只检查一个账号
        async with self._semaphore:
            try:
                # 随机延迟，避免请求过于规律（仅在use_delay为True时）
                if use_delay:
                    await self._random_delay()
                
                # 尝试使用Cookie访问闲鱼API
                from utils.xianyu_utils import trans_cookies, generate_device_id
                
                # 如果cookie_string是字典，转换为字符串
                if isinstance(cookie_string, dict):
                    cookie_string = '; '.join([f"{k}={v}" for k, v in cookie_string.items()])
                
                cookies = trans_cookies(cookie_string)
                if 'unb' not in cookies:
                    return False, "Cookie中缺少必需的'unb'字段"
                
                # 构建测试请求
                device_id = generate_device_id(cookies['unb'])
                
                # 使用随机User-Agent
                user_agent = self._get_random_user_agent()
                
                # 尝试访问闲鱼用户信息API
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': 'https://www.goofish.com/',
                    'Cookie': cookie_string,
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin',
                    'Cache-Control': 'max-age=0'
                }
                
                # 使用更长的超时时间
                timeout = aiohttp.ClientTimeout(total=15, connect=10)
                
                # 创建TCP连接器，禁用SSL验证（避免证书问题）
                connector = aiohttp.TCPConnector(ssl=False)
                
                async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                    # 尝试访问闲鱼首页
                    async with session.get(
                        'https://www.goofish.com/',
                        headers=headers,
                        allow_redirects=True,
                        skip_auto_headers=['User-Agent']  # 使用自定义User-Agent
                    ) as response:
                        if response.status == 200:
                            # 检查响应内容是否包含登录状态相关的标记
                            content = await response.text()
                            
                            # 如果返回内容包含登录相关的错误信息，说明Cookie失效
                            if '登录' in content and '超时' in content:
                                return False, "Cookie已过期，需要重新登录"
                            
                            if '请登录' in content or '未登录' in content:
                                return False, "Cookie已失效，需要重新登录"
                            
                            # 检查是否被风控
                            if '验证码' in content or '验证' in content:
                                logger.warning(f"Cookie {cookie_id} 可能触发风控")
                                return True, "Cookie有效（但可能触发风控）"
                            
                            return True, "Cookie有效"
                        elif response.status == 401 or response.status == 403:
                            return False, f"Cookie已失效 (HTTP {response.status})"
                        elif response.status == 429:
                            logger.warning(f"Cookie {cookie_id} 请求过于频繁，暂停检查")
                            return True, "Cookie状态未知（请求过于频繁）"
                        else:
                            return False, f"验证失败 (HTTP {response.status})"
                            
            except asyncio.TimeoutError:
                return False, "验证超时，请检查网络连接"
            except ClientConnectorError as e:
                logger.error(f"验证Cookie {cookie_id} 时连接失败: {e}")
                return False, f"连接失败，请检查网络: {str(e)}"
            except ClientError as e:
                logger.error(f"验证Cookie {cookie_id} 时客户端错误: {e}")
                return False, f"请求失败: {str(e)}"
            except Exception as e:
                logger.error(f"验证Cookie {cookie_id} 时出错: {e}")
                return False, f"验证出错: {str(e)}"
    
    async def _check_all_cookies(self):
        """检查所有Cookie的有效性（顺序检查，避免并发）"""
        try:
            from db_manager import db_manager
            
            # 获取所有Cookie
            all_cookies = db_manager.get_all_cookies()
            
            if not all_cookies:
                logger.info("没有需要检查的Cookie")
                return
            
            # 筛选需要检查的Cookie（排除最近已通过心跳验证的）
            cookies_to_check = {}
            skipped_count = 0
            
            for cookie_id, cookie_value in all_cookies.items():
                # 检查该Cookie的验证状态
                validation_status = db_manager.get_cookie_validation_status(cookie_id)
                
                if validation_status and validation_status.get('is_valid') == True:
                    # 检查最后验证时间
                    last_validated = validation_status.get('last_validated_at')
                    if last_validated:
                        try:
                            from datetime import datetime, timedelta
                            # 解析时间字符串
                            if isinstance(last_validated, str):
                                last_time = datetime.fromisoformat(last_validated.replace('Z', '+00:00'))
                            else:
                                last_time = last_validated
                            
                            # 如果30分钟内已经验证过，跳过
                            if datetime.now(last_time.tzinfo) - last_time < timedelta(minutes=30):
                                logger.debug(f"Cookie {cookie_id} 30分钟内已通过心跳验证，跳过主动检查")
                                skipped_count += 1
                                continue
                        except Exception as e:
                            logger.debug(f"解析验证时间失败: {e}")
                
                cookies_to_check[cookie_id] = cookie_value
            
            if not cookies_to_check:
                logger.info(f"所有Cookie都已通过心跳验证，无需主动检查 (跳过 {skipped_count} 个)")
                return
            
            logger.info(f"开始顺序检查 {len(cookies_to_check)} 个Cookie的有效性 (跳过 {skipped_count} 个已通过心跳验证)...")
            logger.info(f"预计检查时间: {len(cookies_to_check) * (self.min_delay + self.max_delay) // 2} - {len(cookies_to_check) * self.max_delay} 秒")
            
            # 顺序检查Cookie，避免并发请求
            valid_count = 0
            invalid_count = 0
            unknown_count = 0
            
            for cookie_id, cookie_value in cookies_to_check.items():
                try:
                    is_valid, message = await self._check_and_update_cookie(cookie_id, cookie_value)
                    
                    if is_valid and "未知" not in message:
                        valid_count += 1
                    elif not is_valid:
                        invalid_count += 1
                    else:
                        unknown_count += 1
                        
                except Exception as e:
                    logger.error(f"检查Cookie {cookie_id} 时出错: {e}")
                    unknown_count += 1
            
            logger.info(f"Cookie检查完成: 有效 {valid_count} 个, 无效 {invalid_count} 个, 未知 {unknown_count} 个, 跳过 {skipped_count} 个")
            
        except Exception as e:
            logger.error(f"检查所有Cookie时出错: {e}")
    
    async def _check_and_update_cookie(self, cookie_id: str, cookie_value: str, use_delay: bool = True):
        """检查并更新单个Cookie的状态"""
        try:
            is_valid, message = await self.validate_cookie(cookie_id, cookie_value, use_delay)
            
            # 更新数据库中的状态
            from db_manager import db_manager
            db_manager.update_cookie_validation_status(cookie_id, is_valid, message)
            
            # 通知状态变更
            await self._notify_status_change(cookie_id, is_valid, message)
            
            if not is_valid:
                logger.warning(f"Cookie {cookie_id} 已失效: {message}")
            else:
                logger.debug(f"Cookie {cookie_id} 有效: {message}")
            
            return is_valid, message
            
        except Exception as e:
            logger.error(f"检查Cookie {cookie_id} 时出错: {e}")
            return False, str(e)
    
    async def _run_periodic_check(self):
        """运行定期检查任务"""
        logger.info(f"Cookie验证器已启动，检查间隔: {self.check_interval}秒")
        logger.info(f"检查延迟: {self.min_delay}-{self.max_delay}秒")
        logger.info("使用顺序检查模式，避免并发请求")
        
        while self._running:
            try:
                await self._check_all_cookies()
            except Exception as e:
                logger.error(f"定期检查Cookie时出错: {e}")
            
            # 等待下一次检查
            await asyncio.sleep(self.check_interval)
    
    def start(self):
        """启动定期检查任务"""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._run_periodic_check())
            logger.info("Cookie验证器已启动")
    
    def stop(self):
        """停止定期检查任务"""
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
                self._task = None
            logger.info("Cookie验证器已停止")
    
    async def check_cookie_now(self, cookie_id: str) -> tuple[bool, str]:
        """
        立即检查指定Cookie的有效性（手动验证时不使用延迟）
        
        Args:
            cookie_id: Cookie ID
            
        Returns:
            (是否有效, 消息)
        """
        from db_manager import db_manager
        
        cookie_value = db_manager.get_cookie_by_id(cookie_id)
        if not cookie_value:
            return False, "Cookie不存在"
        
        # 手动验证时不使用延迟，直接检查
        return await self._check_and_update_cookie(cookie_id, cookie_value, use_delay=False)


# 全局Cookie验证器实例
cookie_validator = CookieValidator()


def start_cookie_validation(check_interval: int = 7200, min_delay: int = 30, max_delay: int = 120):
    """
    启动Cookie验证服务
    
    Args:
        check_interval: 检查间隔（秒），默认2小时
        min_delay: 检查间隔最小延迟（秒），默认30秒
        max_delay: 检查间隔最大延迟（秒），默认120秒
    """
    global cookie_validator
    cookie_validator = CookieValidator(check_interval, min_delay, max_delay)
    cookie_validator.start()
    logger.info(f"Cookie验证服务已启动，检查间隔: {check_interval}秒")


def stop_cookie_validation():
    """停止Cookie验证服务"""
    global cookie_validator
    if cookie_validator:
        cookie_validator.stop()
        logger.info("Cookie验证服务已停止")


async def validate_cookie_now(cookie_id: str) -> tuple[bool, str]:
    """
    立即验证指定Cookie
    
    Args:
        cookie_id: Cookie ID
        
    Returns:
        (是否有效, 消息)
    """
    global cookie_validator
    if not cookie_validator:
        cookie_validator = CookieValidator()
    
    return await cookie_validator.check_cookie_now(cookie_id)
