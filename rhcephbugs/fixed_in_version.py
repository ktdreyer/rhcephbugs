from collections import OrderedDict
import re
import productmd.common

# Special-case certain build names.
RHEL_ONLY = ('ceph-ansible', 'ceph-installer')


class Build(object):
    @staticmethod
    def factory(nvr, distro=None):
        if distro == 'RHEL' \
          or nvr.endswith('.el7') \
          or nvr.endswith('.el7cp') \
          or nvr.endswith('.el7scon'):
            return RhelBuild(nvr)
        elif distro == 'Ubuntu':
            return UbuntuBuild(nvr)
        else:
            raise NotImplementedError(distro)

    def __init__(self, nvr):
        self.nvr = nvr

    def __str__(self):
        return self.nvr

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.nvr)


class RhelBuild(Build):

    distro = 'RHEL'

    def __init__(self, nvr):
        self.nevra_dict = productmd.common.parse_nvra(nvr)
        super(RhelBuild, self).__init__(nvr)

    @property
    def name(self):
        """ Return the name of an RPM build, eg "ruby-rkerberos" or "ceph". """
        return self.nevra_dict['name']


class UbuntuBuild(Build):
    # This class is somewhat copied from rhcephcompose's Build class...

    distro = 'Ubuntu'
    name_version_re = re.compile('^([^_]+)_([^_]+)')

    @property
    def name(self):
        """
        Return the name of a Debian build, eg "ruby-rkerberos" or "ceph".
        """
        return self.name_version_re.match(self.nvr).group(1)


class FixedInVersion(object):
    def __init__(self, value):
        self._orig = value
        self._parse(value)

    def _parse(self, value):
        """ From a string, populate self.data as distros, names, builds.

        For example:

        {'RHEL': {'ceph': RhelBuild(ceph-10.2.5-1.el7cp),
                  'nfs-ganesha': RhelBuild(nfs-ganesha-2.4.2-1.el7cp)},
         'Ubuntu': {'ceph': UbuntuBuild(ceph_10.2.5-2redhat1),
                    'nfs-ganesha': UbuntuBuild(nfs-ganesha_2.4.2-2redhat1)}}

        """
        self.data = OrderedDict()
        dstrs = re.split('(RHEL|Ubuntu):', value)
        if dstrs[0] == '':
            dstrs.pop(0)
        i = iter(dstrs)
        for distro, nvrs in zip(i, i):
            self.data[distro] = OrderedDict()
            for nvr in nvrs.split(' '):
                if nvr == '':
                    continue
                build = Build.factory(nvr, distro)
                self.data[distro][build.name] = build

    def update(self, new):
        """ Update self.data with this new build. """
        if self.data.get(new.distro, None) is None:
            self.data[new.distro] = OrderedDict()
        self.data[new.distro][new.name] = new

    def __str__(self):
        distrostrs = []
        for distro, names in self.data.items():
            buildstr = ' '.join([str(b) for b in names.values()])
            distrostrs.append('%s: %s' % (distro, buildstr))
        result = ' '.join(distrostrs)
        if result == '' and self._orig != '':
            return self._orig
        return result

    @property
    def fixed(self):
        """ Return a bool whether this BZ is completely "fixed" or not. """
        # Rule: if Fixed-In-Version is blank, then it's obviously not fixed.
        if str(self) == '':
            return False
        rhel = self.data.get('RHEL', {})
        ubuntu = self.data.get('Ubuntu', {})
        if len(rhel) == 0 and str(self) != '':
            # We have a non-distro labeled value, eg "ceph-ansible-1-1.el7scon"
            build = Build.factory(str(self))
            # Rule: it's fixed iff this package is on the RHEL-only whitelist.
            return build.name in RHEL_ONLY
        # Rule: every "RHEL:" labeled build must have a corresponding Ubuntu
        # build also.
        for build in rhel.values():
            # ...Unless it's on the RHEL-only whitelist.
            if build.name in RHEL_ONLY:
                continue
            # ...or unless it's calamari, which has a different name on Ubuntu.
            if build.name == 'calamari-server' and 'calamari' in ubuntu:
                continue
            # ...If the corresponding Ubuntu build is missing, this is unfixed.
            if build.name not in ubuntu:
                return False
        return True
