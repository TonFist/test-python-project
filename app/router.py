import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


class Request:
    def __init__(self, handler: BaseHTTPRequestHandler):
        self.method = handler.command
        self.raw_path = handler.path
        parsed = urlparse(handler.path)
        self.path = parsed.path
        self.query = {k: v for k, v in parse_qs(parsed.query).items()}
        self.headers = handler.headers
        length = int(handler.headers.get("Content-Length", 0))
        self.body = handler.rfile.read(length) if length > 0 else b""

    def with_path(self, path: str) -> "Request":
        clone = Request.__new__(Request)
        clone.method = self.method
        clone.raw_path = self.raw_path
        clone.path = path
        clone.query = self.query
        clone.headers = self.headers
        clone.body = self.body
        return clone


class Response:
    def __init__(self, status: int, body: bytes, headers: dict[str, str] | None = None):
        self.status = status
        self.body = body
        self.headers = headers or {}

    @staticmethod
    def text(text: str, status: int = HTTPStatus.OK) -> "Response":
        return Response(int(status), text.encode("utf-8"), {"Content-Type": "text/plain; charset=utf-8"})

    @staticmethod
    def json(data: object, status: int = HTTPStatus.OK) -> "Response":
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        return Response(int(status), payload, {"Content-Type": "application/json; charset=utf-8"})

    @staticmethod
    def bytes(body: bytes, status: int = HTTPStatus.OK, content_type: str = "application/octet-stream") -> "Response":
        return Response(int(status), body, {"Content-Type": content_type})


class Router:
    def __init__(self):
        self._routes: dict[tuple[str, str], callable] = {}
        self._mounts: list[tuple[str, "Router"]] = []
        self._static_dir: Path | None = None
        self._static_url_prefix = "/static"

    def add(self, method: str, path: str, handler):
        key = (method.upper(), path)
        self._routes[key] = handler

    def get(self, path: str):
        def decorator(handler):
            self.add("GET", path, handler)
            return handler

        return decorator

    def post(self, path: str):
        def decorator(handler):
            self.add("POST", path, handler)
            return handler

        return decorator

    def mount(self, prefix: str, router: "Router") -> None:
        if not prefix.startswith("/"):
            prefix = "/" + prefix
        if prefix != "/" and prefix.endswith("/"):
            prefix = prefix.rstrip("/")
        self._mounts.append((prefix, router))

    def enable_static(self, directory: str | Path, url_prefix: str = "/static") -> None:
        if not url_prefix.startswith("/"):
            url_prefix = "/" + url_prefix
        if url_prefix != "/" and url_prefix.endswith("/"):
            url_prefix = url_prefix.rstrip("/")
        self._static_dir = Path(directory)
        self._static_url_prefix = url_prefix

    def dispatch(self, request: Request) -> Response:
        route = self._routes.get((request.method, request.path))
        if route is not None:
            return route(request)

        for prefix, router in self._mounts:
            if prefix == "/":
                sub_path = request.path
            elif request.path == prefix:
                sub_path = "/"
            elif request.path.startswith(prefix + "/"):
                sub_path = request.path[len(prefix):]
            else:
                continue
            return router.dispatch(request.with_path(sub_path))

        static_response = self._try_static(request)
        if static_response is not None:
            return static_response

        return Response.text("Not found", status=HTTPStatus.NOT_FOUND)

    def _try_static(self, request: Request) -> Response | None:
        if self._static_dir is None:
            return None
        if request.method != "GET":
            return None
        if not request.path.startswith(self._static_url_prefix + "/"):
            return None

        rel_path = unquote(request.path[len(self._static_url_prefix):]).lstrip("/")
        if rel_path == "":
            rel_path = "index.html"

        base_dir = self._static_dir.resolve()
        target = (base_dir / rel_path).resolve()
        if not str(target).startswith(str(base_dir)):
            return Response.text("Forbidden", status=HTTPStatus.FORBIDDEN)
        if not target.exists() or not target.is_file():
            return Response.text("Not found", status=HTTPStatus.NOT_FOUND)

        content_type, _ = mimetypes.guess_type(target.name)
        body = target.read_bytes()
        return Response.bytes(body, content_type=content_type or "application/octet-stream")

    def handle(self, handler: BaseHTTPRequestHandler):
        request = Request(handler)
        response = self.dispatch(request)

        handler.send_response(response.status)
        for key, value in response.headers.items():
            handler.send_header(key, value)
        handler.send_header("Content-Length", str(len(response.body)))
        handler.end_headers()
        handler.wfile.write(response.body)


def make_handler(router: Router):
    class RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            router.handle(self)

        def do_POST(self):
            router.handle(self)

        def log_message(self, format, *args):
            return

    return RequestHandler
