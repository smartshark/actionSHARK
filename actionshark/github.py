import json
from typing import Optional
from time import sleep
import os
import sys
from dataclasses import dataclass, field
import requests
from requests.api import head, options


'''
Notes:
API requests using Basic Authentication or OAuth, you can make up to 5,000 requests per hour.
Secondary rate limits are not intended to interfere with legitimate use of the API.
Your normal rate limits should be the only limit you target.

Errors:
400 Bad Request
401 Unauthorized
403 Forbidden *
404 Not Found *
422 Unprocessable Entity
'''

# @dataclass
# class ErrorHandler():
#     error_code: int
#     is_error: bool = field(default=False)

#     @is_error.setter
#     def is_error(self, value: bool):
#         self.is_error = value

#     def error_handler(self):
#         if self.error_code == 200:
#             print('Successful Request.')
#             # log.debug('')
#             self.is_error = False

#         elif self.error_code == 403:
#             print('Limit exceeded.')
#             # log.debug('')
#             self.is_error = True

#         elif self.error_code == 404:
#             print('Error Request.')
#             # log.debug('')
#             self.is_error = True


class GitHub():
    """
    Managing different type of get Request to fetch data from GitHub REST API"""

    base_url = 'https://api.github.com/'

    __search_dict = {
        'issues' : 'search/issues',
        'code' : 'search/code',
        'repositories' : 'search/repositories',
        'users': 'search/users'
    }

    __sleep_interval = 2

    total_requests = 0


    def __init__(self, file_path: Optional[str] = None, env_variable: Optional[str] = None, with_token: bool = True, create_folders: bool = True) -> None:
        """
        Extract Token from settings file for Authentication"""
        if create_folders: self.create_folders()
        self.__headers = {'Accept': 'application/vnd.github.v3+json'}


        if with_token:
            if not file_path and not env_variable:
                print(f'ERROR: Add the path to JSON file with Access Token')
                sys.exit(1)

            if file_path:
                if not file_path.split('.')[-1] == 'json':
                    print('Please pass a "json" file path or add file extention in case the file is "json".')
                    sys.exit(1)

                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = json.load(f)
                self.__token = lines.get('access_token')

                if not self.__token:
                    print('Please set the token key to "access_token".')
                    sys.exit(1)

            elif env_variable:
                self.__token = os.environ.get(env_variable)
            else: self.__token = None


            if self.__token:
                self.__headers['Authorization'] = f'token {self.__token}'
            else:
                print(f'ERROR retriving token, please make sure you set the "file_path" or "env_variable" correctly.')
                sys.exit(1)



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



    @property
    def sleep_time(self):
        return self.__sleep_interval



    @sleep_time.setter
    def sleep_time(self, t):
        self.__sleep_interval = t


    @sleep_time.deleter
    def sleep_time(self):
        self.__sleep_interval = 0



    @property
    def search_types(self):
        return [key for key in self.__search_dict.keys()]



    def handel_requests(self, url: Optional[str] = None, header: Optional[dict] = None, verbose: bool = False):
        if not url or not header: sys.exit(1)

        response = requests.get(url, headers=header)
        self.total_requests += 1
        if verbose: print('Total Requests:', self.total_requests)

        return response



    def save_JSON(self, response: requests.models.Response, save_path: Optional[str] = None, checker: Optional[str] = None, verbose: bool = False) -> bool:
        """Saving a JSON response from GitHub API after checking response status.

        Args:
            save_path (str): File name and path to where the response should be saved.
            response (requests.models.Response): The response from GitHub API.
            verbose (bool): Print extra information to console.
        """
        if response.status_code == 200:

            response_JSON = response.json()

            if verbose: print('Successful Request!')

            if checker:
                if not response_JSON.get(checker):
                    if verbose: print(f'Response is Empty ... Stopping.\n', '-+'*30, sep='')
                    return False
            else:
                if not response_JSON: return False


            with open( save_path, 'w', encoding='utf-8') as f:
                json.dump(response_JSON, f, indent=4)
            if verbose: print(f'Response is saved in: {save_path}')
            if verbose: print('_'*(22+len(save_path)))

            return True

        else:
            print(f'ERROR: {response.status_code}')
            if verbose: print(f'ERROR: {response.reason}')
            print('-'*len(response.reason))

            return False



    def authenticate_user(self, verbose: bool = False):

        basic_auth = self.handel_requests(self.base_url + 'user', self.__headers, verbose)

        if basic_auth.status_code == 200:
            # self.save_JSON(basic_auth, './auth.json', '', verbose)
            basic_auth_json = basic_auth.json()
            if verbose:
                print(basic_auth.status_code)
                print(basic_auth_json['name'])
                print(basic_auth_json['html_url'])
                print('_'*60)

            return True
        else:
            print(basic_auth.status_code)
            print(basic_auth.reason)
            return False



    def get_limit(self, verbose: bool = False):

        response = self.handel_requests(self.base_url + 'rate_limit', self.__headers, verbose)

        if response.status_code == 200:
            self.save_JSON(response, './rate-limit.json', '', verbose)
            if verbose:
                print(response.status_code)
                print('_'*60)

            return True
        else:
            print(response.status_code)
            print(response.reason)
            return False



    def parameter_constructor(self, q: dict):
        """Reformatting dictionary to GitHub API URL syntax.

        Args:
            q (dict): Query parameters as dictionary.

        Returns:
            str: Query string to add to GitHub URL
        """
        return '&'.join(['='.join(i) for i in q.items()])



    def paginating(self, github_url: Optional[str] = None, page: int = 1, checker: Optional[str] = None, save_path: Optional[str] = None, use_sleep: bool = True, verbose: bool = False):

        while True:

            github_url += f'&page={page}'

            response = self.handel_requests(github_url, self.__headers, verbose)

            if verbose: print('GitHub API URL:', github_url)

            iter_save_path = save_path[:-5] + f'_{page}.json'

            if not self.save_JSON(response, iter_save_path, checker, verbose): break

            github_url = github_url[:-len(f'&page={page}')]

            page += 1

            if use_sleep: sleep(self.__sleep_interval)



    def get_search(self, search_type: Optional[str] = None, q: Optional[dict] = None, per_page: int = 100, page: int = 1, save_path: Optional[str] = None, use_sleep: bool = True, verbose: bool = False) -> None:
        """Fetching search data from GitHub API for types like issues, user, ... etc.

        Args:
            search_type (str): Use get_search_types() to get all search types.
            q (dict, optional): Search parameters as a Dictionary like {"parameter": "value"}. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/search/search_{search_type}.json".
            verbose (bool): Print extra information to console.
        """
        if search_type in self.__search_dict:
            url = self.base_url + self.__search_dict[search_type]
        else:
            print('Unrecognized or Unsupported search criteria!')

        if q != None:
            q = self.parameter_constructor(q)
            github_url = url + '?q=' + q
        else:
            github_url = url

        github_url += '&per_page=' + str(per_page)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/search/search_{search_type}.json'

        self.paginating(github_url, page, 'items', save_path, use_sleep, verbose)



    def get_owner_repostries(self, owner: Optional[str] = None, per_page: int = 100, page: int = 1, save_path: Optional[str] = None, use_sleep: bool = True, verbose: bool = False) -> None:
        """Fetching repositories data from GitHub API for specific owner.

        Args:
            owner (Optional[str], optional): owner name. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/repos/{owner}_repos.json".
            verbose (bool): Print extra information to console.
        """
        if not owner :
            print('Please pass the owner name.')
            sys.exit(1)

        # url = 'orgs/{org}/actions/permissions/repositories'
        url = 'orgs/{org}/repos?per_page={per_page}'
        github_url = self.base_url + url.format(org=owner, per_page=per_page)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/repositories/{owner}_repos.json'

        self.paginating(github_url, page, None, save_path, use_sleep, verbose)



    def get_workflow(self, owner: Optional[str] = None, repo: Optional[str] = None, per_page: int = 100, page: int = 1, save_path: Optional[str] = None, use_sleep: bool = True, verbose: bool = False) -> None:
        """Fetching workflows data from GitHub API for specific repository and owner.

        Args:
            owner (Optional[str], optional): Owner of the repository. Defaults to None.
            repo (Optional[str], optional): Name of the repository. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/workflows/{owner}_{repo}_workflows.json".
            verbose (bool): Print extra information to console.
        """
        if not owner or not repo:
            print('Please make to sure to pass both the owner and repo names.')
            sys.exit(1)

        url = 'repos/{owner}/{repo}/actions/workflows?per_page={per_page}'

        github_url = self.base_url + url.format(owner=owner, repo=repo, per_page=per_page)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/workflows/{owner}_{repo}_workflows.json'

        self.paginating(github_url, page, 'workflows', save_path, use_sleep, verbose)



    def get_runs(self, owner: Optional[str] = None, repo: Optional[str] = None, per_page: int = 100, page: int = 1, exclude_pull_requests: bool = True, save_path: Optional[str] = None, use_sleep: bool = True, verbose: bool = False) -> None:
        """Fetching workflow runs data from GitHub API for specific repository and owner.

        Args:
            owner (Optional[str], optional): Owner of the repository. Defaults to None.
            repo (Optional[str], optional): Name of the repository. Defaults to None.
            per_page (int, optional): [description]. Defaults to 100.
            page (int, optional): [description]. Defaults to 1.
            created ([type], optional): [description]. Defaults to None.
            exclude_pull_requests (bool, optional): [description]. Defaults to True.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/runs/{owner}_{repo}_runs.json".
            use_sleep (bool, optional): [description]. Defaults to False.
            verbose (bool): Print extra information to console.
        """

        if not owner or not repo:
            print('Please make to sure to pass both the owner and repo names.')
            sys.exit(1)

        q = {'per_page': str(per_page), 'exclude_pull_requests': str(exclude_pull_requests) }

        url = 'repos/{owner}/{repo}/actions/runs'
        github_url = self.base_url + url.format(owner=owner, repo=repo) + f'?{self.parameter_constructor(q)}'

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/runs/{owner}_{repo}_runs.json'

        self.paginating(github_url, page, 'workflow_runs', save_path, use_sleep, verbose)



    def get_run_artifacts(self, owner: Optional[str] = None, repo: Optional[str] = None, run_id: Optional[int] = None, per_page: int = 100, page: int = 1, save_path: Optional[str] = None, use_sleep: bool = True, verbose: bool = False) -> None:
        """Fetching run artifacts data from GitHub API for specific repository, owner, and run.

        Args:
            owner (Optional[str], optional): Owner of the repository. Defaults to None.
            repo (Optional[str], optional): Name of the repository. Defaults to None.
            run_id (int, optional): Run id. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/runs/artifacts/{owner}_{repo}_run_{run_id}_artifacts.json".
            verbose (bool): Print extra information to console.
        """

        if not owner or not repo or not run_id:
            print('Please make to sure to pass both the owner and repo names.')
            sys.exit(1)

        url = 'repos/{owner}/{repo}/actions/runs/{run_id}/artifacts?per_page{per_page}'
        github_url = self.base_url + url.format(owner=owner, repo=repo, run_id=run_id, per_page=per_page)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/artifacts/{owner}_{repo}_run_{run_id}_artifacts.json'

        self.paginating(github_url, page, 'artifacts', save_path, use_sleep, verbose)



    def get_run_jobs(self, owner: Optional[str] = None, repo: Optional[str] = None, run_id: Optional[int] = None, per_page: int = 100, page: int = 1, save_path: Optional[str] = None, use_sleep: bool = True, verbose: bool = False) -> None:
        """Fetching run artifacts data from GitHub API for specific repository, owner, and run.

        Args:
            owner (Optional[str], optional): Owner of the repository. Defaults to None.
            repo (Optional[str], optional): Name of the repository. Defaults to None.
            run_id (int, optional): Run id. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/runs/artifacts/{owner}_{repo}_run_{run_id}_artifacts.json".
            verbose (bool): Print extra information to console.
        """

        if not owner or not repo or not run_id:
            print('Please make to sure to pass the owner, repo name, and run id.')
            sys.exit(1)

        url = 'repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page{per_page}'
        github_url = self.base_url + url.format(owner=owner, repo=repo, run_id=run_id, per_page=per_page)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/jobs/{owner}_{repo}_run_{run_id}_jobs.json'

        self.paginating(github_url, page, 'jobs', save_path, use_sleep, verbose)



    def get_all(self, owner: Optional[str] = None, repo: Optional[str] = None, run_id: Optional[int] = None, per_page: int = 100, page: int = 1, save_path: Optional[str] = None, use_sleep: bool = True, verbose: bool = False) -> None:

        if not self.authenticate_user(verbose):
            print("Wrong token, please try again.")
            sys.exit(1)

        # cls_GitHub.get_owner_repostries(owner_name, verbose=True)

        # cls_GitHub.get_workflow(owner_name, repo_name, verbose=True)

        # cls_GitHub.get_runs(owner_name, repo_name, verbose=True)

        # TODO function to loop over run ids

        # cls_GitHub.get_run_jobs(owner_name, repo_name, verbose=True)

        # cls_GitHub.get_run_artifacts(owner_name, repo_name, verbose=True)


if __name__ == '__main__':

    cls_GitHub = GitHub(env_variable = 'GITHUB_Token')
    cls_GitHub.get_limit(verbose=True)


    # owner_name = 'freeCodeCamp'
    # repo_name = 'freeCodeCamp'
    # run_id = 1511226364
    # run_id = 1514809363


    owner_name = 'apache'
    repo_name = 'commons-lang'
    # cls_GitHub.get_all(owner_name, repo_name, verbose=True)