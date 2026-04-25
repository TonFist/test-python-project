import argparse
import socketserver
import sys
from pathlib import Path

from app.router import make_handler
from app.routes import router


def run_cli() -> int:
    print("Hello from main.py")
    return 0


def run_dev_server(port: int) -> int:
    static_dir = Path(__file__).parent / "static"
    router.enable_static(static_dir, url_prefix="/static")
    handler = make_handler(router)
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving on http://localhost:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Simple Python starter")
    parser.add_argument("--serve", action="store_true", help="Run a basic dev server")
    parser.add_argument("--port", type=int, default=8000, help="Port for --serve")
    args = parser.parse_args(argv)

    if args.serve:
        return run_dev_server(args.port)

    return run_cli()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
