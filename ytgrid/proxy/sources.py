import os
from typing import List
from ytgrid.proxy.models import Proxy, ProxyProtocol
from ytgrid.utils.logger import log_error

class ProxySource:
    """Abstract base for proxy providers."""
    def fetch(self) -> List[Proxy]:
        return []

class FileProxySource(ProxySource):
    """Load proxies from a local file (host:port:user:pass or host:port per line)."""
    def __init__(self, filepath: str):
        self.filepath = filepath

    def fetch(self) -> List[Proxy]:
        proxies = []
        if not os.path.exists(self.filepath):
            log_error(f"Proxy file not found: {self.filepath}")
            return proxies

        try:
            with open(self.filepath, 'r') as f:
                lines = f.readlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(':')
                if len(parts) == 2:
                    proxies.append(Proxy(host=parts[0], port=int(parts[1])))
                elif len(parts) == 4:
                    proxies.append(Proxy(host=parts[0], port=int(parts[1]), username=parts[2], password=parts[3]))
        except Exception as e:
            log_error(f"Failed to load proxies from {self.filepath}: {e}")

        return proxies

class EnvProxySource(ProxySource):
    """Load proxies from YTGRID_PROXY_LIST environment variable."""
    def fetch(self) -> List[Proxy]:
        proxies = []
        val = os.getenv("YTGRID_PROXY_LIST", "")
        if not val:
            return proxies
        for line in val.split(','):
            parts = line.strip().split(':')
            if len(parts) == 2:
                proxies.append(Proxy(host=parts[0], port=int(parts[1])))
            elif len(parts) == 4:
                proxies.append(Proxy(host=parts[0], port=int(parts[1]), username=parts[2], password=parts[3]))
        return proxies

class APIProxySource(ProxySource):
    """Fetch proxies from a paid provider API."""
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key

    def fetch(self) -> List[Proxy]:
        # Implement provider-specific API logic
        return []
