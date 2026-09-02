"""Command-line entry points."""

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(prog="crawl-skku")
    subparsers = parser.add_subparsers(dest="command", required=True)
    serve = subparsers.add_parser("serve", help="Run the HTTP API server.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()

    if args.command == "serve":
        uvicorn.run("crawl_skku.api:app", host=args.host, port=args.port)
