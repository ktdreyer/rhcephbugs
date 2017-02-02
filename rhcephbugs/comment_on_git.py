from collections import defaultdict
import os
import re
import bugzilla
from rdopkg.utils.cmd import git
from rdopkg.utils.exception import CommandFailed


REPO_TYPES = {
    'RHEL dist-git': {
        'match': 'git://pkgs.devel.redhat.com/rpms/(?:[^/]+)$',
        'tmpl': 'http://pkgs.devel.redhat.com/cgit/rpms/%(pkg)s/commit/?id=%(commit)s',  # NOQA: E501
    },
    'RHEL patches': {
        'match': 'https://code.engineering.redhat.com/gerrit/(?:[^/]+)$',
        'tmpl': 'https://code.engineering.redhat.com/gerrit/gitweb?p=%(pkg)s.git;a=commit;h=%(commit)s',  # NOQA: E501
    },
    'Ubuntu dist-git': {
        'match': 'https://code.engineering.redhat.com/gerrit/rcm/ceph-ubuntu/(?:[^/]+)$',  # NOQA: E501
        'tmpl': 'https://code.engineering.redhat.com/gerrit/gitweb?p=rcm/ceph-ubuntu/%(pkg)s.git;a=commit;h=%(commit)s',  # NOQA: E501
    },
}


class Repo(object):
    def __init__(self, url):
        """
        Initialize with a Git URL (the URL we fetch from in Jenkins, $GIT_URL).

        For example:

        git://pkgs.devel.redhat.com/rpms/calamari-server
        https://code.engineering.redhat.com/gerrit/calamari-server
        https://code.engineering.redhat.com/gerrit/rcm/ceph-ubuntu/calamari-server
        """
        self.url = url

    @property
    def description(self):
        """ Provide a human-readable description of this repository type. """
        for description, settings in REPO_TYPES.iteritems():
            if re.match(settings['match'], self.url):
                return description
        raise RuntimeError('Cannot identify %s' % self.url)

    @property
    def _gitweb_template(self):
        """ Returns a format string of an HTTP URL. """
        return REPO_TYPES[self.description]['tmpl']

    def gitweb(self, pkg, commit):
        """ Returns an HTTP URL for this package and commit (sha1). """
        return self._gitweb_template % {'pkg': pkg, 'commit': commit}


def comment_in_bug(bzapi, id_, comment):
    """ Add a comment to bug id_ using bzapi. """
    url = bzapi.url.replace('xmlrpc.cgi', str(id_))
    print('Updating %s' % url)
    print(comment)
    update = bzapi.build_update(comment=comment, comment_private=True)
    bzapi.update_bugs(id_, update)


def bugs_to_commits(previous, current):
    """
    Build a dict of bugs-to-commits.

    For example, {'12345': ['154fce30', 'b4c1c387e']}
    """
    bz_commits = defaultdict(set)
    for (abbrev, desc, bzs) in git.get_commit_bzs(previous, current):
        sha = git('rev-parse', abbrev, log_cmd=False)
        for bz in bzs:
            bz_commits[bz].add(sha)
    return bz_commits


def build_comment(bz, shas, pkg, branch, repo):
    """ Return a comment for this BZ and shas. """
    committers = defaultdict(set)
    for sha in shas:
        committer = git('log', '-1', '--pretty=format:%cn <%ce>', sha,
                        log_cmd=False)
        committers[committer].add(sha)

    comment = ''
    for committer, shas in committers.iteritems():
        comment += "%s committed to %s in %s:\n" % \
                   (committer, branch, repo.description)
        for sha in shas:
            comment += repo.gitweb(pkg, sha) + "\n"
    return comment


def sanity_check_commits(previous, current):
    """
    Sanity-check some things about our "previous" and "current" Git commits.

    Exit with non-zero exit code if we fail.
    """
    if previous == current:
        print('Previous and current commits are the same: %s' % current)
        raise SystemExit('No intermediate commmits to compare. Exiting.')
    try:
        git('merge-base', '--is-ancestor', previous, current, log_cmd=False)
    except CommandFailed:
        print('%s is not an ancestor of %s' % (previous, current))
        raise SystemExit('This is not a fast-forward merge. Exiting.')


def run(bz_url, git_url, pkg, branch, previous, current):

    sanity_check_commits(previous, current)

    bzapi = bugzilla.Bugzilla(bz_url)
    # Note that python-bugzilla expects to find a user token in the Jenkins
    # slave's $HOME/.bugzillatoken. You can generate it with the "bugzilla
    # login" command.
    if not bzapi.logged_in:
        raise SystemExit('Not logged into %s. See ~/.bugzillatoken.' % bz_url)

    # Strip the "origin/" prefix from the branch
    branch = re.sub('^origin/', '', branch)

    repo = Repo(git_url)

    # Build a dict of bugs-to-commits.
    # For example, {'12345': ['154fce30', 'b4c1c387e']}
    bz_commits = bugs_to_commits(previous, current)

    # Comment in each bug with the corresponding commits.
    for bz, shas in bz_commits.iteritems():
        comment = build_comment(bz, shas, pkg, branch, repo)
        comment_in_bug(bzapi, bz, comment)
        # TODO: make this more robust against accidental duplicate comments?
        # (Store the list of shas in JSON in the bug's devel whiteboard?)
        # (Ensure that we're only operating on a Ceph bug?)


def main(argv):
    if not os.getenv('GIT_PREVIOUS_SUCCESSFUL_COMMIT'):
        print('Missing GIT_PREVIOUS_SUCCESSFUL_COMMIT environment variable.')
        print('Normally this happens because this job has never run for this '
              'branch until now. Now Jenkins will set it for the next job '
              'that runs for this branch. Exiting.')
        raise SystemExit()

    try:
        # Eg: git://pkgs.devel.redhat.com/rpms/calamari-server
        git_url = os.environ['GIT_URL']
        pkg = os.environ['PKG']
        branch = os.environ['GIT_BRANCH']
        previous = os.environ['GIT_PREVIOUS_SUCCESSFUL_COMMIT']
        current = os.environ['GIT_COMMIT']
    except KeyError as e:
        raise SystemExit('Missing environment variable %s' % e.message)

    bz_url = 'bugzilla.redhat.com'
    if '--staging' in argv:
        bz_url = 'partner-bugzilla.redhat.com'
        print('Using staging server %s' % bz_url)
    run(bz_url, git_url, pkg, branch, previous, current)
