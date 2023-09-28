import logging
import socket
import threading
import time
from dataclasses import dataclass
from . import configurations
from . import subscriber


@dataclass
class Node:
    ip: str
    failed_pings: int = 0

    def __hash__(self):
        return hash(self.ip)

    def __eq__(self, __value) -> bool:
        if isinstance(__value, Node):
            return self.ip == __value.ip
        return False


class Discovery:
    """Handles discovery of other environmental control nodes in the network"""

    def __init__(self, configs: configurations.Configurations):
        self._logger = logging.getLogger("services." + self.__class__.__name__)

        broadcast_port = configs["discovery"].getint("port")
        self.broadcast_address = ("255.255.255.255", broadcast_port)
        self.is_broadcasting = False
        self.is_broadcasting_lock = threading.Lock()

        self.ping_port = 9433

        self.message = "environmental_control_node_broadcast"
        self.response = "environmental_control_node_ok"
        self.ping_message = "p!ng"
        self.ping_response = "p0ng"
        self.message_size = len(self.message.encode("utf8"))
        self.response_size = len(self.response.encode("utf8"))
        self.ping_message_size = len(self.ping_message.encode("utf8"))
        self.ping_response_size = len(self.ping_response.encode("utf8"))

        self.nodes: set[Node] = set()
        self.nodes_lock = threading.Lock()

        self.subscribers: set[subscriber.Subscriber] = set()

        # IPv4 (AF_INET) UDP (SOCK_DGRAM) connections
        self.broadcast_listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ping_listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ping_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.know_self_ip_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # listen for a connection from any host on the defined port
        self.broadcast_listen_socket.bind(("", broadcast_port))
        self.ping_listen_socket.bind(("", self.ping_port))

        # allow socket to be reused (ex: on restart) and allow broadcast usage
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # set socket timeouts
        self.broadcast_socket.settimeout(5)
        self.ping_socket.settimeout(5)

    def broadcast_listen(self):
        """listens for broadcasts (ref: https://github.com/jholtmann/ip_discovery)"""
        self._logger.info("listening for broadcasts...")

        while True:
            # blocks while waiting for broadcast
            data, address = self.broadcast_listen_socket.recvfrom(self.message_size)
            if data.decode("utf-8", "replace") == self.message:
                ip = str(address[0])  # socket.AF_INET = (host, port)
                if ip == self.own_ip():
                    continue

                self._logger.info(f"received broadcast from {ip}")
                self.add_node(ip)
                self.broadcast_listen_socket.sendto(self.response.encode(), address)

    def broadcast(self):
        """sends broadcasts with 3 retries (ref: https://github.com/jholtmann/ip_discovery)"""
        with self.is_broadcasting_lock:
            if self.is_broadcasting:
                return
            self.is_broadcasting = True

        tries = 3
        for i in range(tries):
            self._logger.info(f"broadcasting, {i+1}/{tries} tries...")

            try:
                self.broadcast_socket.sendto(
                    self.message.encode(), self.broadcast_address
                )

                while True:
                    # blocks while waiting for response
                    data, address = self.broadcast_socket.recvfrom(self.response_size)
                    if data.decode("utf-8", "replace") == self.response:
                        ip = str(address[0])  # socket.AF_INET = (host, port)
                        if ip == self.own_ip():
                            continue

                        self._logger.info(
                            f"received response to broadcast from {address[0]}"
                        )

                        self.add_node(ip)

            except socket.timeout:
                continue

        with self.is_broadcasting_lock:
            self.is_broadcasting = False

    def ping_listen(self):
        """listens for pings"""
        self._logger.info("listening for pings...")

        while True:
            # blocks while waiting for pings
            data, address = self.ping_listen_socket.recvfrom(self.ping_message_size)
            if data.decode("utf-8", "replace") == self.ping_message:
                ip = str(address[0])  # socket.AF_INET = (host, port)
                if ip == self.own_ip():
                    continue

                self.ping_listen_socket.sendto(self.ping_response.encode(), address)

    def ping(self):
        """
        pings known nodes.
        Sends "ping" packets every 5 seconds.
        A node is considered dead if it fails to respond to 3 consecutive pings"
        """
        self._logger.info("pinging known nodes...")

        while True:
            current_nodes = []
            with self.nodes_lock:
                current_nodes = list(self.nodes)

            if len(current_nodes) > 0:
                for node in current_nodes:
                    try:
                        self.ping_socket.sendto(
                            self.ping_message.encode(), (node.ip, self.ping_port)
                        )

                        # blocks while waiting for response
                        data, address = self.ping_socket.recvfrom(
                            self.ping_response_size
                        )
                        if data.decode("utf-8", "replace") == self.ping_response:
                            ip = str(address[0])  # socket.AF_INET = (host, port)
                            if ip == self.own_ip():
                                continue

                            # node is alive, reset its ping counter
                            with self.nodes_lock:
                                if node in self.nodes:
                                    # replace existing node with the updated one
                                    self.nodes.discard(node)
                                    node.failed_pings = 0
                                    self.nodes.add(node)

                    except socket.timeout:
                        # no response from node, increment counter
                        with self.nodes_lock:
                            if node in self.nodes:
                                # replace existing node with the updated one
                                self.nodes.discard(node)
                                node.failed_pings += 1
                                self.nodes.add(node)

                        # more than 3 consecutive response failures leads to removal of node
                        if node.failed_pings >= 3:
                            self._logger.info(
                                f"node {node.ip} failed 3 consecutive ping attempts. removing node..."
                            )
                            self.remove_node(node.ip)

            time.sleep(5)

    def own_ip(self) -> str:
        # connect() for UDP doesn't send packets
        self.know_self_ip_socket.connect(("8.8.8.8", 1))
        return self.know_self_ip_socket.getsockname()[0]

    def known_nodes(self) -> list[str]:
        with self.nodes_lock:
            return [node.ip for node in self.nodes]

    #
    # subscription methods
    #

    def subscribe(self, *subscribers: subscriber.Subscriber):
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

    def add_node(self, ip: str):
        """adds node ip to known node ips list"""
        notify = False

        node = Node(ip=ip)
        with self.nodes_lock:
            if node not in self.nodes:
                self.nodes.add(node)
                notify = True

        if notify:
            threading.Thread(target=self._notify_new_ip, args=(ip,)).start()

    def remove_node(self, ip: str):
        """removes node ip from known node ips list"""
        notify = False

        node = Node(ip=ip)
        with self.nodes_lock:
            if node in self.nodes:
                self.nodes.discard(node)
                notify = True

        if notify:
            threading.Thread(target=self._notify_remove_ip, args=(ip,)).start()
