
from oauthlib.oauth2 import BackendApplicationClient
from requests.adapters import HTTPAdapter
from requests_oauthlib import OAuth2Session
from urllib3 import Retry

from ocd_backend.settings import TAPI_ROOT_URL, USER_AGENT, TAPI_CLIENT_ID, TAPI_CLIENT_SECRET


def get_client(client_id, scope=None):
    session = OAuth2Session(client=BackendApplicationClient(client_id=client_id), scope=scope)
    retry = Retry(
        connect=2,
        backoff_factor=1,
        status_forcelist=(500, 502, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    return session


def get_token(client, client_secret, scope):
    token_url = TAPI_ROOT_URL + 'o/token/'
    return client.fetch_token(
        token_url=token_url,
        client_id=client.client_id,
        client_secret=client_secret,
        scope=scope
    )


def get_client_with_token(client_id, client_secret, scope=None):
    client = get_client(client_id, scope)
    get_token(client, client_secret, scope)
    return client


class OauthMixin(object):
    """A mixin that can be used by enrichers that connect to the Topics API.
    :class:`requests_oauthlib.OAuth2Session` is used to take advantage of HTTP Keep-Alive.
    """

    _oauth_session = None

    @property
    def oauth_session(self, retries=3):
        """Returns a :class:`requests_oauthlib.OAuth2Session` object.
        A new session is created if it doesn't already exist.
        """
        if not self._oauth_session:
            if not (TAPI_CLIENT_ID and TAPI_CLIENT_SECRET):
                raise ValueError("TAPI credentials are not set: {}".format({
                    'TAPI_CLIENT_ID': TAPI_CLIENT_ID,
                    'TAPI_CLIENT_SECRET': TAPI_CLIENT_SECRET,
                }))

            session = get_client_with_token(
                client_id=TAPI_CLIENT_ID,
                client_secret=TAPI_CLIENT_SECRET
            )
            session.headers['User-Agent'] = USER_AGENT
            self._oauth_session = session

        return self._oauth_session
