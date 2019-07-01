# For more details, see
# http://docs.sqlalchemy.org/en/latest/orm/tutorial.html#declare-a-mapping
from anthill.framework.utils.asynchronous import as_future
from anthill.framework.db import db
from anthill.framework.utils import timezone
from anthill.platform.api.internal import InternalAPIMixin
from anthill.platform.auth import RemoteUser
from sqlalchemy_utils.types import JSONType, ScalarListType
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates
from typing import Generator


class VoteError(Exception):
    pass


class Vote(db.Model):
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(512), nullable=False)
    start_at = db.Column(db.DateTime, default=timezone.now)
    finish_at = db.Column(db.DateTime, nullable=False)
    items = db.Column(ScalarListType(), nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    anonymous = db.Column(db.Boolean, default=True)
    can_revote = db.Column(db.Boolean, default=True)
    select_count = db.Column(db.Integer, default=1)

    memderships = db.relationship('VoteMembership', backref='vote', lazy='dynamic')

    @validates('finish_at')
    def validate_finish_at(self, key, value):
        if value <= self.start_at:
            raise ValueError('`finish_at` must be more then `start_at`')
        return value

    @hybrid_property
    def active(self) -> bool:
        return self.finish_at > timezone.now() >= self.start_at and self.enabled

    def result(self) -> Generator:
        if timezone.now() < self.start_at:
            raise VoteError('Vote not started')
        if timezone.now() < self.finish_at:
            raise VoteError('Vote not finished')
        if self.anonymous:
            return (m.result for m in self.memderships)
        else:
            return ((m.result, m.user_id) for m in self.memderships)

    @as_future
    def join(self, user_id: str) -> None:
        m = VoteMembership(user_id=user_id, vote_id=self.id)
        self.memderships.append(m)
        db.session.add(m)
        db.session.commit()


class VoteMembership(InternalAPIMixin, db.Model):
    __tablename__ = 'vote_memberships'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    vote_id = db.Column(db.Integer, db.ForeignKey('votes.id'), nullable=False)
    result = db.Column(ScalarListType(), nullable=False)
    created = db.Column(db.DateTime, default=timezone.now)
    updated = db.Column(db.DateTime, onupdate=timezone.now)
    enabled = db.Column(db.Boolean, default=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_user(self) -> RemoteUser:
        data = await self.internal_request('login', 'get_user', user_id=self.user_id)
        return RemoteUser(**data)

    @hybrid_property
    def voted(self) -> bool:
        return bool(self.result)

    @as_future
    def do_vote(self, items: list) -> None:
        if not self.vote.active:
            raise VoteError('Vote not active')
        if not self.enabled:
            raise VoteError('Vote membership disabled')
        if self.voted and not self.vote.can_revote:
            raise VoteError('Already voted')
        if len(items) != self.vote.select_count:
            raise VoteError('Voted items count: %s/%s' % (len(items), self.vote.select_count))
        if not set(items).issubset(self.vote.items):
            raise VoteError('Voted items is %s. Must be a subset '
                            'of %s' % (','.join(items), ','.join(self.vote.items)))
        self.result = items
        self.save()
