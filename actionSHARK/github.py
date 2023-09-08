from typing import Callable, Optional
from time import sleep
import os
import sys
import datetime as dt
import requests
import logging


# start logger
logger = logging.getLogger("main.github")


class GitHub:
    """
    Managing different type of get Request to fetch data from GitHub REST API"""

    # base url
    api_url = "https://api.github.com/"

    # request header default value
    __headers = {"Accept": "application/vnd.github.v3+json"}

    # API URLs for each action
    actions_url = {
        "workflow": "repos/{owner}/{repo}/actions/workflows?per_page={per_page}",
        "run": "repos/{owner}/{repo}/actions/runs?per_page={per_page}",
        "job": "repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page={per_page}",
        "artifact": "repos/{owner}/{repo}/actions/artifacts?per_page={per_page}",
    }

    # essential variable
    current_action = None

    # tracking requests
    total_requests = 0
    limit_handler_counter = 0

    def __init__(
        self,
        save_mongo: Callable,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        per_page: int = 100,
        token: Optional[str] = None,
    ) -> None:
        """Initializing essential variables.

        Args:
            save_mongo (callable): Callable function to save items in MongoDB.
            owner (str): Owner of the repository.
            repo (str): The repository name.
            per_page (int): Number of items in a response. Defaults to 100.
            token (str): GitHub token to use in header to autherize requests.
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
            self.__token = token
            self.__headers["Authorization"] = f"token {token}"

        # MongoDB save function
        self.save_mongo = save_mongo

        # essential variables
        self.owner = owner
        self.repo = repo
        self.per_page = per_page
        self.runs_ids = []

    def authenticate_user(self):
        """
        Authenticate the passed token by requesting user information."""

        basic_auth = requests.get(self.api_url + "user", headers=self.__headers)

        self.total_requests += 1

        # if 401 = 'Unauthorized', but other responses mean the user is authorized
        # Unauthorized users have much lower limit, 60 per hour.
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
            github_url (str): GitHub API url to loop over and collect responses.
            checker (str, optional): The key to the element, who has all items. Defaults to None.
        Returns:
            result (list): List of JSON entries.
        """
        result = []
        while True:
            # append page number to the url
            github_url += f"&page={self.page}"

            # GET response
            response = requests.get(github_url, headers=self.__headers)

            self.total_requests += 1

            # Abort if unknown error occurred
            if response.status_code not in [200, 403]:
                logger.error(f"Error in request status_code: {response.status_code}")
                logger.error(f"Error in request github_url: {github_url}")
                logger.error(response)
                sys.exit(1)

            # handle number of requests limitation
            if response.status_code == 403:

                self.rate_limit_handler(response)
                # after sleeping restart last loop to continue from last action
                continue

            # get the items from a sub key
            response_JSON = response.json()
            if checker:
                response_JSON = response_JSON.get(checker)
                result.extend(response_JSON)
            # count number of items
            response_count = len(response_JSON)

            # if no items, jump to next action
            if not response_JSON:
                break

            # handel page incrementing
            github_url = github_url[: -len(f"&page={self.page}")]
            self.page += 1

            # updating metric variables
            self.total_requests += 1

            # break after saving if number of items is less than per_page
            if response_count < self.per_page:
                break
        return result

    def rate_limit_handler(self, response):
        """
        Handles rate limiting for API requests by calculating the time until the rate limit is reset and sleeping for that duration
        before continuing with the next API request.


        Args:
            response(requests.Response): The response object from the API request.

        Returns:
            None

        """
        # get the next reset time
        headers_dict = response.headers
        ratelimit = headers_dict.get("X-RateLimit-Reset")
        if ratelimit:
            reset_time = dt.datetime.fromtimestamp(int(ratelimit))
        else:
            logger.error(
                f"Error fetching 'X-RateLimit-Reset' from request's header."
            )
            logger.error(f"The value is: X-RateLimit-Reset = {ratelimit}")
            sys.exit(1)
        # calculate the sleep time
        current_time = dt.datetime.now().replace(microsecond=0)
        sleep_time = (reset_time - current_time).seconds
        self.limit_handler_counter += 1
        logger.debug(f"Limit handler is triggered")
        logger.debug(
            f"Program will sleep for approximately {sleep_time:n} seconds."
        )
        logger.debug(f"Next Restart will be on {reset_time}")
        # sleep till limit reset
        sleep(sleep_time)
        logger.debug(
            f"Continue with fetching {self.current_action} from last GET request"
        )

    def get_workflows(self) -> None:
        """Fetching workflows data from GitHub API."""

        # set what action to run and starting page
        self.current_action = "workflow"
        self.page = 1

        # constructing the GET url
        url = self.actions_url["workflow"].format(
            owner=self.owner, repo=self.repo, per_page=self.per_page
        )
        github_url = self.api_url + url

        # start fetching
        logger.debug(f"Start fetching workflows")

        result = self.paginating(github_url, "workflows")

        # save items to mongodb
        self.save_mongo(result, "workflow")
        logger.debug(f"Finish fetching workflows")

    def get_runs(self, last_updated=None) -> None:
        """Fetching workflows' runs data from GitHub API.

        Args:
            last_updated(Datetime): last_updated for a VCS system.
        """

        # set what action to run and starting page
        self.current_action = "run"
        self.page = 1

        # constructing the GET url
        url = self.actions_url["run"].format(
            owner=self.owner, repo=self.repo, per_page=self.per_page
        )
        if last_updated is not None:
            year_month_day_format = '%Y-%m-%d'
            date = last_updated.strftime(year_month_day_format)
            url = url + '&created=>' + date
        github_url = self.api_url + url

        # start fetching
        logger.debug(f"Start fetching runs")

        result = self.paginating(github_url, "workflow_runs")

        if len(result) > 0:
            self.runs_ids = [run['id'] for run in result]
            self.save_mongo(result, "run")

        logger.debug(f"Finish fetching runs")

    def get_jobs(self, run_id: int) -> None:
        """Fetching runs' jobs data from GitHub API for specific run id.

        Args:
            run_id (int): Run id to get the jobs.
        """

        # set what action to run and starting page
        self.current_action = "job"
        self.page = 1

        # constructing the GET url
        url = self.actions_url["job"].format(
            owner=self.owner, repo=self.repo, run_id=run_id, per_page=self.per_page
        )
        github_url = self.api_url + url

        result = self.paginating(github_url, "jobs")
        if len(result) > 0:
            self.save_mongo(result, "job")

    def get_artifacts(self) -> None:
        """Fetching artifacts data from GitHub API."""

        # set what action to run and starting page
        self.current_action = "artifact"
        self.page = 1

        # constructing the GET url
        url = self.actions_url["artifact"].format(
            owner=self.owner, repo=self.repo, per_page=self.per_page
        )
        github_url = self.api_url + url

        # start fetching
        logger.debug(f"Start fetching artifacts")

        result = self.paginating(github_url, "artifacts")
        self.save_mongo(result, "artifact")

        logger.debug(f"Finish fetching artifacts")

    def __finishing_message(self):
        """
        Finish message to append after finishing run()
        """
        logger.debug(f"Number of requests: {self.total_requests}")
        logger.debug(f"Number of stopping: {self.limit_handler_counter}")
        logger.debug("Finished fetching actions.")

    def run(self, last_updated=None) -> None:
        """Collect all action's data form a repository.

        Args:
            last_updated (Datetime): last_updated for a VCS system.
        """

        # verify correct token if any
        if self.__token:
            if not self.authenticate_user():
                sys.exit(1)

        if not self.__token:
            logger.debug(f"Proceding without token")

        # fetching actions
        self.get_workflows()
        self.get_artifacts()
        self.get_runs(last_updated)

        # logger is used here to not log each time the function executes
        logger.debug(f"Start fetching jobs")
        for run in self.runs_ids:
            self.get_jobs(run)
        logger.debug(f"Finish fetching jobs")

        self.__finishing_message()
