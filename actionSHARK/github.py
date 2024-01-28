from typing import Callable, Optional
from time import sleep
import sys
import datetime as dt
import requests
import logging
from pycoshark.mongomodels import CiSystem, Project, ActionWorkflow, ActionRun, ActionJob, RunArtifact, VCSSystem
from .utils import parse_date, to_int, format_repository_url, run_head_repository_url, commit_object_id, create_job_step, create_pull_requests
from deepdiff import DeepDiff

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
        "run": "repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs?per_page={per_page}",
        "job": "repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page={per_page}",
        "artifact": "repos/{owner}/{repo}/actions/runs/{run_id}/artifacts?per_page={per_page}",
    }

    # essential variable
    current_action = None

    # tracking requests
    total_requests = 0
    limit_handler_counter = 0

    def __init__(
        self,
        project: Project,
        tracking_url: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        per_page: int = 100,
        token: Optional[str] = None,
    ) -> None:
        """Initializing essential variables.

        Args:
            owner (str): Owner of the repository.
            repo (str): The repository name.
            per_page (int): Number of items in a response. Defaults to 100.
            token (str): GitHub token to use in header to autherize requests.
        """
        self.workflow_id = None
        self.run_id = None
        self.parsed_actions = {'workflows': {}, 'runs': {}, 'jobs': {}, 'artifacts': {}}
        self.old_actions = {'workflows': {}}
        self.actions_diff = {}
        # check owner and repo
        if not owner or not repo:
            logger.error(
                f"Please make to sure to pass owner and repo names and save_mongo function."
            )
            sys.exit(1)

        # add token to header
        self.__token = None
        if token:
            self.__token = token
            self.__headers["Authorization"] = f"token {token}"

        # essential variables
        self.owner = owner
        self.repo = repo
        self.per_page = per_page
        self.project = project
        self.tracking_url = tracking_url

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

        for workflow in result:
            self.workflow_id = str(workflow.get("id"))
            try:
                mongo_workflow = ActionWorkflow.objects.get(ci_system_ids=self.last_system_id, external_id=self.workflow_id)
                self.old_actions['workflows'][self.workflow_id] = mongo_workflow
            except ActionWorkflow.DoesNotExist:
                mongo_workflow = None

            new_workflow = ActionWorkflow(ci_system_ids=[self.ci_system.id], external_id=self.workflow_id)
            new_workflow.name = workflow.get("name")
            new_workflow.path = workflow.get("path")
            new_workflow.state = workflow.get("state")
            new_workflow.created_at = parse_date(workflow.get("created_at"))
            new_workflow.updated_at = parse_date(workflow.get("updated_at"))
            new_workflow.project_id = self.project.id

            self.parsed_actions['workflows'][self.workflow_id] = new_workflow

            self.check_diff_workflow(mongo_workflow, new_workflow)
            self.get_runs(mongo_workflow)

        logger.debug(f"Finish fetching workflows")

    def get_runs(self, mongo_workflow) -> None:
        """
          Fetches workflow runs data from the GitHub API.

          Args:
              mongo_workflow: MongoWorkflow
                  An optional MongoWorkflow object for comparison with existing data in the database.

          Returns:
              None
        """

        # set what action to run and starting page
        self.current_action = "run"
        self.page = 1

        # constructing the GET url
        url = self.actions_url["run"].format(
            owner=self.owner, repo=self.repo, workflow_id=self.workflow_id, per_page=self.per_page
        )

        github_url = self.api_url + url

        # start fetching
        result = self.paginating(github_url, "workflow_runs")

        for run in result:
            self.run_id = str(run.get("id"))
            logger.debug(f"Start fetching run {self.run_id}")
            mongo_run = None
            if mongo_workflow:
                try:
                    mongo_run = ActionRun.objects.get(workflow_id=mongo_workflow.id, external_id=self.run_id)
                except ActionRun.DoesNotExist:
                    mongo_run = None

            new_run = ActionRun(external_id=str(run.get("id")))
            new_run.run_number = to_int(run.get("run_number"))
            new_run.event = run.get("event")
            new_run.status = run.get("status")
            new_run.conclusion = run.get("conclusion")
            f = create_pull_requests
            new_run.pull_requests = [f(d) for d in run.get("pull_requests")]
            new_run.created_at = parse_date(run.get("created_at"))
            new_run.updated_at = parse_date(run.get("updated_at"))
            new_run.run_started_at = parse_date(run.get("run_started_at"))
            new_run.run_attempt = to_int(run.get("run_attempt"))
            new_run.triggering_commit_sha = run.get("head_sha")
            new_run.triggering_commit_branch = run.get("head_branch")
            new_run.triggering_commit_message = run["head_commit"].get("message")
            new_run.triggering_commit_timestamp = parse_date(run["head_commit"].get("timestamp"))

            if run.get("head_repository"):
                new_run.triggering_repository_url = run_head_repository_url(run["head_repository"].get("full_name"))
            new_run.triggering_commit_id = commit_object_id(run.get("head_sha"), self.last_vcs_system_id)

            if self.workflow_id not in self.parsed_actions['runs']:
                self.parsed_actions['runs'][self.workflow_id] = {}
            self.parsed_actions['runs'][self.workflow_id][self.run_id] = new_run
            self.check_diff_run(mongo_run, new_run)
            self.get_jobs(mongo_run)
            self.get_artifacts(mongo_run)

        logger.debug(f"Finish fetching runs")

    def get_jobs(self, mongo_run) -> None:
        """
         Fetches run jobs data from the GitHub API for a specific run id.

         Args:
             mongo_run: MongoRun
                 An optional MongoRun object for comparison with existing data in the database.
         Returns:
             None
        """

        # set what action to run and starting page
        self.current_action = "job"
        self.page = 1

        # constructing the GET url
        url = self.actions_url["job"].format(
            owner=self.owner, repo=self.repo, run_id=self.run_id, per_page=self.per_page
        )
        github_url = self.api_url + url

        result = self.paginating(github_url, "jobs")

        for job in result:
            mongo_job = None
            if mongo_run:
                try:
                    mongo_job = ActionJob.objects.get(run_id=mongo_run.id, external_id=str(job.get("id")))
                except ActionJob.DoesNotExist:
                    mongo_job = None

            new_job = ActionJob(external_id=str(job.get("id")))
            new_job.name = job.get("name")
            new_job.head_sha = job.get("head_sha")
            new_job.run_attempt = to_int(job.get("run_attempt"))
            new_job.status = job.get("status")
            new_job.conclusion = job.get("conclusion")
            new_job.started_at = parse_date(job.get("started_at"))
            new_job.completed_at = parse_date(job.get("completed_at"))
            new_job.runner_id = to_int(job.get("runner_id"))
            new_job.runner_name = job.get("runner_name")
            new_job.runner_group_id = to_int(job.get("runner_group_id"))
            new_job.runner_group_name = job.get("runner_group_name")
            f = create_job_step
            new_job.steps = [f(d) for d in job.get("steps")]

            if (self.workflow_id, self.run_id) not in self.parsed_actions['jobs']:
                self.parsed_actions['jobs'][(self.workflow_id, self.run_id)] = {}
            self.parsed_actions['jobs'][(self.workflow_id, self.run_id)][str(job.get("id"))] = new_job
            self.check_diff_job_artifacts(mongo_job, new_job)

    def get_artifacts(self, mongo_run) -> None:
        """Fetching artifacts data from GitHub API."""

        # set what action to run and starting page
        self.current_action = "artifact"
        self.page = 1

        # constructing the GET url
        url = self.actions_url["artifact"].format(
            owner=self.owner, repo=self.repo, run_id=self.run_id, per_page=self.per_page
        )
        github_url = self.api_url + url

        # start fetching
        result = self.paginating(github_url, "artifacts")

        for artifact in result:
            mongo_artifact = None
            if mongo_run:
                try:
                    mongo_artifact = RunArtifact.objects.get(run_id=mongo_run.id, external_id=str(artifact.get("id")))
                except RunArtifact.DoesNotExist:
                    mongo_artifact = None

            new_artifact = RunArtifact(external_id=str(artifact.get("id")))
            new_artifact.name = artifact.get("name")
            new_artifact.size_in_bytes = to_int(artifact.get("size_in_bytes"))
            new_artifact.archive_download_url = artifact.get("archive_download_url")
            new_artifact.expired = bool(artifact.get("expired"))
            new_artifact.created_at = parse_date(artifact.get("created_at"))
            new_artifact.updated_at = parse_date(artifact.get("updated_at"))
            new_artifact.expires_at = parse_date(artifact.get("expires_at"))
            new_artifact.project_id = self.project.id

            if (self.workflow_id, self.run_id) not in self.parsed_actions['artifacts']:
                self.parsed_actions['artifacts'][(self.workflow_id, self.run_id)] = {}
            self.parsed_actions['artifacts'][(self.workflow_id, self.run_id)][str(artifact.get("id"))] = new_artifact
            self.check_diff_job_artifacts(mongo_artifact, new_artifact)

    def __finishing_message(self):
        """
        Finish message to append after finishing run()
        """
        logger.debug(f"Number of requests: {self.total_requests}")
        logger.debug(f"Number of stopping: {self.limit_handler_counter}")
        logger.debug("Finished fetching actions.")

    def run(self) -> None:
        """Collect all action's data form a repository.

        """

        # verify correct token if any

        last_system = CiSystem.objects.filter(project_id=self.project.id).order_by('-collection_date').first()
        self.last_system_id = last_system.id if last_system else None

        self.ci_system = CiSystem(project_id=self.project.id, url=self.tracking_url, collection_date=dt.datetime.now())
        self.ci_system.save()

        last_vcs_system = VCSSystem.objects.filter(url=self.tracking_url).order_by('-collection_date').first()
        self.last_vcs_system_id = last_vcs_system.id if last_vcs_system else None

        if self.__token:
            if not self.authenticate_user():
                sys.exit(1)

        if not self.__token:
            logger.debug(f"Proceding without token")

        # fetching actions
        self.get_workflows()

        self.save_actions()

        self.__finishing_message()

    def save_actions(self):
        """
        Iterates through parsed action data and saves relevant workflow, run, job, and artifact configurations
        based on the detected differences in the 'actions_diff' attribute.

        :return: None
        """

        for workflow_id, workflow in self.parsed_actions['workflows'].items():
            if workflow_id in self.actions_diff and self.actions_diff[workflow_id]:
                workflow.save()
                if workflow_id not in self.parsed_actions['runs']:
                    continue
                for run_id, run in self.parsed_actions['runs'][workflow_id].items():
                    run.workflow_id = workflow.id
                    run.save()
                    for field in ['jobs', 'artifacts']:
                        if (workflow_id, run_id) not in self.parsed_actions[field]:
                            continue
                        for item_id, item in self.parsed_actions[field][(workflow_id, run_id)].items():
                            item.run_id = run.id
                            item.save()
            else:
                self.old_actions['workflows'][workflow_id]['ci_system_ids'].append(self.ci_system.id)
                self.old_actions['workflows'][workflow_id].save()

    def check_diff_workflow(self, old, new):
        """
        Compares two sets of data representing different workflow configurations,
        excluding the 'ci_system_ids' attribute from the comparison.

        :param old: dict
            The old workflow configuration data.
        :param new: dict
            The new workflow configuration data.

        :return: None
        """

        self.check_diff(old, new, 'ci_system_ids')

    def check_diff_run(self, old, new):
        """
        Compares two sets of data representing different run configurations
        and checks for differences in the 'workflow_id' attribute.

        :param old: dict
            The old run configuration data.
        :param new: dict
            The new run configuration data.

        :return: None
        """

        self.check_diff(old, new, 'workflow_id')

    def check_diff_job_artifacts(self, old, new):
        """
        Compares two sets of data representing different job artifacts configurations
        and checks for differences in the 'run_id' attribute.

        :param old: dict
            The old job artifacts configuration data.
        :param new: dict
            The new job artifacts configuration data.

        :return: None
        """

        self.check_diff(old, new, 'run_id')

    def check_diff(self, old, new, ex_path):
        """
        Compare and identify differences between old and new objects.

        This function compares two objects, `old` and `new`, typically representing data from different
        states, to identify differences between them. The comparison is performed by utilizing the
        DeepDiff library. Differences are stored in the `actions_diff` dictionary for the pull request
        identified by `self.pr_id`. If differences are found, the corresponding key in `actions_diff`
        is set to `True`.

        :param old: The old object to be compared.
        :param new: The new object to be compared.
        :param ex_path: List of paths to be excluded from the comparison.

        """
        if self.workflow_id not in self.actions_diff:
            self.actions_diff[self.workflow_id] = False

        if old:
            diff = DeepDiff(t1=old.to_mongo().to_dict(), t2=new.to_mongo().to_dict(), exclude_paths=[ex_path, '_id'])
            if diff:
                self.actions_diff[self.workflow_id] = True
        else:
            self.actions_diff[self.workflow_id] = True

