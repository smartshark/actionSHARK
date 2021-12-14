import os
import sys
import logging

import pycoshark.utils as utils
from actionshark.config import Config
from actionshark.mongo import Mongo
from actionshark.github import GitHub


# logger configuration
logging.basicConfig(
    filename="logs/actionshark.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
    )


def collect_args():
    parser = utils.get_base_argparser('Collects information from command line.', '0.0.1')

    # GitHub Args
    parser.add_argument('-t', '--token', help='', required=False, type=str)
    parser.add_argument('-env', '--token-env', help='', required=False, type=str)
    parser.add_argument('-o', '--owner', help='', required=True, type=str)
    parser.add_argument('-r', '--repository', help='', required=True, type=str)

    # General
    parser.add_argument('--debug', help='Sets the debug level.', default='DEBUG',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

    return parser.parse_args()



def main(cfg, verbose: bool = False):

    # initializing logger
    logger = logging.getLogger("actionshark")

    # set logging level
    logger.setLevel( cfg.logger_level )

    # Start logger message
    logger.debug('Start Logging')

    # initiate mongo instance
    mongo = Mongo(cfg.db_user, cfg.db_password, cfg.db_hostname, cfg.db_port, cfg.db_database, cfg.db_authentication, cfg.db_ssl)

    # initiate GitHub instance
    github = GitHub(owner=cfg.owner, repo=cfg.repo, token=cfg.token, save_mongo=mongo.save_documents, verbose=verbose)

    # get all actions
    github.run( mongo.runs )

    # Finish logging message
    logger.debug('Finish Logging')


if __name__ == "__main__":
    # collect args from terminal
    args = collect_args()

    # map args to variables and authenticate token
    cls_config = Config(args)

    # handel github and mongodb side
    main(cls_config)