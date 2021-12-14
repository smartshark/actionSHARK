import os
import logging

# start logger
logger = logging.getLogger(__name__)


class Config:

    def __init__(self, args):

        self.token = args.token
        self.owner = args.owner
        self.repo = args.repository
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


        logger.debug('Arguments mapped')




    def __str__(self):
        return '\n'.join([
            f'token: {self.token}',
            f'owner: {self.owner}',
            f'repo: {self.repo}',
            f'db_database: {self.db_database}',
            f'db_user: {self.db_user}',
            f'db_password: {self.db_password}',
            f'db_hostname: {self.db_hostname}',
            f'db_port: {self.db_port}',
            f'db_authentication: {self.db_authentication}',
            f'db_ssl: {self.db_ssl}'
        ])



    def get_logger_level(self, level: str = 'debug'):

        levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

        if level in levels.keys():
            return levels[level]
        else:
            logger.debug("logging level not declared.")
            return None

