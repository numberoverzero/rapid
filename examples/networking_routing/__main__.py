import sys
from examples.networking_routing import client


def main(mode: str, host: str) -> None:
    if mode == "client":
        client.main(host)
    else:
        raise ValueError(f"Unknown mode {mode}")


main(mode=sys.argv[1], host=sys.argv[2])
