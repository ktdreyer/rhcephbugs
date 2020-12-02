from __future__ import print_function
import errno
import yaml
from rhcephbugs.triage.models import Person
from rhcephbugs.triage.models import Bug as BugModel
from rhcephbugs.triage.models import create_all, get_session
from rhcephbugs.triage.template import report_everyone
from rhcephbugs.triage.bz import query_params, search


"""
Print the "all users" report to STDOUT.
"""


def add_parser(subparsers):
    """ Add our "report" parser to this top-level subparsers object. """
    parser = subparsers.add_parser('report', help='report BZ statuses')

    parser.add_argument('target_release', help='for example: 3.0, or 3.1')
    parser.set_defaults(func=report)


def report(args):
    release = args.target_release

    payload = query_params(release)
    bugs = search(payload)

    print('Found %d bugs blocking %s' % (len(bugs), release))

    session = setup_db(bugs)
    people = session.query(Person).order_by(Person.name).all()
    report = report_everyone(release, people)
    print(report)


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
