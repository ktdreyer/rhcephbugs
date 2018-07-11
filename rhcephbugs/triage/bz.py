from __future__ import print_function, absolute_import
import errno
import pickle
from bugzilla import Bugzilla
from bugzilla.bug import Bug


BZ_URL = 'bugzilla.redhat.com'
PRODUCT = 'Red Hat Ceph Storage'

bzapi = Bugzilla(BZ_URL)

if not bzapi.logged_in:
    raise SystemExit('Not logged in, see ~/.bugzillatoken.')


def search(payload):
    """
    Send a payload to the Bug.search RPC, and translate the result into
    bugzilla.bug.Bug results.
    """
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


def bug_cache(bugs=None):
    """
    read/write a list of bugs from/to pickle file

    :param bugs: if None, simply return the cache results. If not None, write
                 the data to the cache.
    """
    filename = 'bugs.pickle'
    if bugs is None:
        # Read and return the pickle file
        try:
            with open(filename, 'rb') as fh:
                return pickle.load(fh)
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
            return None
    with open(filename, 'wb') as fh:
        pickle.dump(bugs, fh)
    return bugs
