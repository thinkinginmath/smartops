"""Database Models."""
import datetime
import logging
import simplejson as json
import yaml

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ColumnDefault
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import relationship, backref
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator
from sqlalchemy import UniqueConstraint

from smartops.db import exception
from smartops.utils import util


BASE = declarative_base()


class JSONEncoded(TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""

    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class YAMLEncoded(TypeDecorator):
    """Represents an immutable structure as yaml-encoded string."""

    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = yaml.dump(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = yaml.load(value)
        return value


class TimeStampMixin(object):
    created_at = Column(DateTime, default=lambda: datetime.datetime.now())
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(),
                        onupdate=lambda: datetime.datetime.now())


class HelperMixin(object):
    """General table fields for all smartops models."""

    def initialize(self):
        self.update()

    def update(self):
        # Please override in child classes
        pass

    @staticmethod
    def type_compatible(value, column_type):
        """Check if value type is compatible with the column type."""
        if value is None:
            return True
        if not hasattr(column_type, 'python_type'):
            return True
        column_python_type = column_type.python_type
        if isinstance(value, column_python_type):
            return True
        if issubclass(column_python_type, basestring):
            return isinstance(value, basestring)
        if column_python_type in [int, long]:
            return type(value) in [int, long]
        if column_python_type in [float]:
            return type(value) in [float]
        if column_python_type in [bool]:
            return type(value) in [bool]
        return False


    def validate(self):
        """Generate validate function to make sure the record is legal."""
        columns = self.__mapper__.columns
        for key, column in columns.items():
            value = getattr(self, key)
            if not self.type_compatible(value, column.type):
                raise exception.InvalidParameter(
                    'column %s value %r type is unexpected: %s' % (
                        key, value, column.type
                    )
                )


    def to_dict(self):
        """General function to convert record to dict.
        Convert all columns not starting with '_' to
        {<column_name>: <column_value>}
        """
        keys = self.__mapper__.columns.keys()
        dict_info = {}
        for key in keys:
            if key.startswith('_'):
                continue
            value = getattr(self, key)
            if value is not None:
                if isinstance(value, datetime.datetime):
                    value = util.format_datetime(value)
                dict_info[key] = value
        return dict_info


class StatusMixin(TimeStampMixin, HelperMixin):

    status = Column(
        Enum(
            'CREATING_STEP_0', 'CREATING_STEP_1', 'CREATING_STEP_2',
            'CREATING_STEP_3', 'CREATING_STEP_4', 'PLANNING', 'PLAN_GENERATED',
            'LAUNCHING', 'LAUNCHED', 'ERROR', 'DELETING', 'DELETED'
        ),
        ColumnDefault('CREATING_STEP_0')
    )
    message = Column(String(200), default='')
    severity = Column(
        Enum('INFO', 'WARNING', 'ERROR'),
        ColumnDefault('INFO')
    )

    def update(self):
        if self.status in ('PLANNING', 'LAUNCHING') and self.severity == 'ERROR':
            self.staatus = 'ERROR'
        super(StatusMixin, self).update()


class AppBlueprint(BASE, TimeStampMixin, HelperMixin):
    """AppBlueprint Table."""
    __tablename__ = 'blueprint'
    id = Column(Integer, primary_key=True)
    entrypoints = Column(JSONEncoded, default=[])
    content = Column(JSONEncoded, default=[])
    content_string = Column(YAMLEncoded, default='')
    topology = Column(JSONEncoded, default={})
    app_id = Column(
        Integer,
        ForeignKey('app.id', onupdate='CASCADE', ondelete='CASCADE')
    )

    def __init__(self, content, content_string, entrypoints, app_id, **kwargs):
        self.content = content
        self.content_string = content_string
        self.entrypoints = entrypoints
        self.app_id = app_id
        super(AppBlueprint, self).__init__(**kwargs)


class AppSla(BASE, TimeStampMixin, HelperMixin):
    """AppSla Table."""
    __tablename__ = 'sla'
    id = Column(Integer, primary_key=True)
    app_id = Column(
        Integer,
        ForeignKey('app.id', onupdate='CASCADE', ondelete='CASCADE')
    )
    error_rate = Column(Float)
    latency = Column(Integer)
    cost = Column(Float, default=100.0)

    def __init__(self, error_rate, latency, cost, app_id):
        self.error_rate = error_rate
        self.latency = latency
        self.cost = cost
        self.app_id = app_id
        super(AppSla, self).__init__()


class AppStatus(BASE, StatusMixin):
    """AppStatus Table."""
    __tablename__ = 'app_status'
    id = Column(
        Integer,
        ForeignKey('app.id', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True
    )

    def __init__(self, **kwargs):
        super(AppStatus, self).__init__(**kwargs)

    def __str__(self):
        return 'App Status [id:%s,status:%s,message:%s,severity:%s]' % (self.id,
            self.status, self.message, self.severity)


class CapacityPlanStatus(BASE, StatusMixin):
    """CapacityPlan Table."""
    __tablename__ = 'capacity_plan_status'
    id = Column(
        Integer,
        ForeignKey('capacity_plan.id', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True
    )

    def __init__(self, **kwargs):
        super(CapacityPlanStatus, self).__init__(**kwargs)

    def __str__(self):
        return 'Capacity Plan '
        '[id:%s,status:%s,message:%s,severity:%s]' % (self.id,
        self.status, self.message, self.severity)


class CapacityPlan(BASE, TimeStampMixin, HelperMixin):
    """CapacityPlan Table."""
    __tablename__ = 'capacity_plan'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    is_auto = Column(Boolean, default=False)
    config = Column(JSONEncoded, default={})
    start_time = Column(DateTime, default=lambda: datetime.datetime.now())
    app_id = Column(
        Integer,
        ForeignKey('app.id', onupdate='CASCADE', ondelete='CASCADE')
    )
    status = relationship(
        CapacityPlanStatus,
        uselist=False,
        passive_deletes=True, passive_updates=True,
        cascade='all, delete-orphan',
        backref=backref('capacity_plan')
    )

    def __init__(self, **kwargs):
        self.start_time = self.created_at
        super(CapacityPlan, self).__init__(**kwargs)

#    def __str__(self):
#        return {
#            'id': self.id,
#            'app_id': self.app_id
#        }

    def to_dict(self):
        dict_info = super(App, self).to_dict()
        dict_info['status'] = status.status
        dict_info['status_message'] = status.message
        return dict_info


class App(BASE, TimeStampMixin, HelperMixin):
    """App table."""
    __tablename__ = 'app'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    entrypoint = Column(String(80))
    test_plan = Column(JSONEncoded, default={})
    containers = Column(Integer, default=0)
    pods = Column(Integer, default=0)
    services = Column(Integer, default=0)
    status = relationship(
        AppStatus,
        uselist=False,
        passive_deletes=True, passive_updates=True,
        cascade='all, delete-orphan',
        backref=backref('app')
    )
    blueprint = relationship(
        AppBlueprint,
        uselist=False,
        passive_deletes=True, passive_updates=True,
        cascade='all, delete-orphan',
        backref=backref('app')
    )
    sla = relationship(
        AppSla,
        uselist=False,
        passive_deletes=True, passive_updates=True,
        cascade='all, delete-orphan',
        backref=backref('app')
    )
    capacity_plan = relationship(
        CapacityPlan,
        uselist=False,
        passive_deletes=True, passive_updates=True,
        cascade='all, delete-orphan',
        backref=backref('app')
    )

    def __init__(self, name, **kwargs):
        self.name = name
        self.status = AppStatus()
        super(App, self).__init__(**kwargs)

    def __str__(self):
        return 'App[%s:%s]' % (self.id, self.name)

    def update(self):
        self.status.update()
        super(App, self).update()

    def status_dict(self):
        return self.status.to_dict()

    def to_dict(self):
        dict_info = super(App, self).to_dict()
        dict_info['status'] = self.status_dict()
        return dict_info
