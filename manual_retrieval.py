#!usr/bin/env python
# Sometimes it is necessary to manually get data from e.g. iBabs for troubleshooting. The problem is that iBabs only allows whitelisted
# IP addresses to connect. In our case connections from wolf are allowed, so any query you want to execute should be proxied via wolf:
# - In a terminal setup port forwarding: `ssh -gD 8090 wolf`
# - To get data edit and run this script from Docker container `ori_backend_1`. This script uses the proxy via session.proxies.
# - You can test the proxy setup by running e.g. `curl --proxy socks5://host.docker.internal:8090 https://www.nu.nl` in the container        

from pprint import pprint
from requests import Session
from zeep.client import Client, Settings
from zeep.exceptions import Error
from zeep.cache import SqliteCache
from zeep.transports import Transport

from ocd_backend import settings
from ocd_backend.settings import SOURCES_CONFIG_FILE, \
        DEFAULT_INDEX_PREFIX, DUMPS_DIR, REDIS_HOST, REDIS_PORT

class IbabsManualRetrieval: 

    def __init__(self, *args, **kwargs):
        soap_settings = Settings(
            strict=False,
            xml_huge_tree=True,
            xsd_ignore_sequence_order=True,
            extra_http_headers={'User-Agent': settings.USER_AGENT},
        )
        cache = SqliteCache(path='/tmp/sqlite.db', timeout=60)

        session = Session()
        session.proxies = {
            'http': 'socks5://host.docker.internal:8090',
            'https': 'socks5://host.docker.internal:8090'
        }
        transport=Transport(session=session, cache=cache)

        try:
            self.client = Client(settings.IBABS_WSDL,
                                port_name='BasicHttpsBinding_IPublic',
                                settings=soap_settings, transport=transport)
            
        except Error as e:
            print(f'Unable to instantiate iBabs client: {str(e)}')

    def retrieve(self):
        meeting_types = self.client.service.GetMeetingtypes(
            'aa-en-maas'
        )

        pprint(meeting_types)

p = IbabsManualRetrieval()
p.retrieve()