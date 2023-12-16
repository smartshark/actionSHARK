import datetime
import unittest
import json
import mongoengine
from unittest.mock import patch
from argparse import Namespace
import mongomock
from pycoshark.mongomodels import Project, CiSystem, ActionWorkflow, RunArtifact, ActionRun, ActionJob, VCSSystem, Commit
from actionSHARK.github import GitHub


with open('tests/fixtures/artifact.json') as f:
    artifact = json.loads(f.read())

with open('tests/fixtures/job.json') as f:
    job = json.loads(f.read())

with open('tests/fixtures/run.json') as f:
    run = json.loads(f.read())

with open('tests/fixtures/workflow.json') as f:
    workflow = json.loads(f.read())

with open('tests/fixtures/user.json') as f:
    person = json.loads(f.read())


def mock_return(*args, **kwargs):
    url = args[0].split('?')[0]
    if 'user' in url:
        return person
    if url.endswith('/workflows'):
        return workflow
    if url.endswith('/runs'):
        return run
    if url.endswith('/jobs'):
        return job
    if url.endswith('/artifacts'):
        return artifact


class TestGithubBackend(unittest.TestCase):
    """Test Github Backend."""

    def setUp(self):
        """Setup the mongomock connection."""
        mongoengine.connection.disconnect()
        mongoengine.connect('testdb', host='mongodb://localhost', mongo_client_class=mongomock.MongoClient)
        p = Project(name='test')
        p.save()

        pr_system = CiSystem(project_id=p.id, url='https://localhost/repos/smartshark/test/actions', collection_date=datetime.datetime.now())
        pr_system.save()

    def tearDown(self):
        """Tear down the mongomock connection."""
        mongoengine.connection.disconnect()

    @patch('actionSHARK.github.GitHub.paginating', side_effect=mock_return)
    def test_actions(self, mock_request):

        cfg = Namespace(tracking_url='https://localhost/repos/smartshark/test/actions')
        project = Project.objects.get(name='test')
        vcs_system = VCSSystem(project_id=project.id, url='https://github.com/apache/commons-rdf.git',
                               repository_type='git', collection_date=datetime.datetime.now())
        vcs_system.save()

        c = Commit(vcs_system_ids=[vcs_system.id], revision_hash='d0aa1bbe13372e629f7ae205a4c963dd29b4f184')
        c.save()

        gp = GitHub(tracking_url=cfg.tracking_url, token='', owner='apache',repo='commons-rdf', project=project)
        gp.run()
        w = ActionWorkflow.objects.get(external_id='19196438')
        r = ActionRun.objects.get(external_id='7206977332')
        j = ActionJob.objects.get(external_id='19632879334')
        a = RunArtifact.objects.get(external_id='1111849070')

        self.assertEqual(w.name, workflow[0]['name'])
        self.assertEqual(w.path, workflow[0]['path'])
        self.assertEqual(w.state, workflow[0]['state'])
        self.assertEqual(w.created_at, datetime.datetime(2022, 2, 3, 12, 2, 55))
        self.assertEqual(w.updated_at, datetime.datetime(2022, 2, 3, 12, 2, 55))
        self.assertEqual(w.project_id, project.id)

        self.assertEqual(r.run_number, run[0]['run_number'])
        self.assertEqual(r.event, run[0]['event'])
        self.assertEqual(r.status, run[0]['status'])
        self.assertEqual(r.conclusion, run[0]['conclusion'])
        self.assertEqual(r.pull_requests, run[0]['pull_requests'])
        self.assertEqual(r.created_at, datetime.datetime(2023, 12, 14, 9, 33, 21))
        self.assertEqual(r.updated_at, datetime.datetime(2023, 12, 14, 9, 35, 59))
        self.assertEqual(r.run_attempt, run[0]['run_attempt'])
        self.assertEqual(r.run_started_at, datetime.datetime(2023, 12, 14, 9, 33, 21))
        self.assertEqual(r.triggering_repository_url, 'https://github.com/apache/commons-rdf.git')
        self.assertEqual(r.triggering_commit_id, c.id)
        self.assertEqual(r.triggering_commit_sha, 'd0aa1bbe13372e629f7ae205a4c963dd29b4f184')
        self.assertEqual(r.triggering_commit_branch, 'master')
        self.assertEqual(r.triggering_commit_message, 'Bump github/codeql-action from 2.22.9 to 2.22.10')
        self.assertEqual(r.triggering_commit_message, 'Bump github/codeql-action from 2.22.9 to 2.22.10')
        self.assertEqual(r.triggering_commit_timestamp, datetime.datetime(2023, 12, 13, 12, 51, 14))

        self.assertEqual(j.name, job[0]['name'])
        self.assertEqual(j.head_sha, job[0]['head_sha'])
        self.assertEqual(j.run_attempt, job[0]['run_attempt'])
        self.assertEqual(j.status, job[0]['status'])
        self.assertEqual(j.conclusion, job[0]['conclusion'])
        self.assertEqual(j.started_at, datetime.datetime(2023, 12, 14, 9, 33, 28))
        self.assertEqual(j.completed_at, datetime.datetime(2023, 12, 14, 9, 35, 57))
        self.assertEqual(j.steps[0].name, job[0]['steps'][0]['name'])
        self.assertEqual(j.steps[0].status, job[0]['steps'][0]['status'])
        self.assertEqual(j.steps[0].conclusion, job[0]['steps'][0]['conclusion'])
        self.assertEqual(j.steps[0].number, job[0]['steps'][0]['number'])
        self.assertEqual(j.steps[0].started_at, datetime.datetime(2023, 12, 14, 9, 33, 28))
        self.assertEqual(j.steps[0].completed_at, datetime.datetime(2023, 12, 14, 9, 33, 32))
        self.assertEqual(j.runner_id, job[0]['runner_id'])
        self.assertEqual(j.runner_name, job[0]['runner_name'])
        self.assertEqual(j.runner_group_id, job[0]['runner_group_id'])
        self.assertEqual(j.runner_group_name, job[0]['runner_group_name'])

        self.assertEqual(a.name, artifact[0]['name'])
        self.assertEqual(a.size_in_bytes, artifact[0]['size_in_bytes'])
        self.assertEqual(a.archive_download_url, artifact[0]['archive_download_url'])
        self.assertEqual(a.expired, artifact[0]['expired'])
        self.assertEqual(a.created_at, datetime.datetime(2023, 12, 13, 12, 52, 18))
        self.assertEqual(a.updated_at, datetime.datetime(2023, 12, 13, 12, 52, 19))
        self.assertEqual(a.expires_at, datetime.datetime(2023, 12, 18, 12, 52, 6))
        self.assertEqual(a.project_id, project.id)


















