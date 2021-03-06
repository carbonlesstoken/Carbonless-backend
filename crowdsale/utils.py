from dataclasses import dataclass, field
from typing import List, Optional
from web3 import Web3, HTTPProvider, contract
from web3.types import ChecksumAddress
from web3.middleware import geth_poa_middleware
import logging


@dataclass
class Token:
    address: str
    cryptocompare_symbol: str
    symbol: str
    decimals: int


@dataclass
class Config:
    django_secret_key: str
    django_static_url: str
    django_allowed_hosts: List[str]
    carbonsale_contract_address: str
    carbonsale_contract_abi: str
    address: str
    token_decimals: int
    private_key: str
    cryptocompare_api_url: str
    node: str
    signature_expiration_timeout_minutes: int
    rates_update_timeout_minutes: int
    tokens: List[Token]
    debug: Optional[bool] = False
    carbonsale_contract: contract = field(init=False, default=None)
    w3: Web3 = field(init=False, default=None)

    def __post_init__(self):
        self.w3 = Web3(HTTPProvider(self.node))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        carbonsale_address_checksum = Web3.toChecksumAddress(self.carbonsale_contract_address)
        self.carbonsale_contract = self.w3.eth.contract(
            address=carbonsale_address_checksum,
            abi=self.carbonsale_contract_abi
        )
        print(self.carbonsale_contract, flush=True)

    def get_token_by_address(self, address: ChecksumAddress):
        try:
            return [token for token in self.tokens if token.address == address][0]
        except IndexError:
            logging.error(f'Cannot find token with address {address}')
            raise ValueError(f'Cannot find token with address {address}')
