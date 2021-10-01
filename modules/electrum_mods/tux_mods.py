import time
from functools import wraps
from multiprocessing import Lock
from typing import List, Tuple, Union

from aiorpcx import TaskGroup
from electrum.bitcoin import address_to_scripthash, deserialize_privkey

from modules.coins import CoinNetwork, ALL_COINS
from modules.electrum_mods.functions import *
from modules.electrum_mods.tux_tx import PartialTxOutput, PartialTxInput, Transaction, TxOutpoint, PartialTransaction
from modules.electrumx import ElectrumX

LEGACY_TX = 0
SEGWIT_TX = 1

networkLocks = {}
network_lock: Lock = Lock()


def network_context(symbol_net: Union[str, CoinNetwork]):
    def network_decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            with NetworkLock(symbol_net):
                return func(*args, **kwargs)

        return decorated_function

    return network_decorator


class NetworkLock(object):
    def __init__(self, symbol_net: Union[str, CoinNetwork]):
        if isinstance(symbol_net, str):
            self.symbol = symbol_net
        elif isinstance(symbol_net, CoinNetwork):
            self.symbol = symbol_net.symbol

        assert self.symbol

        if self.symbol not in networkLocks:
            with network_lock:
                networkLocks[self.symbol] = 0

    @property
    def other_keys_exist(self):
        network_lock.acquire()
        for key in (x for x in networkLocks if x != self.symbol):
            if networkLocks[key] > 0:
                network_lock.release()
                return True
        return False

    def __enter__(self):
        # check to see if any other sessions are active
        p = False
        while self.other_keys_exist:
            if not p:
                p = True
            time.sleep(0.01)
        networkLocks[self.symbol] += 1
        network_lock.release()

        if networkLocks[self.symbol] == 1:
            constants.net = ALL_COINS[self.symbol]

    def __exit__(self, type, value, traceback):
        with network_lock:
            networkLocks[self.symbol] -= 1

        if networkLocks[self.symbol] == 0:
            constants.net = None


def serialize_privkey(secret: bytes, compressed: bool, txin_type: str, *,
                      internal_use: bool = False, net: CoinNetwork) -> str:
    # we only export secrets inside curve range
    secret = ecc.ECPrivkey.normalize_secret_bytes(secret)
    if internal_use:
        prefix = bytes([(WIF_SCRIPT_TYPES[txin_type] + net.WIF_PREFIX) & 255])
    else:
        prefix = bytes([net.WIF_PREFIX])
    suffix = b'\01' if compressed else b''
    vchIn = prefix + secret + suffix
    base58_wif = EncodeBase58Check(vchIn)
    if internal_use:
        return base58_wif
    else:
        return '{}:{}'.format(txin_type, base58_wif)


# def deserialize_privkey(key: str, coin: CoinNetwork) -> Tuple[str, bytes, bool]:
#     if is_minikey(key):
#         return 'p2pkh', minikey_to_private_key(key), False
#
#     txin_type = None
#     if ':' in key:
#         txin_type, key = key.split(sep=':', maxsplit=1)
#         if txin_type not in WIF_SCRIPT_TYPES:
#             raise BitcoinException('unknown script type: {}'.format(txin_type))
#     try:
#         vch = DecodeBase58Check(key)
#     except Exception as e:
#         neutered_privkey = str(key)[:3] + '..' + str(key)[-2:]
#         raise BaseDecodeError(f"cannot deserialize privkey {neutered_privkey}") from e
#
#     if txin_type is None:
#         # keys exported in version 3.0.x encoded script type in first byte
#         prefix_value = vch[0] - coin.WIF_PREFIX
#         try:
#             txin_type = WIF_SCRIPT_TYPES_INV[prefix_value]
#         except KeyError as e:
#             raise BitcoinException('invalid prefix ({}) for WIF key (1)'.format(vch[0])) from None
#     else:
#         # all other keys must have a fixed first byte
#         if vch[0] != coin.WIF_PREFIX:
#             raise BitcoinException('invalid prefix ({}) for WIF key (2)'.format(vch[0]))
#
#     if len(vch) not in [33, 34]:
#         raise BitcoinException('invalid vch len for WIF key: {}'.format(len(vch)))
#     compressed = False
#     if len(vch) == 34:
#         if vch[33] == 0x01:
#             compressed = True
#         else:
#             raise BitcoinException(f'invalid WIF key. length suggests compressed pubkey, '
#                                    f'but last byte is {vch[33]} != 0x01')
#
#     if is_segwit_script_type(txin_type) and not compressed:
#         raise BitcoinException('only compressed public keys can be used in segwit scripts')
#
#     secret_bytes = vch[1:33]
#     # we accept secrets outside curve range; cast into range here:
#     secret_bytes = ecc.ECPrivkey.normalize_secret_bytes(secret_bytes)
#     return txin_type, secret_bytes, compressed
#
#
# def address_to_scripthash(addr: str, net: CoinNetwork = None) -> str:
#     script = address_to_script(addr, net=net)
#     return script_to_scripthash(script)


async def get_transaction(tx_hash: str, coin: CoinNetwork) -> str:
    if not is_hash256_str(tx_hash):
        raise Exception(f"{repr(tx_hash)} is not a txid")
    raw = await coin.electrum_call(ElectrumX.blockchain_transaction_get, [tx_hash])
    # validate response
    if not is_hex_str(raw):
        raise RequestCorrupted(f"received garbage (non-hex) as tx data (txid {tx_hash}): {raw!r}")
    tx = Transaction(raw, coin.TX_VERSION)
    try:
        tx.deserialize()  # see if raises
    except Exception as e:
        raise RequestCorrupted(f"cannot deserialize received transaction (txid {tx_hash})") from e
    if tx.txid() != tx_hash:
        raise RequestCorrupted(f"received tx does not match expected txid {tx_hash} (got {tx.txid()})")
    return raw


async def _append_utxos_to_inputs(*,
                                  inputs: List[PartialTxInput],
                                  net: CoinNetwork,
                                  pubkey: str,
                                  txin_type: str,
                                  imax: int) -> None:
    with NetworkLock(net):
        if txin_type in ('p2pkh', 'p2wpkh', 'p2wpkh-p2sh'):
            address = pubkey_to_address(txin_type, pubkey)
            scripthash = address_to_scripthash(address)
        elif txin_type == 'p2pk':
            script = public_key_to_p2pk_script(pubkey)
            scripthash = script_to_scripthash(script)
        else:
            raise Exception(f'unexpected txin_type to sweep: {txin_type}')

    async def append_single_utxo(item):
        prev_tx_raw = await get_transaction(item['tx_hash'], net)
        prev_tx = Transaction(prev_tx_raw)
        prev_txout = prev_tx.outputs()[item['tx_pos']]
        if scripthash != script_to_scripthash(prev_txout.scriptpubkey.hex()):
            raise Exception('scripthash mismatch when sweeping')
        prevout_str = item['tx_hash'] + ':%d' % item['tx_pos']
        prevout = TxOutpoint.from_str(prevout_str)
        txin = PartialTxInput(prevout=prevout)
        txin.utxo = prev_tx
        txin.block_height = int(item['height'])
        txin.script_type = txin_type
        txin.pubkeys = [bytes.fromhex(pubkey)]

        # # BCH SPECIFIC
        # txin.prevout_n = item['tx_pos']
        # txin.prevout_hash = item['tx_hash']
        # txin.x_pubkeys = [bfh(pubkey)]
        # txin.signatures = [None]

        txin.num_sig = 1
        if txin_type == 'p2wpkh-p2sh':
            txin.redeem_script = bytes.fromhex(p2wpkh_nested_script(pubkey))
        inputs.append(txin)

    u = await listunspent_for_scripthash(scripthash, net)
    async with TaskGroup() as group:
        for item in u:
            if len(inputs) >= imax:
                break
            await group.spawn(append_single_utxo(item))


async def listunspent_for_scripthash(sh: str, net: CoinNetwork) -> List[dict]:
    if not is_hash256_str(sh):
        raise Exception(f"{repr(sh)} is not a scripthash")
    # do request

    res = await net.electrum_call(ElectrumX.blockchain_scripthash_listunspent, [sh])
    # check response
    assert_list_or_tuple(res)
    for utxo_item in res:
        assert_dict_contains_field(utxo_item, field_name='tx_pos')
        assert_dict_contains_field(utxo_item, field_name='value')
        assert_dict_contains_field(utxo_item, field_name='tx_hash')
        assert_dict_contains_field(utxo_item, field_name='height')
        assert_non_negative_integer(utxo_item['tx_pos'])
        assert_non_negative_integer(utxo_item['value'])
        assert_non_negative_integer(utxo_item['height'])
        assert_hash256_str(utxo_item['tx_hash'])
    return res


async def dust_threshold(coin: CoinNetwork) -> int:
    """Returns the dust limit in satoshis."""
    # Change <= dust threshold is added to the tx fee
    dust_lim = 182 * 3 * await coin.relay_fee  # in msat
    # convert to sat, but round up:
    return (dust_lim // 1000) + (dust_lim % 1000 > 0)


async def sweep_preparations(privkeys, net: CoinNetwork, imax=100):
    async def find_utxos_for_privkey(txin_type, privkey, compressed):
        pubkey = ecc.ECPrivkey(privkey).get_public_key_hex(compressed=compressed)
        await _append_utxos_to_inputs(
            inputs=inputs,
            net=net,
            pubkey=pubkey,
            txin_type=txin_type,
            imax=imax)
        keypairs[pubkey] = privkey, compressed

    inputs = []  # type: List[PartialTxInput]
    keypairs = {}

    with NetworkLock(net):
        deserialized = [(deserialize_privkey(sec), sec) for sec in privkeys]

    async with TaskGroup() as group:
        for dat, sec in deserialized:
            txin_type, privkey, compressed = dat
            await group.spawn(find_utxos_for_privkey(txin_type, privkey, compressed))
            # do other lookups to increase support coverage
            if is_minikey(sec):
                # minikeys don't have a compressed byte
                # we lookup both compressed and uncompressed pubkeys
                await group.spawn(find_utxos_for_privkey(txin_type, privkey, not compressed))
            elif txin_type == 'p2pkh':
                # WIF serialization does not distinguish p2pkh and p2pk
                # we also search for pay-to-pubkey outputs
                await group.spawn(find_utxos_for_privkey('p2pk', privkey, compressed))
    if not inputs:
        raise ValueError('No inputs found.')
    return inputs, keypairs


async def sweep(
        privkeys,
        *,
        net: CoinNetwork,
        to_address: str,
        fee: int = None,
        imax=100,
        locktime=None,
        tx_version=None
) -> Tuple[PartialTransaction, dict]:
    inputs, keypairs = await sweep_preparations(privkeys, net, imax)
    total = sum(txin.value_sats() for txin in inputs)

    if tx_version is None:
        tx_version = net.TX_VERSION

    if fee is None:
        outputs = [PartialTxOutput(scriptpubkey=bytes.fromhex(net.address_to_script(to_address)), value=total)]
        tx = PartialTransaction.from_io(inputs, outputs, version=tx_version)
        fee_estimate = await net.current_feerate
        # Using static value shipped with electrum
        with NetworkLock(net):
            fee = round(quantize_feerate(fee_estimate) * tx.estimated_size(net))
    if total - fee < 0:
        raise Exception('Not enough funds on address.' + '\nTotal: %d satoshis\nFee: %d' % (total, fee))

    dust_thresh = await dust_threshold(net)
    if total - fee < dust_thresh:
        raise Exception('Not enough funds on address.' + '\nTotal: %d satoshis\n'
                                                         'Fee: %d\nDust Threshold: %d' % (total, fee, dust_thresh))

    if locktime is None:
        locktime = 0  # Set to zero, this is normally determined by the network object but is really optional

    outputs = [PartialTxOutput(scriptpubkey=bytes.fromhex(net.address_to_script(to_address)), value=total - fee)]
    tx = PartialTransaction.from_io(inputs, outputs, locktime=locktime, version=tx_version)
    return tx, keypairs
