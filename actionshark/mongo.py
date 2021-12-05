import pycoshark.utils as utils

# https://cloud.mongodb.com/v2/6182ecb3f5d77671953f0a32#clusters
# mongodb+srv://<username>:<password>@cluster0.3dpvx.mongodb.net/DB_name


class Repositories(utils.Document):
    id = utils.IntField(unique=True)
    name = utils.StringField()
    description =  utils.StringField()
    # "owner": { # do users/organization instead of for owners and contributor
    #     "login": "freeCodeCamp",
    #     "id": 9892522,
    #     "type": "Organization",
    # },
    pass



class Workflows(utils.Document):
    id = utils.IntField(unique=True)
    name = utils.StringField()
    path = utils.StringField()
    state = utils.StringField()
    created_at = utils.DateTimeField(default=None)
    updated_at = utils.DateTimeField(default=None)
    pass



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
    pass



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
    pass



class Artifacts(utils.Document):
    id = utils.IntField(unique=True)
    name = utils.StringField()
    size_in_bytes = utils.IntField()
    archive_download_url = utils.StringField()
    expired = utils.BooleanField()
    created_at = utils.DateTimeField(default=None)
    updated_at = utils.DateTimeField(default=None)
    expires_at = utils.DateTimeField(default=None)
    pass



class Mongo:
    __conn_uri = utils.create_mongodb_uri_string(db_user=None, db_password=None, db_hostname='localhost', db_port=27017, db_authentication_database=None, db_ssl_enabled=False)
    __conn = utils.MongoClient(__conn_uri)

    def is_connected(self):
        return print(self.__conn)


if __name__ == '__main__':

    cls_mongo = Mongo()
    cls_mongo.is_connected()