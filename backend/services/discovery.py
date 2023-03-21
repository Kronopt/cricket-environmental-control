import abc
import socket
import threading
import time
import configparser


class Subscriber:
    @abc.abstractmethod
    def notify(self, ip: str) -> None:
        raise NotImplementedError


class Discovery:
    """Handles discovery of other environmental control nodes in the network"""

    def __init__(self, configs: configparser.ConfigParser):
        port = configs["discovery"].getint("port")

        self.broadcast_address = ("255.255.255.255", port)

        self.message = "environmental_control_node_broadcast"
        self.response = "environmental_control_node_ok"
        self.message_size = len(self.message.encode("utf8"))
        self.response_size = len(self.response.encode("utf8"))

        self.node_ips: set[str] = set()
        self.lock = threading.Lock()

        self.subscribers: set[Subscriber] = set()

        # IPv4 UDP connections
        self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # listen for a connection from any host on the defined port
        self.listening_socket.bind(("", port))

        # allow socket to be reused (ex: on restart) and allow broadcast usage
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.settimeout(5)

    def listen(self):
        """listens for broadcasts (ref: https://github.com/jholtmann/ip_discovery)"""

        while True:
            # blocks while waiting for broadcast
            data, address = self.listening_socket.recvfrom(self.message_size)
            if data.decode("utf-8", "replace") == self.message:
                self.listening_socket.sendto(self.response.encode(), address)

    def broadcast(self):
        """sends broadcasts with 3 retries (ref: https://github.com/jholtmann/ip_discovery)"""

        for _ in range(3):
            try:
                self.broadcast_socket.sendto(
                    self.message.encode(), self.broadcast_address
                )

                while True:
                    # blocks while waiting for response
                    data, address = self.broadcast_socket.recvfrom(self.response_size)
                    if data.decode("utf-8", "replace") == self.response:
                        ip = str(address[0])  # socket.AF_INET = (host, port)
                        with self.lock:
                            if ip not in self.node_ips:
                                self.node_ips.add(ip)
                                self.notify(ip)

            except TimeoutError:
                time.sleep(5)
                continue

    def notify(self, ip: str):
        """notify subscribers of new node ip"""
        for sub in self.subscribers:
            sub.notify(ip)

    def subscribe(self, subscriber: Subscriber):
        """add subscriber"""
        self.subscribers.add(subscriber)

    def remove_ip(self, ip: str):
        """removes ip from known node ips list"""
        self.node_ips.discard(ip)
