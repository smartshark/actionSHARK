import datetime as dt
from typing import Optional, Any
import logging
from mongoengine.fields import EmbeddedDocumentField

from pycoshark.utils import create_mongodb_uri_string
from pycoshark.mongomodels import VCSSystem

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
    workflow_id = IntField(default=None)
    name = StringField(default=None)
    path = StringField(default=None)
    state = StringField(default=None)
    created_at = DateTimeField(default=None)
    updated_at = DateTimeField(default=None)
    repo_id = ObjectIdField(default=None)
    repo_url = StringField(default=None)


class RunPullRequest(EmbeddedDocument):
    run_pull_request_id = IntField(default=None)
    number = IntField(default=None)
    head_id = IntField(default=None)
    head_ref = StringField(default=None)
    head_name = StringField(default=None)
    base_id = IntField(default=None)
    base_ref = StringField(default=None)
    base_name = StringField(default=None)


class RunHeadCommit(EmbeddedDocument):
    message = StringField(default=None)
    timestamp = DateTimeField(default=None)


class RunHeadRepository(EmbeddedDocument):
    full_name = StringField(default=None)
    repo_id = ObjectIdField(default=None)


class Run(Document):
    run_id = IntField(default=None)
    name = StringField(default=None)
    run_number = IntField(default=None)
    event = StringField(required=True)
    status = StringField(default=None)
    conclusion = StringField(default=None)
    workflow_id = ObjectIdField(default=None)
    workflow_github_id = IntField(default=None)
    pull_requests = EmbeddedDocumentListField(RunPullRequest, default=[])
    created_at = DateTimeField(default=None)
    updated_at = DateTimeField(default=None)
    run_attempt = IntField(default=None)
    run_started_at = DateTimeField(default=None)
    head_repository = EmbeddedDocumentField(RunHeadRepository, default=None)
    head_commit = EmbeddedDocumentField(RunHeadCommit, default=None)


class JobStep(EmbeddedDocument):
    name = StringField(default=None)
    status = StringField(default=None)
    conclusion = StringField(default=None)
    number = IntField(default=None)
    started_at = DateTimeField(default=None)
    completed_at = DateTimeField(default=None)


class Job(Document):
    job_id = IntField(default=None)
    name = StringField(default=None)
    run_id = ObjectIdField(default=None)
    run_attempt = IntField(default=None)
    status = StringField(default=None)
    conclusion = StringField(default=None)
    started_at = DateTimeField(default=None)
    completed_at = DateTimeField(default=None)
    steps = EmbeddedDocumentListField(JobStep, default=[])
    runner_id = IntField(default=None)
    runner_name = StringField(default=None)
    runner_group_id = IntField(default=None)
    runner_group_name = StringField(default=None)


class Artifact(Document):
    artifact_id = IntField(default=None)
    name = StringField(default=None)
    size_in_bytes = IntField(default=None)
    archive_download_url = StringField(default=None)
    expired = BooleanField()
    created_at = DateTimeField(default=None)
    updated_at = DateTimeField(default=None)
    expires_at = DateTimeField(default=None)


class Mongo:
    def __init__(
        self,
        db_user: Optional[str] = None,
        db_password: Optional[str] = None,
        db_hostname: str = "localhost",
        db_port: int = 27017,
        db_name: Optional[str] = None,
        db_authentication_database: Optional[str] = None,
        db_ssl_enabled: bool = False,
        repo_url: Optional[str] = None,
    ) -> None:
        self.__operations = {
            "workflow": self.__create_workflow,
            "run": self.__create_run,
            "job": self.__create_job,
            "artifact": self.__create_artifact,
        }

        self.db_name = db_name
        self.repo_url = repo_url

        self.__conn_uri = create_mongodb_uri_string(
            db_user,
            db_password,
            db_hostname,
            db_port,
            db_authentication_database,
            db_ssl_enabled,
        )

        self.__conn = connect(db_name, host=self.__conn_uri)

        logger.debug(f"Mongo connected to {db_name}")

    @property
    def runs(self):
        return Run

    def drop_database(self) -> None:
        """Drop current connected database."""
        self.__conn.drop_database(self.db_name)
        logger.debug(f"Database { self.db_name } is dropped")

    def drop_collection(self, col_name: Optional[str] = None) -> None:
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
            not in self.__conn.get_database(self.db_name).list_collection_names()
        ):
            logger.error(f"Collection { col_name } is Not Found")
            return False

        # Delete if found
        self.__conn.get_database(self.db_name).drop_collection(col_name)

        logger.debug(f"Collection { col_name } is dropped")

        return True

    def save_documents(
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
            logger.error(
                f"Action {action} was not found in predefined operations")
            return None

        # call the mapping function
        func = self.__operations[action]

        # map and save all documents
        for document in documents:

            try:
                func(document).save()
            except:
                logger.error(
                    f'Failed saving document action:{action}, id:{document["id"]}'
                )
                continue

    def __create_embedded_docs(
        self,
        sub_operation: Optional[str] = None,
        sub_documents: Optional[list[dict]] = None,
    ) -> list[Any]:

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

    def __create_workflow(self, obj: Optional[dict] = None) -> Workflow:
        """Map object to the appropriate files of Workflows.

        Args:
            obj (dict): The Object to map. Defaults to None.

        Returns:
            Workflows: A MongoDB object ready to save.
        """
        if not obj:
            return None

        workflow = Workflow()

        workflow.workflow_id = int(obj.get("id"))
        workflow.name = obj.get("name")
        workflow.path = obj.get("path")
        workflow.state = obj.get("state")
        workflow.created_at = self.__parse_date(obj.get("created_at"), True)
        workflow.updated_at = self.__parse_date(obj.get("updated_at"), True)
        workflow.repo_id = self.__repo_object_id(self.repo_url)
        workflow.repo_url = self.repo_url

        return workflow

    def __create_run(self, obj: Optional[dict] = None) -> Run:
        """Map object to the appropriate files of Runs.

        Args:
            obj (dict): The Object to map. Defaults to None.

        Returns:
            Runs: A MongoDB object ready to save.
        """
        if not obj:
            return None

        run = Run()

        run.run_id = int(obj.get("id"))
        run.name = obj.get("name")
        run.run_number = int(obj.get("run_number"))
        run.event = obj.get("event")
        run.status = obj.get("status")
        run.conclusion = obj.get("conclusion")
        run.workflow_id = self.__workflow_object_id(
            v_workflow_id=int(obj.get("workflow_id")), v_name=obj.get("name"))
        run.workflow_github_id = int(obj.get("workflow_id"))
        run.pull_requests = self.__create_embedded_docs(
            "run_pull_request", obj.get("pull_requests"))
        run.created_at = self.__parse_date(obj.get("created_at"))
        run.updated_at = self.__parse_date(obj.get("updated_at"))
        run.run_attempt = int(obj.get("run_attempt"))
        run.run_started_at = obj.get("run_started_at")
        run.head_repository = self.__create_run_head_repo(
            obj.get("head_repository"))
        run.head_commit = self.__create_run_head_commit(
            obj.get("head_commit"))

        return run

    def __create_run_pull_request(self, obj: Optional[dict] = None) -> RunPullRequest:
        """Map object to the appropriate files of RunPullRequests.

        Args:
            obj (dict): The Object to map. Defaults to None.

        Returns:
            RunPullRequests: A MongoDB object ready to save.
        """
        if not obj:
            return None

        run_pull = RunPullRequest()

        run_pull.run_pull_request_id = obj.get("id")
        run_pull.number = obj.get("number")
        run_pull.head_ref = obj["head"].get("ref")
        run_pull.head_id = obj["head"]["repo"].get("id")
        run_pull.head_name = obj["head"]["repo"].get("name")
        run_pull.base_ref = obj["base"].get("ref")
        run_pull.base_id = obj["base"]["repo"].get("id")
        run_pull.base_name = obj["base"]["repo"].get("name")

        return run_pull

    def __create_run_head_commit(self, obj: Optional[dict] = None) -> RunHeadCommit:
        """Map object to the appropriate files of RunHeadCommit.

        Args:
            obj (dict): The Object to map. Defaults to None.

        Returns:
            RunHeadCommit: A MongoDB object ready to save.
        """
        if not obj:
            return None

        run_head_commit = RunHeadCommit()

        run_head_commit.message = obj.get("message")
        run_head_commit.timestamp = self.__parse_date(
            obj.get("timestamp"))

        return run_head_commit

    def __create_run_head_repo(self, obj: Optional[dict] = None) -> RunHeadRepository:
        """Map object to the appropriate files of RunHeadRepository.

        Args:
            obj (dict): The Object to map. Defaults to None.

        Returns:
            RunHeadRepository: A MongoDB object ready to save.
        """
        if not obj:
            return None

        run_head_repo = RunHeadRepository()

        run_head_repo.full_name = obj.get("full_name")
        run_head_repo.repo_id = self.__head_commit_object_id(
            obj.get("full_name"))

        return run_head_repo

    def __create_job(self, obj: Optional[dict] = None) -> Job:
        """Map object to the appropriate files of Jobs.

        Args:
            obj (dict): The Object to map. Defaults to None.

        Returns:
            Jobs: A MongoDB object ready to save.
        """
        if not obj:
            return None

        job = Job()

        job.job_id = int(obj.get("id"))
        job.name = obj.get("name")
        job.run_id = self.__run_object_id(int(obj.get("run_id")))
        job.run_attempt = int(obj.get("run_attempt"))
        job.status = obj.get("status")
        job.conclusion = obj.get("conclusion")
        job.started_at = self.__parse_date(obj.get("started_at"))
        job.completed_at = self.__parse_date(obj.get("completed_at"))
        job.steps = self.__create_embedded_docs("job_step", obj.get("steps"))
        job.runner_id = int(obj.get("runner_id")) if obj.get(
            "runner_id") else None
        job.runner_name = obj.get("runner_name")
        job.runner_group_id = (
            int(obj.get("runner_group_id")) if obj.get(
                "runner_group_id") else None
        )
        job.runner_group_name = obj.get("runner_group_name")

        return job

    def __create_job_step(self, obj: Optional[dict] = None) -> JobStep:
        """Map object to the appropriate files of JobSteps.

        Args:
            obj (dict): The Object to map. Defaults to None.

        Returns:
            JobSteps: A MongoDB object ready to save.
        """
        if not obj:
            return None

        job_step = JobStep()

        job_step.name = obj.get("name")
        job_step.status = obj.get("status")
        job_step.conclusion = obj.get("conclusion")
        job_step.number = int(obj.get("number")) if not obj.get(
            "number") else None
        job_step.started_at = self.__parse_date(obj.get("started_at"), True)
        job_step.completed_at = self.__parse_date(
            obj.get("completed_at"), True)

        return job_step

    def __create_artifact(self, obj: Optional[dict] = None) -> Artifact:
        """Map object to the appropriate files of Artifacts.

        Args:
            obj (dict): The Object to map. Defaults to None.

        Returns:
            Artifacts: A MongoDB object ready to save.
        """
        if not obj:
            return None

        artifact = Artifact()

        artifact.artifact_id = int(obj.get("id"))
        artifact.name = obj.get("name")
        artifact.size_in_bytes = int(obj.get("size_in_bytes"))
        artifact.archive_download_url = obj.get("archive_download_url")
        artifact.expired = bool(obj.get("expired"))
        artifact.created_at = self.__parse_date(obj.get("created_at"))
        artifact.updated_at = self.__parse_date(obj.get("updated_at"))
        artifact.expires_at = self.__parse_date(obj.get("expires_at"))

        return artifact

    def __parse_date(self, value: str = None, is_millisecond: bool = False):
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
            return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
        else:
            return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")

    def __workflow_object_id(self, v_workflow_id: Optional[int] = None, v_name: Optional[str] = None) -> str:

        if not v_workflow_id or not v_name:
            return None

        try:
            r = Workflow.objects.get(workflow_id=v_workflow_id).id
        except Workflow.DoesNotExist:
            r = None

        # check workflow by name, when it has different id
        # like when a workflow get updated with the same name
        # if not r:
        #     try:
        #         r = Workflow.objects.get(name=v_name).id
        #     except Workflow.DoesNotExist:
        #         r = None

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

    def __repo_object_id(self, value: Optional[str] = None) -> str:

        if not value:
            return None

        try:
            r = VCSSystem.objects.get(url=value).project_id
        except VCSSystem.DoesNotExist:
            logger.error(f"VCSSystem not found url:{value}")
            r = None
        return r

    def __head_commit_object_id(self, value: Optional[str] = None) -> str:

        if not value:
            return None

        value = "https://github.com/" + value + ".git"
        try:
            r = VCSSystem.objects.get(url=value).project_id
        except VCSSystem.DoesNotExist:
            r = None
        return r

    def __run_object_id(self, value: Optional[int] = None) -> str:

        if not value:
            return None

        try:
            r = Run.objects.get(run_id=value).id
        except Run.DoesNotExist:
            logger.error(f"Run not found run_id:{value}")
            r = None
        return r
