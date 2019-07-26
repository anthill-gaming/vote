from anthill.platform.api.rest.handlers.detail import DetailMixin
from anthill.platform.api.rest.handlers.edit import (
    CreatingMixin, UpdatingMixin, DeletionMixin, ModelFormHandler)
from anthill.platform.api.rest.handlers.list import ListHandler
from vote.models import Voting, VotingMember
from vote.api.v1.rest.forms import VotingMemberForm


class VotingHandler(CreatingMixin, UpdatingMixin, DeletionMixin, DetailMixin,
                    ModelFormHandler):
    """Multiple operations with voting items."""
    model = Voting


class VotingListHandler(ListHandler):
    """Get list of voting items."""
    model = Voting


class VoteHandler(CreatingMixin, ModelFormHandler):
    """Create VotingMember object."""
    model = VotingMember
    form_class = VotingMemberForm

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


class DiscardHandler(ModelFormHandler):
    """Discard voting result."""
    model = VotingMember

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
    model = Voting

    async def get(self, *args, **kwargs):
        # noinspection PyAttributeOutsideInit
        self.object = await self.get_object()
        self.write_json(data=self.object.result)
