import json
from typing import Optional
from time import sleep
import os

import requests
from requests.auth import HTTPBasicAuth


'''
Notes:
API requests using Basic Authentication or OAuth, you can make up to 5,000 requests per hour
checking limit: https://api.github.com/users/hatahetahmad
Secondary rate limits are not intended to interfere with legitimate use of the API.
Your normal rate limits should be the only limit you target.

'''

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

    __sleep_interval = 1

    __basic_auth_json = None


    def __init__(self, file_path: Optional[str] = None, env_variable: Optional[str] = None, with_token: bool = True) -> None:
        """
        Extract Token from settings file for Authentication"""

        self.__headers = {'Accept': 'application/vnd.github.v3+json'}


        if with_token:
            if not file_path and not env_variable:
                print(f'ERROR: Add the path to JSON file with Access Token')
                exit()

            if file_path:
                if not file_path.split('.')[-1] == 'json':
                    print('Please pass a "json" file path or add file extention in case the file is "json".')
                    exit()

                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = json.load(f)
                self.__token = lines.get('access_token')

                if not self.__token:
                    print('Please set the token key to "access_token".')
                    exit()

            elif env_variable:
                self.__token = os.environ.get(env_variable)
            else: self.__token = None

            if self.__token:
                self.__headers['Authorization'] = f'token {self.__token}'
            else:
                print(f'ERROR retriving token, please make sure you set the "file_path" or "env_variable" correctly.')
                exit()

        print(self.__headers)


    def authenticate_user(self, token: str = None, verbose: bool = False):
        if not token: token = self.__token
        else: self.__token = token

        basic_auth = requests.get(self.base_url + 'user', headers=self.__headers)

        if basic_auth.status_code == 200:
            self.save_JSON('./auth.json', basic_auth, '', verbose)

            self.__basic_auth_json = basic_auth.json()

            if verbose:
                print(basic_auth.status_code)
                print(self.__basic_auth_json['name'])
                print(self.__basic_auth_json['html_url'])


            return True
        else:
            print(basic_auth.status_code)
            print(basic_auth.reason)
            return False

    @property
    def sleep_time(self):
        return self.__sleep_interval

    @sleep_time.setter
    def sleep_time(self, t):
        self.__sleep_interval = t

    @property
    def search_types(self):
        return [key for key in self.__search_dict.keys()]



    def save_JSON(self, save_path: str, response: requests.models.Response, checker: Optional[str] = None, verbose: bool = False) -> bool:
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



    def parameter_constructor(self, q: dict):
        """Reformatting dictionary to GitHub API URL syntax.

        Args:
            q (dict): Query parameters as dictionary.

        Returns:
            str: Query string to add to GitHub URL
        """
        return '&'.join(['='.join(i) for i in q.items()])



    def get_search(self, search_type: str, q: dict = None, save_path: Optional[str] = None, verbose: bool = False) -> None:
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
            print('Unrecognized / Unsupported search criteria!')

        if q != None:
            q = self.parameter_constructor(q)
            github_url = url + '?q=' + q
        else:
            github_url = url

        response = requests.request('GET', github_url, headers=self.__headers)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/search/search_{search_type}.json'

        self.save_JSON(save_path, response=response, checker='items', verbose=verbose)



    def get_workflow(self, owner: Optional[str] = None, repo: Optional[str] = None, save_path: Optional[str] = None, verbose: bool = False) -> None:
        """Fetching workflows data from GitHub API for specific repository and owner.

        Args:
            owner (Optional[str], optional): Owner of the repository. Defaults to None.
            repo (Optional[str], optional): Name of the repository. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/workflows/{owner}_{repo}_workflows.json".
            verbose (bool): Print extra information to console.
        """
        if not owner or not repo:
            print('Please make to sure to pass both the owner and repo names.')
            exit()

        url = 'repos/{owner}/{repo}/actions/workflows'
        github_url = self.base_url + url.format(owner=owner, repo=repo)

        response = requests.request('GET', github_url, headers=self.__headers)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/workflows/{owner}_{repo}_workflows.json'

        self.save_JSON(save_path, response=response, checker='workflows', verbose=verbose)



    def get_organization_repostries(self, organization: Optional[str] = None, save_path: Optional[str] = None, verbose: bool = False) -> None:
        """Fetching repositories data from GitHub API for specific organization.

        Args:
            organization (Optional[str], optional): Organization name. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/repos/{organization}_repos.json".
            verbose (bool): Print extra information to console.
        """
        if not organization :
            print('Please pass the organization name.')
            exit()

        # url = 'orgs/{org}/actions/permissions/repositories'
        url = 'orgs/{org}/repos?per_page=100'
        github_url = self.base_url + url.format(org=organization)

        response = requests.request('GET', github_url, headers=self.__headers)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/repos/{organization}_repos.json'

        self.save_JSON(save_path, response=response, checker=None, verbose=verbose)



    def get_runs(self, owner: Optional[str] = None, repo: Optional[str] = None, per_page: int = 100, page: int = 1, created = None, exclude_pull_requests: bool = True, save_path: Optional[str] = None, use_sleep: bool = False, verbose: bool = False) -> None:
        """Fetching workflow runs data from GitHub API for specific repository and owner.

        Args:
            owner (Optional[str], optional): Owner of the repository. Defaults to None.
            repo (Optional[str], optional): Name of the repository. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/runs/{owner}_{repo}_runs.json".
            verbose (bool): Print extra information to console.
        """

        # https://api.github.com/repos/freeCodeCamp/freeCodeCamp/actions/runs?page=1&per_page=100&sort=created_at&order=desc&created=2021-11-28

        if not owner or not repo:
            print('Please make to sure to pass both the owner and repo names.')
            exit()

        q = {'per_page': str(per_page), 'created': created, 'exclude_pull_requests': str(exclude_pull_requests) }
        if not created: del q['created']

        url = 'repos/{owner}/{repo}/actions/runs'
        github_url = self.base_url + url.format(owner=owner, repo=repo) + f'?{self.parameter_constructor(q)}'

        if not save_path:
                if not created: save_path = f'./data/runs/{owner}_{repo}_runs.json'
                else: save_path = f'./data/runs/{owner}_{repo}_runs_{created}.json'

        page -=1
        while True:

            page += 1
            github_url += f'&page={page}'

            response = requests.request('GET', github_url, headers=self.__headers)

            if verbose: print('GitHub API URL:', github_url)

            iter_save_path = save_path[:-5] + f'_{page}.json'

            if not self.save_JSON(save_path=iter_save_path, response=response, checker='workflow_runs', verbose=verbose): break

            github_url = github_url[:-len(f'&page={page}')]

            if use_sleep: sleep(self.__sleep_interval)


    def get_run_artifacts(self, owner: Optional[str] = None, repo: Optional[str] = None, run_id: int = None, save_path: Optional[str] = None, verbose: bool = False) -> None:
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
            exit()
        url = 'repos/{owner}/{repo}/actions/runs/{run_id}/artifacts'
        github_url = self.base_url + url.format(owner=owner, repo=repo, run_id=run_id)

        response = requests.request('GET', github_url, headers=self.__headers)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/runs/artifacts/{owner}_{repo}_run_{run_id}_artifacts.json'

        self.save_JSON(save_path, response=response, checker='artifacts', verbose=verbose)


    def get_run_jobs(self, owner: Optional[str] = None, repo: Optional[str] = None, run_id: int = None, save_path: Optional[str] = None, verbose: bool = False) -> None:
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
            exit()

        url = 'repos/{owner}/{repo}/actions/runs/{run_id}/jobs'
        github_url = self.base_url + url.format(owner=owner, repo=repo, run_id=run_id)

        response = requests.request('GET', github_url, headers=self.__headers)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/runs/artifacts/{owner}_{repo}_run_{run_id}_artifacts.json'

        self.save_JSON(save_path, response=response, checker='jobs', verbose=verbose)

if __name__ == '__main__':


    cls_GitHub = GitHub(file_path = 'settings.json')
    # cls_GitHub = GitHub(env_variable = 'GITHUB_Token')


    # cls_GitHub.authenticate_user(verbose=True)

    # q = {
    #     'language' : 'python',
    #     'star' : '>50',
    #     'label' : 'open'
    # }
    # cls_GitHub.get_search('issues', q)


    # Get all organization
    # q = {'type':'org'}
    # cls_GitHub.get_search('users', q)

    # owner_name = 'smartshark'
    # repo_name = 'issueSHARK'

    # owner_name = 'fireship-io'
    # # repo_name = 'fireship' # neither artifacts or workflows
    # repo_name = '225-github-actions-demo' # only workflows
    # cls_GitHub.get_workflow(owner_name, repo_name)
    # cls_GitHub.get_runs(owner_name, repo_name)

    # org_name = 'fireship-io'
    # cls_GitHub.get_organization_repostries(org_name)

    # org_name = 'smartshark'
    # cls_GitHub.get_organization_repostries(org_name)

    # get all artifacts for runs
    # with open ('./data/fireship-io_225-github-actions-demo_action_runs.json', 'r', encoding='utf-8') as f:
    #     runs = json.load(f)

    # count_runs = 0
    # for run in runs['workflow_runs']:
    #     # print(run['repository']['owner']['login'],run['repository']['name'],type(run['id']) )
    #     count_runs += 1
    #     cls_GitHub.get_run_artifacts(run['repository']['owner']['login'],run['repository']['name'],run['id'])
    #     # break
    # print('count_runs:', count_runs)


    # owner_name = 'freeCodeCamp'
    # repo_name = 'freeCodeCamp'
    # last_stop = 251
    # cls_GitHub.sleep_time = 1
    # cls_GitHub.get_runs(owner_name, repo_name, page=last_stop, use_sleep=True, verbose=True)
    # cls_GitHub.get_runs(owner_name, repo_name, created='2021-11-28', use_sleep=True, verbose=True)