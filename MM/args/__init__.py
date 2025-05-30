from dataclasses import dataclass
from argparse import ArgumentParser

@dataclass
class Args:
    cfg_path: str


def parse_args() -> Args:
    parser = ArgumentParser(
        description = "Runs a marketmaking strategy defined by cfg"
    )
    parser.add_argument(
        "--cfg",
        type = str,
        required = True,
        help = "Path to TOML config"
    )
    args = parser.parse_args()
    return Args(cfg_path = args.cfg)