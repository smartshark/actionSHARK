from typing import Optional, Any, Tuple, List
from mongoengine import ObjectIdField
from pycoshark.mongomodels import Commit, JobStep, RunPullRequest
import datetime as dt
import dateutil
import pytz


def parse_date(value: Optional[str] = None) -> Optional[dt.datetime]:
    """Convert Datetime string to actual Datetime object.

    Args:
        value (str): The datetime string to be converted. Defaults to None.

    Returns:
        datetime: datetime formated or None if no string passed.
    """
    if not value:
        return None

    date = dateutil.parser.parse(value)
    date = date.astimezone(pytz.UTC).replace(tzinfo=None)

    return date


def to_int(value: Optional[str] = None) -> Optional[int]:
    """
    Converting string to integer.

    Args:
        value (str, optional): The value to convert. Defaults to None.

    Returns:
        Optional[int]
    """

    if not value:
        return None

    return int(value)


def format_repository_url(value: Optional[str] = None) -> Optional[str]:

    if not value:
        return None

    value = value.replace("api.", "")
    value = value.replace("repos/", "")
    value = value.replace(".git", "")
    value = value + ".git"

    return value


def run_head_repository_url(value: str) -> str:
    """
    Construct URL from repository full name "owner/repository"

    Args:
        value (str): Foramt "owner/repository"

    Returns:
        str: GitHub .git url
    """
    return "https://github.com/" + value + ".git"


def commit_object_id(value: Optional[str] = None, vcs_system_id: Optional[str] = None) -> Optional[ObjectIdField]:
    """
    Find Run object_id from Run collection.

    Args:
        value (str):  Revision hash.
        vcs_system_id: VCS system id

    Returns:
        Optional[ObjectIdField]
    """

    if not value or not vcs_system_id:
        return None

    try:
        r = Commit.objects.get(revision_hash=value, vcs_system_ids=vcs_system_id).id
    except Commit.DoesNotExist:
        # disable logging just for now, because most of the commits are not in commit collection
        # logger.error(f"Commit not found revision_hash:{value}")
        r = None
    return r


def create_job_step(obj: dict) -> JobStep:
    """Create an embedded document step for a Job document.

    Args:
        obj (dict): The dict to create a JobStep.

    Returns:
        JobStep Object
    """

    job_step = JobStep()

    job_step.name = obj.get("name")
    job_step.status = obj.get("status")
    job_step.conclusion = obj.get("conclusion")
    job_step.number = to_int(obj.get("number"))
    job_step.started_at = parse_date(obj.get("started_at"))
    job_step.completed_at = parse_date(obj.get("completed_at"))

    return job_step


def create_pull_requests(obj):

    """Create an embedded document pull request for a Run document.

    Args:
        obj (dict): The dict to create a RunPullRequest.

    Returns:
        RunPullRequest Object
    """

    run_pull = RunPullRequest()

    run_pull.pull_request_id = to_int(obj.get("id"))
    run_pull.pull_request_number = to_int(obj.get("number"))

    run_pull.target_branch = obj["head"].get("ref")
    run_pull.target_sha = obj["head"].get("sha")
    run_pull.target_id = to_int(obj["head"]["repo"].get("id"))
    run_pull.target_url = format_repository_url(
        obj["head"]["repo"].get("url")
    )

    run_pull.source_branch = obj["base"].get("ref")
    run_pull.source_sha = obj["base"].get("sha")
    run_pull.source_id = to_int(obj["base"]["repo"].get("id"))
    run_pull.source_url = format_repository_url(
        obj["base"]["repo"].get("url")
    )
    return run_pull
