from typing import Callable, Optional
from time import sleep
import os
import sys
import datetime as dt
import requests
import logging


"""
change limit to when its triggered parse next reset time from header
remove sleep between requests
"""

# start logger
logger = logging.getLogger("main.github")


class GitHub:
    """
    Managing different type of get Request to fetch data from GitHub REST API"""

    api_url = "https://api.github.com/"

    __headers = {"Accept": "application/vnd.github.v3+json"}

    actions_url = {
        "workflow": "repos/{owner}/{repo}/actions/workflows?per_page={per_page}",
        "run": "repos/{owner}/{repo}/actions/runs?per_page={per_page}",
        "job": "repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page={per_page}",
        "artifact": "repos/{owner}/{repo}/actions/artifacts?per_page={per_page}",
    }

    total_requests = 0
    current_action = None
    limit_handler_counter = 0

    def __init__(
        self,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        per_page: int = 100,
        token: Optional[str] = None,
        save_mongo: Callable = None,
    ) -> None:
        """Initializing essential variables to use in the requests.

        Args:
            owner (str): Owner of the repository. Defaults to None.
            repo (str): The repository name. Defaults to None.
            per_page (int): Number of items in a response. Defaults to 100.
            save_mongo (callable): Callable function to save items in MongoDB. Defaults to None.
            sleep_interval (int): Time to wait between requests in seconds. Defaults to 2.
        """

        # check owner and repo
        if not owner or not repo or not save_mongo:
            logger.error(
                f"Please make to sure to pass owner and repo names and save_mongo function."
            )
            sys.exit(1)

        # add token to header
        self.__token = None
        if token:
            self.__headers["Authorization"] = f"token {token}"
            self.__token = token

        # MongoDB
        self.save_mongo = save_mongo

        # main variables
        self.owner = owner
        self.repo = repo
        self.per_page = per_page
        self.page = 1

    def authenticate_user(self):
        """
        Authenticate passed token by requesting user information."""

        basic_auth = requests.get(self.api_url + "user", headers=self.__headers)

        self.total_requests += 1

        # if 401 = 'Unauthorized', but other response means the use is authorized
        if basic_auth.status_code == 401:

            logger.error(f"Error authenticated using token")
            logger.error("Authentication status_code:", basic_auth.status_code)
            logger.error(basic_auth.reason)
            logger.error(self.api_url + "user")

            return False

        logger.debug(f"Successfully authenticated using token")

        return True

    def paginating(self, github_url: str, checker: Optional[str] = None):
        """Fetch all pages for an action and handel API limitation.

        Args:
            github_url (str): GitHub API url to loop over and collect responses. Defaults to None.
            checker (str, optional): The key to the element, who has all items. Defaults to None.
        """

        # case 1: limit achieved and action was not fully fetched -> stopped while paginating
        # case 2: got response but was last action page and last remaining the same time
        # case 3: still remaining and last page was achieved -> jump to next action
        # case 4: limit was not reached and an hour passed -> reset limit variables

        while True:
            # append page number to url
            github_url += f"&page={self.page}"

            # get response
            response = requests.get(github_url, headers=self.__headers)

            self.total_requests += 1

            # Abort if unknown error occurred
            if response.status_code not in [200, 403]:
                logger.error(f"Error in request status_code: {response.status_code}")
                logger.error(f"Error in request github_url: {github_url}")
                logger.error(response)
                sys.exit(1)

            # handel case: limit achieved and action was not fully fetched -> stopped while paginating
            # handel case: got response but was last action page and last remaining the same time
            if response.status_code == 403:

                headers_dict = response.headers

                reset_time = dt.datetime.fromtimestamp(
                    int(headers_dict.get("X-RateLimit-Reset"))
                )

                current_time = dt.datetime.now().replace(microsecond=0)

                sleep_time = (reset_time - current_time).seconds

                self.limit_handler_counter += 1

                logger.debug(f"Limit handler is triggered")
                logger.debug(
                    f"Program will sleep for approximately {sleep_time:n} seconds."
                )
                logger.debug(f"Next Restart will be on {reset_time}")

                # long sleep till limit reset
                sleep(sleep_time)

                logger.debug(
                    f"Continue with fetching {self.current_action} from last GET request"
                )
                continue

            # check if key is not empty
            response_JSON = response.json()
            if checker:
                response_JSON = response_JSON.get(checker)

            # count number of documents
            response_count = len(response_JSON)

            # handel case: limit was not reached and an hour passed -> reset limit variables
            if not response_JSON:
                break

            # save documents to mongodb
            self.save_mongo(response_JSON, self.current_action)

            # handel page incrementing
            github_url = github_url[: -len(f"&page={self.page}")]
            self.page += 1

            # updating variables to deal with limits
            self.total_requests += 1

            # break after saving if response_count is less than per_page
            if response_count < self.per_page:
                break

    def get_workflows(self) -> None:
        """Fetching workflows data from GitHub API for specific repository and owner."""

        self.current_action = "workflow"
        self.page = 1

        url = self.actions_url["workflow"].format(
            owner=self.owner, repo=self.repo, per_page=self.per_page
        )
        github_url = self.api_url + url

        logger.debug(f"Start fetching workflows")

        self.paginating(github_url, "workflows")

        logger.debug(f"Finish fetching workflows")

    def get_runs(self) -> None:
        """Fetching workflow runs data from GitHub API for specific repository and owner."""

        self.current_action = "run"
        self.page = 1

        url = self.actions_url["run"].format(
            owner=self.owner, repo=self.repo, per_page=self.per_page
        )
        url += f"&exclude_pull_requests=False"
        github_url = self.api_url + url

        logger.debug(f"Start fetching runs")

        self.paginating(github_url, "workflow_runs")

        logger.debug(f"Finish fetching runs")

    def get_jobs(self, run_id: int = None) -> None:
        """Fetching run artifacts data from GitHub API for specific repository, owner, and run.

        Args:
            run_id (int): The run id. Defaults to None.
        """

        if not run_id:
            logger.error(
                "Please make to sure to pass the owner, repo name, and run id."
            )
            sys.exit(1)

        self.current_action = "job"
        self.page = 1

        url = self.actions_url["job"].format(
            owner=self.owner, repo=self.repo, run_id=run_id, per_page=self.per_page
        )
        github_url = self.api_url + url

        self.paginating(github_url, "jobs")

    def get_artifacts(self) -> None:
        """Fetching run artifacts data from GitHub API for specific repository, owner, and run."""

        self.current_action = "artifact"
        self.page = 1

        url = self.actions_url["artifact"].format(
            owner=self.owner, repo=self.repo, per_page=self.per_page
        )
        github_url = self.api_url + url

        logger.debug(f"Start fetching artifacts")

        self.paginating(github_url, "artifacts")

        logger.debug(f"Finish fetching artifacts")

    def run(self, runs_object=None) -> None:
        """Collect all action for a repository.

        Args:
            runs_object (Document): Runs collection to extract all run ids. Defaults to None.
        """

        # verify correct token if any
        if self.__token:
            if not self.authenticate_user():
                sys.exit(1)

        if not self.__token:
            logger.debug(f"Proceding without token")

        self.get_workflows()
        self.get_artifacts()
        self.get_runs()

        # if Runs object was passed, for each Run get
        if runs_object:
            # collect ids in a list to avoid cursor timeout
            logger.debug("Collecting run ids")
            run_ids = [run.run_id for run in runs_object.objects()]

            # logger is used here to not log each time the function excutes
            logger.debug(f"Start fetching jobs")
            for run in run_ids:
                self.get_jobs(run)
            logger.debug(f"Finish fetching jobs")
