import os
import json
import datetime as dt
from mongoengine import connect
from mongoengine.fields import StringField
import pycoshark.utils as utils

# https://cloud.mongodb.com/v2/6182ecb3f5d77671953f0a32#clusters
# mongodb+srv://<username>:<password>@cluster0.3dpvx.mongodb.net/DB_name


class Repositories(utils.Document):
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
    topics = utils.ListField( StringField() )



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
        return f'id : {self.id}\nname : {self.name}\npath : {self.path}\nstate : {self.state}\ncreated_at : {self.created_at}\nupdated_at : {self.updated_at}'



class Runs(utils.Document):
    id = utils.IntField(unique=True)
    name = utils.StringField()
    head_branch = utils.StringField()
    run_number = utils.IntField()
    event = utils.StringField(max_length=15, required=True)
    status = utils.StringField()
    conclusion = utils.StringField()
    workflow_id = utils.ObjectIdField()
    pull_requests =  utils.DateTimeField(default=None)
    created_at = utils.DateTimeField(default=None)
    updated_at = utils.DateTimeField(default=None)
    run_attempt = utils.IntField()
    run_started_at = utils.DateTimeField(default=None)
    head_commit =  utils.ObjectIdField()



class Jobs(utils.Document):
    id = utils.IntField(unique=True)
    name = utils.StringField()
    run_number = utils.ObjectIdField()
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



class Artifacts(utils.Document):
    id = utils.IntField(unique=True)
    name = utils.StringField()
    size_in_bytes = utils.IntField()
    archive_download_url = utils.StringField()
    expired = utils.BooleanField()
    created_at = utils.DateTimeField(default=None)
    updated_at = utils.DateTimeField(default=None)
    expires_at = utils.DateTimeField(default=None)



class Mongo:
    __conn_uri = utils.create_mongodb_uri_string(db_user=None, db_password=None, db_hostname='localhost', db_port=27017, db_authentication_database=None, db_ssl_enabled=False)


    def __init__(self, db_name: str = 'actionshark') -> None:
        self.__operations = {
            'save_workflows': ('workflows', self.__create_mongo_workflow),
            'save_repositories': (None, self.__create_mongo_repo)
        }
        connect(db_name, host=self.__conn_uri)



    def insert_JSON(self, file_path: str = None, operation: str = None):

        if not file_path or not operation : return None


        if operation in self.__operations.keys():
            key, func = self.__operations[operation]
        else: return None

        if not file_path.split('.')[-1] == 'json':
            if file_path[-1] != '/': file_path += '/'
            files = [file_path + f for f in os.listdir(file_path)]
        else:
            files = [file_path]


        for file in files:
            with open( file, 'r', encoding='utf-8') as data:
                documents = json.load(data)

            if key: documents = documents[key]

            for document in documents:
                func(document).save()



    def __create_mongo_workflow(self, obj: json = None):
        if not obj: return None

        workflow = Workflows()

        workflow.id = int( obj.get('id') )
        workflow.name = obj.get('name')
        workflow.path = obj.get('path')
        workflow.state = obj.get('state')
        workflow.created_at = dt.datetime.fromisoformat( obj.get('created_at') )
        workflow.updated_at = dt.datetime.fromisoformat( obj.get('updated_at') )

        return workflow



    def __create_mongo_repo(self, obj: json = None):
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



if __name__ == '__main__':

    cls_mongo = Mongo()
    # cls_mongo.insert_JSON('./data/workflows/apache_commons-lang_workflows_1.json', 'save_workflows')
    cls_mongo.insert_JSON('./data/repositories', 'save_repositories')