#20251203 新增连接池功能，先开一个文件便于后续网络拓展
#
#todo 按照chatgpt说的把连接池按照生命周期搭建一下
#20251216 事实证明千问的写法最好，避免循环依赖也避免全局函数访问冲突，真的棒！

import httpx
from fastapi import Request
from typing import AsyncGenerator

class HTTPClientProvider:
    #精简实用的HTTP客户端提供者
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._global_client = None  # 全局客户端
    
    async def init(self):
        #初始化全局客户端（应用启动时调用）
        self._global_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=50.0,
            limits=httpx.Limits() # 配置连接池大小,用默认就行主要参数有max_connections，max_keepalive_connections
        )
    
    async def close(self):
        #关闭客户端（应用关闭时调用）
        if self._global_client:
            await self._global_client.aclose()
            
    
    
    # 核心！一个依赖函数解决所有场景
    async def dependency(self, request: Request = None) -> AsyncGenerator[httpx.AsyncClient, None]:
        # 智能依赖函数：
        # - 有request：使用全局客户端（99%场景）
        # - 无request：也使用全局客户端（后台任务等）
        yield self._global_client
        
        
    #加一个属性值（加鲁棒性用）
    @property
    def client(self) -> httpx.AsyncClient:
        if self._global_client is None:
            raise RuntimeError("HTTPClientProvider 未初始化：请在 startup 里 await init()")
        return self._global_client    

# 创建实例,到时候各个地方复用就行 
http_client = HTTPClientProvider("http://127.0.0.1:2077")















#############  
# 公司服务器： 暴露端口 
# 内  2041  2042  2043  2044  2045
# 外  2031  2032  2033  2034  2035
#############

##########
#mqtt 配置文件（已废弃）
##########
# -p <宿主机端口>:<容器内部端口>

# docker run -d --name emqx  -p 2041:1883         -p 2042:8883                   -p 2043:8083                             -p 2044:8084                -p 2045:18083                          emqx/emqx:5.8.6
#                          标准MQTT的TCP端口   MQTT over TLS（加密）的标准端口    MQTT over WebSocket（WS）的端口。   MQTT over WebSocket + TLS（WSS）   EMQX Dashboard（可视化管理界面）的 HTTP 端口。