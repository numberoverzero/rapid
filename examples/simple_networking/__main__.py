import sys
from examples.simple_networking import client, server


def main(mode: str, host: str) -> None:
    if mode == "client":
        client.main(host)
    elif mode == "server":
        server.main(host)
    else:
        raise ValueError(f"Unknown mode {mode}")


main(mode=sys.argv[1], host=sys.argv[2])
