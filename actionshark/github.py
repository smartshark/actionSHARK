import json
from typing import Callable, Optional
from time import sleep
import os
import sys
import datetime as dt
import requests
import logging

# start logger
logger = logging.getLogger(__name__)

class GitHub():
    """
    Managing different type of get Request to fetch data from GitHub REST API"""

    api_url = 'https://api.github.com/'

    __headers = {'Accept': 'application/vnd.github.v3+json'}

    actions_url = {
        'repos': 'orgs/{org}/repos?per_page={per_page}',
        'workflows': 'repos/{owner}/{repo}/actions/workflows?per_page={per_page}',
        'runs': 'repos/{owner}/{repo}/actions/runs?per_page={per_page}',
        'jobs': 'repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page={per_page}',
        'artifacts': 'repos/{owner}/{repo}/actions/runs/{run_id}/artifacts?per_page={per_page}'
    }

    total_requests = 0
    current_action = None
    limit_handler_counter = 0


    def __init__(self, owner: Optional[str] = None, repo: Optional[str] = None, per_page: int = 100, token: Optional[str] = None, save_mongo: Callable = None, sleep_interval: int = 2, verbose: bool = True) -> None:
        """Initializing essential variables to use in the requests.

        Args:
            owner (str): Owner of the repository. Defaults to None.
            repo (str): The repository name. Defaults to None.
            per_page (int): Number of items in a response. Defaults to 100.
            save_mongo (callable): Callable function to save items in MongoDB. Defaults to None.
            sleep_interval (int): Time to wait between requests in seconds. Defaults to 2.
            verbose (bool): Print log messages to console. Defaults to True.
        """

        # check owner and repo
        if not owner or not repo or not save_mongo:
            logger.debug(f'not all owner and repo names and save_mongo function was passed')
            print('Please make to sure to pass owner and repo names and save_mongo function.')
            sys.exit(1)

        # add token to header and check initial quota
        if token:
            self.__headers['Authorization'] = f'token {token}'

        # MongoDB
        self.save_mongo = save_mongo

        # main variables
        self.owner = owner
        self.repo = repo
        self.per_page = per_page
        self.page = 1
        self.sleep_betw_requests = sleep_interval
        self.verbose = verbose

        # initiate limit variables
        self.update_limit_variables()
        self.last_stop_datetime = self.get_dt_now()



    def __str__(self) -> str:
        return '\n'.join([
            "_"*30, ""
            f"Owner: {self.owner}",
            f"Repository: {self.repo}",
            f"API URL: {self.api_url}",
            f"Limit requests: {self.limit}",
            f"Remaining requests: {self.remaining}",
            f"Next Reset: {self.reset_datetime}",
            f"Last Stop: {self.last_stop_datetime}",
            f"SleepInterval: {self.sleep_betw_requests}",
            f"verbose: {self.verbose}",
            "_"*30, ""
        ])



    def authenticate_user(self, verbose: bool = False):
        """Authenticate passed token by requesting user information.

        Args:
            verbose (bool, optional): [Description] . Defaults to False.
        """

        basic_auth = requests.get(self.api_url + 'user', headers=self.__headers)

        self.total_requests += 1
        self.remaining -= 1

        # if 401 = 'Unauthorized', but other response means the use is authorized
        if basic_auth.status_code == 401:

            logger.debug(f'Error authenticated using token')

            if verbose:
                print('Error Authentication:', basic_auth.status_code)
                print(basic_auth.reason)
                print(self.api_url + 'user')

            return False

        logger.debug(f'Successfully authenticated using token')

        basic_auth_json = basic_auth.json()

        if verbose:
            print('Successful Authentication:', basic_auth.status_code)
            print(basic_auth_json['name'])
            print(basic_auth_json['html_url'])
            print('_'*60)

        return True



    def get_dt_now(self) -> dt:
        return dt.datetime.now().replace(microsecond=0)



    def get_limit(self, verbose: bool = False):
        """Collect limitation parameters.

        Args:
            verbose (bool, optional): [description]. Defaults to False.
        """

        response = requests.get(self.api_url + 'rate_limit', headers=self.__headers)

        if response.status_code == 200:
            temp = response.json()['resources']['core']
            self.remaining = temp["remaining"]
            self.reset_datetime = dt.datetime.fromtimestamp(temp["reset"])
            self.limit = temp["limit"]

            if verbose: # local verbose
                print("__"*30)
                print(f'Limit :{self.limit}')
                print(f'Used :{temp["used"]}')
                print(f'Remaining :{self.remaining}')
                print(f'Reset :{self.reset_datetime}')
                print("__"*30)

        else:
            self.remaining = 0
            self.reset_datetime = self.get_dt_now()

            print('Error getting limit and quota', response.status_code)
            print(response.reason)



    def limit_handler(self) -> None:
        """Handel limitation by sleeping till next reset time.
        """

        # 401 = 'Unauthorized'
        # 403 = 'rate limit exceeded'

        self.last_stop_datetime = dt.datetime.now().replace(microsecond=0)
        self.force_to_sleep = (self.reset_datetime - self.last_stop_datetime).seconds

        self.limit_handler_counter += 1

        if self.verbose:
            print('\\\\'*40)
            print(f'Limit handler is triggered')
            print(f'Program will sleep for approximately {self.force_to_sleep:n} seconds.')
            print(f'Next Restart will be on {self.reset_datetime.time()}')
            print('//'*40)

        logger.debug(f'Limit handler is triggered, program will sleep for approximately {self.force_to_sleep:n} seconds.')
        logger.debug(f'Next Restart will be on {self.reset_datetime.time()}')

        # long sleep till limit reset
        sleep(self.force_to_sleep)

        # update limit variables
        self.update_limit_variables()

        logger.debug(f'Continue with {self.current_action} from page {self.page}')

        if self.verbose:
            print('\\\\'*40)
            print(f'Continue with {self.current_action} from page {self.page}...')

            #* DEBUGGING
            self.get_limit(verbose=True)
            print('//'*40)



    def update_limit_variables(self):
        """Update limitation parameters.
        """
        # update limit variables and error margin
        self.get_limit()
        self.remaining -= 2
        self.reset_datetime += dt.timedelta(seconds=2)

        logger.debug(f'Updating limit handler variables')
        logger.debug(f'limit variable remaining: {self.remaining}')
        logger.debug(f'limit variable reset_datetime: {self.reset_datetime}')
        logger.debug(f'limit variable limit: {self.limit}')
        logger.debug(f'Finished limit handler variables')

        if self.verbose:
            print(f'-- Update limit handler variables.')



    def paginating(self, github_url: Optional[str] = None, checker: Optional[str] = None):
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
            github_url += f'&page={self.page}'

            # get response
            response = requests.get(github_url, headers=self.__headers)

            if self.verbose:
                print(f'{self.current_action} url:', github_url)

            # Abort if unknown error occurred
            if response.status_code != 200 and response.status_code != 403:

                logger.debug(f'Error in request status_code: {response.status_code}')
                logger.debug(f'Error in request github_url: {github_url}')

                print("Error in request.")
                print(response.status_code)
                print(response)
                sys.exit(1)

            # handel case: limit achieved and action was not fully fetched -> stopped while paginating
            # handel case: got response but was last action page and last remaining the same time
            if response.status_code == 403 or self.remaining < 1:
                self.limit_handler()
                # skip current loop with same action and page
                continue

            # check if key is not empty
            response_JSON = response.json()
            if checker:
                response_JSON = response_JSON.get(checker)
            # count number of documents
            response_count = len(response_JSON)

            # handel case: limit was not reached and an hour passed -> reset limit variables
            if not response_JSON:
                if self.verbose:
                    print(f'Response is Empty ... Stopping.')
                    print('-'*( len(github_url)+20) )
                break

            # save documents to mongodb
            self.save_mongo(response_JSON, self.current_action)

            # *DEBUGGING
            # self.save_JSON(response_JSON, save_path)

            # break after saving if response_count is less than per_page
            if response_count < self.per_page:
                if self.verbose:
                    print(f'Full Response is saved ... Stopping.')
                    print('-'*( len(github_url)+20))
                break

            # handel page incrementing
            github_url = github_url[:-len(f'&page={self.page}')]
            self.page += 1

            # sleep between requests
            sleep(self.sleep_betw_requests)

            # updating variables to deal with limits
            self.total_requests += 1
            self.remaining -= 1

            # handel case: limit was not reached and an hour passed -> reset limit variables
            if (self.get_dt_now() - dt.timedelta(hours=1) ) >= self.last_stop_datetime:
                logger.debug('Hour passed without hitting the limit')
                self.update_limit_variables()



    def get_workflows(self) -> None:
        """Fetching workflows data from GitHub API for specific repository and owner.
        """

        self.current_action = 'workflows'
        self.page = 1

        url = self.actions_url['workflows'].format(owner=self.owner, repo=self.repo, per_page=self.per_page)
        github_url = self.api_url + url

        logger.debug(f'start fetching workflows')

        if self.verbose:
            print('-'*( len(github_url)+20) )

        self.paginating(github_url, 'workflows')

        logger.debug(f'finish fetching workflows')



    def get_runs(self) -> None:
        """Fetching workflow runs data from GitHub API for specific repository and owner.
        """

        self.current_action = 'runs'
        self.page = 1

        url = self.actions_url['runs'].format(owner=self.owner, repo=self.repo, per_page=self.per_page)
        url += f'&exclude_pull_requests=False'
        github_url = self.api_url + url

        logger.debug(f'start fetching runs')

        if self.verbose:
            print('-'*( len(github_url)+20) )

        self.paginating(github_url, 'workflow_runs')

        logger.debug(f'finish fetching runs')



    def get_jobs(self, run_id: int = None) -> None:
        """Fetching run artifacts data from GitHub API for specific repository, owner, and run.

        Args:
            run_id (int): The run id. Defaults to None.
        """

        if not run_id:
            print('Please make to sure to pass the owner, repo name, and run id.')
            sys.exit(1)

        self.current_action = 'jobs'
        self.page = 1

        url = self.actions_url['jobs'].format(owner=self.owner, repo=self.repo, run_id=run_id, per_page=self.per_page)
        github_url = self.api_url + url

        if self.verbose:
            print('-'*( len(github_url)+20) )

        self.paginating(github_url, 'jobs')




    def get_artifacts(self, run_id: int = None) -> None:
        """Fetching run artifacts data from GitHub API for specific repository, owner, and run.

        Args:
            run_id (int): The run id. Defaults to None.
        """

        if not run_id:
            print('Please make to sure to pass both the owner and repo names.')
            sys.exit(1)

        self.current_action = 'artifacts'
        self.page = 1

        url = self.actions_url['artifacts'].format(owner=self.owner, repo=self.repo, run_id=run_id, per_page=self.per_page)
        github_url = self.api_url + url

        if self.verbose:
            print('-'*( len(github_url)+20) )

        self.paginating(github_url, 'artifacts')



    def run(self, runs_object = None) -> None:
        """Collect all action for a repository.

        Args:
            runs_object (Document): Runs collection to extract all run ids. Defaults to None.
        """

        # verify correct token if any
        if 'Authorization' in self.__headers.keys():
            if not self.authenticate_user(verbose=True):

                logger.debug(f'Wrong token')

                print("Wrong token, please try again.")
                sys.exit(1)
        else:
            logger.debug(f'proceding without token')

        self.get_workflows()
        self.get_runs()

        # if Runs object was passed, for each Run get
        if runs_object:
            # collect ids in a list to avoid cursor timeout
            logger.debug('Collecting run ids')
            run_ids = [run.id for run in runs_object.objects()]
            logger.debug('Done collecting run ids')
            if self.verbose:
                print('Collecting run idsCollecting run ids')

            # logger is used here to not log each time the function excutes
            logger.debug(f'Start fetching jobs')
            for run in run_ids:
                self.get_jobs(run)
            logger.debug(f'Finish fetching jobs')


            logger.debug(f'Start fetching artifacts')
            for run in run_ids:
                self.get_artifacts(run)
            logger.debug(f'Finish fetching artifacts')