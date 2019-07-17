# For more details about routing, see
# http://www.tornadoweb.org/en/stable/routing.html
from tornado.web import url
from . import handlers

route_patterns = [
    url(r'^/voting/(?P<id>[^/]+)/?$', handlers.VotingHandler, name='voting'),
    url(r'^/voting/?$', handlers.VotingHandler, name='voting_create'),
    url(r'^/voting-list/?$', handlers.VotingsListHandler, name='voting_list'),
    url(r'^/vote/?$', handlers.VoteHandler, name='vote'),
    url(r'^/discard/?$', handlers.DiscardHandler, name='discard'),
    url(r'^/result/?$', handlers.ResultHandler, name='result'),
]
