import threading


class Subscriber:
    """Handles adding and removing new node ips"""

    def __init__(self):
        self._known_ips: set[str] = set()
        self._known_ips_lock = threading.Lock()

    def add_ip(self, ip: str):
        with self._known_ips_lock:
            self._known_ips.add(ip)

    def remove_ip(self, ip: str):
        with self._known_ips_lock:
            self._known_ips.discard(ip)
