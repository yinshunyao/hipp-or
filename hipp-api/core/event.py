#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2022/3/21 11:03 
# @File           : event.py
# @IDE            : PyCharm
# @desc           : 全局事件


from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from application.settings import REDIS_DB_URL, MONGO_DB_URL, MONGO_DB_NAME, EVENTS
from utils.cache import Cache
from redis import asyncio as aioredis
from redis.exceptions import AuthenticationError, TimeoutError, RedisError
from contextlib import asynccontextmanager
from utils.tools import import_modules_async
from sqlalchemy.exc import ProgrammingError
from core.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):

    await import_modules_async(EVENTS, "全局事件", app=app, status=True)

    yield

    await import_modules_async(EVENTS, "全局事件", app=app, status=False)


async def connect_redis(app: FastAPI, status: bool):
    """
    把 redis 挂载到 app 对象上面

    博客：https://blog.csdn.net/wgPython/article/details/107668521
    博客：https://www.cnblogs.com/emunshe/p/15761597.html
    官网：https://aioredis.readthedocs.io/en/latest/getting-started/
    Github: https://github.com/aio-libs/aioredis-py

    aioredis.from_url(url, *, encoding=None, parser=None, decode_responses=False, db=None, password=None, ssl=None,
    connection_cls=None, loop=None, **kwargs) 方法是 aioredis 库中用于从 Redis 连接 URL 创建 Redis 连接对象的方法。

    以下是该方法的参数说明：
    url：Redis 连接 URL。例如 redis://localhost:6379/0。
    encoding：可选参数，Redis 编码格式。默认为 utf-8。
    parser：可选参数，Redis 数据解析器。默认为 None，表示使用默认解析器。
    decode_responses：可选参数，是否将 Redis 响应解码为 Python 字符串。默认为 False。
    db：可选参数，Redis 数据库编号。默认为 None。
    password：可选参数，Redis 认证密码。默认为 None，表示无需认证。
    ssl：可选参数，是否使用 SSL/TLS 加密连接。默认为 None。
    connection_cls：可选参数，Redis 连接类。默认为 None，表示使用默认连接类。
    loop：可选参数，用于创建连接对象的事件循环。默认为 None，表示使用默认事件循环。
    **kwargs：可选参数，其他连接参数，用于传递给 Redis 连接类的构造函数。

    aioredis.from_url() 方法的主要作用是将 Redis 连接 URL 转换为 Redis 连接对象。
    除了 URL 参数外，其他参数用于指定 Redis 连接的各种选项，例如 Redis 数据库编号、密码、SSL/TLS 加密等等。可以根据需要选择使用这些选项。

    health_check_interval 是 aioredis.from_url() 方法中的一个可选参数，用于设置 Redis 连接的健康检查间隔时间。
    健康检查是指在 Redis 连接池中使用的连接对象会定期向 Redis 服务器发送 PING 命令来检查连接是否仍然有效。
    该参数的默认值是 0，表示不进行健康检查。如果需要启用健康检查，则可以将该参数设置为一个正整数，表示检查间隔的秒数。
    例如，如果需要每隔 5 秒对 Redis 连接进行一次健康检查，则可以将 health_check_interval 设置为 5
    :param app:
    :param status:
    :return:
    """
    if status:
        rd = aioredis.from_url(REDIS_DB_URL, decode_responses=True, health_check_interval=1)
        app.state.redis = rd
        try:
            response = await rd.ping()
            if response:
                print("Redis 连接成功")
            else:
                print("Redis 连接失败")
        except AuthenticationError as e:
            raise AuthenticationError(f"Redis 连接认证失败，用户名或密码错误: {e}")
        except TimeoutError as e:
            raise TimeoutError(f"Redis 连接超时，地址或者端口错误: {e}")
        except RedisError as e:
            raise RedisError(f"Redis 连接失败: {e}")
        try:
            await Cache(app.state.redis).cache_tab_names()
        except ProgrammingError as e:
            logger.error(f"sqlalchemy.exc.ProgrammingError: {e}")
            print(f"sqlalchemy.exc.ProgrammingError: {e}")
    else:
        print("Redis 连接关闭")
        await app.state.redis.close()


async def start_media_orphan_gc(app: FastAPI, status: bool):
    """
    每日 Asia/Shanghai 指定整点清理平台 chat 孤儿媒体（上传未发送且超宽限期）。
    依赖 Redis 日锁；无 Redis 时仍跑，但多 worker 可能重复扫（删已不存在视为成功）。
    """
    import asyncio
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    from application import settings

    tz = ZoneInfo("Asia/Shanghai")

    async def _try_lock(day_key: str) -> bool:
        rd = getattr(app.state, "redis", None)
        if rd is None:
            return True
        try:
            # 锁约 26h，避免同日重复
            ok = await rd.set(f"or:media_orphan_gc:{day_key}", "1", nx=True, ex=26 * 3600)
            return bool(ok)
        except Exception:
            logger.exception("media orphan gc redis lock failed")
            return False

    async def _loop() -> None:
        hour = int(getattr(settings, "MEDIA_ORPHAN_GC_HOUR", 3) or 3)
        hour = min(23, max(0, hour))
        min_age = int(getattr(settings, "MEDIA_ORPHAN_GC_MIN_AGE_HOURS", 24) or 24)
        while True:
            try:
                now = datetime.now(tz)
                target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                if now >= target:
                    target = target + timedelta(days=1)
                wait_s = max(5.0, (target - now).total_seconds())
                await asyncio.sleep(wait_s)
                day_key = datetime.now(tz).strftime("%Y%m%d")
                if not await _try_lock(day_key):
                    logger.info("media orphan gc skip: lock held day=%s", day_key)
                    await asyncio.sleep(60)
                    continue
                from apps.mp_chat.media_cleanup import run_orphan_media_gc

                await run_orphan_media_gc(min_age_hours=min_age)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("media orphan gc loop error")
                await asyncio.sleep(60)

    if status:
        app.state.media_orphan_gc_task = asyncio.create_task(_loop())
        print(
            f"媒体孤儿 GC 已启动：每日 {getattr(settings, 'MEDIA_ORPHAN_GC_HOUR', 3)}:00 "
            f"(Asia/Shanghai)，宽限期 {getattr(settings, 'MEDIA_ORPHAN_GC_MIN_AGE_HOURS', 24)}h"
        )
    else:
        task = getattr(app.state, "media_orphan_gc_task", None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass
        print("媒体孤儿 GC 已停止")


async def connect_mongo(app: FastAPI, status: bool):
    """
    把 mongo 挂载到 app 对象上面

    博客：https://www.cnblogs.com/aduner/p/13532504.html
    mongodb 官网：https://www.mongodb.com/docs/drivers/motor/
    motor 文档：https://motor.readthedocs.io/en/stable/
    :param app:
    :param status:
    :return:
    """
    if status:
        client: AsyncIOMotorClient = AsyncIOMotorClient(
            MONGO_DB_URL,
            maxPoolSize=10,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000
        )
        app.state.mongo_client = client
        app.state.mongo = client[MONGO_DB_NAME]
        # 尝试连接并捕获可能的超时异常
        try:
            # 触发一次服务器通信来确认连接
            data = await client.server_info()
            print("MongoDB 连接成功", data)
        except Exception as e:
            raise ValueError(f"MongoDB 连接失败: {e}")
    else:
        print("MongoDB 连接关闭")
        app.state.mongo_client.close()
