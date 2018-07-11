from __future__ import print_function
import errno
import pickle
import yaml
from bugzilla import Bugzilla
from bugzilla.bug import Bug
from rhcephbugs.triage.models import Person
from rhcephbugs.triage.models import Bug as BugModel
from rhcephbugs.triage.models import create_all, get_session
from rhcephbugs.triage.report import report_everyone


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


def load_status(bug):
    """ Load a bug's status from disk. """
    filename = 'status/%d.yml' % bug.id
    try:
        with open(filename, 'r') as stream:
            return yaml.safe_load(stream)
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise
        return {}


def setup_db(bugs):
    """
    Return an in-memory sqlite database from all the YAML files' data.
    """
    create_all()
    session = get_session()

    for bug in bugs:
        status = load_status(bug)
        if not status:
            continue

        # Get/Create a Person for this bug.
        person_name = status['action'].split(' ', 1)[0]
        person = session.query(Person).filter_by(name=person_name).first()
        if not person:
            person = Person(name=person_name)
            session.add(person)
            session.commit()

        # Insert this Bug into the bugs table
        new_bug = BugModel(id=bug.id,
                           summary=bug.summary,
                           status=bug.status,
                           last_change_time=status['last_change_time'],
                           action=status['action'],
                           person=person)
        session.add(new_bug)
        session.commit()
    return session


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


def main():
    release = '3.1'
    milestone = 'rc'
    bugs = bug_cache()
    # HACK: pickle bugs for this release so we don't have to load BZ each time.
    if bugs is None:
        print('no bugs cached, quering Bugzilla')
        payload = query_params(release, milestone)
        bugs = search(payload)
        bug_cache(bugs)
    print('Found %d bugs blocking %s %s' % (len(bugs), release, milestone))

    session = setup_db(bugs)
    people = session.query(Person).order_by(Person.name).all()
    report = report_everyone(release, milestone, people)
    print(report)


if __name__ == '__main__':
    main()
