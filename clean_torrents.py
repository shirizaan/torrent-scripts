#! /usr/bin/env python3

"""
A simple script to log into a qbittorrent client and clean up completed torrents.
"""

from dataclasses import dataclass
import logging

from configparser import ConfigParser, NoOptionError, NoSectionError
import string
from qbittorrent import Client
from pathlib import Path
from requests.exceptions import InvalidSchema

# Set up logging

logging.basicConfig(level=logging.INFO)

# Set up config

config_file = Path(Path(__file__).stem + ".conf")

logging.debug(__file__)
logging.debug(config_file)

config_opts = ConfigParser()

# Check if config file exists.

if not config_file.is_file():
    logging.error("Config file not found. Exiting.")
    exit(1)

logging.info("Digesting config file.")


@dataclass
class Category:
    _name: str
    _ratio: float
    _status: str
    _action: str

    @property
    def name(self) -> str:
        return self._name

    @property
    def ratio(self) -> float:
        return self._ratio

    @ratio.setter
    def ratio(self, value: str):
        self._ratio = float(value)

    @property
    def status(self) -> str:
        return self._status

    @property
    def action(self):
        return getattr(Client, self._action)

    @action.setter
    def action(self, value):
        if value in ["delete", "pause", "delete_permanently"]:
            self._action = value
        else:
            raise ValueError("Invalid action.")


def is_complete(torrent) -> bool:
    # Check if torrent is complete and return boolean
    return int(torrent["amount_left"]) == 0


def get_ratio(torrent) -> float:
    # Get ratio of torrent and return float
    return float(torrent["ratio"])


config_opts.read(config_file)

categories = []


for element in config_opts.sections():
    if element == "qbittorrent":
        qb_host = config_opts.get(element, "host")
        qb_user = config_opts.get(element, "user")
        qb_pass = config_opts.get(element, "pass")
    else:
        categories.append(
            Category(
                element,
                float(config_opts.get(element, "ratio")),
                config_opts.get(element, "status"),
                config_opts.get(element, "action"),
            )
        )

qb = Client(qb_host)

# Login to qbittorrent client
try:
    qb.login(qb_user, qb_pass)
except InvalidSchema:
    logging.error(
        "Invalid hostname or port. Did you forget to include http://? or use quotes?"
    )
    exit(1)

# Process categories

for category in categories:
    torrents = qb.torrents(category=category.name, filter=category.status)

    for torrent in torrents:
        if is_complete(torrent):
            if get_ratio(torrent) >= category.ratio:
                logging.info(f"Actioning {torrent['name']}")
                category.action(qb, torrent["hash"])

try:
    qb.logout()
except:
    # If session is invalid, do nothing.
    pass
