from __future__ import print_function, absolute_import
import errno
import pickle
from bugzilla import Bugzilla
from bugzilla.bug import Bug


BZ_URL = 'bugzilla.redhat.com'
PRODUCT = 'Red Hat Ceph Storage'


def connect():
    """ Return a logged-in connection. """
    bzapi = Bugzilla(BZ_URL)
    if not bzapi.logged_in:
        raise SystemExit('Not logged in, see ~/.bugzillatoken.')
    return bzapi


def search(payload):
    """
    Send a payload to the Bug.search RPC, and translate the result into
    bugzilla.bug.Bug results.
    """
    bzapi = connect()
    result = bzapi._proxy.Bug.search(payload)
    bugs = [Bug(bzapi, dict=r) for r in result['bugs']]
    return bugs


def query_params(release, milestone):
    """
    Return a dict of basic Bugzilla search parameters.

    :param release: eg. "3.0"
    :param milestone: eg. "z4"
    """
    params = {
        'include_fields': ['id', 'summary', 'status', 'last_change_time'],
        'f1': 'product',
        'o1': 'equals',
        'v1': PRODUCT,
        'f2': 'component',
        'o2': 'notequals',
        'v2': 'Documentation',
        'f3': 'target_release',
        'o3': 'equals',
        'v3': release,
        'f4': 'target_milestone',
        'o4': 'equals',
        'v4': milestone,
        'f5': 'keywords',
        'o5': 'nowords',
        'v5': ['Tracking', 'TestOnly'],
        'f6': 'bug_status',
        'o6': 'anywords',
        'v6': 'NEW ASSIGNED POST MODIFIED ON_DEV'
    }
    return params.copy()


def sort_by_status(bug):
    if bug.status == 'NEW':
        return 0
    if bug.status == 'ASSIGNED':
        return 1
    if bug.status == 'POST':
        return 2
    if bug.status == 'ON_DEV':
        return 3
    if bug.status == 'MODIFIED':
        return 4
    if bug.status == 'ON_QA':
        return 5
