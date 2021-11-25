import json
import requests
from requests.auth import HTTPBasicAuth


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


    def __init__(self, file_path: str = None) -> None:
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



    def save_JSON(self, save_path: str, response: requests.models.Response):
        if response.status_code == 200:
            print('Successful Request!')
            with open( save_path, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f, indent=4)
            print(f'Response is saved in {save_path}')
        else:
            print(f'ERROR: {response.status_code}')
            print(f'ERROR: {response.reason}')

    def query_string(self, q: dict):
        """
        Reformatting deictionry to GitHub API URL syntax"""
        return '&'.join(['='.join(i) for i in q.items()])



    def get_search(self, search_type: str, q: dict = None, save_path: str = None):
        """
        constructing URL to fetch responses"""
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


        if not save_path:
            save_path = f'./data/search/search_{search_type}.json'
        self.save_JSON(save_path, response)



    def get_workflow(self, owner: str = None, repo: str = None, pp_results: int = 100, page_number: int = 1, save_path: str = None):
        """
        constructing URL to fetch actions"""
        if not owner or not repo: raise 'Please make to sure to pass both the owner and repo names.'

        url = 'repos/{owner}/{repo}/actions/workflows'
        github_url = self.base_url + url.format(owner=owner, repo=repo) + f'?per_page={pp_results}&paage={page_number}'

        response = requests.request('GET', github_url, headers=self.headers)

        if not save_path:
            save_path = f'./data/workflows/{owner}_{repo}_workflows.json'

        self.save_JSON(save_path, response)



    def get_orgnization_repostries(self, orgnization: str = None, save_path: str = None):

        """
        constructing URL to fetch repos permissions"""
        if not orgnization : raise 'Please pass the orgnization name.'

        # url = 'orgs/{org}/actions/permissions/repositories'
        url = 'orgs/{org}/repos'
        github_url = self.base_url + url.format(org=orgnization)

        response = requests.request('GET', github_url, headers=self.headers)

        if not save_path:
            save_path = f'./data/repos/{orgnization}_repos.json'

        self.save_JSON(save_path, response)



    def get_workflow_runs(self, owner: str = None, repo: str = None, pp_results: int = 100, page_number: int = 1, save_path: str = None):
        """
        constructing URL to fetch actions"""
        if not owner or not repo: raise 'Please make to sure to pass both the owner and repo names.'

        url = 'repos/{owner}/{repo}/actions/runs'
        # github_url = self.base_url + url.format(owner=owner, repo=repo) + f'?per_page={pp_results}&paage={page_number}'
        github_url = self.base_url + url.format(owner=owner, repo=repo)

        response = requests.request('GET', github_url, headers=self.headers)

        if not save_path:
            save_path = f'./data/runs/{owner}_{repo}_runs.json'

        self.save_JSON(save_path, response)


    def get_workflow_runs_artifacts(self, owner: str = None, repo: str = None, run_id: int = None, pp_results: int = 100, page_number: int = 1, save_path: str = None):
        if not owner or not repo or not run_id: raise 'Please make to sure to pass both the owner and repo names.'
        url = '/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts'
        github_url = self.base_url + url.format(owner=owner, repo=repo, run_id=run_id)

        response = requests.request('GET', github_url, headers=self.headers)

        if not save_path:
            save_path = f'./data/runs/artifacts/{owner}_{repo}_run_{run_id}_artifacts.json'

        self.save_JSON(save_path, response)

if __name__ == '__main__':


    cls = GitHub('settings.json')

    q = {
        'language' : 'python',
        'star' : '>50',
        'label' : 'open'
    }
    cls.get_search('issues', q)


    # Get all organization
    q = {'type':'org'}
    cls.get_search('users', q)

    # owner_name = 'smartshark'
    # repo_name = 'issueSHARK'

    owner_name = 'fireship-io'
    # repo_name = 'fireship' # neither artifacts or workflows
    repo_name = '225-github-actions-demo' # only workflows
    cls.get_workflow(owner_name, repo_name)
    cls.get_workflow_runs(owner_name, repo_name)

    org_name = 'fireship-io'
    cls.get_orgnization_repostries(org_name)

    org_name = 'smartshark'
    cls.get_orgnization_repostries(org_name)