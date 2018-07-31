from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


Base = declarative_base()


class User(Base):
    """ Red Hat user """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    dn = Column(String, nullable=False, unique=True)
    displayName = Column(String, nullable=False)
    manager = Column(String, nullable=False)
    mail = Column(String, nullable=False, unique=True)
    uid = Column(String, nullable=False, unique=True)
    aliases = relationship('Alias',
                           order_by='Alias.address',
                           back_populates='user')


class Alias(Base):
    """ Email address alias """
    __tablename__ = 'aliases'
    id = Column(Integer, primary_key=True)
    address = Column(String, nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='aliases')


engine = create_engine('sqlite:///rhcephbugs.db')


def create_all():
    """ Create all the tables. """
    Base.metadata.create_all(engine)


def get_session():
    """ get the DBSesion """
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    return DBSession()
