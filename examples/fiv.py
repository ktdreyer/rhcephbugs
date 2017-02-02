import re
from rhcephbugs.fixed_in_version import FixedInVersion, Build
import bugzilla

# Pretend these values came from CI:
branch = 'ceph-2-rhel-7'
build = 'ceph-10.2.5-1.el7cp'

# Pretend this bug number came from a library that can parse CI messages for
# rhbz ID numbers:
ids = [1367539]

BZURL = 'partner-bugzilla.redhat.com'
# BZURL = 'bugzilla.redhat.com'


def get_distro(branch):
    if re.search('-rhel-\d+$', branch):
        return 'RHEL'
    if re.search('-(?:ubuntu|trusty|xenial)$', branch):
        return 'Ubuntu'
    raise RuntimeError('unknown distro in branch %s' % branch)


def update_fiv(bzapi, ids, build):
    bugs = bzapi.getbugs(ids, include_fields=['id', 'fixed_in'])

    for bug in bugs:
        url = 'https://%s/%d' % (BZURL, bug.id)

        fiv = FixedInVersion(bug.fixed_in)
        new = Build.factory(build, get_distro(branch))
        fiv.update(new)

        if bug.fixed_in == str(fiv):
            print('%s Fixed In Version is already set to "%s"' % (url, fiv))
            continue

        print('%s changing Fixed In Version "%s" to "%s"' % (url, bug.fixed_in,
                                                             fiv))
        update = bzapi.build_update(fixed_in=str(fiv))
        bzapi.update_bugs(bug.id, update)


if __name__ == '__main__':

    bzapi = bugzilla.Bugzilla(BZURL)
    if not bzapi.logged_in:
        raise SystemExit('Not logged into %s. See ~/.bugzillatoken.' % BZURL)

    update_fiv(bzapi, ids, build)
