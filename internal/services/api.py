from http import HTTPStatus
from nicegui import app
from starlette.responses import Response
from discovery import Subscriber


class API(Subscriber):
    """API to interact with sensors, actuators, configs, etc"""

    def __init__(self):
        super().__init__()
        self.base_url = "/api/"
        self.known_ips = set()

        @app.middleware("http")
        async def verify_request_origin(request, call_next):
            if (
                request.url.path.startswith(self.base_url)
                and request.client.host not in self.known_ips
            ):
                return Response(status_code=HTTPStatus.UNAUTHORIZED)

            response = await call_next(request)
            return response

        @app.get(self.base_url + "_/health", status_code=HTTPStatus.OK)
        def health():
            pass

        # TODO more endpoints
        # TODO for endpoints that MODIFY data, should verify

    # subscription methods

    def add_ip(self, ip: str):
        self.known_ips.add(ip)

    def remove_ip(self, ip: str):
        self.known_ips.discard(ip)
