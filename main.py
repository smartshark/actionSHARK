import os
import sys
import argparse


from pycoshark.utils import get_base_argparser
from actionshark.config import Config
'''
github token
github repo
githubowner
github action
github run id
github job id
github artifacts id
mongo db name
mongo db user
mongo db password
mongo db host
mongo db port
mongo db cluster url
'''

'''
Scenarios to cover:
1. if not token or env var and owner and repo  - github error
2. if db name == localhost and db port then no db name or db password
3. if  not db name or not db password or not ...
4.
'''

def start():
    # parser = get_base_argparser('Collects information from command line.', '0.0.1')
    parser = argparse.ArgumentParser('Collects information from command line.', '0.0.1')

    # GitHub Args
    parser.add_argument('-gt', '--github-token', help='', required=False, type=str)
    parser.add_argument('-gtv', '--github-token-env', help='', required=False, type=str)
    parser.add_argument('-go', '--github-owner', help='', required=True, type=str)
    parser.add_argument('-gr', '--github-repository', help='', required=True, type=str)
    parser.add_argument('-gwork', '--github-workflow', help='', required=False, type=int)
    parser.add_argument('-grun', '--github-run', help='', required=False, type=int)
    parser.add_argument('-gjob', '--github-job', help='', required=False, type=int)


    # MongoDB Args
    # handeled with get_base_argparser()
    # parser.add_argument('-mh', '--mongodb-host', help='', required=False, default='localhost')
    # parser.add_argument('-mp', '--mongodb-port', help='', required=False, default=27017, type=int)
    # parser.add_argument('-mu', '--mongodb-username', help='', required=False, type=str)
    # parser.add_argument('-mpass', '--mongodb-password', help='', required=False, type=str)
    # parser.add_argument('-mdb', '--mongodb-database', help='', required=False, type=str)
    # parser.add_argument('-mc', '--mongodb-cluster-url', help='', required=False, type=str)



    # General
    parser.add_argument('--debug', help='Sets the debug level.', default='DEBUG',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

    args = parser.parse_args()
    print(args)
    print()
    print(os.environ.get(args.github_token_env))
    # cfg = Config(args)


if __name__ == "__main__":
    start()