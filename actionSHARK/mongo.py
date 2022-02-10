import sys
import datetime as dt
from typing import Optional, Any, Tuple, List
import logging

from pycoshark.utils import create_mongodb_uri_string
from pycoshark.mongomodels import VCSSystem, Commit

from mongoengine import connect
from mongoengine import (
    Document,
    StringField,
    DateTimeField,
    IntField,
    BooleanField,
    ObjectIdField,
    EmbeddedDocument,
    EmbeddedDocumentListField,
)


# start logger
logger = logging.getLogger("main.mongo")


class Workflow(Document):
    workflow_id = IntField()
    name = StringField()
    path = StringField(default=None)
    state = StringField()
    created_at = DateTimeField()
    updated_at = DateTimeField()
    project_url = StringField(default=None)
    project_id = ObjectIdField(default=None)
    vcs_system_id = ObjectIdField(default=None)


class RunPullRequest(EmbeddedDocument):
    pull_request_id = IntField()
    pull_request_number = IntField()

    target_id = IntField()
    target_branch = StringField()
    target_sha = StringField()
    target_url = StringField()

    source_id = IntField()
    source_branch = StringField()
    source_sha = StringField()
    source_url = StringField()


class Run(Document):
    run_id = IntField()
    run_number = IntField()
    event = StringField()
    status = StringField()
    conclusion = StringField()
    workflow_id = ObjectIdField()
    pull_requests = EmbeddedDocumentListField(RunPullRequest, default=[])
    created_at = DateTimeField()
    updated_at = DateTimeField()
    run_attempt = IntField()
    run_started_at = DateTimeField(default=None)

    triggering_commit_id = ObjectIdField(default=None)
    triggering_repository_url = StringField(default=None)
    triggering_commit_sha = StringField()
    triggering_commit_branch = StringField()
    triggering_commit_message = StringField()
    triggering_commit_timestamp = DateTimeField()


class JobStep(EmbeddedDocument):
    name = StringField()
    status = StringField()
    conclusion = StringField()
    number = IntField()
    started_at = DateTimeField()
    completed_at = DateTimeField()


class Job(Document):
    job_id = IntField()
    name = StringField()
    run_id = ObjectIdField()
    head_sha = StringField()
    run_attempt = IntField()
    status = StringField()
    conclusion = StringField()
    started_at = DateTimeField()
    completed_at = DateTimeField()
    steps = EmbeddedDocumentListField(JobStep, default=[])

    runner_id = IntField()
    runner_name = StringField()
    runner_group_id = IntField()
    runner_group_name = StringField()


class Artifact(Document):
    artifact_id = IntField()
    name = StringField()
    size_in_bytes = IntField(default=None)
    archive_download_url = StringField(default=None)
    expired = BooleanField()
    created_at = DateTimeField()
    updated_at = DateTimeField()
    expires_at = DateTimeField()
    project_id = ObjectIdField(default=None)
    vcs_system_id = ObjectIdField(default=None)


class Mongo:
    def __init__(
        self,
        db_database: str,
        project_url: str,
        db_user: Optional[str] = None,
        db_password: Optional[str] = None,
        db_hostname: str = "localhost",
        db_port: int = 27017,
        db_authentication_database: Optional[str] = None,
        db_ssl_enabled: bool = False,
    ) -> None:

        self.__operations = {
            "workflow": self.__upsert_workflow,
            "run": self.__upsert_run,
            "job": self.__upsert_job,
            "artifact": self.__upsert_artifact,
        }

        self.db_database = db_database
        self.project_url = project_url

        self.__conn_uri = create_mongodb_uri_string(
            db_user,
            db_password,
            db_hostname,
            db_port,
            db_authentication_database,
            db_ssl_enabled,
        )

        self.__conn = connect(db_database, host=self.__conn_uri)

        logger.debug(f"Mongo connected to {db_database}")

    # to pass to github class for fetching jobs
    @property
    def runs(self):
        return Run

    # ~ essential functions

    def drop_database(self) -> None:
        """Drop current connected database."""
        self.__conn.drop_database(self.db_database)
        logger.debug(f"Database { self.db_database } is dropped")

    def drop_collection(self, col_name: Optional[str] = None) -> bool:
        """Drop collection if found.

        Args:
            col_name (str): Collection name. Defaults to None.
        """

        # check if collection name is passed
        if not col_name:
            return False

        # check if collection is in database
        if (
            col_name
            not in self.__conn.get_database(self.db_database).list_collection_names()
        ):
            logger.error(f"Collection { col_name } is Not Found")
            return False

        # Delete if found
        self.__conn.get_database(self.db_database).drop_collection(col_name)

        logger.debug(f"Collection { col_name } is dropped")

        return True

    def upsert_documents(
        self, documents: Optional[dict] = None, action: Optional[str] = None
    ) -> None:
        """Loop over Elements, to map and save. This function should be passed to GitHub instance as "save_mongo=save_documents".

        Args:
            documents (dict): Elements. Defaults to None.
            action (str): Action name to map objects to. Defaults to None.
        """

        # check if documents and action are not None
        if not documents or not action:
            logger.error(f"No documents or action got passed")
            return None

        # check if the passed action is available
        if action not in self.__operations.keys():
            logger.error(f"Action {action} was not found in predefined operations")
            return None

        # call the mapping function
        func = self.__operations[action]

        # map and save all documents
        for document in documents:

            try:
                func(document)
            except Exception as e:
                logger.error(
                    f'Failed saving document action:{action}, id:{document["id"]}'
                )
                logger.exception(e)
                # continue to avoid system crash if saving document is failed
                continue

    def __create_list_embedded_docs(
        self,
        sub_operation: Optional[str] = None,
        sub_documents: Optional[List[dict]] = None,
    ) -> Optional[List[Any]]:

        if not sub_operation or not sub_documents:
            return []

        sub_operations = {
            "job_step": self.__create_job_step,
            "run_pull_request": self.__create_run_pull_request,
        }

        if sub_operation not in sub_operations.keys():
            logger.error(
                f"Embedded Document sub_operation was not found {sub_operation}"
            )
            return []

        f = sub_operations[sub_operation]

        return [f(d) for d in sub_documents]

    # ~ create documents

    def __upsert_workflow(self, obj: dict) -> None:
        """Map object to the appropriate files of Workflows.

        Args:
            obj (dict): The Object to map.

        Returns:
            Workflows: A MongoDB object ready to save.
        """

        temp_dict = {
            "workflow_id": self.__to_int(obj.get("id")),
            "name": obj.get("name"),
            "path": obj.get("path"),
            "state": obj.get("state"),
            "created_at": self.__parse_date(obj.get("created_at"), True),
            "updated_at": self.__parse_date(obj.get("updated_at"), True),
        }

        temp_dict["vcs_system_id"], temp_dict["project_id"] = self.__project_object_id(
            self.project_url
        )

        # if project not yet in vcs_system add the repository url
        if not temp_dict["project_id"]:
            temp_dict["project_url"] = self.project_url

        Workflow.objects(**temp_dict).upsert_one(**temp_dict)

    def __upsert_run(self, obj: dict) -> None:
        """Map object to the appropriate files of Runs.

        Args:
            obj (dict): The Object to map.

        Returns:
            Runs: A MongoDB object ready to save.
        """

        temp_dict = {
            "run_id": self.__to_int(obj.get("id")),
            "run_number": self.__to_int(obj.get("run_number")),
            "event": obj.get("event"),
            "status": obj.get("status"),
            "conclusion": obj.get("conclusion"),
            "workflow_id": self.__workflow_object_id(
                v_workflow_id=self.__to_int(obj.get("workflow_id")),
                v_name=obj.get("name"),
            ),
            "pull_requests": self.__create_list_embedded_docs(
                "run_pull_request", obj.get("pull_requests")
            ),
            "created_at": self.__parse_date(obj.get("created_at")),
            "updated_at": self.__parse_date(obj.get("updated_at")),
            "run_attempt": self.__to_int(obj.get("run_attempt")),
            "run_started_at": self.__parse_date(obj.get("run_started_at")),
            "triggering_commit_sha": obj.get("head_sha"),
            "triggering_commit_branch": obj.get("head_branch"),
            "triggering_commit_message": obj["head_commit"].get("message"),
            "triggering_commit_timestamp": obj["head_commit"].get("timestamp"),
        }

        # add triggering repository url if available
        if obj.get("head_repository"):
            temp_dict["triggering_repository_url"] = self.__run_head_repository_url(
                obj["head_repository"].get("full_name")
            )

        # if commit object_id is None avoid adding to temp_dict
        triggering_commit_id = self.__commit_object_id(obj.get("head_sha"))
        if triggering_commit_id:
            temp_dict["triggering_commit_id"] = triggering_commit_id

        Run.objects(**temp_dict).upsert_one(**temp_dict)

    def __create_run_pull_request(self, obj: dict) -> RunPullRequest:
        """Map object to the appropriate files of RunPullRequests.

        Args:
            obj (dict): The Object to map.

        Returns:
            RunPullRequests: A MongoDB object ready to save.
        """
        run_pull = RunPullRequest()

        run_pull.pull_request_id = self.__to_int(obj.get("id"))
        run_pull.pull_request_number = self.__to_int(obj.get("number"))

        run_pull.target_branch = obj["head"].get("ref")
        run_pull.target_sha = obj["head"].get("sha")
        run_pull.target_id = self.__to_int(obj["head"]["repo"].get("id"))
        run_pull.target_url = self.__format_repository_url(
            obj["head"]["repo"].get("url")
        )

        run_pull.source_branch = obj["base"].get("ref")
        run_pull.source_sha = obj["base"].get("sha")
        run_pull.source_id = self.__to_int(obj["base"]["repo"].get("id"))
        run_pull.source_url = self.__format_repository_url(
            obj["base"]["repo"].get("url")
        )

        return run_pull

    def __upsert_job(self, obj: dict) -> None:
        """Map object to the appropriate files of Jobs.

        Args:
            obj (dict): The Object to map.

        Returns:
            Jobs: A MongoDB object ready to save.
        """
        temp_dict = {
            "job_id": self.__to_int(obj.get("id")),
            "name": obj.get("name"),
            "run_id": self.__run_object_id(self.__to_int(obj.get("run_id"))),
            "head_sha": obj.get("head_sha"),
            "run_attempt": self.__to_int(obj.get("run_attempt")),
            "status": obj.get("status"),
            "conclusion": obj.get("conclusion"),
            "started_at": self.__parse_date(obj.get("started_at")),
            "completed_at": self.__parse_date(obj.get("completed_at")),
            "steps": self.__create_list_embedded_docs("job_step", obj.get("steps")),
            "runner_id": self.__to_int(obj.get("runner_id")),
            "runner_name": obj.get("runner_name"),
            "runner_group_id": self.__to_int(obj.get("runner_group_id")),
            "runner_group_name": obj.get("runner_group_name"),
        }

        Job.objects(**temp_dict).upsert_one(**temp_dict)

    def __create_job_step(self, obj: dict) -> JobStep:
        """Map object to the appropriate files of JobSteps.

        Args:
            obj (dict): The Object to map.

        Returns:
            JobSteps: A MongoDB object ready to save.
        """
        job_step = JobStep()

        job_step.name = obj.get("name")
        job_step.status = obj.get("status")
        job_step.conclusion = obj.get("conclusion")
        job_step.number = self.__to_int(obj.get("number"))
        job_step.started_at = self.__parse_date(obj.get("started_at"), True)
        job_step.completed_at = self.__parse_date(obj.get("completed_at"), True)

        return job_step

    def __upsert_artifact(self, obj: dict) -> None:
        """Map object to the appropriate files of Artifacts.

        Args:
            obj (dict): The Object to map.

        Returns:
            Artifacts: A MongoDB object ready to save.
        """

        temp_dict = {
            "artifact_id": self.__to_int(obj.get("id")),
            "name": obj.get("name"),
            "size_in_bytes": self.__to_int(obj.get("size_in_bytes")),
            "archive_download_url": obj.get("archive_download_url"),
            "expired": bool(obj.get("expired")),
            "created_at": self.__parse_date(obj.get("created_at")),
            "updated_at": self.__parse_date(obj.get("updated_at")),
            "expires_at": self.__parse_date(obj.get("expires_at")),
        }

        temp_dict["vcs_system_id"], temp_dict["project_id"] = self.__project_object_id(
            self.project_url
        )

        # if project not yet in vcs_system add the repository url
        if not temp_dict["project_id"]:
            temp_dict["project_url"] = self.project_url

        Artifact.objects(**temp_dict).upsert_one(**temp_dict)

    # ~ query mongo collections

    def __workflow_object_id(
        self, v_workflow_id: Optional[int] = None, v_name: Optional[str] = None
    ) -> Optional[ObjectIdField]:
        """
        Find Workflow object_id from Workflow collection.

        Args:
            v_workflow_id (int, optional): Workflow id. Defaults to None.
            v_name (str, optional): Workflow Name. Defaults to None.

        Returns:
            Optional[ObjectIdField]
        """

        if not v_workflow_id or not v_name:
            return None

        try:
            r = Workflow.objects.get(workflow_id=v_workflow_id).id
        except Workflow.DoesNotExist:
            r = None

        # create workflow if not found by name or id
        if not r:
            self.__create_workflow(
                {"id": v_workflow_id, "name": v_name, "state": "deleted"}
            ).save()

        try:
            r = Workflow.objects.get(workflow_id=v_workflow_id).id
        except Workflow.DoesNotExist:
            logger.error(
                f"Workflow not found, workflow_id:{v_workflow_id}, name:{v_name}"
            )
            r = None

        return r

    def __project_object_id(
        self, value: str
    ) -> Tuple[Optional[ObjectIdField], Optional[ObjectIdField]]:
        """
        Find Repository project id from VCSSystem collection.

        Args:
            value (str): The URL to the repo.

        Returns:
            Optional(ObjectIdField, ObjectIdField)
        """
        try:
            r = VCSSystem.objects.get(url=value)
        except VCSSystem.DoesNotExist:
            logger.error(f"VCSSystem not found url:{value} to fetch project_id")
            return None, None
        return r.id, r.project_id

    def __run_object_id(self, value: Optional[int] = None) -> Optional[ObjectIdField]:
        """
        Find Run object_id from Run collection.

        Args:
            value (int, optional): Run id. Defaults to None.

        Returns:
            Optional[ObjectIdField]
        """

        if not value:
            return None

        try:
            r = Run.objects.get(run_id=value).id
        except Run.DoesNotExist:
            logger.error(f"Run not found run_id:{value}")
            r = None
        return r

    def __commit_object_id(
        self, value: Optional[str] = None
    ) -> Optional[ObjectIdField]:
        """
        Find Run object_id from Run collection.

        Args:
            value (int, optional): Run id. Defaults to None.

        Returns:
            Optional[ObjectIdField]
        """

        if not value:
            return None

        try:
            r = Commit.objects.get(revision_hash=value).id
        except Commit.DoesNotExist:
            # disable logging just for now, because most of the commits are not in commit collection
            # logger.error(f"Commit not found revision_hash:{value}")
            r = None
        return r

    # ~ helper functions

    def __parse_date(
        self, value: str = None, is_millisecond: bool = False
    ) -> Optional[dt.datetime]:
        """Convert Datetime string to actual Datetime.

        Args:
            value (str): The datetime string to be converted. Defaults to None.
            is_millisecond (bool, optional): If datetime has millisecond in the string. Defaults to False.

        Returns:
            datetime: datetime formated or None if no string passed.
        """
        if not value:
            return None

        date_fmt = "%Y-%m-%dT%H:%M:%S%z"
        if is_millisecond:
            date_fmt = "%Y-%m-%dT%H:%M:%S.%f%z"

        if sys.version_info.minor < 8:
            date_fmt = date_fmt.replace("%z", "Z")
        return dt.datetime.strptime(value, date_fmt)

    def __to_int(self, value: Optional[str] = None) -> Optional[int]:
        """
        Converting string to integer if any.

        Args:
            value (str, optional): The value to convert. Defaults to None.

        Returns:
            Optional[int]
        """

        if not value:
            return None

        return int(value)

    def __run_head_repository_url(self, value: str) -> str:
        """
        Construct URL from repository full name "owner/repository"

        Args:
            value (str): Foramt "owner/repository"

        Returns:
            str: GitHub .git url
        """
        return "https://github.com/" + value + ".git"

    def __format_repository_url(self, value: Optional[str] = None) -> Optional[str]:

        if not value:
            return None

        value = value.replace("api.", "")
        value = value.replace("repos/", "")
        value = value.replace(".git", "")
        value = value + ".git"

        return value
