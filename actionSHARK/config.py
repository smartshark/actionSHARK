import os
import logging
import logging.config
import json
import datetime as dt
from typing import Optional


class Config:
    def __init__(self, args):

        self.token = args.token
        self.parse_url(args.owner, args.repository, args.url)
        self.db_database = args.db_database
        self.db_user = args.db_user
        self.db_password = args.db_password
        self.db_hostname = args.db_hostname
        self.db_port = args.db_port
        self.db_authentication = args.db_authentication
        self.db_ssl = args.ssl
        self.logger_level = self.get_logger_level(args.debug)

        # if environment variable passed and not concrete token
        if not self.token and args.token_env:
            self.token = os.environ.get(args.token_env)

    def __str__(self):
        return "\n".join(
            [
                f"token: {self.token}",
                f"owner: {self.owner}",
                f"repo: {self.repo}",
                f"url: {self.url}",
                f"db_database: {self.db_database}",
                f"db_user: {self.db_user}",
                f"db_password: {self.db_password}",
                f"db_hostname: {self.db_hostname}",
                f"db_port: {self.db_port}",
                f"db_authentication: {self.db_authentication}",
                f"db_ssl: {self.db_ssl}",
                f"logger_level: {self.logger_level}",
            ]
        )

    def parse_url(
        self,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        url: Optional[str] = None,
    ) -> None:

        self.owner = owner
        self.repo = repo

        if url:
            url_parts = url.replace("api.", "")
            url_parts = url_parts.replace(".git", "")
            url_parts = url_parts.split("/")

            self.owner = url_parts[3]
            self.repo = url_parts[4]

        self.url = f"https://github.com/{self.owner}/{self.repo}.git"

    def get_logger_level(self, level: str = "DEBUG"):

        level = level.capitalize()

        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        # defult level to DEBUG
        if level not in levels:
            level = "DEBUG"

        return level


# modifying logger configuration
def init_logger(level):
    # load logger configuration
    with open(
        "{}/../logger_config.json".format(os.path.dirname(os.path.abspath(__file__))),
        "r",
    ) as f:
        logging_cfg = json.load(f)

    current_time = dt.datetime.strftime(dt.datetime.now(), "%Y-%m-%d_%H-%M-%S")

    # add date and time to log file name
    logging_cfg["handlers"]["debug"]["filename"] = logging_cfg["handlers"]["debug"][
        "filename"
    ].replace(".log", f"_{current_time}.log")
    logging_cfg["handlers"]["error"]["filename"] = logging_cfg["handlers"]["error"][
        "filename"
    ].replace(".log", f"{current_time}.log")

    logging_cfg["loggers"]["main"]["level"] = level

    # load logging configuration
    logging.config.dictConfig(logging_cfg)
