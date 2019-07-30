from anthill.platform.api.rest.handlers.detail import DetailMixin
from anthill.platform.api.rest.handlers.edit import (
    CreatingMixin, UpdatingMixin, DeletionMixin, ModelFormHandler)
from anthill.platform.api.rest.handlers.list import ListHandler
from vote.models import Voting, VotingMember
from vote.api.v1.rest.forms import VotingMemberForm


class VotingHandler(CreatingMixin, UpdatingMixin, DeletionMixin, DetailMixin,
                    ModelFormHandler):
    """Multiple operations with voting items."""
    queryset = Voting.query.filter_by(active=True)


class VotingListHandler(ListHandler):
    """Get list of voting items."""
    queryset = Voting.query.filter_by(active=True)


class VoteHandler(CreatingMixin, ModelFormHandler):
    """Create VotingMember object."""
    form_class = VotingMemberForm
    queryset = VotingMember.query.filter_by(enabled=True)

    def configure_object(self, form):
        super().configure_object(form)
        self.object.user_id = self.current_user.id

    async def form_valid(self, form):
        if self.object is None:
            model = self.get_model()
            # noinspection PyAttributeOutsideInit
            self.object = model()
        self.configure_object(form)
        await self.object.vote()
        self.write_json(data='OK')


class DiscardHandler(ModelFormHandler):
    """Discard voting result."""
    queryset = VotingMember.query.filter_by(enabled=True)

    async def delete(self, *args, **kwargs):
        # noinspection PyAttributeOutsideInit
        self.object = await self.get_object()
        await self.object.discard()

    async def post(self, *args, **kwargs):
        await self.delete(*args, **kwargs)

    async def put(self, *args, **kwargs):
        await self.delete(*args, **kwargs)


class ResultHandler(ModelFormHandler):
    """Get voting result."""
    queryset = Voting.query.filter_by(active=True)

    async def get(self, *args, **kwargs):
        # noinspection PyAttributeOutsideInit
        self.object = await self.get_object()
        self.write_json(data=self.object.result)
