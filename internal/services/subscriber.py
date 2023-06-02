class Subscriber:
    """Handles adding and removing new node ips"""

    def __init__(self):
        self.known_ips = set()

    def add_ip(self, ip: str):
        self.known_ips.add(ip)

    def remove_ip(self, ip: str):
        self.known_ips.discard(ip)
