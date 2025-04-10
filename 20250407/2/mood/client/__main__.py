"""Точка входа для запуска клиента MOOD."""

import argparse
import sys
from ..common import constants as const
from ..client.game_client import start_client


def parse_args():
    """
    Разобрать аргументы командной строки.

    Returns:
        argparse.Namespace: Аргументы командной строки.
    """
    parser = argparse.ArgumentParser(description='MOOD Client')
    parser.add_argument(
        'username',
        type=str,
        help='Your username for the game'
    )
    parser.add_argument(
        '--host',
        type=str,
        default=const.DEFAULT_HOST,
        help=f'Server host (default: {const.DEFAULT_HOST})'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=const.DEFAULT_PORT,
        help=f'Server port (default: {const.DEFAULT_PORT})'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Path to a command file (.mood) to execute'
    )
    return parser.parse_args()


def main():
    """Основная функция запуска клиента."""
    args = parse_args()
    try:
        start_client(args.host, args.port, args.username, args.file)
    except KeyboardInterrupt:
        print("\nExiting game...")
        sys.exit(0)


if __name__ == "__main__":
    main()