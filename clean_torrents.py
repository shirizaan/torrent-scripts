#! /usr/bin/env python3

"""
A simple script to log into a qbittorrent client and clean up completed torrents.
"""

import logging

from configparser import ConfigParser, NoOptionError, NoSectionError
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

config_opts.read(config_file)

try:
    for element in config_opts.sections():
        if element == "qbittorrent":
            qb_host = config_opts.get(element, "host")
            qb_user = config_opts.get(element, "user")
            qb_pass = config_opts.get(element, "pass")
        elif element == "pause":
            pause_ration = config_opts.get(element, "ratio")
            pause_categories = config_opts.get(element, "categories").split(",")
        elif element == "delete":
            delete_ratio = config_opts.get(element, "ratio")
            delete_categories = config_opts.get(element, "categories").split(",")
except [NoOptionError, NoSectionError]:
    logging.error("Config file is missing required options. Exiting.")
    exit(1)


def is_complete(torrent) -> bool:
    # Check if torrent is complete and return boolean
    return int(torrent["amount_left"]) == 0


def get_ratio(torrent) -> float:
    # Get ratio of torrent and return float
    return float(torrent["ratio"])


qb = Client(qb_host)

# Login to qbittorrent client
try:
    qb.login(qb_user, qb_pass)
except InvalidSchema:
    logging.error(
        "Invalid hostname or port. Did you forget to include http://? or use quotes?"
    )
    exit(1)

# Stop *arr downloads if completed. The *arr will handle removal.

for category in pause_categories:
    torrents = qb.torrents(category=category, filter="Seeding")

    for torrent in torrents:
        if is_complete(torrent) and get_ratio(torrent) >= float(pause_ration):
            logging.debug(
                torrent["hash"] + " " + torrent["name"] + " " + str(get_ratio(torrent))
            )
            logging.info("Pausing torrent: " + torrent["name"])
            qb.pause(torrent["hash"])

# Remove sports downloads if completed. Plex will handle file deletion.

for category in delete_categories:
    torrents = qb.torrents(category=category, filter="Seeding")

    for torrent in torrents:
        if is_complete(torrent) and get_ratio(torrent) >= float(delete_ratio):
            logging.debug(
                torrent["hash"] + " " + torrent["name"] + " " + str(get_ratio(torrent))
            )
            logging.info("Deleting torrent: " + torrent["name"])
            qb.delete(torrent["hash"])

# TODO: Add support for permanent deletion of torrents.

# Logout of qbittorrent client if session is still valid.

try:
    qb.logout()
except:
    # If session is invalid, do nothing.
    pass
