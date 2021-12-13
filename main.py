import os
import sys

import pycoshark.utils as utils
from actionshark.config import Config
from actionshark.actionshark import Actions
from actionshark.mongo import Mongo
from actionshark.github import GitHub

def collect_args():
    # parser = get_base_argparser('Collects information from command line.', '0.0.1')
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


def main(cfg):
    mongo = Mongo(cfg.db_user, cfg.db_password, cfg.db_hostname, cfg.db_port, cfg.db_database, cfg.db_authentication, cfg.ssl)
    github = GitHub()


if __name__ == "__main__":
    args = collect_args()

    # map args to variables and authenticate token
    cls_config = Config(args)

    # handel github and mongodb side
    cls_actions = Actions(cls_config)
    cls_actions.start()