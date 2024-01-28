import os
import logging
import logging.config
import sys
import pycoshark.utils as utils
from actionSHARK.config import Config, init_logger
from actionSHARK.github import GitHub
from pycoshark.mongomodels import Project
from mongoengine import connect, ConnectionFailure


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# create logs folder
if not os.path.exists(f"{BASE_DIR}/logs"):
    os.mkdir(f"{BASE_DIR}/logs")


# parsing command line arguments
def collect_args():
    parser = utils.get_base_argparser(
        "Collects information from command line.", "1.0.0"
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
    parser.add_argument('-pn', '--project-name', help='Name of the project.', required=True)

    # General
    parser.add_argument(
        "--debug",
        help="Select the debug level.",
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
    i = logging.StreamHandler(sys.stdout)
    e = logging.StreamHandler(sys.stderr)

    i.setLevel(logging.DEBUG)
    e.setLevel(logging.ERROR)

    logger.addHandler(i)
    logger.addHandler(e)
    logger.debug("Start Logging")

    # initiate mongo instance

    # get all actions
    conn_uri = utils.create_mongodb_uri_string(
        cfg.db_user,
        cfg.db_password,
        cfg.db_hostname,
        cfg.db_port,
        cfg.db_authentication,
        cfg.db_ssl,
    )
    try:
        conn = connect(cfg.db_database, host=conn_uri)
    except ConnectionFailure:
        conn = None
        logger.error("Failed to connect to MongoDB")

    try:
        project = Project.objects.get(name=cfg.project_name)
    except Project.DoesNotExist:
        logger.error('Project %s not found!', cfg.project_name)
        sys.exit(1)

    # initiate GitHub instance
    github = GitHub(
        tracking_url=cfg.tracking_url,
        owner=cfg.owner,
        repo=cfg.repo,
        token=cfg.token,
        project=project,
    )
    try:
        github.run()
    except(KeyboardInterrupt, Exception) as e:
        logger.error(f"Program did not run successfully. Reason:{e}")
        logger.info(f"Deleting uncompleted data .....")
        utils.delete_last_system_data_on_failure('ci_system', cfg.tracking_url, db_user=cfg.db_user,
                                           db_password=cfg.db_password,
                                           db_hostname=cfg.db_hostname, db_port=cfg.db_port,
                                           db_authentication_db=cfg.db_authentication,
                                           db_ssl=cfg.db_ssl, db_name=cfg.db_database)

    # Finish logging message
    logger.debug("Finish Logging")


if __name__ == "__main__":
    main()
