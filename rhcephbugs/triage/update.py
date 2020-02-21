import errno
import yaml
from rhcephbugs.triage.bz import query_params, search, sort_by_status
try:
    # Python 2 backwards compat
    from __builtin__ import raw_input as input
except ImportError:
    pass


def add_parser(subparsers):
    """ Add our "update" parser to this top-level subparsers object. """
    parser = subparsers.add_parser('update', help='update BZ statuses')

    parser.add_argument('target_release', help='for example: 3.0, or 3.1')
    parser.add_argument('target_milestone', help='for example: rc, or z1')
    parser.set_defaults(func=update)


def update(args):
    release = args.target_release
    milestone = args.target_milestone
    payload = query_params(release, milestone)
    bugs = search(payload)
    total_count = len(bugs)
    print('Found %d bugs blocking %s %s' % (total_count, release, milestone))

    sorted_bugs = sorted(bugs, key=sort_by_status)

    for index, bug in enumerate(sorted_bugs, start=1):
        print('(%d of %d) https://bugzilla.redhat.com/%d - %s' %
              (index, total_count, bug.id, bug.status))
        print('  ' + bug.summary)
        # TODO: does this print the human-readable delta?
        # Would be nice to break this into business days too
        # time = bug.last_change_time.value
        # converted = datetime.datetime.strptime(time, "%Y%m%dT%H:%M:%S")
        # print('Last changed: %s' % converted)
        print('Action: %s' % find_action(bug))
        print('')


def prompt_new_action(old_action):
    prompt = 'Enter an action for this bug: >'
    if old_action:
        print('Old action was:')
        print(old_action)
        prompt = 'Enter to keep this action, or type a new one: >'
    try:
        new_action = input(prompt)
    except KeyboardInterrupt:
        raise SystemExit("\nNot proceeding")
    if new_action:
        return new_action
    return old_action


def find_action(bug):
    status = load_status(bug)
    action = status.get('action')
    last_change_time = status.get('last_change_time')
    if not last_change_time:
        print('No last recorded date for %s' % bug.bug_id)
        action = prompt_new_action(action)
        save_status(bug, action)
        return action
    if bug.last_change_time.value > last_change_time:
        print('%s has changed since last recorded action' % bug.bug_id)
        # TODO: maybe give other options here:
        # 1) "go back" if you want to edit the previous one
        # 2) "show last comment" to see the final comment ...
        #    ... or do this by default?
        action = prompt_new_action(action)
        save_status(bug, action)
    return action


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


def save_status(bug, action):
    """ Persist a bug's action to disk. """
    filename = 'status/%d.yml' % bug.id
    data = {
        'action': action,
        'last_change_time': bug.last_change_time.value,
    }
    with open(filename, 'w') as stream:
        yaml.dump(data, stream, default_flow_style=False)
