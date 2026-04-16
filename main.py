import argparse
import http.server
import socketserver
import sys


def run_cli() -> int:
    print("Hello from main.py")
    return 0


def run_dev_server(port: int) -> int:
    handler = http.server.SimpleHTTPRequestHandler
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
