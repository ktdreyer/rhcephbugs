from rhcephbugs.fixed_in_version import FixedInVersion, Build
import pytest

SAMPLE_STRINGS = (
    'RHEL: ceph-10.2.5-1.el7cp',
    'RHEL: ceph-10.2.5-1.el7cp nfs-ganesha-2.4.2-1.el7cp',
    'RHEL: ceph-10.2.5-1.el7cp Ubuntu: ceph_10.2.5-2redhat1',
    'RHEL: ceph-10.2.5-1.el7cp nfs-ganesha-2.4.2-1.el7cp '
    'Ubuntu: ceph_10.2.5-2redhat1 nfs-ganesha_2.4.2-2redhat1',
)


def test_blank():
    fiv = FixedInVersion('')
    assert str(fiv) == ''


def test_no_distro():
    fiv = FixedInVersion('ceph-10.2.5-1.el7cp')
    assert str(fiv) == 'ceph-10.2.5-1.el7cp'


@pytest.mark.parametrize('sample', SAMPLE_STRINGS)
def test_simple_interpolation(sample):
    fiv = FixedInVersion(sample)
    assert str(fiv) == sample


@pytest.mark.parametrize('sample', (
    '',                           # Empty string
    'RHEL: ceph-10.2.5-1.el7cp',  # Lower NVR
    'RHEL: ceph-10.2.5-2.el7cp',  # Same NVR
    'RHEL: ceph-10.2.5-3.el7cp',  # Higher NVR
))
def test_simple_add(sample):
    fiv = FixedInVersion(sample)
    new = Build.factory('ceph-10.2.5-2.el7cp', 'RHEL')
    fiv.update(new)
    assert str(fiv) == 'RHEL: ceph-10.2.5-2.el7cp'


def test_update_no_distro():
    fiv = FixedInVersion('ceph-10.2.5-1.el7cp')
    new = Build.factory('ceph-10.2.5-2.el7cp', 'RHEL')
    fiv.update(new)
    assert str(fiv) == 'RHEL: ceph-10.2.5-2.el7cp'


def test_multi_distro_add():
    fiv = FixedInVersion('RHEL: ceph-10.2.5-2.el7cp')
    new = Build.factory('ceph_10.2.5-2redhat1', 'Ubuntu')
    fiv.update(new)
    assert str(fiv) == 'RHEL: ceph-10.2.5-2.el7cp Ubuntu: ceph_10.2.5-2redhat1'


@pytest.mark.parametrize('sample,expected', [
    ('', False),
    ('ceph-10.2.5-2.el7cp', False),
    ('RHEL: ceph-10.2.5-1.el7cp', False),
    ('RHEL: ceph-10.2.5-2.el7cp Ubuntu: ceph_10.2.5-2redhat1', True),
    ('RHEL: calamari-server-1.5.5-1.el7cp Ubuntu: calamari_1.5.5-2redhat1', True),  # NOQA E501
    ('ceph-ansible-2.2.0-1.el7cp', True),
    ('RHEL: ceph-ansible-2.2.0-1.el7cp', True),
    ('RHEL: ceph-10.2.5-1.el7cp ceph-ansible-2.2.0-1.el7cp', False),
    ('ceph-installer-1.3.0-1.el7cp', True),
])
def test_fixed(sample, expected):
    fiv = FixedInVersion(sample)
    assert fiv.fixed is expected
