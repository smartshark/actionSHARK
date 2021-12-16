import os
import json
import datetime as dt
from typing import DefaultDict, Optional
import logging

from mongoengine import connect, EmbeddedDocumentListField
from mongoengine.document import Document
import pycoshark.utils as utils

# start logger
logger = logging.getLogger(__name__)


class Repositories(utils.Document):
    # to remove after finding the similar one in smartShark
    meta = {
        'collection': 'repositories'
    }
    id = utils.IntField(primary_key=True)
    name = utils.StringField()
    description =  utils.StringField()
    fork = utils.BooleanField()
    forks_count = utils.IntField()
    size = utils.IntField()
    created_at = utils.DateTimeField(default=None)
    updated_at = utils.DateTimeField(default=None)
    pushed_at = utils.DateTimeField(default=None)
    stargazers_count = utils.IntField()
    watchers_count = utils.IntField()
    open_issues = utils.IntField()
    visibility = utils.StringField()
    topics = utils.ListField( utils.StringField() )

    def __str__(self):
        return '\n'.join([
            f'id : {self.id}',
            f'name : {self.name}',
            f'description : {self.description}',
            f'fork : {self.fork}',
            f'forks_count : {self.forks_count}',
            f'size : {self.size}',
            f'created_at : {self.created_at}',
            f'updated_at : {self.updated_at}',
            f'pushed_at : {self.pushed_at}',
            f'stargazers_count : {self.stargazers_count}',
            f'watchers_count : {self.watchers_count}',
            f'open_issues : {self.open_issues}',
            f'visibility : {self.visibility}',
            f'topics : {self.topics}'
        ])


class Workflows(utils.Document):
    meta = {
        'collection': 'workflows'
    }
    id = utils.IntField(primary_key=True)
    name = utils.StringField()
    path = utils.StringField()
    state = utils.StringField()
    created_at = utils.DateTimeField(default=None)
    updated_at = utils.DateTimeField(default=None)

    def __str__(self):
        return '\n'.join([
            f'id : {self.id}',
            f'name : {self.name}',
            f'path : {self.path}',
            f'state : {self.state}',
            f'created_at : {self.created_at}',
            f'updated_at : {self.updated_at}'
        ])


class RunPullRequests(Document):
    id = utils.IntField()
    number = utils.IntField()
    head_id = utils.IntField()
    head_ref = utils.StringField()
    head_name = utils.StringField()
    base_id = utils.IntField()
    base_ref = utils.StringField()
    base_name = utils.StringField()


class Runs(utils.Document):
    meta = {
        'collection': 'runs'
    }
    id = utils.IntField(primary_key=True)
    name = utils.StringField()
    run_number = utils.IntField()
    event = utils.StringField(required=True)
    status = utils.StringField()
    conclusion = utils.StringField()
    workflow_id = utils.IntField()
    pull_requests =  EmbeddedDocumentListField(RunPullRequests, default=[])
    created_at = utils.DateTimeField(default=None)
    updated_at = utils.DateTimeField(default=None)
    run_attempt = utils.IntField(default=None)
    run_started_at = utils.DateTimeField(default=None)
    head_commit =  utils.DictField(default=None) # TODO either delete or select keys
    head_repository =  utils.DictField(default=None) # TODO either delete or select keys

    def __str__(self):
        return '\n'.join([
            f'id : {self.id}',
            f'name : {self.name}',
            f'run_number : {self.run_number}',
            f'event : {self.event}',
            f'status : {self.status}',
            f'conclusion : {self.conclusion}',
            f'workflow_id : {self.workflow_id}',
            f'created_at : {self.created_at}',
            f'updated_at : {self.updated_at}',
            f'run_attempt : {self.run_attempt}',
            f'run_started_at : {self.run_started_at}',
            f'head_commit : {self.head_commit}',
            f'head_repository : {self.head_repository}'
        ])


class JobSteps(Document):
    name = utils.StringField()
    status = utils.StringField()
    conclusion = utils.StringField()
    number = utils.IntField()
    started_at = utils.DateTimeField(default=None)
    completed_at = utils.DateTimeField(default=None)


class Jobs(utils.Document):
    meta = {
        'collection': 'jobs'
    }
    id = utils.IntField(primary_key=True)
    name = utils.StringField()
    run_id = utils.IntField()
    run_attempt = utils.IntField()
    status = utils.StringField()
    conclusion = utils.StringField()
    started_at = utils.DateTimeField(default=None)
    completed_at = utils.DateTimeField(default=None)
    steps = EmbeddedDocumentListField(JobSteps, default=[])
    runner_id = utils.IntField(default=None)
    runner_name = utils.StringField(default=None)
    runner_group_id = utils.IntField(default=None)
    runner_group_name = utils.StringField(default=None)

    def __str__(self):
        return '\n'.join([
            f'id : {self.id}',
            f'name : {self.name}',
            f'run_id : {self.run_id}',
            f'run_attempt : {self.run_attempt}',
            f'status : {self.status}',
            f'conclusion : {self.conclusion}',
            f'started_at : {self.started_at}',
            f'completed_at : {self.completed_at}',
            f'runner_id : {self.runner_id}',
            f'runner_name : {self.runner_name}',
            f'runner_group_id : {self.runner_group_id}',
            f'runner_group_name : {self.runner_group_name}'
        ])


class Artifacts(utils.Document):
    meta = {
        'collection': 'artifacts'
    }
    id = utils.IntField(primary_key=True)
    name = utils.StringField()
    size_in_bytes = utils.IntField()
    archive_download_url = utils.StringField()
    expired = utils.BooleanField()
    created_at = utils.DateTimeField(default=None)
    updated_at = utils.DateTimeField(default=None)
    expires_at = utils.DateTimeField(default=None)

    def __str__(self):
        return '\n'.join([
            f'id : {self.id}',
            f'name : {self.name}',
            f'size_in_bytes : {self.size_in_bytes}',
            f'archive_download_url : {self.archive_download_url}',
            f'expired : {self.expired}',
            f'created_at : {self.created_at}',
            f'updated_at : {self.updated_at}',
            f'expires_at : {self.expires_at}'
        ])


class Mongo:

    def __init__(self, db_user: Optional[str] = None, db_password: Optional[str] = None, db_hostname: Optional[str] = None, db_port: Optional[int] = None, db_name: Optional[str] = None, db_authentication_database: Optional[str] = None, db_ssl_enabled: bool = False, verbose: bool = False) -> None:
        self.__operations = {
            'repos': self.__create_mongo_repo,
            'workflows': self.__create_mongo_workflow,
            'runs': self.__create_mongo_run,
            'jobs': self.__create_mongo_job,
            'artifacts': self.__create_mongo_artifact
        }

        self.verbose = verbose

        self.__conn_uri = utils.create_mongodb_uri_string(db_user, db_password, db_hostname, db_port, db_authentication_database, db_ssl_enabled)
        self.db_name = db_name
        self.__conn = connect(db_name, host=self.__conn_uri)

        logger.debug(f'Mongo connected to {db_name}')
        # logger.debug(f'Connection parameter db_user: {db_user}, db_password: {db_password}, db_hostname: {db_hostname}, db_port: {db_port}, db_authentication_database: {db_authentication_database}, db_ssl_enabled: {db_ssl_enabled},')


    @property
    def repositories(self):
        return Repositories


    @property
    def workflows(self):
        return Workflows


    @property
    def runs(self):
        return Runs


    @property
    def jobs(self):
        return Jobs


    @property
    def artifacts(self):
        return Artifacts


    def drop_database(self) -> None:
        """Drop current connected database.
        """
        self.__conn.drop_database(self.db_name)
        logger.debug(f'Database { self.db_name } is dropped')

        if self.verbose:
            print(f'Database { self.db_name } is dropped')



    def drop_collection(self, col_name: Optional[str] = None) -> None:
        """Drop collection if found.

        Args:
            col_name (str): Collection name. Defaults to None.
        """

        # check if collection name is passed
        if not col_name:
            return None

        # check if collection is in database
        if col_name not in self.__conn.get_database(self.db_name).list_collection_names():
            logger.debug(f'Collection { col_name } is dropped')

            if self.verbose:
                print(f'Collection {col_name} not found.')

            return False

        # Delete if found
        self.__conn.get_database(self.db_name).drop_collection(col_name)

        logger.debug(f'Collection { col_name } is dropped')

        if self.verbose:
            print(f'Collection {col_name} is dropped.')

        return True



    def save_documents(self, documents: Optional[dict] = None, action: Optional[str] = None) -> None:
        """Loop over Elements, to map and save. This function should be passed to GitHub instance as "save_mongo=save_documents".

        Args:
            documents (dict): Elements. Defaults to None.
            action (str): Action name to map objects to. Defaults to None.
        """

        # check if documents and action are not None
        if not documents or not action:
            logger.debug(f'No documents or action got passed')
            return None

        # check if the passed action is available
        if action not in self.__operations.keys():
            logger.debug(f'Action {action} was not found in predefined operations')
            return None

        # call the mapping function
        func = self.__operations[action]

        # map and save all documents
        for document in documents:
                func(document).save()



    def __create_mongo_repo(self, obj: Optional[dict] = None) -> Repositories:
        """Map object to the appropriate files of Repositories.

        Args:
            obj (dict): The Object to map. Defaults to None.

        Returns:
            Repositories: A MongoDB object ready to save.
        """
        if not obj: return None

        repo = Repositories()

        repo.id = int( obj.get('id') )
        repo.name = obj.get('name')
        repo.description = obj.get('description')
        repo.fork = bool( obj.get('fork') )
        repo.forks_count = int( obj.get('forks_count') )
        repo.size = int( obj.get('size') )
        repo.created_at = self.parse_date( obj.get('created_at') )
        repo.updated_at = self.parse_date( obj.get('updated_at') )
        repo.pushed_at = self.parse_date( obj.get('pushed_at') )
        repo.stargazers_count = int( obj.get('stargazers_count') )
        repo.watchers_count = int( obj.get('watchers_count') )
        repo.open_issues = int( obj.get('open_issues') )
        repo.visibility = obj.get('visibility')
        repo.topics = obj.get('topics')

        return repo



    def __create_mongo_workflow(self, obj: Optional[dict] = None) -> Workflows:
        """Map object to the appropriate files of Workflows.

        Args:
            obj (dict): The Object to map. Defaults to None.

        Returns:
            Workflows: A MongoDB object ready to save.
        """
        if not obj: return None

        workflow = Workflows()

        workflow.id = int( obj.get('id') )
        workflow.name = obj.get('name')
        workflow.path = obj.get('path')
        workflow.state = obj.get('state')
        workflow.created_at = self.parse_date( obj.get('created_at'), True)
        workflow.updated_at = self.parse_date( obj.get('updated_at'), True)

        return workflow



    def __create_mongo_run(self, obj: Optional[dict] = None) -> Runs:
        """Map object to the appropriate files of Runs.

        Args:
            obj (dict): The Object to map. Defaults to None.

        Returns:
            Runs: A MongoDB object ready to save.
        """
        if not obj: return None

        run = Runs()

        run.id = int( obj.get('id') )
        run.name = obj.get('name')
        run.run_number = int( obj.get('run_number') )
        run.event = obj.get('event')
        run.status = obj.get('status')
        run.conclusion = obj.get('conclusion')
        run.workflow_id = int( obj.get('workflow_id') )
        run.pull_requests = obj.get('pull_requests')
        run.created_at = self.parse_date( obj.get('created_at') )
        run.updated_at = self.parse_date( obj.get('updated_at') )
        run.run_attempt = int( obj.get('run_attempt') )
        run.run_started_at = obj.get('run_started_at')
        run.head_commit = obj.get('head_commit')
        run.head_repository = obj.get('head_repository')

        return run


    def __create_mongo_run_pull_request(self, obj: Optional[dict] = None) -> RunPullRequests:
        """Map object to the appropriate files of RunPullRequests.

        Args:
            obj (dict): The Object to map. Defaults to None.

        Returns:
            RunPullRequests: A MongoDB object ready to save.
        """
        if not obj: return None

        run_pull = RunPullRequests()

        run_pull.id = obj.get('id')
        run_pull.number = obj.get('number')
        run_pull.head_ref = obj['head'].get('ref')
        run_pull.head_id = obj['head']['repo'].get('id')
        run_pull.head_name = obj['head']['repo'].get('name')
        run_pull.base_ref = obj['base'].get('ref')
        run_pull.base_id = obj['base']['repo'].get('id')
        run_pull.base_name = obj['base']['repo'].get('name')

        return run_pull



    def __create_mongo_job(self, obj: Optional[dict] = None) -> Jobs:
        """Map object to the appropriate files of Jobs.

        Args:
            obj (dict): The Object to map. Defaults to None.

        Returns:
            Jobs: A MongoDB object ready to save.
        """
        if not obj: return None

        job = Jobs()

        job.id = int( obj.get('id') )
        job.name = obj.get('name')
        job.run_id = int( obj.get('run_id') )
        job.run_attempt = int( obj.get('run_attempt') )
        job.status = obj.get('status')
        job.conclusion = obj.get('conclusion')
        job.started_at = self.parse_date( obj.get('started_at') )
        job.completed_at = self.parse_date( obj.get('completed_at') )
        job.steps = obj.get('steps')
        job.runner_id = int( obj.get('runner_id') ) if obj.get('runner_id') else None
        job.runner_name = obj.get('runner_name')
        job.runner_group_id = int( obj.get('runner_group_id') ) if obj.get('runner_group_id') else None
        job.runner_group_name = obj.get('runner_group_name')

        return job


    def __create_mongo_job_step(self, obj: Optional[dict] = None) -> JobSteps:
        """Map object to the appropriate files of JobSteps.

        Args:
            obj (dict): The Object to map. Defaults to None.

        Returns:
            JobSteps: A MongoDB object ready to save.
        """
        if not obj: return None

        job_step = JobSteps()

        job_step.name = obj.get('name')
        job_step.status = obj.get('status')
        job_step.conclusion = obj.get('conclusion')
        job_step.number = obj.get('number')
        job_step.started_at = self.parse_date( obj.get('started_at'), True )
        job_step.completed_at = self.parse_date( obj.get('completed_at'), True )

        return job_step



    def __create_mongo_artifact(self, obj: Optional[dict] = None) -> Artifacts:
        """Map object to the appropriate files of Artifacts.

        Args:
            obj (dict): The Object to map. Defaults to None.

        Returns:
            Artifacts: A MongoDB object ready to save.
        """
        if not obj: return None

        artifact = Artifacts()

        artifact.id = int( obj.get('id') )
        artifact.name = obj.get('name')
        artifact.size_in_bytes = int( obj.get('size_in_bytes') )
        artifact.archive_download_url = obj.get('archive_download_url')
        artifact.expired = bool( obj.get('expired') )
        artifact.created_at = self.parse_date( obj.get('created_at') )
        artifact.updated_at = self.parse_date( obj.get('updated_at') )
        artifact.expires_at = self.parse_date( obj.get('expires_at') )

        return artifact


    def parse_date(self, value: str = None, is_millisecond: bool = False):
        """Convert Datetime string to actual Datetime.

        Args:
            value (str): The datetime string to be converted. Defaults to None.
            is_millisecond (bool, optional): If datetime has millisecond in the string. Defaults to False.

        Returns:
            datetime: datetime formated or None if no string passed.
        """
        if not value:
            return None

        if is_millisecond:
            return dt.datetime.strptime( value, '%Y-%m-%dT%H:%M:%S.%f%z' )
        else:
            return dt.datetime.strptime( value, '%Y-%m-%dT%H:%M:%S%z' )
