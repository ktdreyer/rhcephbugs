from __future__ import print_function
import errno
import yaml
from rhcephbugs.triage.models import Person
from rhcephbugs.triage.models import Bug as BugModel
from rhcephbugs.triage.models import create_all, get_session
from rhcephbugs.triage.report import report_everyone
from rhcephbugs.triage.bz import query_params, search, bug_cache


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


def main():
    # TODO: a CLI with subcommands:
    # triage update 3.1 rc
    #  Refresh all data from Bugzilla, and set any new actions as needed.
    #
    # triage set-action <bznumber>
    #  Rewrite action description for this single bz.
    #
    # triage report
    #   Print the "all users" report to STDOUT
    #
    # This will make it possible to store all the data directly with SQLAlchemy
    # and avoid the YAML files.

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
