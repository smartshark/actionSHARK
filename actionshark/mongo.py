import os
import json
import datetime as dt
import github as gh
from typing import Optional

from mongoengine import connect
import pycoshark.utils as utils


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



class Runs(utils.Document):
    meta = {
        'collection': 'runs'
    }
    id = utils.IntField(primary_key=True)
    name = utils.StringField()
    run_number = utils.IntField()
    event = utils.StringField(max_length=15, required=True)
    status = utils.StringField()
    conclusion = utils.StringField()
    workflow_id = utils.IntField()
    pull_requests =  utils.ListField( utils.DictField(default=None) )
    created_at = utils.DateTimeField(default=None)
    updated_at = utils.DateTimeField(default=None)
    run_attempt = utils.IntField()
    run_started_at = utils.DateTimeField(default=None)
    head_commit =  utils.DictField()
    head_repository =  utils.DictField()

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
    steps = utils.ListField( utils.DictField() )
    runner_id = utils.IntField()
    runner_name = utils.StringField()
    runner_group_id = utils.IntField()
    runner_group_name = utils.StringField()

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
    __conn_uri = utils.create_mongodb_uri_string(db_user=None, db_password=None, db_hostname='localhost', db_port=27017, db_authentication_database=None, db_ssl_enabled=False)


    def __init__(self, db_name: str = 'actionshark') -> None:
        self.__operations = {
            'repos': self.__create_mongo_repo,
            'workflows': self.__create_mongo_workflow,
            'runs': self.__create_mongo_run,
            'jobs': self.__create_mongo_job,
            'artifacts': self.__create_mongo_artifact
        }

        connect(db_name, host=self.__conn_uri)



    def save_documents(self, documents: Optional[dict] = None, action: Optional[str] = None) -> None:

        if not documents or not action:
            return None

        if action not in self.__operations.keys():
            return None

        func = self.__operations[action]

        for document in documents:
                func(document).save()


    # *DEBUGGING
    def insert_JSON(self, file_path: Optional[str] = None, operation: Optional[str] = None) -> None:

        if not file_path or not operation:
            return None

        # load the action function
        if operation in self.__operations.keys():
            func = self.__operations[operation]
        else:
            return None


        # add all files to a list
        if not file_path.split('.')[-1] == 'json':
            if file_path[-1] != '/': file_path += '/'
            files = [file_path + f for f in os.listdir(file_path)]
        else:
            files = [file_path]


        # loop over all files in a directory
        for file in files:
            with open( file, 'r', encoding='utf-8') as data:
                documents = json.load(data)

            for document in documents:
                func(document).save()



    def __create_mongo_repo(self, obj: Optional[dict] = None) -> Repositories:
        if not obj: return None

        repo = Repositories()

        repo.id = int( obj.get('id') )
        repo.name = obj.get('name')
        repo.description = obj.get('description')
        repo.fork = bool( obj.get('fork') )
        repo.forks_count = int( obj.get('forks_count') )
        repo.size = int( obj.get('size') )
        repo.created_at = dt.datetime.strptime( obj.get('created_at'), '%Y-%m-%dT%H:%M:%SZ' )
        repo.updated_at = dt.datetime.strptime( obj.get('updated_at'), '%Y-%m-%dT%H:%M:%SZ' )
        repo.pushed_at = dt.datetime.strptime( obj.get('pushed_at'), '%Y-%m-%dT%H:%M:%SZ' )
        repo.stargazers_count = int( obj.get('stargazers_count') )
        repo.watchers_count = int( obj.get('watchers_count') )
        repo.open_issues = int( obj.get('open_issues') )
        repo.visibility = obj.get('visibility')
        repo.topics = obj.get('topics')

        return repo



    def __create_mongo_workflow(self, obj: Optional[dict] = None) -> Workflows:
        if not obj: return None

        workflow = Workflows()

        workflow.id = int( obj.get('id') )
        workflow.name = obj.get('name')
        workflow.path = obj.get('path')
        workflow.state = obj.get('state')
        workflow.created_at = dt.datetime.fromisoformat( obj.get('created_at') )
        workflow.updated_at = dt.datetime.fromisoformat( obj.get('updated_at') )

        return workflow



    def __create_mongo_run(self, obj: Optional[dict] = None) -> Runs:
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
        run.created_at = dt.datetime.strptime( obj.get('created_at'), '%Y-%m-%dT%H:%M:%SZ' )
        run.updated_at = dt.datetime.strptime( obj.get('updated_at'), '%Y-%m-%dT%H:%M:%SZ' )
        run.run_attempt = int( obj.get('run_attempt') )
        run.run_started_at = obj.get('run_started_at')
        run.head_commit = obj.get('head_commit')
        run.head_repository = obj.get('head_repository')

        return run



    def __create_mongo_job(self, obj: Optional[dict] = None) -> Jobs:
        if not obj: return None

        job = Jobs()

        job.id = int( obj.get('id') )
        job.name = obj.get('name')
        job.run_id = int( obj.get('run_id') )
        job.run_attempt = int( obj.get('run_attempt') )
        job.status = obj.get('status')
        job.conclusion = obj.get('conclusion')
        job.started_at = dt.datetime.strptime( obj.get('started_at'), '%Y-%m-%dT%H:%M:%SZ' )
        job.completed_at = dt.datetime.strptime( obj.get('completed_at'), '%Y-%m-%dT%H:%M:%SZ' )
        job.steps = obj.get('steps')
        job.runner_id = int( obj.get('runner_id') )
        job.runner_name = obj.get('runner_name')
        job.runner_group_id = int( obj.get('runner_group_id') )
        job.runner_group_name = obj.get('runner_group_name')

        return job



    def __create_mongo_artifact(self, obj: Optional[dict] = None) -> Artifacts:
        if not obj: return None

        artifact = Artifacts()

        artifact.id = int( obj.get('id') )
        artifact.name = obj.get('name')
        artifact.size_in_bytes = int( obj.get('size_in_bytes') )
        artifact.archive_download_url = obj.get('archive_download_url')
        artifact.expired = bool( obj.get('expired') )
        artifact.created_at = dt.datetime.strptime( obj.get('created_at'), '%Y-%m-%dT%H:%M:%SZ' )
        artifact.updated_at = dt.datetime.strptime( obj.get('updated_at'), '%Y-%m-%dT%H:%M:%SZ' )
        artifact.expires_at = dt.datetime.strptime( obj.get('expires_at'), '%Y-%m-%dT%H:%M:%SZ' )

        return artifact


if __name__ == '__main__':

    cls_mongo = Mongo()
    # cls_mongo.insert_JSON('./data/workflows', 'workflows')
    # cls_mongo.insert_JSON('./data/repositories', 'repositories')
    # cls_mongo.insert_JSON('./data/runs', 'runs')
    # cls_mongo.insert_JSON('./data/jobs', 'jobs')
    # cls_mongo.insert_JSON('./data/artifacts', 'artifacts')

    # for obj in Runs.objects():
    #    print(obj.id)