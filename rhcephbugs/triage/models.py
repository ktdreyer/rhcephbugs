from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


Base = declarative_base()


class Person(Base):
    __tablename__ = 'people'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    # Many Bugs to one Person
    bugs = relationship('Bug',
                        order_by='Bug.id',
                        back_populates='person')


class Bug(Base):
    __tablename__ = 'bugs'
    id = Column(Integer, primary_key=True)
    summary = Column(String, nullable=False)
    status = Column(String, nullable=False)
    last_change_time = Column(String, nullable=False)
    action = Column(String, nullable=False)
    person_id = Column(Integer, ForeignKey('people.id'))
    person = relationship('Person', back_populates='bugs')


engine = create_engine('sqlite://')


def create_all():
    """ Create all the tables. """
    Base.metadata.create_all(engine)


def get_session():
    """ get the DBSesion """
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    return DBSession()
