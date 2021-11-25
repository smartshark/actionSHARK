import json
import requests
from requests.auth import HTTPBasicAuth
from typing import Optional


class GitHub():
    """
    Managing different type of get Request to fetch data from GitHub REST API"""

    base_url = 'https://api.github.com/'

    search_types = {
        'issues' : 'search/issues',
        'code' : 'search/code',
        'repositories' : 'search/repositories',
        'users': 'search/users'
    }


    def __init__(self, file_path: Optional[str] = None) -> None:
        """
        Extract Token from settings file for Authentication"""
        if not file_path: raise f'ERROR: Add the path to JSON file with Access Token'

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = json.load(f)
        self.token = lines.get('access_token')
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authentication': f'token {self.token}'
        }



    def save_JSON(self, save_path: str, response: requests.models.Response, verbose: bool = False) -> str:
        """Saving a JSON response from GitHub API after checking response status.

        Args:
            save_path (str): File name and path to where the response should be saved.
            response (requests.models.Response): The response from GitHub API.
            verbose (bool): Print extra information to console.
        """
        if response.status_code == 200:
            if verbose: print('Successful Request!')
            with open( save_path, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f, indent=4)
            if verbose: print(f'Response is saved in: {save_path}')
            if verbose: print('-'*60)
        else:
            print(f'ERROR: {response.status_code}')
            if verbose: print(f'ERROR: {response.reason}')
            print('-'*60)



    def query_string(self, q: dict):
        """Reformatting deictionry to GitHub API URL syntax.

        Args:
            q (dict): Query parameters as dictionary.

        Returns:
            str: Query strin to add to GitHub URL
        """
        return '&'.join(['='.join(i) for i in q.items()])



    def get_search_types(self) -> list[str]:
        return [key for key in self.search_types.keys()]



    def get_search(self, search_type: str, q: dict = None, save_path: Optional[str] = None, verbose: bool = False) -> None:
        """Fetching search data from GitHub API for types like issues, user, ... etc.

        Args:
            search_type (str): Use get_search_types() to get all search types.
            q (dict, optional): Search parameters as a Dictionary like {"parameter": "value"}. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/search/search_{search_type}.json".
            verbose (bool): Print extra information to console.
        """
        if search_type in self.search_types:
            url = self.base_url + self.search_types[search_type]
        else:
            print('Unrecognized / Unsupported search criteria!')

        if q != None:
            q = self.query_string(q)
            github_url = url + '?q=' + q
        else:
            github_url = url

        response = requests.request('GET', github_url, headers=self.headers)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/search/search_{search_type}.json'

        self.save_JSON(save_path, response)



    def get_workflow(self, owner: Optional[str] = None, repo: Optional[str] = None, save_path: Optional[str] = None, verbose: bool = False) -> None:
        """Fetching workflows data from GitHub API for specific reposotory and owner.

        Args:
            owner (Optional[str], optional): Owner of the reposotory. Defaults to None.
            repo (Optional[str], optional): Name of the reposotory. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/workflows/{owner}_{repo}_workflows.json".
            verbose (bool): Print extra information to console.
        """
        if not owner or not repo: raise 'Please make to sure to pass both the owner and repo names.'

        url = 'repos/{owner}/{repo}/actions/workflows'
        github_url = self.base_url + url.format(owner=owner, repo=repo)

        response = requests.request('GET', github_url, headers=self.headers)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/workflows/{owner}_{repo}_workflows.json'

        self.save_JSON(save_path, response)



    def get_orgnization_repostries(self, orgnization: Optional[str] = None, save_path: Optional[str] = None, verbose: bool = False) -> None:
        """Fetching reosotories data from GitHub API for specific orgnization.

        Args:
            orgnization (Optional[str], optional): Orgnization name. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/repos/{orgnization}_repos.json".
            verbose (bool): Print extra information to console.
        """
        if not orgnization : raise 'Please pass the orgnization name.'

        # url = 'orgs/{org}/actions/permissions/repositories'
        url = 'orgs/{org}/repos'
        github_url = self.base_url + url.format(org=orgnization)

        response = requests.request('GET', github_url, headers=self.headers)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/repos/{orgnization}_repos.json'

        self.save_JSON(save_path, response)



    def get_workflow_runs(self, owner: Optional[str] = None, repo: Optional[str] = None, save_path: Optional[str] = None, verbose: bool = False) -> None:
        """Fetching workflow runs data from GitHub API for specific reposotory and owner.

        Args:
            owner (Optional[str], optional): Owner of the reposotory. Defaults to None.
            repo (Optional[str], optional): Name of the reposotory. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/runs/{owner}_{repo}_runs.json".
            verbose (bool): Print extra information to console.
        """
        if not owner or not repo: raise 'Please make to sure to pass both the owner and repo names.'

        url = 'repos/{owner}/{repo}/actions/runs'
        github_url = self.base_url + url.format(owner=owner, repo=repo)

        response = requests.request('GET', github_url, headers=self.headers)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/runs/{owner}_{repo}_runs.json'

        self.save_JSON(save_path, response)



    def get_workflow_runs_artifacts(self, owner: Optional[str] = None, repo: Optional[str] = None, run_id: int = None, save_path: Optional[str] = None, verbose: bool = False) -> None:
        """Fetching run artifacts data from GitHub API for specific reposotory, owner, and run.

        Args:
            owner (Optional[str], optional): Owner of the reposotory. Defaults to None.
            repo (Optional[str], optional): Name of the reposotory. Defaults to None.
            run_id (int, optional): Run id. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/runs/artifacts/{owner}_{repo}_run_{run_id}_artifacts.json".
            verbose (bool): Print extra information to console.
        """

        if not owner or not repo or not run_id: raise 'Please make to sure to pass both the owner and repo names.'
        url = 'repos/{owner}/{repo}/actions/runs/{run_id}/artifacts'
        github_url = self.base_url + url.format(owner=owner, repo=repo, run_id=run_id)

        response = requests.request('GET', github_url, headers=self.headers)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/runs/artifacts/{owner}_{repo}_run_{run_id}_artifacts.json'

        self.save_JSON(save_path, response, verbose)

if __name__ == '__main__':


    cls = GitHub('settings.json')

    # q = {
    #     'language' : 'python',
    #     'star' : '>50',
    #     'label' : 'open'
    # }
    # cls.get_search('issues', q)


    # Get all organization
    # q = {'type':'org'}
    # cls.get_search('users', q)

    # owner_name = 'smartshark'
    # repo_name = 'issueSHARK'

    # owner_name = 'fireship-io'
    # # repo_name = 'fireship' # neither artifacts or workflows
    # repo_name = '225-github-actions-demo' # only workflows
    # cls.get_workflow(owner_name, repo_name)
    # cls.get_workflow_runs(owner_name, repo_name)

    # org_name = 'fireship-io'
    # cls.get_orgnization_repostries(org_name)

    # org_name = 'smartshark'
    # cls.get_orgnization_repostries(org_name)

    # get all artifacts for runs
    # with open ('./data/fireship-io_225-github-actions-demo_action_runs.json', 'r', encoding='utf-8') as f:
    #     runs = json.load(f)

    # count_runs = 0
    # for run in runs['workflow_runs']:
    #     # print(run['repository']['owner']['login'],run['repository']['name'],type(run['id']) )
    #     count_runs += 1
    #     cls.get_workflow_runs_artifacts(run['repository']['owner']['login'],run['repository']['name'],run['id'])
    #     # break
    # print('count_runs:', count_runs)