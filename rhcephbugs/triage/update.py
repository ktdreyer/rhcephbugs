import os
import humanize
import datetime
import errno
import yaml
from rhcephbugs.triage.bz import query_params, search, sort_by_status
from colorama import init, Fore, Style
try:
    # Python 2 backwards compat
    from __builtin__ import raw_input as input
except ImportError:
    pass


def add_parser(subparsers):
    """ Add our "update" parser to this top-level subparsers object. """
    parser = subparsers.add_parser('update', help='update BZ statuses')

    parser.add_argument('target_release', help='for example: 4.2, or 4.2z1')
    parser.add_argument('--all', action='store_true',
                        help='Query all BZ states, not just '
                             'POST/ON_DEV/MODIFIED. Use this to get a bigger '
                             'picture of the release, not just build '
                             'team-related bugs.')
    parser.set_defaults(func=update)


def update(args):
    release = args.target_release
    payload = query_params(release, args.all)
    bugs = search(payload)
    total_count = len(bugs)
    init(autoreset=True)
    print('Found %d bugs blocking %s' % (total_count, release))

    sorted_bugs = sorted(bugs, key=sort_by_status)

    for index, bug in enumerate(sorted_bugs, start=1):
        assignee = find_assignee(bug)
        title = f'{index} of {total_count} {bug.status} ' \
            f'https://bugzilla.redhat.com/{bug.id} - {assignee}'
        print(Style.BRIGHT + Fore.YELLOW + title)
        print('  ' + bug.summary)
        delta = naturaldelta(bug.last_change_time.value)
        print(Style.DIM + '  Last changed %s ago' % delta)
        print(Fore.GREEN + 'Action: %s' % find_action(bug))
        print('')


def naturaldelta(time_str):
    """ humanize.naturaldelta() on a xmlrpc.client.DateTime value string. """
    # TODO: Would be nice to break this into business days too
    time = datetime.datetime.strptime(time_str, "%Y%m%dT%H:%M:%S")
    difference = time - datetime.datetime.utcnow()
    return humanize.naturaldelta(difference)


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
    """
    Persist a bug's action to disk.

    Why do we store the results in plaintext YAML files instead of the sqlite
    database that we use for reporting? The reason is that humans have to
    read, search, and edit the data by hand. Here are some use-cases:

    - I have to correct a status for a particular ID after I submit it.
    - I have to correct a set of statuses that contain a particular substring
      where I got the status wrong or typo'd someone's name.
    - I have to grep and count all the bugs that have the same substring in
      their status (For example, to count how many bugs will be fixed by a
      planned rebase).
    - I have to grep to find a bug that has a substring in its status in order
      to paste that status into other bugs.

    It is easier to write the canonical statuses to the YAML files, and then
    load those into sqlite later for processing and reporting.
    """

    filename = 'status/%d.yml' % bug.id
    data = {
        'action': action,
        'last_change_time': bug.last_change_time.value,
    }
    with open(filename, 'w') as stream:
        yaml.dump(data, stream, default_flow_style=False)


def find_assignee(bug):
    """Read human name from a cache and fall back to Bugzilla's user name
    """
    xdg_cache_home = os.getenv('XDG_CACHE_HOME', '~/.cache')
    xdg_cache_home = os.path.expanduser(xdg_cache_home)
    cache_path = os.path.join(xdg_cache_home, 'rhcephbugs', bug.assigned_to)
    try:
        with open(cache_path) as file:
            name = file.read().strip()
    except FileNotFoundError:
        name = bug.assigned_to_detail['real_name']
    return name
