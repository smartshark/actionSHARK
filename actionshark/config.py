import os
import logging


# start logger
logger = logging.getLogger("main.config")


class Config:
    def __init__(self, args):

        self.token = args.token
        self.url = args.url
        self.parse_url(args.owner, args.repository, self.url)
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

        logger.debug("Arguments mapped")

    def __str__(self):
        return "\n".join(
            [
                f"token: {self.token}",
                f"owner: {self.owner}",
                f"repo: {self.repo}",
                f"db_database: {self.db_database}",
                f"db_user: {self.db_user}",
                f"db_password: {self.db_password}",
                f"db_hostname: {self.db_hostname}",
                f"db_port: {self.db_port}",
                f"db_authentication: {self.db_authentication}",
                f"db_ssl: {self.db_ssl}",
                f"verbose: {self.verbose}",
            ]
        )

    def parse_url(self, owner=None, repo=None, url=None) -> None:

        self.owner = owner
        self.repo = repo

        if url:
            url_parts = url.replace("api.", "")
            url_parts = url_parts.replace(".git", "")
            url_parts = url_parts.split("/")

            self.owner = url_parts[3]
            self.repo = url_parts[4]

        else:
            self.url = f"https://github.com/{owner}/{repo}.git"

    def get_logger_level(self, level: str = "DEBUG"):

        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        # defult level to DEBUG
        if level not in levels.keys():
            level = "DEBUG"

        return levels[level]
