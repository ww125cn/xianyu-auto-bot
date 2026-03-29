"""
闲鱼商品一键擦亮功能
支持批量擦亮、定时擦亮、智能延迟
"""

import asyncio
import random
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger
import aiohttp


@dataclass
class PolishResult:
    """擦亮结果"""
    item_id: str
    success: bool
    message: str
    polished_at: Optional[datetime] = None


@dataclass
class PolishTask:
    """擦亮任务"""
    cookie_id: str
    item_ids: List[str]
    scheduled_time: Optional[datetime] = None
    random_delay: bool = True
    callback: Optional[Callable] = None


class ItemPolisher:
    """商品擦亮器"""
    
    # 用户代理列表
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    def __init__(self):
        self._running = False
        self._scheduled_tasks: Dict[str, asyncio.Task] = {}
        self._polish_history: Dict[str, List[PolishResult]] = {}
        self._semaphore = asyncio.Semaphore(3)  # 限制并发数
        
    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.USER_AGENTS)
    
    async def _random_delay(self, min_seconds: int = 3, max_seconds: int = 10):
        """随机延迟，模拟人类行为"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.debug(f"随机延迟 {delay:.2f} 秒")
        await asyncio.sleep(delay)
    
    async def get_on_sale_items(self, cookie_id: str, cookie_str: str) -> List[Dict]:
        """
        获取在售商品列表
        
        Returns:
            List[Dict]: 商品列表，每个商品包含 item_id, title, price 等信息
        """
        try:
            from utils.xianyu_utils import trans_cookies, generate_device_id
            
            # 处理cookie_str可能是字典的情况
            if isinstance(cookie_str, dict):
                cookies = cookie_str
                # 将字典转换回字符串格式用于headers
                cookie_str = '; '.join([f"{k}={v}" for k, v in cookie_str.items()])
            else:
                cookies = trans_cookies(cookie_str)
            if 'unb' not in cookies:
                logger.error(f"【{cookie_id}】Cookie中缺少必需的'unb'字段")
                return []
            
            device_id = generate_device_id(cookies['unb'])
            
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'application/json',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': 'https://www.goofish.com/',
                'Cookie': cookie_str,
            }
            
            # 调用闲鱼API获取在售商品
            # 这里使用闲鱼的商品列表API
            url = 'https://h5api.m.goofish.com/h5/mtop.taobao.idle.item.list/1.0/'
            
            params = {
                'jsv': '2.7.2',
                'appKey': '34839810',
                't': str(int(time.time() * 1000)),
                'sign': '',  # 需要计算签名
                'api': 'mtop.taobao.idle.item.list',
                'v': '1.0',
                'type': 'originaljson',
                'dataType': 'json',
            }
            
            data = {
                'data': '{"pageNumber":1,"pageSize":20,"status":"selling"}'
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                async with session.post(url, params=params, data=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        # 解析商品列表
                        items = self._parse_items(result)
                        logger.info(f"【{cookie_id}】获取到 {len(items)} 个在售商品")
                        return items
                    else:
                        logger.error(f"【{cookie_id}】获取商品列表失败: HTTP {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"【{cookie_id}】获取在售商品失败: {e}")
            return []
    
    def _parse_items(self, api_response: Dict) -> List[Dict]:
        """解析API响应，提取商品信息"""
        items = []
        try:
            data = api_response.get('data', {})
            item_list = data.get('items', [])
            
            for item in item_list:
                items.append({
                    'item_id': item.get('itemId', ''),
                    'title': item.get('title', ''),
                    'price': item.get('price', ''),
                    'image': item.get('image', ''),
                    'status': item.get('status', ''),
                })
        except Exception as e:
            logger.error(f"解析商品列表失败: {e}")
        
        return items
    
    async def polish_item(self, cookie_id: str, cookie_str: str, item_id: str) -> PolishResult:
        """
        擦亮单个商品
        
        Args:
            cookie_id: Cookie ID
            cookie_str: Cookie字符串
            item_id: 商品ID
            
        Returns:
            PolishResult: 擦亮结果
        """
        async with self._semaphore:
            try:
                from utils.xianyu_utils import trans_cookies, generate_device_id
                
                # 随机延迟，避免请求过于规律
                await self._random_delay(2, 5)
                
                # 处理cookie_str可能是字典的情况
                if isinstance(cookie_str, dict):
                    cookies = cookie_str
                    # 将字典转换回字符串格式用于headers
                    cookie_str = '; '.join([f"{k}={v}" for k, v in cookie_str.items()])
                else:
                    cookies = trans_cookies(cookie_str)
                if 'unb' not in cookies:
                    return PolishResult(
                        item_id=item_id,
                        success=False,
                        message="Cookie中缺少必需的'unb'字段"
                    )
                
                device_id = generate_device_id(cookies['unb'])
                
                headers = {
                    'User-Agent': self._get_random_user_agent(),
                    'Accept': 'application/json',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'Referer': 'https://www.goofish.com/',
                    'Cookie': cookie_str,
                }
                
                # 调用闲鱼擦亮API
                url = 'https://h5api.m.goofish.com/h5/mtop.taobao.idle.item.refresh/1.0/'
                
                params = {
                    'jsv': '2.7.2',
                    'appKey': '34839810',
                    't': str(int(time.time() * 1000)),
                    'sign': '',  # 需要计算签名
                    'api': 'mtop.taobao.idle.item.refresh',
                    'v': '1.0',
                    'type': 'originaljson',
                    'dataType': 'json',
                }
                
                data = {
                    'data': f'{{"itemId":"{item_id}"}}'
                }
                
                timeout = aiohttp.ClientTimeout(total=30)
                connector = aiohttp.TCPConnector(ssl=False)
                
                async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                    async with session.post(url, params=params, data=data, headers=headers) as response:
                        result = await response.json()
                        
                        # 解析响应
                        ret = result.get('ret', [])
                        if any('SUCCESS' in str(r) for r in ret):
                            logger.info(f"【{cookie_id}】商品 {item_id} 擦亮成功")
                            return PolishResult(
                                item_id=item_id,
                                success=True,
                                message="擦亮成功",
                                polished_at=datetime.now()
                            )
                        else:
                            error_msg = str(ret[0]) if ret else "未知错误"
                            logger.warning(f"【{cookie_id}】商品 {item_id} 擦亮失败: {error_msg}")
                            return PolishResult(
                                item_id=item_id,
                                success=False,
                                message=error_msg
                            )
                            
            except Exception as e:
                logger.error(f"【{cookie_id}】擦亮商品 {item_id} 失败: {e}")
                return PolishResult(
                    item_id=item_id,
                    success=False,
                    message=f"异常: {str(e)[:50]}"
                )
    
    async def polish_all_items(self, cookie_id: str, cookie_str: str) -> List[PolishResult]:
        """
        一键擦亮所有在售商品
        
        Args:
            cookie_id: Cookie ID
            cookie_str: Cookie字符串
            
        Returns:
            List[PolishResult]: 擦亮结果列表
        """
        logger.info(f"【{cookie_id}】开始一键擦亮所有商品...")
        
        # 获取在售商品
        items = await self.get_on_sale_items(cookie_id, cookie_str)
        if not items:
            logger.warning(f"【{cookie_id}】没有在售商品需要擦亮")
            return []
        
        results = []
        for i, item in enumerate(items):
            item_id = item.get('item_id')
            if not item_id:
                continue
            
            logger.info(f"【{cookie_id}】正在擦亮商品 {i+1}/{len(items)}: {item.get('title', item_id)}")
            
            result = await self.polish_item(cookie_id, cookie_str, item_id)
            results.append(result)
            
            # 保存历史记录
            if cookie_id not in self._polish_history:
                self._polish_history[cookie_id] = []
            self._polish_history[cookie_id].append(result)
        
        # 统计结果
        success_count = sum(1 for r in results if r.success)
        logger.info(f"【{cookie_id}】一键擦亮完成: {success_count}/{len(results)} 个成功")
        
        return results
    
    async def schedule_daily_polish(self, cookie_id: str, cookie_str: str, 
                                   hour: int = 9, minute: int = 0,
                                   random_delay: bool = True):
        """
        设置每日定时擦亮
        
        Args:
            cookie_id: Cookie ID
            cookie_str: Cookie字符串
            hour: 小时 (0-23)
            minute: 分钟 (0-59)
            random_delay: 是否添加随机延迟
        """
        task_id = f"{cookie_id}_daily_polish"
        
        # 取消已存在的定时任务
        if task_id in self._scheduled_tasks:
            self._scheduled_tasks[task_id].cancel()
            logger.info(f"【{cookie_id}】取消已存在的定时擦亮任务")
        
        async def daily_task():
            while self._running:
                try:
                    now = datetime.now()
                    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # 如果今天的时间已过，设置为明天
                    if target_time <= now:
                        target_time += timedelta(days=1)
                    
                    wait_seconds = (target_time - now).total_seconds()
                    
                    # 添加随机延迟 (0-30分钟)
                    if random_delay:
                        delay = random.randint(0, 1800)
                        wait_seconds += delay
                        logger.info(f"【{cookie_id}】定时擦亮任务将在 {wait_seconds/60:.1f} 分钟后执行（含随机延迟 {delay/60:.1f} 分钟）")
                    else:
                        logger.info(f"【{cookie_id}】定时擦亮任务将在 {wait_seconds/60:.1f} 分钟后执行")
                    
                    await asyncio.sleep(wait_seconds)
                    
                    # 执行擦亮
                    logger.info(f"【{cookie_id}】执行定时擦亮任务...")
                    await self.polish_all_items(cookie_id, cookie_str)
                    
                except asyncio.CancelledError:
                    logger.info(f"【{cookie_id}】定时擦亮任务已取消")
                    break
                except Exception as e:
                    logger.error(f"【{cookie_id}】定时擦亮任务出错: {e}")
                    await asyncio.sleep(3600)  # 出错后等待1小时再试
        
        self._running = True
        task = asyncio.create_task(daily_task())
        self._scheduled_tasks[task_id] = task
        
        logger.info(f"【{cookie_id}】已设置每日定时擦亮: {hour:02d}:{minute:02d}")
    
    def cancel_scheduled_polish(self, cookie_id: str):
        """取消定时擦亮任务"""
        task_id = f"{cookie_id}_daily_polish"
        if task_id in self._scheduled_tasks:
            self._scheduled_tasks[task_id].cancel()
            del self._scheduled_tasks[task_id]
            logger.info(f"【{cookie_id}】已取消定时擦亮任务")
            return True
        return False
    
    def get_polish_history(self, cookie_id: str, limit: int = 10) -> List[PolishResult]:
        """获取擦亮历史记录"""
        history = self._polish_history.get(cookie_id, [])
        return history[-limit:] if history else []
    
    def stop(self):
        """停止所有定时任务"""
        self._running = False
        for task_id, task in self._scheduled_tasks.items():
            task.cancel()
            logger.info(f"已取消定时任务: {task_id}")
        self._scheduled_tasks.clear()


# 全局擦亮器实例
item_polisher = ItemPolisher()


async def polish_items_now(cookie_id: str, cookie_str: str) -> List[PolishResult]:
    """立即擦亮所有商品（便捷函数）"""
    return await item_polisher.polish_all_items(cookie_id, cookie_str)


async def schedule_daily_polish(cookie_id: str, cookie_str: str, 
                               hour: int = 9, minute: int = 0):
    """设置每日定时擦亮（便捷函数）"""
    await item_polisher.schedule_daily_polish(cookie_id, cookie_str, hour, minute)
