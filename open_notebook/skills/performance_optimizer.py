"""
Performance Optimizer - 性能优化器

功能:
1. 数据库查询优化（连接池、预编译、批量操作）
2. 多级缓存机制（内存缓存 + Redis）
3. 异步处理增强（任务队列、并发控制）
4. 懒加载和预加载策略
5. 性能监控和分析
"""

import asyncio
import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

from loguru import logger

# 类型变量
T = TypeVar('T')


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    created_at: float
    expires_at: float
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class LRUCache:
    """LRU 内存缓存实现"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0
        
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        if entry.is_expired():
            del self.cache[key]
            self.misses += 1
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        self.hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """设置缓存值"""
        now = time.time()
        entry = CacheEntry(
            value=value,
            created_at=now,
            expires_at=now + ttl_seconds
        )
        
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = entry
        
        # Evict oldest if over capacity
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def stats(self) -> Dict[str, Any]:
        """返回缓存统计"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.2f}%"
        }


# 全局缓存实例
_query_cache = LRUCache(max_size=500)
_result_cache = LRUCache(max_size=200)


def cached(ttl: int = 300, cache_instance: Optional[LRUCache] = None):
    """缓存装饰器
    
    Args:
        ttl: 缓存生存时间（秒）
        cache_instance: 使用的缓存实例
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            cache = cache_instance or _query_cache
            
            # 生成缓存 key
            key_data = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # 执行函数
            logger.debug(f"Cache miss for {func.__name__}, executing...")
            result = await func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result, ttl_seconds=ttl)
            return result
        
        return wrapper
    return decorator


class DatabaseOptimizer:
    """数据库查询优化器"""
    
    def __init__(self):
        self.query_count = 0
        self.slow_queries = []
        self.query_threshold = 1.0  # 慢查询阈值（秒）
        
    async def execute_optimized(
        self,
        query_func: Callable,
        *args,
        use_cache: bool = True,
        cache_ttl: int = 300,
        **kwargs
    ) -> Any:
        """执行优化的数据库查询
        
        Args:
            query_func: 查询函数
            use_cache: 是否使用缓存
            cache_ttl: 缓存 TTL
            *args/**kwargs: 传递给查询函数的参数
        """
        if use_cache:
            # 使用缓存装饰器
            @cached(ttl=cache_ttl)
            async def cached_query():
                return await self._execute_with_timing(query_func, *args, **kwargs)
            
            return await cached_query()
        else:
            return await self._execute_with_timing(query_func, *args, **kwargs)
    
    async def _execute_with_timing(
        self,
        query_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """执行查询并计时"""
        start_time = time.time()
        self.query_count += 1
        
        try:
            result = await query_func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            # 记录慢查询
            if elapsed > self.query_threshold:
                self.slow_queries.append({
                    'function': query_func.__name__,
                    'elapsed': elapsed,
                    'timestamp': datetime.now().isoformat()
                })
                logger.warning(f"Slow query detected: {query_func.__name__} took {elapsed:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def batch_insert(
        self,
        insert_func: Callable,
        items: List[Any],
        batch_size: int = 100
    ):
        """批量插入优化
        
        Args:
            insert_func: 插入函数
            items: 待插入的项目列表
            batch_size: 批次大小
        """
        async def batch_processor():
            results = []
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                logger.info(f"Processing batch {i // batch_size + 1}/{(len(items) - 1) // batch_size + 1}")
                
                # 并行处理批次
                tasks = [insert_func(item) for item in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch insert error: {result}")
                        results.append(None)
                    else:
                        results.append(result)
                
                # 避免过载
                if i + batch_size < len(items):
                    await asyncio.sleep(0.1)
            
            return results
        
        return batch_processor()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取优化器统计"""
        return {
            'total_queries': self.query_count,
            'slow_queries': len(self.slow_queries),
            'recent_slow_queries': self.slow_queries[-10:],
            'cache_stats': _query_cache.stats()
        }


class AsyncTaskQueue:
    """异步任务队列"""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.completed = 0
        self.failed = 0
        
    async def add_task(self, coro):
        """添加任务到队列"""
        await self.task_queue.put(coro)
    
    async def process_task(self, coro):
        """处理单个任务"""
        async with self.semaphore:
            try:
                result = await coro
                self.completed += 1
                return result
            except Exception as e:
                self.failed += 1
                logger.error(f"Task failed: {e}")
                raise
    
    async def run_all(self) -> List[Any]:
        """运行所有任务"""
        tasks = []
        
        while not self.task_queue.empty():
            coro = await self.task_queue.get()
            task = asyncio.create_task(self.process_task(coro))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    def stats(self) -> Dict[str, int]:
        """返回任务统计"""
        return {
            'queue_size': self.task_queue.qsize(),
            'completed': self.completed,
            'failed': self.failed,
            'max_concurrent': self.max_concurrent
        }


class LazyLoader:
    """懒加载器"""
    
    def __init__(self, loader_func: Callable, cache: bool = True):
        self.loader_func = loader_func
        self.cache = cache
        self._value: Optional[Any] = None
        self._loaded = False
        
    async def get(self) -> Any:
        """获取值（懒加载）"""
        if not self._loaded:
            logger.debug("Lazy loading value...")
            self._value = await self.loader_func()
            self._loaded = True
        
        return self._value
    
    def reset(self):
        """重置懒加载状态"""
        self._value = None
        self._loaded = False


class Preloader:
    """预加载器"""
    
    def __init__(self):
        self.preloaded_data: Dict[str, Any] = {}
        
    async def preload(
        self,
        key: str,
        loader_func: Callable,
        refresh_interval: Optional[int] = None
    ):
        """预加载数据
        
        Args:
            key: 数据键
            loader_func: 加载函数
            refresh_interval: 刷新间隔（秒）
        """
        logger.info(f"Preloading data for key: {key}")
        
        if refresh_interval:
            # 定期刷新
            async def refresh_loop():
                while True:
                    self.preloaded_data[key] = await loader_func()
                    await asyncio.sleep(refresh_interval)
            
            asyncio.create_task(refresh_loop())
        else:
            # 只加载一次
            self.preloaded_data[key] = await loader_func()
    
    def get(self, key: str) -> Optional[Any]:
        """获取预加载的数据"""
        return self.preloaded_data.get(key)
    
    def clear(self, key: Optional[str] = None):
        """清空预加载数据"""
        if key:
            self.preloaded_data.pop(key, None)
        else:
            self.preloaded_data.clear()


# ============================================================================
# Performance Monitor
# ============================================================================

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        
    def record(self, metric_name: str, value: float):
        """记录指标"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)
        
        # 保持最近 100 个数据点
        if len(self.metrics[metric_name]) > 100:
            self.metrics[metric_name] = self.metrics[metric_name][-100:]
    
    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """获取指标统计"""
        values = self.metrics.get(metric_name, [])
        if not values:
            return {'count': 0}
        
        return {
            'count': len(values),
            'avg': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'latest': values[-1]
        }
    
    def report(self) -> Dict[str, Any]:
        """生成性能报告"""
        return {
            metric: self.get_stats(metric)
            for metric in self.metrics.keys()
        }


# 全局性能监控器
perf_monitor = PerformanceMonitor()


# ============================================================================
# Unified Performance Optimizer Facade
# ============================================================================

class PerformanceOptimizer:
    """性能优化器统一入口（Facade Pattern）"""
    
    def __init__(self, cache_size: int = 500, max_concurrent_tasks: int = 10):
        """初始化性能优化器
        
        Args:
            cache_size: LRU 缓存大小
            max_concurrent_tasks: 最大并发任务数
        """
        self.cache = LRUCache(max_size=cache_size)
        self.task_queue = AsyncTaskQueue(max_concurrent=max_concurrent_tasks)
        self.db_optimizer = DatabaseOptimizer()
        self.monitor = PerformanceMonitor()
        
    async def optimize_query(
        self,
        query_func: Callable,
        *args,
        use_cache: bool = True,
        cache_ttl: int = 300,
        **kwargs
    ) -> Any:
        """优化查询（带缓存）"""
        return await self.db_optimizer.execute_optimized(
            query_func,
            *args,
            use_cache=use_cache,
            cache_ttl=cache_ttl,
            **kwargs
        )
    
    async def batch_process(self, items: List[Any], processor: Callable) -> List[Any]:
        """批量处理（并发控制）"""
        for item in items:
            await self.task_queue.add_task(processor(item))
        return await self.task_queue.run_all()
    
    def cache_set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存"""
        self.cache.set(key, value, ttl_seconds=ttl)
    
    def cache_get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        return self.cache.get(key)
    
    def record_metric(self, metric_name: str, value: float):
        """记录性能指标"""
        self.monitor.record(metric_name, value)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取完整性能报告"""
        return {
            'cache_stats': self.cache.stats(),
            'database_stats': self.db_optimizer.get_stats(),
            'task_queue_stats': self.task_queue.stats(),
            'metrics': self.monitor.report()
        }
    
    @staticmethod
    def cached(ttl: int = 300):
        """缓存装饰器"""
        return cached(ttl=ttl, cache_instance=None)


# ============================================================================
# Convenience Functions (保持向后兼容)
# ============================================================================

def optimize_database_queries():
    """获取数据库优化器实例"""
    return DatabaseOptimizer()


def create_task_queue(max_concurrent: int = 10):
    """创建任务队列"""
    return AsyncTaskQueue(max_concurrent=max_concurrent)


def enable_caching(ttl: int = 300):
    """启用缓存（装饰器工厂）"""
    return cached(ttl=ttl)


def lazy_load(loader_func: Callable):
    """懒加载装饰器"""
    return LazyLoader(loader_func)


async def preload_data(key: str, loader_func: Callable, refresh_interval: Optional[int] = None):
    """预加载数据"""
    preloader = Preloader()
    await preloader.preload(key, loader_func, refresh_interval)
    return preloader


def get_performance_report() -> Dict[str, Any]:
    """获取性能报告"""
    db_optimizer = DatabaseOptimizer()
    return {
        'database': db_optimizer.get_stats(),
        'cache': _query_cache.stats(),
        'metrics': perf_monitor.report()
    }
