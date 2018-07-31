import logging
from ldap3 import Server, Connection, Tls, SASL, KERBEROS, ALL, BASE
import ssl
try:
    from rhcephbugs.models import User, Alias, create_all, get_session
except ImportError:
    # Make this easier to run directly from a Git checkout
    import sys
    sys.path.insert(1, '.')
    from rhcephbugs.models import User, Alias, create_all, get_session


logging.basicConfig(format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class NoUsersFoundError(Exception):
    """ Found no users in LDAP for this query """
    pass


class MultipleUsersFoundError(Exception):
    """ Found no multiple users in LDAP that matched this query """
    pass


BASEDN = 'ou=users,dc=redhat,dc=com'
MAILDN = 'ou=mx,dc=redhat,dc=com'


def user_from_email(session, conn, email):
    """
    Find a User who owns this email address string.

    Note: this requires an authenticated LDAP connection.

    :param session: sqlalchemy.orm.session.Session
    :param conn: ldap3.Connection
    :param email: str eg "kdreyer@redhat.com"
    :returns: a User
    """
    user = session.query(User).join(Alias).filter(Alias.address == email).first()
    if not user:
        # try searching for the "mail" attr directly.
        user = session.query(User).filter_by(mail=email).first()
    if user:
        return user
    key = email.split('@')[0]
    query = '(sendmailMTAKey=%s)' % key
    log.debug('searching LDAP for %s' % query)
    conn.search(MAILDN, query, attributes=['sendmailMTAAliasValue'])
    entry = _one_result(conn.entries, query)
    value = entry.sendmailMTAAliasValue.value
    uid = value.split('@')[0]  # "kdreyer"
    user = user_from_uid(session, conn, uid)
    if email != user.mail:
        # Insert this Alias into the aliases table
        new_alias = Alias(address=email, user=user)
        session.add(new_alias)
        session.commit()
    return user


def _one_result(entries, query):
    """
    Ensure there is exactly one result entry for this query, and return it.
    """
    if entries is None:
        raise NoUsersFoundError(query)
    if len(entries) == 0:
        raise NoUsersFoundError(query)
    elif len(entries) > 1:
        raise MultipleUsersFoundError(query)
    return entries[0]


def user_from_dn(session, conn, dn):
    """
    Find a User from this DN string.

    :param session: sqlalchemy.orm.session.Session
    :param conn: ldap3.Connection
    :param dn: str eg "uid=kdreyer,ou=users,dc=redhat,dc=com"
    :returns: a User
    """
    user = session.query(User).filter_by(dn=dn).first()
    if user:
        return user
    log.debug('searching LDAP for %s' % dn)
    conn.search(dn, '(objectClass=*)', BASE, attributes=['*'])
    entry = _one_result(conn.entries, dn)
    user = _to_user(session, entry)
    return user


def user_from_uid(session, conn, uid):
    """
    Find a User from this uid string.

    :param session: sqlalchemy.orm.session.Session
    :param conn: ldap3.Connection
    :param uid: str eg "kdreyer"
    :returns: a User
    """
    user = session.query(User).filter_by(uid=uid).first()
    if user:
        return user
    query = '(&(objectclass=person)(uid=%s))' % uid
    log.debug('searching LDAP for %s' % query)
    conn.search(BASEDN, query, attributes=['*'])
    entry = _one_result(conn.entries, query)
    user = _to_user(session, entry)
    return user


def _to_user(session, entry):
    """
    Translate an LDAP entry to a User object in the database.

    :param entry: an ldap3.abstract.entry.Entry
    :returns: an rhcephbugs.usermodel.User
    """
    user = session.query(User).filter_by(id=entry.uidNumber.value).first()
    if user:
        return user
    user = User(id=entry.uidNumber.value,
                dn=entry.entry_dn,
                displayName=entry.displayName.value,
                manager=entry.manager.value,
                mail=entry.mail.value,
                uid=entry.uid.value,
                )
    session.add(user)
    session.commit()
    return user


def connect():
    hostname = 'ldap.corp.redhat.com'
    tls = Tls(validate=ssl.CERT_REQUIRED)
    server = Server(hostname, use_ssl=True, tls=tls, get_info=ALL)
    conn = Connection(server, authentication=SASL, sasl_mechanism=KERBEROS,
                      check_names=True)
    conn.bind()
    # print(conn.extend.standard.who_am_i())
    return conn


# SQLAlchemy
create_all()
session = get_session()

# LDAP
conn = connect()

"""
user = user_from_email(session, conn, 'shan@redhat.com')
print(user.dn)
for alias in user.aliases:
    print(alias.address)
"""

user = user_from_email(session, conn, 'sage@redhat.com')
print(user.dn)
print(user.displayName)
print(user.manager)
print(user.mail)
print(user.uid)
for alias in user.aliases:
    print(alias.address)

manager = user_from_dn(session, conn, user.manager)
print(manager.displayName)
print(manager.aliases)
