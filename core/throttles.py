from rest_framework.throttling import BaseThrottle
from django.core.cache import cache

class LoginRateLimitThrottle(BaseThrottle):
    cache_format = 'rate-limit:login:%(ident)s'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        if not ident:
            return None
        return self.cache_format % {'ident': ident}

    def allow_request(self, request, view):
        key = self.get_cache_key(request, view)
        if not key:
            return True

        count = cache.get(key, 0)
        return count < 5

    def increment(self, request, view):
        key = self.get_cache_key(request, view)
        if not key:
            return

        if not cache.add(key, 1, timeout=900):
            cache.incr(key)

    def reset(self, request, view):
        key = self.get_cache_key(request, view)
        if key:
            cache.delete(key)

    def wait(self, request, view):
        key = self.get_cache_key(request, view)
        ttl = cache.ttl(key)
        return ttl if ttl is not None else 900
