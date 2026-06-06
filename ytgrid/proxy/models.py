from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional

class ProxyProtocol(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"

class ProxyHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"       # Latency > threshold but functional
    UNHEALTHY = "unhealthy"     # Failed health check
    COOLDOWN = "cooldown"       # Recently used, resting to avoid detection

@dataclass
class Proxy:
    host: str
    port: int
    protocol: ProxyProtocol = ProxyProtocol.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    health: ProxyHealth = ProxyHealth.HEALTHY
    latency_ms: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None
    country: Optional[str] = None

    @property
    def url(self) -> str:
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"{self.protocol.value}://{auth}{self.host}:{self.port}"

    @property
    def extension_url(self) -> str:
        return f"{self.protocol.value}://{self.host}:{self.port}"

    @property
    def failure_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.failure_count / total if total > 0 else 0.0
