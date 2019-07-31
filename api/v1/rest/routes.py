# For more details about routing, see
# http://www.tornadoweb.org/en/stable/routing.html
from tornado.web import url
from . import handlers as h


route_patterns = [
    url(r'^/voting/(?P<id>[^/]+)/?$', h.VotingHandler, name='voting'),
    url(r'^/voting/?$', h.VotingHandler, name='voting_create'),
    url(r'^/voting-list/?$', h.VotingListHandler, name='voting_list'),
    url(r'^/vote/?$', h.VoteHandler, name='vote'),
    url(r'^/discard/?$', h.DiscardHandler, name='discard'),
    url(r'^/result/?$', h.ResultHandler, name='result'),
]
