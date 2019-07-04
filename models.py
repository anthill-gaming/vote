# For more details, see
# http://docs.sqlalchemy.org/en/latest/orm/tutorial.html#declare-a-mapping
from anthill.framework.utils.asynchronous import as_future
from anthill.framework.db import db
from anthill.framework.utils import timezone
from anthill.platform.api.internal import InternalAPIMixin
from anthill.platform.auth import RemoteUser
from sqlalchemy_utils.types import ScalarListType
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates


class VotingError(Exception):
    pass


class Voting(db.Model):
    __tablename__ = 'voting'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(512), nullable=False)
    start_at = db.Column(db.DateTime, default=timezone.now)
    finish_at = db.Column(db.DateTime, nullable=False)
    items = db.Column(ScalarListType(), nullable=False)
    users = db.Column(ScalarListType(), default=[])
    enabled = db.Column(db.Boolean, default=True)
    anonymous = db.Column(db.Boolean, default=True)
    can_discard = db.Column(db.Boolean, default=True)
    select_count = db.Column(db.Integer, default=1)

    members = db.relationship('VotingMember', backref='voting', lazy='dynamic')

    @validates('finish_at')
    def validate_finish_at(self, key, value):
        if value <= self.start_at:
            raise ValueError('`finish_at` must be more then `start_at`')
        return value

    @hybrid_property
    def active(self) -> bool:
        return self.finish_at > timezone.now() >= self.start_at and self.enabled

    def result(self) -> list:
        if timezone.now() < self.start_at:
            raise VotingError('Voting not started')
        if timezone.now() < self.finish_at:
            raise VotingError('Voting not finished')
        if self.anonymous:
            return [m.result for m in self.memderships]
        else:
            return [(m.result, m.user_id) for m in self.memderships]


class VotingMember(InternalAPIMixin, db.Model):
    __tablename__ = 'voting_members'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'voting_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    voting_id = db.Column(db.Integer, db.ForeignKey('voting.id'), nullable=False)
    result = db.Column(ScalarListType(), nullable=False)
    created = db.Column(db.DateTime, default=timezone.now)
    updated = db.Column(db.DateTime, onupdate=timezone.now)
    enabled = db.Column(db.Boolean, default=True)
    voted = db.Column(db.Boolean, default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_user(self) -> RemoteUser:
        data = await self.internal_request('login', 'get_user', user_id=self.user_id)
        return RemoteUser(**data)

    @as_future
    def vote(self, items: list) -> None:
        if not self.voting.active:
            raise VotingError('Voting not active')
        if not self.enabled:
            raise VotingError('Voting member disabled')
        if self.voted:
            raise VotingError('Already voted')
        if len(items) != self.voting.select_count:
            raise VotingError('Voting items count: %s/%s' % (len(items), self.voting.select_count))
        if not set(items).issubset(self.voting.items):
            raise VotingError('Voting items is %s. Must be a subset '
                              'of %s' % (','.join(items), ','.join(self.voting.items)))
        self.result = items
        self.voted = True
        self.save()

    @as_future
    def discard(self) -> None:
        if self.voting.can_discard:
            self.delete()
        else:
            raise VotingError('Cannot discard')
