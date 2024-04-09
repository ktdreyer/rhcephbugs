import argparse
from rhcephbugs.triage import bz


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('target_release', help='For example: 3.0, or 3.1')
    parser.add_argument('old_milestone', help='For example: rc, or z1')
    parser.add_argument('new_milestone', help='For example: z2')
    parser.add_argument('comment', help='For example: "Today we decided..."')
    parser.add_argument('ignore', nargs='*',
                        help='Optionally ignore certain IDs. '
                             'For example: 1801090')

    args = parser.parse_args()

    params = query_params(args.target_release, args.old_milestone, args.ignore)
    bugs = bz.search(params)
    print('Found %d bugs for %s %s' % (len(bugs), args.target_release,
                                       args.old_milestone))

    sorted_bugs = sorted(bugs, key=bz.sort_by_status)

    bzapi = None
    bug_ids = []
    for bug in sorted_bugs:
        print('https://bugzilla.redhat.com/%d - %s - %s'
              % (bug.id, bug.status, bug.summary))
        bug_ids.append(bug.id)
        if bzapi is None:
            bzapi = bug.bugzilla

    update = bzapi.build_update(target_milestone=args.new_milestone,
                                comment=args.comment,
                                comment_private=True)
    bzapi.update_bugs(bug_ids, update)


def query_params(release, milestone, ignore):
    """
    Return a dict of basic Bugzilla search parameters.

    :param str release: eg. "3.0"
    :param str milestone: eg. "z4"
    :param list ignore: list of bug id strings, to ignore, eg. ["1801090"]
    """
    params = {
        'include_fields': ['id', 'summary', 'status'],
        'f1': 'product',
        'o1': 'equals',
        'v1': bz.PRODUCT,
        'f2': 'target_release',
        'o2': 'equals',
        'v2': release,
        'f3': 'target_milestone',
        'o3': 'equals',
        'v3': milestone,
        'f4': 'bug_status',
        'o4': 'anywords',
        'v4': 'NEW ASSIGNED POST MODIFIED ON_DEV'
    }
    for idx, bug_id in enumerate(ignore, start=5):
        params['f%d' % idx] = 'bug_id'
        params['o%d' % idx] = 'notequals'
        params['v%d' % idx] = bug_id
    return params.copy()
