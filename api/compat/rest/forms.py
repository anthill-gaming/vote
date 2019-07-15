from anthill.framework.forms.orm import (
    ModelForm, ModelUpdateForm, ModelCreateForm, ModelSearchForm)
from vote.models import VotingMember


class VotingMemberForm(ModelForm):
    class Meta:
        model = VotingMember
        exclude = ['user_id']
        include = ['voting_id']
