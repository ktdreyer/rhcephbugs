from __future__ import print_function, absolute_import
from bugzilla import Bugzilla
from bugzilla.bug import Bug


BZ_URL = 'bugzilla.redhat.com'
PRODUCT = 'Red Hat Ceph Storage'


def connect():
    """ Return a logged-in connection. """
    bzapi = Bugzilla(BZ_URL)
    if not bzapi.logged_in:
        raise SystemExit('Not logged in, see ~/.config/python-bugzilla/bugzillarc.')
    return bzapi


def search(payload):
    """
    Send a payload to the Bug.search RPC, and translate the result into
    bugzilla.bug.Bug results.

    :param dict payload: A payload to search. Warning: this method mutates
                         this dict, adding "limit" and "offset" parameters.
    """
    bzapi = connect()
    result = bzapi._proxy.Bug.search(payload)
    bugs = [Bug(bzapi, dict=r) for r in result['bugs']]
    total_matches = result['total_matches']
    payload['limit'] = result['limit']
    payload['offset'] = result['offset']
    while len(bugs) < total_matches:
        payload['offset'] += result['limit']
        result = bzapi._proxy.Bug.search(payload)
        more_bugs = [Bug(bzapi, dict=r) for r in result['bugs']]
        bugs.extend(more_bugs)
    return bugs


def query_params(release, all_statuses):
    """
    Return a dict of basic Bugzilla search parameters.

    :param release: eg. "4.2" or "4.2z1"
    :param bool all_statuses: If True, query all BZ states, not just POST and
                              MODIFIED
    """
    if all_statuses:
        statuses = 'NEW ASSIGNED POST MODIFIED ON_DEV'
    else:
        statuses = 'POST MODIFIED ON_DEV'
    params = {
        'include_fields': [
            'id',
            'summary',
            'status',
            'last_change_time',
            'assigned_to',
            'qa_contact',
        ],
        'f1': 'product',
        'o1': 'equals',
        'v1': PRODUCT,
        'f2': 'component',
        'o2': 'notequals',
        'v2': 'Documentation',
        'f3': 'target_release',
        'o3': 'equals',
        'v3': release,
        'f4': 'bug_status',
        'o4': 'anywords',
        'v4': statuses,
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
