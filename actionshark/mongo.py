from pycoshark.utils import *
from pymongo import MongoClient
from mongoengine import Document, StringField, IntField, ObjectIdField, DateTimeField, ListField, BooleanField, DictField

# https://cloud.mongodb.com/v2/6182ecb3f5d77671953f0a32#clusters
# mongodb+srv://<username>:<password>@cluster0.3dpvx.mongodb.net/DB_name


class GitHub_Repository(Document):
    id = IntField(unique=True)
    name = StringField()
    description =  StringField()
    # "owner": { # do users/organization instead of for owners and contributor
    #     "login": "freeCodeCamp",
    #     "id": 9892522,
    #     "type": "Organization",
    # },
    pass



class GitHub_Workflow(Document):
    id = IntField(unique=True)
    name = StringField()
    path = StringField()
    state = StringField()
    created_at = DateTimeField(default=None)
    updated_at = DateTimeField(default=None)
    pass



class GitHub_Run(Document):
    id = IntField(unique=True)
    name = StringField()
    head_branch = StringField()
    run_number = IntField()
    event = StringField(max_length=15, required=True)
    status = StringField()
    conclusion = StringField()
    workflow_id = ObjectIdField()
    pull_requests =  DateTimeField(default=None)
    created_at = DateTimeField(default=None)
    updated_at = DateTimeField(default=None)
    run_attempt = IntField()
    run_started_at = DateTimeField(default=None)
    head_commit =  ObjectIdField()
    pass



class GitHub_Job(Document):
    id = IntField(unique=True)
    name = StringField()
    run_number = ObjectIdField()
    run_attempt = IntField()
    status = StringField()
    conclusion = StringField()
    started_at = DateTimeField(default=None)
    completed_at = DateTimeField(default=None)
    steps = ListField( DictField() )
    runner_id = IntField()
    runner_name = StringField()
    runner_group_id = IntField()
    runner_group_name = StringField()
    pass



class GitHub_Artifacts(Document):
    id = IntField(unique=True)
    name = StringField()
    size_in_bytes = IntField()
    archive_download_url = StringField()
    expired = BooleanField()
    created_at = DateTimeField(default=None)
    updated_at = DateTimeField(default=None)
    expires_at = DateTimeField(default=None)
    pass



class Mongo:
    __conn_uri = create_mongodb_uri_string(db_user=None, db_password=None, db_hostname='localhost', db_port=27017, db_authentication_database=None, db_ssl_enabled=False)
    __conn = MongoClient(__conn_uri)

    def is_connected(self):
        return print(self.__conn)


if __name__ == '__main__':

    cls_mongo = Mongo()
    cls_mongo.is_connected()