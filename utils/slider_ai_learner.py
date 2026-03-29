"""
滑块验证AI学习系统
通过机器学习优化滑块验证成功率
"""

import json
import os
import random
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from loguru import logger
import numpy as np


@dataclass
class SliderAttempt:
    """单次滑块尝试记录"""
    timestamp: str
    success: bool
    slide_distance: float
    total_steps: int
    base_delay: float
    final_left_px: float
    completion_used: bool
    strategy: str
    duration_ms: float
    error_message: str = ""


@dataclass
class TrajectoryFeatures:
    """轨迹特征"""
    total_distance: float
    step_count: int
    avg_step_size: float
    max_step_size: float
    min_step_size: float
    step_variance: float
    total_duration: float
    avg_delay: float
    delay_variance: float
    acceleration_pattern: str  # 'linear', 'ease_out', 'ease_in', 'custom'


class SliderAILearner:
    """
    滑块验证AI学习器
    
    功能：
    1. 记录每次滑块尝试的成功/失败数据
    2. 分析成功轨迹的特征
    3. 根据历史数据优化滑动参数
    4. 自适应调整策略
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'slider_learning')
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.history_file = os.path.join(self.data_dir, f'slider_history_{user_id}.json')
        self.model_file = os.path.join(self.data_dir, f'slider_model_{user_id}.json')
        
        self.attempts: List[SliderAttempt] = []
        self.success_patterns: List[TrajectoryFeatures] = []
        self.failure_patterns: List[TrajectoryFeatures] = []
        
        self._load_history()
        self._load_model()
        
    def _load_history(self):
        """加载历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.attempts = [SliderAttempt(**item) for item in data.get('attempts', [])]
                logger.info(f"【{self.user_id}】加载滑块历史记录: {len(self.attempts)} 条")
            except Exception as e:
                logger.error(f"【{self.user_id}】加载滑块历史记录失败: {e}")
                self.attempts = []
    
    def _save_history(self):
        """保存历史记录"""
        try:
            data = {
                'attempts': [asdict(attempt) for attempt in self.attempts],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"【{self.user_id}】保存滑块历史记录失败: {e}")
    
    def _load_model(self):
        """加载学习模型"""
        if os.path.exists(self.model_file):
            try:
                with open(self.model_file, 'r', encoding='utf-8') as f:
                    model = json.load(f)
                    self.success_patterns = [TrajectoryFeatures(**item) for item in model.get('success_patterns', [])]
                    self.failure_patterns = [TrajectoryFeatures(**item) for item in model.get('failure_patterns', [])]
                logger.info(f"【{self.user_id}】加载滑块学习模型: {len(self.success_patterns)} 成功模式, {len(self.failure_patterns)} 失败模式")
            except Exception as e:
                logger.error(f"【{self.user_id}】加载滑块学习模型失败: {e}")
                self.success_patterns = []
                self.failure_patterns = []
    
    def _save_model(self):
        """保存学习模型"""
        try:
            model = {
                'success_patterns': [asdict(p) for p in self.success_patterns],
                'failure_patterns': [asdict(p) for p in self.failure_patterns],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.model_file, 'w', encoding='utf-8') as f:
                json.dump(model, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"【{self.user_id}】保存滑块学习模型失败: {e}")
    
    def record_attempt(self, success: bool, slide_distance: float, trajectory_data: dict,
                      strategy: str = "default", duration_ms: float = 0, error_message: str = ""):
        """
        记录一次滑块尝试
        
        Args:
            success: 是否成功
            slide_distance: 滑动距离
            trajectory_data: 轨迹数据
            strategy: 使用的策略
            duration_ms: 耗时（毫秒）
            error_message: 错误信息
        """
        attempt = SliderAttempt(
            timestamp=datetime.now().isoformat(),
            success=success,
            slide_distance=slide_distance,
            total_steps=trajectory_data.get('total_steps', 0),
            base_delay=trajectory_data.get('base_delay', 0),
            final_left_px=trajectory_data.get('final_left_px', 0),
            completion_used=trajectory_data.get('completion_used', False),
            strategy=strategy,
            duration_ms=duration_ms,
            error_message=error_message
        )
        
        self.attempts.append(attempt)
        
        # 只保留最近1000条记录
        if len(self.attempts) > 1000:
            self.attempts = self.attempts[-1000:]
        
        self._save_history()
        
        # 提取轨迹特征
        features = self._extract_features(trajectory_data)
        if success:
            self.success_patterns.append(features)
            if len(self.success_patterns) > 100:
                self.success_patterns = self.success_patterns[-100:]
        else:
            self.failure_patterns.append(features)
            if len(self.failure_patterns) > 100:
                self.failure_patterns = self.failure_patterns[-100:]
        
        self._save_model()
        
        logger.info(f"【{self.user_id}】记录滑块尝试: 成功={success}, 策略={strategy}, 距离={slide_distance}px")
    
    def _extract_features(self, trajectory_data: dict) -> TrajectoryFeatures:
        """从轨迹数据中提取特征"""
        steps = trajectory_data.get('steps', [])
        delays = trajectory_data.get('delays', [])
        
        if not steps:
            return TrajectoryFeatures(
                total_distance=0,
                step_count=0,
                avg_step_size=0,
                max_step_size=0,
                min_step_size=0,
                step_variance=0,
                total_duration=0,
                avg_delay=0,
                delay_variance=0,
                acceleration_pattern='unknown'
            )
        
        step_sizes = [abs(s) for s in steps]
        
        return TrajectoryFeatures(
            total_distance=sum(step_sizes),
            step_count=len(steps),
            avg_step_size=np.mean(step_sizes) if step_sizes else 0,
            max_step_size=max(step_sizes) if step_sizes else 0,
            min_step_size=min(step_sizes) if step_sizes else 0,
            step_variance=np.var(step_sizes) if len(step_sizes) > 1 else 0,
            total_duration=sum(delays) if delays else 0,
            avg_delay=np.mean(delays) if delays else 0,
            delay_variance=np.var(delays) if len(delays) > 1 else 0,
            acceleration_pattern=self._detect_acceleration_pattern(steps)
        )
    
    def _detect_acceleration_pattern(self, steps: List[float]) -> str:
        """检测加速度模式"""
        if len(steps) < 3:
            return 'linear'
        
        # 计算每一步的变化
        changes = [steps[i+1] - steps[i] for i in range(len(steps)-1)]
        
        # 检测趋势
        increasing = sum(1 for c in changes if c > 0)
        decreasing = sum(1 for c in changes if c < 0)
        
        if increasing > len(changes) * 0.7:
            return 'ease_in'  # 加速
        elif decreasing > len(changes) * 0.7:
            return 'ease_out'  # 减速
        else:
            return 'custom'  # 自定义
    
    def get_success_rate(self, last_n: int = 50) -> float:
        """获取最近N次尝试的成功率"""
        if not self.attempts:
            return 0.0
        
        recent = self.attempts[-last_n:]
        if not recent:
            return 0.0
        
        success_count = sum(1 for a in recent if a.success)
        return success_count / len(recent)
    
    def get_optimal_parameters(self, slide_distance: float) -> dict:
        """
        根据历史数据获取最优参数
        
        Args:
            slide_distance: 滑动距离
            
        Returns:
            最优参数字典
        """
        if not self.success_patterns:
            # 使用默认参数
            return self._get_default_parameters(slide_distance)
        
        # 找到相似距离的成功模式
        similar_patterns = [
            p for p in self.success_patterns
            if abs(p.total_distance - slide_distance) < 50
        ]
        
        if not similar_patterns:
            similar_patterns = self.success_patterns
        
        # 计算平均参数
        avg_step_count = int(np.mean([p.step_count for p in similar_patterns]))
        avg_delay = np.mean([p.avg_delay for p in similar_patterns])
        
        # 根据距离调整
        distance_factor = slide_distance / 300  # 假设标准距离300px
        optimal_steps = max(10, min(50, int(avg_step_count * distance_factor)))
        optimal_delay = max(0.01, min(0.1, avg_delay))
        
        return {
            'step_count': optimal_steps,
            'base_delay': optimal_delay,
            'acceleration': 'ease_out',  # 通常减速模式更自然
            'jitter_amount': random.uniform(0.5, 2.0)
        }
    
    def _get_default_parameters(self, slide_distance: float) -> dict:
        """获取默认参数"""
        # 根据距离计算步数
        distance_factor = slide_distance / 300
        step_count = max(10, min(50, int(25 * distance_factor)))
        
        return {
            'step_count': step_count,
            'base_delay': 0.03,
            'acceleration': 'ease_out',
            'jitter_amount': 1.0
        }
    
    def get_recommended_strategy(self) -> str:
        """获取推荐的策略"""
        success_rate = self.get_success_rate(last_n=20)
        
        if success_rate >= 0.8:
            return 'ultra_fast'  # 高成功率，使用极速模式
        elif success_rate >= 0.5:
            return 'adaptive'  # 中等成功率，使用自适应模式
        else:
            return 'conservative'  # 低成功率，使用保守模式
    
    def analyze_patterns(self) -> dict:
        """分析成功和失败的模式"""
        if not self.attempts:
            return {'message': '暂无数据'}
        
        total = len(self.attempts)
        success_count = sum(1 for a in self.attempts if a.success)
        
        # 按策略统计
        strategy_stats = {}
        for attempt in self.attempts:
            strategy = attempt.strategy
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {'total': 0, 'success': 0}
            strategy_stats[strategy]['total'] += 1
            if attempt.success:
                strategy_stats[strategy]['success'] += 1
        
        # 计算每个策略的成功率
        for strategy in strategy_stats:
            stats = strategy_stats[strategy]
            stats['rate'] = stats['success'] / stats['total'] if stats['total'] > 0 else 0
        
        return {
            'total_attempts': total,
            'success_count': success_count,
            'success_rate': success_count / total if total > 0 else 0,
            'strategy_stats': strategy_stats,
            'best_strategy': max(strategy_stats.items(), key=lambda x: x[1]['rate'])[0] if strategy_stats else 'unknown'
        }
    
    def get_learning_report(self) -> str:
        """获取学习报告"""
        analysis = self.analyze_patterns()
        
        report = f"""
滑块验证AI学习报告
==================
总尝试次数: {analysis['total_attempts']}
成功次数: {analysis['success_count']}
成功率: {analysis['success_rate']:.1%}

策略统计:
"""
        for strategy, stats in analysis.get('strategy_stats', {}).items():
            report += f"  {strategy}: {stats['success']}/{stats['total']} ({stats['rate']:.1%})\n"
        
        report += f"\n推荐策略: {analysis['best_strategy']}\n"
        
        return report


# 全局AI学习器实例
_slider_learners: Dict[str, SliderAILearner] = {}


def get_slider_learner(user_id: str) -> SliderAILearner:
    """获取或创建滑块学习器"""
    if user_id not in _slider_learners:
        _slider_learners[user_id] = SliderAILearner(user_id)
    return _slider_learners[user_id]


# 便捷函数
def record_slider_attempt(user_id: str, success: bool, slide_distance: float, 
                         trajectory_data: dict, strategy: str = "default",
                         duration_ms: float = 0, error_message: str = ""):
    """记录滑块尝试"""
    learner = get_slider_learner(user_id)
    learner.record_attempt(success, slide_distance, trajectory_data, strategy, duration_ms, error_message)


def get_slider_learning_report(user_id: str) -> str:
    """获取学习报告"""
    learner = get_slider_learner(user_id)
    return learner.get_learning_report()
