import unittest

from mnemonic import Mnemonic

from modules.coins import ALL_COINS
from modules.electrum_mods.tux_mods import NetworkLock, serialize_privkey, BIP32Node

TEST_MNEMONIC = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
TEST_PASSPHRASE = "TREZOR"

RECIPIENT_ADDRESSES = {
    "BTC": "bc1qfxn2yv9834367vesdc7ah9prj9nrf67g806jup",
    "BCH": "bitcoincash:qpy6dg3s57xk8tenxphrmku5ywgkvd8teq69qw2xxy",
    "DASH": "XhQGnACeUSotpYPvcQk8ZUwo8onE6eBatn",
    "LTC": "ltc1qfxn2yv9834367vesdc7ah9prj9nrf67grnqky3",
    "tBTC": "tb1qfxn2yv9834367vesdc7ah9prj9nrf67gdfpp8j",
    "tBCH": "bchtest:qpy6dg3s57xk8tenxphrmku5ywgkvd8teq7hyfg3pc",
    "tDASH": "yT2so7H5uzTyAHKUBG4XbWN9R6GbcTvYEt",
    "tLTC": "tltc1qfxn2yv9834367vesdc7ah9prj9nrf67g5prlhm"
}


class TestSweep(unittest.TestCase):

    def test_seed_generation(self):
        mnemo = Mnemonic("english")
        seed = mnemo.to_seed(TEST_MNEMONIC, passphrase=TEST_PASSPHRASE)
        self.assertEqual(seed.hex(),
                         "c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e53495531f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04")

        node = BIP32Node.from_rootseed(seed, xtype='standard')
        self.assertEqual(node.to_xprv(net=ALL_COINS['BTC']),
                         "xprv9s21ZrQH143K3h3fDYiay8mocZ3afhfULfb5GX8kCBdno77K4HiA15Tg23wpbeF1pLfs1c5SPmYHrEpTuuRhxMwvKDwqdKiGJS9XFKzUsAF")

        root_node = node.subkey_at_private_derivation(f"1h/1h/1h")

        for network in ALL_COINS.values():
            recipient_address = network.make_address(root_node, account=1, index=1)
            self.assertEqual(recipient_address, RECIPIENT_ADDRESSES[network.symbol])

            with NetworkLock(network):
                self.assertEqual(network.make_address(root_node, account=1, index=1), recipient_address)

                private_nodes = [root_node.subkey_at_private_derivation(f"/0/{x}") for x in range(5)]
                for x in private_nodes:
                    serialize_privkey(x.eckey.get_secret_bytes(), True,
                                      network.address_format, net=network)


