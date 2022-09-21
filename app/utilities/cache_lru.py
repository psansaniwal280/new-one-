from collections import OrderedDict

class LRUCache():
    def __init__(self, a):
        self._cache = OrderedDict()
        self._capacity = a
    # def __init__(self, cache: LRUCache()):
    #     self._cache=cache
    #     self._capacity = cache.capacity

    def get(self, key):
        if key not in self._cache:
            return -1
        value = self._cache.pop(key)
        self._cache[key] = value
        return value

    def put(self, key, value):
        if key in self._cache:
            self._cache.pop(key)
        elif len(self._cache) >= self._capacity:
            self._cache.popitem(last=False)
        self._cache[key] = value

    def delete(self, key):
        if key in self._cache:
            self._cache.pop(key)
        return self

    def getAll(self):
        if self._cache:
            # print(list(self._cache.items()))
            return list(self._cache.items())
        