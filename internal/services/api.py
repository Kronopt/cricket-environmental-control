from http import HTTPStatus
from nicegui import app
from starlette.responses import Response


class API:
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

    def notify(self, ip: str) -> None:
        self.known_ips.add(ip)
