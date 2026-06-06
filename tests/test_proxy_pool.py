from ytgrid.proxy.models import Proxy, ProxyHealth
from ytgrid.proxy.pool import ProxyPool


def _p(host="1.2.3.4", port=8080, **kw):
    return Proxy(host=host, port=port, **kw)


def test_proxy_url_and_failure_rate():
    p = _p(username="u", password="pw")
    assert p.url == "http://u:pw@1.2.3.4:8080"
    assert p.extension_url == "http://1.2.3.4:8080"
    assert p.failure_rate == 0.0
    p.success_count = 3
    p.failure_count = 1
    assert p.failure_rate == 0.25


def test_empty_pool_returns_none():
    assert ProxyPool([]).get_proxy() is None


def test_get_proxy_marks_usage():
    pool = ProxyPool([_p(port=1), _p(port=2)])
    selected = pool.get_proxy()
    assert selected is not None
    assert selected.last_used is not None
    assert selected.cooldown_until is not None


def test_add_proxies_dedup():
    pool = ProxyPool([_p(port=1)])
    added = pool.add_proxies([_p(port=1), _p(port=2)])
    assert added == 1
    assert pool.stats["total"] == 2


def test_report_failure_marks_unhealthy():
    p = _p()
    pool = ProxyPool([p])
    pool.report_failure(p)
    # A single failure pushes failure_rate (1.0) past the 0.3 threshold.
    assert p.health == ProxyHealth.UNHEALTHY


def test_report_none_is_safe():
    pool = ProxyPool([])
    pool.report_success(None)
    pool.report_failure(None)


def test_only_unhealthy_returns_none():
    pool = ProxyPool([_p(port=1, health=ProxyHealth.UNHEALTHY)])
    assert pool.get_proxy() is None


def test_stats_counts():
    pool = ProxyPool([
        _p(port=1, health=ProxyHealth.HEALTHY),
        _p(port=2, health=ProxyHealth.DEGRADED),
        _p(port=3, health=ProxyHealth.UNHEALTHY),
    ])
    stats = pool.stats
    assert stats["total"] == 3
    assert stats["healthy"] == 1
    assert stats["degraded"] == 1
    assert stats["unhealthy"] == 1
