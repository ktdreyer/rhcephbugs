import argparse
from rhcephbugs.triage import bz


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('old_target', help='For example: 7.0, or 7.0z1')
    parser.add_argument('new_target', help='For example: 7.0z2')
    parser.add_argument('comment', help='For example: "Today we decided..."')
    parser.add_argument('ignore', nargs='*',
                        help='Optionally ignore certain IDs. '
                             'For example: 1801090')

    args = parser.parse_args()

    params = query_params(args.old_target, args.ignore)
    bugs = bz.search(params)
    print('Found %d bugs for %s' % (len(bugs), args.old_target))

    sorted_bugs = sorted(bugs, key=bz.sort_by_status)

    bzapi = None
    bug_ids = []
    for bug in sorted_bugs:
        print('https://bugzilla.redhat.com/%d - %s - %s'
              % (bug.id, bug.status, bug.summary))
        bug_ids.append(bug.id)
        if bzapi is None:
            bzapi = bug.bugzilla

    update = bzapi.build_update(target_release=args.new_target,
                                comment=args.comment,
                                comment_private=True)
    bzapi.update_bugs(bug_ids, update)


def query_params(release, ignore):
    """
    Return a dict of basic Bugzilla search parameters.

    :param str release: eg. "7.0" or "7.0z4"
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
        'f4': 'bug_status',
        'o4': 'anywords',
        'v4': 'NEW ASSIGNED POST MODIFIED ON_DEV'
    }
    for idx, bug_id in enumerate(ignore, start=5):
        params['f%d' % idx] = 'bug_id'
        params['o%d' % idx] = 'notequals'
        params['v%d' % idx] = bug_id
    return params.copy()
