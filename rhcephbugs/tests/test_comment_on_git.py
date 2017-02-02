import rhcephbugs.comment_on_git
from rhcephbugs.comment_on_git import Repo
from rhcephbugs.comment_on_git import comment_in_bug
from rhcephbugs.comment_on_git import bugs_to_commits
from rhcephbugs.comment_on_git import build_comment
import pytest


class TestRepo(object):

    @pytest.fixture
    def rhel_dist_git(self):
        return Repo('git://pkgs.devel.redhat.com/rpms/calamari-server')

    @pytest.fixture
    def rhel_patches(self):
        return Repo('https://code.engineering.redhat.com/gerrit/calamari-server')  # NOQA: E501

    @pytest.fixture
    def ubuntu_dist_git(self):
        return Repo('https://code.engineering.redhat.com/gerrit/rcm/ceph-ubuntu/calamari-server')  # NOQA: E501

    def test_rhel_dist_git(self, rhel_dist_git):
        assert rhel_dist_git.description == 'RHEL dist-git'
        expected = 'http://pkgs.devel.redhat.com/cgit/rpms/foopkg/commit/?id=cafed00d'  # NOQA: E501
        assert rhel_dist_git.gitweb('foopkg', 'cafed00d') == expected

    def test_rhel_patches(self, rhel_patches):
        assert rhel_patches.description == 'RHEL patches'
        expected = 'https://code.engineering.redhat.com/gerrit/gitweb?p=foopkg.git;a=commit;h=cafed00d'  # NOQA: E501
        assert rhel_patches.gitweb('foopkg', 'cafed00d') == expected

    def test_ubuntu_dist_git(self, ubuntu_dist_git):
        assert ubuntu_dist_git.description == 'Ubuntu dist-git'
        expected = 'https://code.engineering.redhat.com/gerrit/gitweb?p=rcm/ceph-ubuntu/foopkg.git;a=commit;h=cafed00d'  # NOQA: E501
        assert ubuntu_dist_git.gitweb('foopkg', 'cafed00d') == expected


class TestCommentInBug(object):

    class FakeBZApi(object):
        url = 'https://bugzilla.example.com/xmlrpc.cgi'

        def build_update(self, **kw):
            self.build_update_called = kw
            return None  # a bogus update value

        def update_bugs(self, *a):
            self.update_bugs_called = a

    @pytest.fixture
    def bzapi(self):
        return self.FakeBZApi()

    def test_comment_in_bug(self, bzapi):
        comment_in_bug(bzapi, 123, 'my test comment')
        assert bzapi.build_update_called
        assert bzapi.build_update_called['comment'] == 'my test comment'
        assert bzapi.build_update_called['comment_private'] is True
        assert bzapi.update_bugs_called
        assert bzapi.update_bugs_called == (123, None)


class TestBugsToCommits(object):
    class FakeGit(object):
        def get_commit_bzs(self, from_revision, to_revision=None):
            return [
                ('154fce30', 'first commit', ['12345']),
                ('b4c1c387e', 'second commit', ['12345']),
            ]

        def __call__(self, *a, **kw):
            if a[0] != 'rev-parse':
                raise RuntimeError('Unexpected Git command: ' + ' '.join(a))
            return a[1]

    def test_bugs_to_commits(self, monkeypatch):
        monkeypatch.setattr(rhcephbugs.comment_on_git, 'git', self.FakeGit())
        previous = 'previoussha1'
        current = 'b4c1c387e'
        result = bugs_to_commits(previous, current)
        assert result == {'12345': set(['154fce30', 'b4c1c387e'])}


class TestBuildComment(object):

    class FakeGit(object):
        def __call__(self, *a, **kw):
            if a[0] != 'log' or a[1] != '-1':
                raise RuntimeError('Unexpected Git command: ' + ' '.join(a))
            if a[2] != '--pretty=format:%cn <%ce>':
                raise RuntimeError('Unexpected Git command: ' + ' '.join(a))
            return 'Mr Developer <cool@example.com>'

    def test_build_comment(self, monkeypatch):
        monkeypatch.setattr(rhcephbugs.comment_on_git, 'git', self.FakeGit())
        bz = 12345
        shas = set(['154fce30', 'b4c1c387e'])
        pkg = 'calamari-server'
        branch = 'ceph-2-rhel-7'
        repo = Repo('git://pkgs.devel.redhat.com/rpms/calamari-server')
        result = build_comment(bz, shas, pkg, branch, repo)
        assert result == '''\
Mr Developer <cool@example.com> committed to ceph-2-rhel-7 in RHEL dist-git:
http://pkgs.devel.redhat.com/cgit/rpms/calamari-server/commit/?id=154fce30
http://pkgs.devel.redhat.com/cgit/rpms/calamari-server/commit/?id=b4c1c387e
'''
