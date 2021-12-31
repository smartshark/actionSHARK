import os
import logging
import logging.config

import pycoshark.utils as utils
from actionshark.config import Config, init_logger
from actionshark.mongo import Mongo
from actionshark.github import GitHub

# create logs folder
if not os.path.exists("./logs"):
    os.mkdir("./logs")


# parsing command line arguments
def collect_args():
    parser = utils.get_base_argparser(
        "Collects information from command line.", "0.0.1"
    )

    # GitHub Args
    parser.add_argument(
        "-t",
        "--token",
        help="GitHub token to authenticate user.",
        required=False,
        type=str,
    )
    parser.add_argument(
        "-env",
        "--token-env",
        help="Environment variable, where token is stored.",
        required=False,
        type=str,
    )
    parser.add_argument(
        "-o",
        "--owner",
        help="Owner name of the repository.",
        default=None,
        required=False,
        type=str,
    )
    parser.add_argument(
        "-r",
        "--repository",
        help="Repository Name.",
        default=None,
        required=False,
        type=str,
    )
    parser.add_argument(
        "-ru",
        "--url",
        help="Repository URL.",
        default=None,
        required=False,
        type=str,
    )

    # General
    parser.add_argument(
        "--debug",
        help="Sets the debug level.",
        default="DEBUG",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )

    return parser.parse_args()


# main function
def main():
    # collect args from terminal to cfg variable
    args = collect_args()
    cfg = Config(args)

    # Start logger
    init_logger(cfg.logger_level)
    logger = logging.getLogger("main")
    logger.debug("Start Logging")

    # initiate mongo instance
    mongo = Mongo(
        cfg.db_user,
        cfg.db_password,
        cfg.db_hostname,
        cfg.db_port,
        cfg.db_database,
        cfg.db_authentication,
        cfg.db_ssl,
        cfg.url,
    )

    # initiate GitHub instance
    github = GitHub(
        owner=cfg.owner, repo=cfg.repo, token=cfg.token, save_mongo=mongo.save_documents
    )

    # get all actions
    github.run(mongo.runs)

    # Finish logging message
    logger.debug("Finish Logging")


if __name__ == "__main__":
    main()
