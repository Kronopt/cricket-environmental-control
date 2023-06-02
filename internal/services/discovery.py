import abc
import logging
import socket
import threading
import configparser
from .subscriber import Subscriber


class Discovery:
    """Handles discovery of other environmental control nodes in the network"""

    def __init__(self, configs: configparser.ConfigParser):
        self.logger = logging.getLogger(self.__class__.__name__)

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

        self.logger.info("listening for broadcasts...")

        while True:
            # blocks while waiting for broadcast
            data, address = self.listening_socket.recvfrom(self.message_size)
            if data.decode("utf-8", "replace") == self.message:
                ip = str(address[0])  # socket.AF_INET = (host, port)

                self.logger.info("received broadcast from: %s", ip)
                self.listening_socket.sendto(self.response.encode(), address)

                self.add_ip(ip)

    def broadcast(self):
        """sends broadcasts with 3 retries (ref: https://github.com/jholtmann/ip_discovery)"""

        self.logger.info("broadcasting...")

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
                                self.logger.info(
                                    "received response to broadcast from: %s",
                                    address[0],
                                )

                                self.add_ip(ip)

            except socket.timeout:
                continue

    # subscription methods

    def subscribe(self, *subscribers: Subscriber):
        """add subscribers"""
        self.subscribers.update(subscribers)

    def _notify_new_ip(self, ip: str):
        """notify subscribers of new node ip"""
        for sub in self.subscribers:
            sub.add_ip(ip)

    def _notify_remove_ip(self, ip: str):
        """notify subscribers of removed node ip"""
        for sub in self.subscribers:
            sub.remove_ip(ip)

    def add_ip(self, ip: str):
        """adds ip to known node ips list"""
        self.node_ips.add(ip)
        self._notify_new_ip(ip)

    def remove_ip(self, ip: str):
        """removes ip from known node ips list"""
        self.node_ips.discard(ip)
        self._notify_remove_ip(ip)
