import json
from typing import Optional
from time import sleep
import os
import sys
import datetime as dt
import requests



class GitHub():
    """
    Managing different type of get Request to fetch data from GitHub REST API"""

    api_url = 'https://api.github.com/'
    __headers = {'Accept': 'application/vnd.github.v3+json'}

    total_requests = 0
    current_action = None

    actions_url = {
        'repos': 'orgs/{org}/repos?per_page={per_page}',
        'workflows': 'repos/{owner}/{repo}/actions/workflows?per_page={per_page}',
        'runs': 'repos/{owner}/{repo}/actions/runs?per_page{per_page}',
        'jobs': 'repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page{per_page}',
        'artifacts': 'repos/{owner}/{repo}/actions/runs/{run_id}/artifacts?per_page{per_page}'
    }


    def __init__(self, owner: Optional[str] = None, repo: Optional[str] = None, per_page: int = 100, file_path: Optional[str] = None, env_variable: Optional[str] = None, debug_mode: bool = True, sleep_interval: int = 2, verbose: bool = True) -> None:
        """Extract Token from settings file or environment variable for Authentication.

        Args:
            file_path (Optional[str], optional): [description]. Defaults to None.
            env_variable (Optional[str], optional): [description]. Defaults to None.
            create_folders (bool, optional): [description]. Defaults to True.
        """

        # *DEVELOPPING
        if debug_mode: self.create_folders()

        # check either json file or environment variable got passed
        if not file_path and not env_variable:
            print(f'ERROR: Add the path to JSON file with Access Token')
            sys.exit(1)

        # check owner and repo
        if not owner or not repo:
            print('Please make to sure to pass both the owner and repo names.')
            sys.exit(1)

        # get token from environment variable
        if env_variable:
            self.__token = os.environ.get(env_variable)

        # get token from a json file
        else:
            if not file_path.split('.')[-1] == 'json':
                print('Please pass a "json" file path or add file extention in case the file is "json".')
                sys.exit(1)

            with open(file_path, 'r', encoding='utf-8') as f:
                lines = json.load(f)
            self.__token = lines.get('access_token')

            if not self.__token:
                print('Please set the token key to "access_token".')
                sys.exit(1)



        if not self.__token:
            print(f'ERROR retriving token, please make sure you set the "file_path" or "env_variable" correctly.')
            sys.exit(1)


        # add token to header and check initial quota
        self.__headers['Authorization'] = f'token {self.__token}'
        # main variables
        self.owner = owner
        self.repo = repo
        self.per_page = per_page
        self.page = 1
        self.sleep_betw_requests = sleep_interval
        self.verbose = verbose

        # initiate limit variables
        self.limit = None
        self.remaining = None
        self.reset_datetime = self.get_dt_now()
        self.last_stop_datetime = self.get_dt_now()


        # update limit variables and error margin
        self.limit, self.remaining, self.reset_datetime = self.get_limit()
        self.remaining -= 2
        self.reset_datetime += dt.timedelta(seconds=2)




    def __str__(self) -> str:
        return f"""
        Owner/Org: {self.owner}
        Repository: {self.repo}
        API URL: {self.api_url}
        Limit requests: {self.limit}
        Remaining requests: {self.remaining}
        Next Reset: {self.reset_datetime}
        Last Stop: {self.last_stop_datetime}
        SleepInterval: {self.sleep_betw_requests}
        verbose: {self.verbose}""".replace("        ", "")



    # *DEVELOPPING
    def create_folders(self):
        # main data
        if not os.path.exists('data'): os.mkdir('data')
        # search
        if not os.path.exists('data/search'): os.mkdir('data/search')
        # repositories
        if not os.path.exists('data/repositories'): os.mkdir('data/repositories')
        # workflows
        if not os.path.exists('data/workflows'): os.mkdir('data/workflows')
        # runs
        if not os.path.exists('data/runs'): os.mkdir('data/runs')
        # jobs
        if not os.path.exists('data/jobs'): os.mkdir('data/jobs')
        # artifacts
        if not os.path.exists('data/artifacts'): os.mkdir('data/artifacts')



    def get_dt_now(self) -> dt:
        return dt.datetime.now().replace(microsecond=0)



    def limit_handler(self) -> bool:
        """Get Request manager

        Args:
            url (Optional[str], optional): [description]. Defaults to None.
            header (Optional[dict], optional): [description]. Defaults to None.
            verbose (bool, optional): [description]. Defaults to False.

        Returns:
            requests.Response: return response as received
        """

        # if an hour passed and requests are not triggered, renew limit variables
        # if  (self.get_dt_now() - dt.timedelta(hours=1) ) >= self.last_stop_datetime:
        #     self.remaining, self.reset_datetime = self.get_limit()

        #     # add error margin
        #     self.remaining -= 2
        #     self.reset_datetime -= dt.timedelta(seconds=2)
        #     self.last_stop_datetime = self.get_dt_now()
        #     ...

        # # handel limitation
        # if self.remaining == 1:
        #     # save last action to continue
        #     # function
        #     # page
        #     #
        #     #
        #     #
        #     #
        #     self.last_stop_datetime = dt.datetime.now().replace(microsecond=0)
        #     self.force_to_sleep = self.last_stop_datetime - self.reset_datetime + dt.timedelta(seconds=2)
        #     sleep()


        # updating variables to deal with limits
        self.total_requests += 1
        # self.remaining -= 1

        ...



    # *DEBUGGING
    def save_JSON(self, response: json, save_path: Optional[str] = None) -> None:
        """Saving a JSON response from GitHub API after checking response status.

        Args:
            response (requests.models.Response): The response from GitHub API.
            save_path (str): File name and path to where the response should be saved.
            checker (Optional[str], optional): Key to check in JSON response in case the response is empty. Defaults to None.
            verbose (bool): Print extra information to console.

        Returns:
            bool: True if response is not empty and saved saved successfully, otherwise False.
        """

            # save file
        with open( save_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=4)

        if self.verbose:
            print(f'Response is saved in: {save_path}')
            print('_'*(25+len(save_path)))



    def authenticate_user(self):
        """[summary]

        Returns:
            [type]: [description]
        """

        basic_auth = requests.get(self.api_url + 'user', self.__headers)

        if basic_auth.status_code == 200:

            basic_auth_json = basic_auth.json()

            if self.verbose:
                print('Successful Request:', basic_auth.status_code)
                print(basic_auth_json['name'])
                print(basic_auth_json['html_url'])
                print('_'*60)

            return True
        else:
            print(basic_auth.status_code)
            print(basic_auth.reason)
            return False



    def get_limit(self, verbose: bool = False):
        """Collect limitation parameters.

        Args:
            verbose (bool, optional): [description]. Defaults to False.

        Returns:
            [type]: [description]
        """

        response = requests.get(self.api_url + 'rate_limit', headers=self.__headers)

        if response.status_code == 200:
            temp = response.json()['resources']['core']
            remaining = temp["remaining"]
            reset_datetime = dt.datetime.fromtimestamp(temp["reset"])
            limit = temp["limit"]

            if verbose: # local verbose
                print(f'Limit :{limit}')
                print(f'Used :{temp["used"]}')
                print(f'Remaining :{remaining}')
                print(f'Reset :{reset_datetime}')

            return limit, remaining, reset_datetime
        else:
            print(response.status_code)
            print(response.reason)
            return False,  False



    def paginating(self, github_url: Optional[str] = None, checker: Optional[str] = None, save_path: Optional[str] = None):
        """Fetch all pages for an action and handel API limitation.

        Args:
            github_url (Optional[str], optional): [description]. Defaults to None.
            checker (Optional[str], optional): [description]. Defaults to None.
            save_path (Optional[str], optional): [description]. Defaults to None.
        """

        while True:
            # append page number to url
            github_url += f'&page={self.page}'

            # get response
            response = requests.get(github_url, headers=self.__headers)

            if self.verbose:
                print('GitHub API URL:', github_url)

            # Abort if unknown error occurred
            if response.status_code != 200 and response.status_code != 403:
                print("Error in request.")
                sys.exit(1)

            # handel api limit
            if response.status_code == 403:
                # update variable
                # handel limit error
                ...

            # check if key is not empty
            response_JSON = response.json()
            if checker:
                response_JSON = response_JSON.get(checker)


            if not response_JSON:
                if self.verbose:
                    print(f'Response is Empty ... Stopping.\n', '-+'*30, sep='')
                break

            # *DEBUGGING
            iter_save_path = save_path[:-5] + f'_{self.page}.json'
            self.save_JSON(response_JSON, iter_save_path)

            # handel page incrementing
            github_url = github_url[:-len(f'&page={self.page}')]
            self.page += 1

            # sleep between requests
            sleep(self.sleep_betw_requests)



    def get_owner_repostries(self, save_path: Optional[str] = None) -> None:
        """Fetching repositories data from GitHub API for specific owner.

        Args:
            save_path (Optional[str], optional): [description]. Defaults to None.
        """

        self.current_action = 'repos'

        url = self.actions_url['repos'].format(org=self.owner, per_page=self.per_page)
        github_url = self.api_url + url

        if not save_path:
            save_path = f'./data/repositories/{self.owner}_repos.json'

        self.paginating(github_url, None, save_path)



    def get_workflows(self, save_path: Optional[str] = None) -> None:
        """Fetching workflows data from GitHub API for specific repository and owner.

        Args:
            save_path (Optional[str], optional): [description]. Defaults to None.
        """

        self.current_action = 'workflows'

        url = self.actions_url['workflows'].format(owner=self.owner, repo=self.repo, per_page=self.per_page)
        github_url = self.api_url + url

        if not save_path:
            save_path = f'./data/workflows/{self.owner}_{self.repo}_workflows.json'

        self.paginating(github_url, 'workflows', save_path)



    def get_runs(self, exclude_pull_requests: bool = False, save_path: Optional[str] = None) -> None:
        """Fetching workflow runs data from GitHub API for specific repository and owner.

        Args:
            exclude_pull_requests (bool, optional): [description]. Defaults to False.
            save_path (Optional[str], optional): [description]. Defaults to None.
        """

        self.current_action = 'runs'

        url = self.actions_url['runs'].format(owner=self.owner, repo=self.repo, per_page=self.per_page)
        url += f'exclude_pull_requests={str(exclude_pull_requests)}'
        github_url = self.api_url + url

        if not save_path:
            save_path = f'./data/runs/{self.owner}_{self.repo}_runs.json'

        self.paginating(github_url, 'workflow_runs', save_path)



    def get_run_artifacts(self, run_id: Optional[int] = None, save_path: Optional[str] = None) -> None:
        """Fetching run artifacts data from GitHub API for specific repository, owner, and run.

        Args:
            run_id (Optional[int], optional): [description]. Defaults to None.
            save_path (Optional[str], optional): [description]. Defaults to None.
        """

        if not run_id:
            print('Please make to sure to pass both the owner and repo names.')
            sys.exit(1)

        self.current_action = 'artifacts'

        url = self.actions_url['artifacts'].format(owner=self.owner, repo=self.repo, run_id=run_id, per_page=self.per_page)
        github_url = self.api_url + url

        if not save_path:
            save_path = f'./data/artifacts/{self.owner}_{self.repo}_run_{run_id}_artifacts.json'

        self.paginating(github_url, 'artifacts', save_path)



    def get_run_jobs(self, run_id: Optional[int] = None, save_path: Optional[str] = None) -> None:
        """Fetching run artifacts data from GitHub API for specific repository, owner, and run.

        Args:
            run_id (Optional[int], optional): [description]. Defaults to None.
            save_path (Optional[str], optional): [description]. Defaults to None.
        """

        if not run_id:
            print('Please make to sure to pass the owner, repo name, and run id.')
            sys.exit(1)

        self.current_action = 'jobs'

        url = self.actions_url['jobs'].format(owner=self.owner, repo=self.repo, run_id=run_id, per_page=self.per_page)
        github_url = self.api_url + url

        if not save_path:
            save_path = f'./data/jobs/{self.owner}_{self.repo}_run_{run_id}_jobs.json'

        self.paginating(github_url, 'jobs', save_path)



    def get_all(self, run_id: Optional[int] = None, save_path: Optional[str] = None) -> None:

        # if not self.authenticate_user(verbose):
        #     print("Wrong token, please try again.")
        #     sys.exit(1)

        # cls_GitHub.get_owner_repostries(owner, verbose=verbose)

        # cls_GitHub.get_workflows(owner, repo, verbose=verbose)

        # cls_GitHub.get_runs(owner, repo, verbose=verbose)

        # TODO function to loop over run ids

        # cls_GitHub.get_run_jobs(owner, repo, verbose=verbose)

        # cls_GitHub.get_run_artifacts(owner, repo, verbose=verbose)

        ...



if __name__ == '__main__':

    # owner_name = 'freeCodeCamp'
    # repo_name = 'freeCodeCamp'
    # run_id = 1511226364
    # run_id = 1514809363


    owner_name = 'apache'
    repo_name = 'commons-lang'

    cls_GitHub = GitHub(owner=owner_name, repo=repo_name, env_variable='GITHUB_Token', verbose=True)
    print(cls_GitHub)
    # cls_GitHub.authenticate_user()


    # cls_GitHub.get_owner_repostries()
    # cls_GitHub.get_workflows()
    # cls_GitHub.get_runs()
    # cls_GitHub.get_all()

    cls_GitHub.get_limit(verbose=True)