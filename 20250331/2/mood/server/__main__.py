"""Точка входа для запуска сервера MOOD."""

import asyncio
import argparse
from ..common import constants as const
from ..server.game_server import run_server


def parse_args():
    """Разобрать аргументы командной строки.

    Returns:
        argparse.Namespace: Аргументы командной строки.
    """
    parser = argparse.ArgumentParser(description='MOOD Server')
    parser.add_argument(
        '--host',
        type=str,
        default=const.DEFAULT_HOST,
        help=f'Host to bind (default: {const.DEFAULT_HOST})'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=const.DEFAULT_PORT,
        help=f'Port to bind (default: {const.DEFAULT_PORT})'
    )
    return parser.parse_args()


def main():
    """Основная функция запуска сервера."""
    args = parse_args()
    try:
        asyncio.run(run_server(args.host, args.port))
    except KeyboardInterrupt:
        print("\nServer shutting down...")


if __name__ == "__main__":
    main()