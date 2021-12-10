import os


class Config:

    def __init__(self, args):

        self.token = args.token
        self.env_variable = args.token_env
        self.owner = args.owner
        self.repo = args.repository
        self.db_database = args.db_database
        self.db_user = args.db_user
        self.db_password = args.db_password
        self.db_hostname = args.db_hostname
        self.db_port = args.db_port
        self.db_authentication = args.db_authentication
        self.db_ssl = args.ssl

        # Handel token
        # if environment variable passed and not concrete token
        if self.env_variable and not self.token:
            self.env_variable = os.environ.get(args.token_env)
        # favor token over environment variable
        else:
            self.env_variable = None

        # self._validate_config()



    def __str__(self):
        return '\n'.join([
            f'token: {self.token}',
            f'env_variable: {self.env_variable}',
            f'owner: {self.owner}',
            f'repo: {self.repo}',
            f'db_database: {self.db_database}',
            f'db_user: {self.db_user}',
            f'db_password: {self.db_password}',
            f'db_hostname: {self.db_hostname}',
            f'db_port: {self.db_port}',
            f'db_authentication: {self.db_authentication}',
            f'db_ssl: {self.db_ssl}'
        ])



    def _validate_config(self):
        pass
