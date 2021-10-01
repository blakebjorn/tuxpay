import asyncio
import datetime
import itertools
import json
import random
import socket
import ssl
import traceback
from collections import defaultdict
from pathlib import Path
from typing import List, Optional

import aiorpcx
from aiorpcx import SOCKSProxy, SOCKSFailure
from aiorpcx.jsonrpc import ProtocolError, Notification, CodeMessageError
from aiorpcx.rawsocket import RSClient
from sqlalchemy import and_

from modules.helpers import read_json, to_json, EPOCH
from modules.logging import logger
from modules.models import ElectrumServer, database
from modules import config


class ElectrumError(ValueError):
    pass


class NoServersError(ElectrumError):
    pass


class NotificationSession(aiorpcx.RPCSession):
    def __init__(self, *args, host_string="", **kwargs):
        super(NotificationSession, self).__init__(*args, **kwargs)
        self.host_string = host_string
        self.subscriptions = defaultdict(list)
        self.cache = {}
        self.default_timeout = 10  # in seconds
        self._msg_counter = itertools.count(start=1)
        self._keepalive: Optional[asyncio.Task] = None
        self.cost_hard_limit = 0  # disable aiorpcx resource limits

    async def handle_request(self, request):
        logger.debug(f"--> {request}")
        try:
            if isinstance(request, Notification):
                params, result = request.args[:-1], request.args[-1]
                key = to_json([request.method, params])
                if key in self.subscriptions:
                    self.cache[key] = result
                    for queue in self.subscriptions[key]:
                        await queue.put(request.args)
                else:
                    raise Exception(f'unexpected notification')
            else:
                raise Exception(f'unexpected request. not a notification')
        except Exception as e:
            logger.info(f"error handling request {request}. exc: {repr(e)}")
            await self.close()

    async def send_request(self, *args, timeout=None, **kwargs):
        # note: semaphores/timeouts/backpressure etc are handled by
        # aiorpcx. the timeout arg here in most cases should not be set
        msg_id = next(self._msg_counter)
        logger.debug(f"<-- {args} {kwargs} (id: {msg_id})")
        try:
            # note: RPCSession.send_request raises TaskTimeout in case of a timeout.
            # TaskTimeout is a subclass of CancelledError, which is *suppressed* in TaskGroups
            response = await asyncio.wait_for(
                super().send_request(*args, **kwargs),
                timeout)
        except (aiorpcx.TaskTimeout, asyncio.TimeoutError) as e:
            raise ConnectionError(f'request timed out: {args} (id: {msg_id})') from e
        except CodeMessageError as e:
            logger.debug(f"--> {repr(e)} (id: {msg_id})")
            raise
        else:
            logger.debug(f"--> {response} (id: {msg_id})")
            return response

    async def keep_alive(self):
        while True:
            await asyncio.sleep(30)
            if self.subscriptions:
                try:
                    async with aiorpcx.timeout_after(5):
                        await self.send_request("server.ping", [])
                except aiorpcx.TaskTimeout:
                    logger.warn(f"timeout when pinging {self.host_string}")
                except:
                    logger.warn(f"unspecified error when pinging {self.host_string}")

    async def subscribe(self, method: str, params: List, queue: asyncio.Queue):
        # note: until the cache is written for the first time,
        # each 'subscribe' call might make a request on the network.
        key = to_json([method, params])
        self.subscriptions[key] = [queue]
        if key in self.cache:
            result = self.cache[key]
        else:
            result = await self.send_request(method, params)
            self.cache[key] = result

        if self._keepalive is None:
            self._keepalive = asyncio.create_task(self.keep_alive())

        await queue.put(params + [result])

    def unsubscribe(self, queue):
        """Unsubscribe a callback to free object references to enable GC."""
        # note: we can't unsubscribe from the server, so we keep receiving
        # subsequent notifications
        for v in self.subscriptions.values():
            if queue in v:
                v.remove(queue)
        for k in list(self.subscriptions.keys()):
            if not self.subscriptions[k]:
                del self.subscriptions[k]

    def default_framer(self):
        # overridden so that max_size can be customized
        # in bytes. 1mb is used for electrum
        return aiorpcx.NewlineFramer(max_size=1_000_000)

    async def teardown(self):
        if self._keepalive is not None:
            self._keepalive.cancel()
        await self.close(force_after=3)
        return self.subscriptions


class ElectrumX:
    blockchain_transaction_get = "blockchain.transaction.get"
    blockchain_transaction_broadcast = "blockchain.transaction.broadcast"
    blockchain_headers_subscribe = "blockchain.headers.subscribe"
    blockchain_scripthash_subscribe = "blockchain.scripthash.subscribe"
    blockchain_scripthash_get_history = "blockchain.scripthash.get_history"
    blockchain_scripthash_listunspent = "blockchain.scripthash.listunspent"
    blockchain_relayfee = "blockchain.relayfee"
    blockchain_estimatefee = "blockchain.estimatefee"
    server_peers_subscribe = "server.peers.subscribe"

    def __init__(self, symbol, default_ports=None):
        self.symbol = symbol
        self.default_servers = read_json(Path(f"data/electrumx-servers.json"), {}).get(symbol)
        self.user_servers = self.load_user_servers()

        self.default_ports = default_ports or {'t': 50001, 's': 50002}
        self.session: Optional[NotificationSession] = None

        # This needs to be instantiated inside the asyncio loop
        self.servers: Optional[dict] = None
        self.connection_lock = None
        self.proxy = None

    def parse_user_server(self, user_string):
        if " " in user_string:
            host, info = user_string.split(" ", maxsplit=1)
            t = None
            s = None
            for x in info.split(" "):
                if x.startswith('s'):
                    s = x[1:] if len(x) > 1 and int(x[1:]) > 1 else self.default_ports['s']
                if x.startswith('t'):
                    t = x[1:] if len(x) > 1 and int(x[1:]) > 1 else self.default_ports['t']
            return f"{host}|{t or ''}|{s or ''}"
        else:
            logger.warn(f"Invalid user electrumX server specification: {user_string}")
            return None

    def load_user_servers(self):
        user_servers = config.get('electrumx_servers', coin=self.symbol)
        if user_servers:
            user_servers = [self.parse_user_server(x) for x in user_servers]
            user_servers = [x for x in user_servers if x]
            self.default_servers.update({k: {} for k in user_servers})
        return user_servers or None

    async def initialize(self):
        if self.connection_lock is None:
            self.connection_lock = asyncio.Lock()
        servers = await database.fetch_all(ElectrumServer.select().where(ElectrumServer.c.symbol == self.symbol))
        servers = {x['host']: {k: v for k, v in x.items() if k not in ('symbol', 'host')} for x in servers}
        a = {host: {} for host in self.default_servers}
        a.update(servers)
        self.servers = a

        _tor_host = config.get("tor_proxy")
        if _tor_host:
            self.proxy = await SOCKSProxy.auto_detect_at_address(_tor_host, None)
            if self.proxy is None:
                logger.warn(f"Could not connect to tor proxy @ {_tor_host}")

    async def random_server(self, exclude=None):
        if self.servers is None:
            await self.initialize()

        options = [x for x in self.servers.keys() if len(str(x).split("|")) == 3]

        if self.user_servers:
            if config.check("electrumx_no_public_fallback", coin=self.symbol):
                options = self.user_servers
            else:
                options = self.user_servers + [x for x in options if x not in self.user_servers]

        if exclude:
            options = [x for x in options if x != exclude]

        if not options:
            return None

        # Sort servers by % reachable (rounded to whole percent), followed by last_seen date
        options = sorted(options, key=self.server_priority, reverse=True)

        # Pick in exponentially decreasing likelihood
        options = options[:10] if len(options) > 10 else options
        return random.choices(options, k=1, weights=[100 ** (0.8 ** x) for x in range(len(options))])[0]

    def server_priority(self, host_string):
        server = self.servers.get(host_string, {})
        reachable = 0
        if server.get("connections"):
            successes = int(server.get("connections")) - int(server.get("failures") or 0)
            reachable = round(successes / int(server.get("connections")), 2)
        return reachable, server.get("last_seen") or EPOCH

    async def save_server_list(self):
        updates = [dict(host=k, symbol=self.symbol, **v) for k, v in self.servers.items() if v.get("id")]
        new = (dict(host=k, symbol=self.symbol, **v) for k, v in self.servers.items() if not v.get("id"))
        new = [{k: v for k, v in x.items() if k in ElectrumServer.c} for x in new]
        for update in updates:
            await database.execute(ElectrumServer.update()
                                   .where(ElectrumServer.c.id == update.pop("id")).values(**update))
        for n in new:
            pk = await database.execute(ElectrumServer.insert().values(**n))
            self.servers[n['host']]['id'] = pk

        await database.execute(ElectrumServer.delete()
                               .where(and_(ElectrumServer.c.last_seen.is_(None),
                                           ElectrumServer.c.connections > 5)))

    async def _find_peers(self, host_string):
        session = await self.make_session(host_string, None)
        if session:
            try:
                ret = await self._call(session, ElectrumX.server_peers_subscribe, [])
                await session.close()
                return host_string, True, ret
            except (aiorpcx.CancelledError, aiorpcx.TaskTimeout, ProtocolError,
                    aiorpcx.RPCError, socket.gaierror, ElectrumError):
                return host_string, False, []
        return host_string, False, []

    async def update_peers(self):
        if self.servers is None:
            await self.initialize()

        logger.info(f"Updating {self.symbol} peer list")
        from_time = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        to_query = [k for k, v in self.servers.items() if
                    (v.get("last_check") or EPOCH) < from_time]

        if len(to_query) > 20:
            logger.info("reducing new servers to query")
            to_query = list(sorted(to_query, key=lambda x: (self.servers[x].get("last_check") or EPOCH)))

        new_peers = []
        rets = await asyncio.gather(*[self._find_peers(host) for host in to_query])
        for host, success, peers in rets:
            if success:
                if isinstance(peers, list):
                    new_peers += peers

        for ip, addr, info in new_peers:
            dat = {"pruning": "-"}
            s, t = None, None
            for x in info:
                x = str(x)
                if x.startswith('v'):
                    dat['version'] = x[1:]
                if x.startswith('p'):
                    dat['pruning'] = x[1:]
                if x.startswith('s'):
                    s = x[1:] if len(x) > 1 and int(x[1:]) > 1 else self.default_ports['s']
                if x.startswith('t'):
                    t = x[1:] if len(x) > 1 and int(x[1:]) > 1 else self.default_ports['t']
            host = f"{addr}|{t or ''}|{s or ''}"
            if host not in self.servers:
                logger.info(f"adding new peer: {host} {dat}")
                self.servers[host] = dat
        await self.save_server_list()

    async def check(self, method, param):
        if method not in self.session.subscriptions or \
                param not in self.session.subscriptions[method]:
            return
        return self.session.subscriptions[method][param]

    def unsubscribe(self, queue):
        if self.session is not None:
            self.session.unsubscribe(queue)

    def create_client(self, host_string):
        hostname, p_tcp, p_ssl = host_string.split("|")
        sslc = ssl.SSLContext(ssl.PROTOCOL_TLS) if p_ssl else None

        proxy = None
        if hostname.endswith(".onion"):
            proxy = self.proxy
            if proxy is None:
                raise ConnectionError("Cannot connect to .onion host without active proxy client")

        return RSClient(hostname,
                        p_ssl if p_ssl else p_tcp,
                        ssl=sslc,
                        proxy=proxy,
                        session_factory=lambda x: NotificationSession(x, host_string=host_string))

    def server_increment(self, host_string, key, delta=1):
        if host_string not in self.servers:
            self.servers[host_string] = {}
        self.servers[host_string][key] = (self.servers[host_string].get(key) or 0) + delta

    async def make_session(self, host, subscriptions):
        self.server_increment(host, "connections")
        self.servers[host]['last_check'] = datetime.datetime.utcnow()

        try:
            client = self.create_client(host)
            async with aiorpcx.timeout_after(10):
                _transport, protocol = await client.create_connection()
        except (aiorpcx.TaskTimeout, aiorpcx.CancelledError, socket.gaierror,
                OSError, SOCKSFailure, ConnectionError) as e:
            self.server_increment(host, "failures")
            logger.info(f"{host} connection failed: {repr(e)}")
            return None
        except:
            self.server_increment(host, "failures")
            traceback.print_exc()
            return None

        self.servers[host]['first_seen'] = self.servers[host].get('first_seen') or datetime.datetime.utcnow()
        self.servers[host]['last_seen'] = datetime.datetime.utcnow()

        session: NotificationSession = protocol.session
        if subscriptions:
            for key, val in subscriptions.items():
                ret = json.loads(key)
                method, params = ret
                logger.info(f"Subscribing: {method} {params}")
                for queue in val:
                    await session.subscribe(method, params, queue=queue)
        return session

    async def get_session(self, host=None, subscriptions=None, exclude=None):
        if self.servers is None:
            await self.initialize()
        async with self.connection_lock:
            if self.session is not None:
                return self.session

            while True:
                if host is None:
                    host = await self.random_server(exclude=exclude)
                    if host is None:
                        await self.update_peers()
                        host = await self.random_server()
                        if host is None:
                            raise NoServersError("No available servers")

                self.session = await self.make_session(host, subscriptions)
                if self.session is None:
                    host = None
                    continue
                return self.session

    def validate_elextrumx_call(self, method, result, args=None):
        def ensure(statement):
            if not statement:
                raise ElectrumError(f"RPC Command {method} failed validation - {result}")

        try:
            if method == ElectrumX.blockchain_transaction_get:
                if (args and len(args) == 1) or (args and len(args) >= 2 and not args[1]):
                    # Raw call validation
                    ensure(isinstance(result, str) and len(result) > 20)
                else:
                    # Verbose call validation
                    ensure('vout' in result and all(('value' in vout for vout in result['vout'])))
                return True
            if method == ElectrumX.blockchain_headers_subscribe:
                # [{"height": int, "hex": str}]
                ensure(isinstance(result, list))
                ensure(isinstance(result[0], dict))
                ensure("height" in result[0])
                return True
            if method == ElectrumX.blockchain_scripthash_get_history:
                ensure(all(('tx_hash' in x and ('fee' in x or 'height' in x) for x in result)))
                return True
            if method in (ElectrumX.blockchain_estimatefee, ElectrumX.blockchain_relayfee):
                ensure(isinstance(result, float))
                ensure(0 < float(result) < 0.1)
                return True
            if method == ElectrumX.server_peers_subscribe:
                ensure(isinstance(result, list))
                ensure(all((len(x) == 3 and isinstance(x[2], list)) for x in result))
                return True
            if method == ElectrumX.blockchain_scripthash_subscribe:
                ensure(isinstance(result, list))
                ensure(isinstance(result[0], str))
                return True
            if method == ElectrumX.blockchain_scripthash_listunspent:
                ensure(isinstance(result, list))
                ensure(all(('tx_hash' in x for x in result)))
                return True
        except ElectrumError:
            raise
        except (TypeError, ValueError, KeyError, IndexError) as e:
            raise ElectrumError(f"RPC Command {method} failed validation due to {e} - {result}")

        logger.warning(f"Non-validated call {method} - {json.dumps(result)}")
        return False

    async def _call(self, session, method, args, queue=None):
        try:
            self.server_increment(session.host_string, "connections")
            async with aiorpcx.timeout_after(10):
                if queue:
                    result = await session.subscribe(method, args, queue)
                    if result is None:
                        result = await queue.get()
                else:
                    result = await session.send_request(method, args)
                self.servers[session.host_string]['last_seen'] = datetime.datetime.utcnow()
                self.validate_elextrumx_call(method, result, args)
                return result
        except:
            self.server_increment(session.host_string, "failures")
            raise

    async def penalize_server(self):
        subs = None
        old_host = self.session.host_string if self.session is not None else None
        if self.session is not None:
            self.server_increment(self.session.host_string, "failures")
            subs = await self.session.teardown()
            self.session = None
        await self.get_session(subscriptions=subs, exclude=old_host)

    async def call(self, method, args, queue=None, host=None):
        while True:
            try:
                await self.get_session(host)
            except NoServersError:
                raise

            try:
                assert self.session is not None
                return await self._call(self.session, method, args, queue=queue)
            except (AssertionError, aiorpcx.CancelledError, aiorpcx.TaskTimeout,
                    ProtocolError, aiorpcx.RPCError, ElectrumError) as e:
                logger.info(f"Electrum call failed - "
                             f"{f'{self.session.host_string} - ' if self.session is not None else ''}"
                             f"{e} - retrying")
                await self.penalize_server()
            except Exception as e:
                logger.exception("Exception calling electrumx", exc_info=e)
                raise
