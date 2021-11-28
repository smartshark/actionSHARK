import json
from typing import Optional

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

    __base_url = 'https://api.github.com/'

    __search_dict = {
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
        self.__headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authentication': f'token {self.token}'
        }


    @property
    def search_types(self):
        return [key for key in self.__search_dict.keys()]



    def save_JSON(self, save_path: str, response: requests.models.Response, verbose: bool = False) -> bool:
        """Saving a JSON response from GitHub API after checking response status.

        Args:
            save_path (str): File name and path to where the response should be saved.
            response (requests.models.Response): The response from GitHub API.
            verbose (bool): Print extra information to console.
        """
        if response.status_code == 200:
            if verbose: print('Successful Request!')

            response_JSON = response.json()
            if not response_JSON.get('workflow_runs'): return False

            with open( save_path, 'w', encoding='utf-8') as f:
                json.dump(response_JSON, f, indent=4)
            if verbose: print(f'Response is saved in: {save_path}')
            if verbose: print('-'*60)

            return True

        else:
            print(f'ERROR: {response.status_code}')
            if verbose: print(f'ERROR: {response.reason}')
            print('-'*60)

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
            url = self.__base_url + self.__search_dict[search_type]
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

        self.save_JSON(save_path, response)



    def get_workflow(self, owner: Optional[str] = None, repo: Optional[str] = None, save_path: Optional[str] = None, verbose: bool = False) -> None:
        """Fetching workflows data from GitHub API for specific repository and owner.

        Args:
            owner (Optional[str], optional): Owner of the repository. Defaults to None.
            repo (Optional[str], optional): Name of the repository. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/workflows/{owner}_{repo}_workflows.json".
            verbose (bool): Print extra information to console.
        """
        if not owner or not repo: raise 'Please make to sure to pass both the owner and repo names.'

        url = 'repos/{owner}/{repo}/actions/workflows'
        github_url = self.__base_url + url.format(owner=owner, repo=repo)

        response = requests.request('GET', github_url, headers=self.__headers)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/workflows/{owner}_{repo}_workflows.json'

        self.save_JSON(save_path, response)



    def get_organization_repostries(self, organization: Optional[str] = None, save_path: Optional[str] = None, verbose: bool = False) -> None:
        """Fetching repositories data from GitHub API for specific organization.

        Args:
            organization (Optional[str], optional): Organization name. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/repos/{organization}_repos.json".
            verbose (bool): Print extra information to console.
        """
        if not organization : raise 'Please pass the organization name.'

        # url = 'orgs/{org}/actions/permissions/repositories'
        url = 'orgs/{org}/repos'
        github_url = self.__base_url + url.format(org=organization)

        response = requests.request('GET', github_url, headers=self.__headers)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/repos/{organization}_repos.json'

        self.save_JSON(save_path, response)



    def get_runs(self, owner: Optional[str] = None, repo: Optional[str] = None, per_page: int = 100, page: int = 1, created = None, exclude_pull_requests: bool = True, save_path: Optional[str] = None, verbose: bool = False) -> None:
        """Fetching workflow runs data from GitHub API for specific repository and owner.

        Args:
            owner (Optional[str], optional): Owner of the repository. Defaults to None.
            repo (Optional[str], optional): Name of the repository. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/runs/{owner}_{repo}_runs.json".
            verbose (bool): Print extra information to console.
        """

        # https://api.github.com/repos/freeCodeCamp/freeCodeCamp/actions/runs?page=1&per_page=100&sort=created_at&order=desc&created=2021-11-28

        if not owner or not repo: raise 'Please make to sure to pass both the owner and repo names.'

        q = {'per_page': str(per_page), 'created': created, 'exclude_pull_requests': str(exclude_pull_requests) }
        if not created: del q['created']

        url = 'repos/{owner}/{repo}/actions/runs'
        github_url = self.__base_url + url.format(owner=owner, repo=repo) + f'?{self.parameter_constructor(q)}'

        next_page = 0
        while True:

            next_page += page
            github_url += f'&page={next_page}'

            response = requests.request('GET', github_url, headers=self.__headers)

            if verbose: print('GitHub API URL:', github_url)

            if not save_path:
                if not created: save_path = f'./data/runs/{owner}_{repo}_runs_{next_page}.json'
                else: save_path = f'./data/runs/{owner}_{repo}_runs_{created}_{next_page}.json'

            if not self.save_JSON(save_path, response): break

            github_url = github_url[:-len(f'&page={next_page}')]


    def get_runs_artifacts(self, owner: Optional[str] = None, repo: Optional[str] = None, run_id: int = None, save_path: Optional[str] = None, verbose: bool = False) -> None:
        """Fetching run artifacts data from GitHub API for specific repository, owner, and run.

        Args:
            owner (Optional[str], optional): Owner of the repository. Defaults to None.
            repo (Optional[str], optional): Name of the repository. Defaults to None.
            run_id (int, optional): Run id. Defaults to None.
            save_path (Optional[str], optional): File name and path to where the response should be saved. Defaults to "./data/runs/artifacts/{owner}_{repo}_run_{run_id}_artifacts.json".
            verbose (bool): Print extra information to console.
        """

        if not owner or not repo or not run_id: raise 'Please make to sure to pass both the owner and repo names.'
        url = 'repos/{owner}/{repo}/actions/runs/{run_id}/artifacts'
        github_url = self.__base_url + url.format(owner=owner, repo=repo, run_id=run_id)

        response = requests.request('GET', github_url, headers=self.__headers)

        if verbose: print('GitHub API URL:', github_url)

        if not save_path:
            save_path = f'./data/runs/artifacts/{owner}_{repo}_run_{run_id}_artifacts.json'

        self.save_JSON(save_path, response, verbose)

if __name__ == '__main__':


    cls_GitHub = GitHub('settings.json')

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
    #     cls_GitHub.get_runs_artifacts(run['repository']['owner']['login'],run['repository']['name'],run['id'])
    #     # break
    # print('count_runs:', count_runs)


    owner_name = 'freeCodeCamp'
    repo_name = 'freeCodeCamp'
    cls_GitHub.get_runs(owner_name, repo_name, verbose=True)
    # cls_GitHub.get_runs(owner_name, repo_name, created='2021-11-28')