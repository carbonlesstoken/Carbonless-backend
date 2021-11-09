from rest_framework.decorators import api_view
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from .settings import config
from web3 import Web3
from eth_account import Account, messages
from .models import UsdRate
from datetime import datetime, timedelta


@swagger_auto_schema(
    method='POST',
    operation_description='Signature view',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'token_address': openapi.Schema(type=openapi.TYPE_STRING),
            'amount_to_pay': openapi.Schema(type=openapi.TYPE_STRING),
        },
        required=['token_address', 'amount_to_pay']
    ),
    responses={
        200: openapi.Response(
            description='Signature response',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'token_address': openapi.Schema(type=openapi.TYPE_STRING),
                    'amount_to_pay': openapi.Schema(type=openapi.TYPE_STRING),
                    'amount_to_receive': openapi.Schema(type=openapi.TYPE_STRING),
                    'signature_expiration_timestamp': openapi.Schema(type=openapi.TYPE_STRING),
                    'signature': openapi.Schema(type=openapi.TYPE_STRING),
                },
            )
        ),
        400: openapi.Response(
            description='Invalid parameters response',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(type=openapi.TYPE_STRING),
                },
            )
        ),
    }
)
@api_view(http_method_names=['POST'])
def signature_view(request):
    data = request.data
    token_address = data['token_address']
    amount_to_pay = int(data['amount_to_pay'])

    try:
        token_address_checksum = Web3.toChecksumAddress(token_address)
        token = config.get_token_by_address(token_address_checksum)
    except ValueError:
        return Response({'detail': 'INVALID_TOKEN_ADDRESS'}, status=400)

    contract = config.carbonsale_contract
    print('contract: ', contract, flush=True)
    current_price = contract.functions.price().call() * 10 ** 9
    print('current_price: ', current_price, flush=True)
    usd_rate = UsdRate.objects.get(symbol=token.cryptocompare_symbol)
    usd_amount_to_pay = amount_to_pay / usd_rate.value
    print('usd_amount_to_pay: ', usd_amount_to_pay, flush=True)
    decimals = 10 ** (config.token_decimals - token.decimals)
    print('decimals: ', decimals, flush=True)
    amount_to_receive = int(usd_amount_to_pay / (current_price * decimals))
    print('first_amount_to_receive: ', amount_to_receive, flush=True)
    if amount_to_receive > 10000000 * 10 ** 9:
        amount_to_receive = amount_to_receive * 1.04
    print('amount_to_receive: ', amount_to_receive, flush=True)
    amount_to_receive = int(amount_to_receive)
    signature_expires_at = datetime.now() + timedelta(minutes=config.signature_expiration_timeout_minutes)
    signature_expiration_timestamp = int(signature_expires_at.timestamp())
    print([token_address_checksum, amount_to_pay, amount_to_receive, signature_expiration_timestamp])
    keccak_hex = Web3.solidityKeccak(
        ['address', 'uint256', 'uint256', 'uint256'],
        [token_address_checksum, amount_to_pay, amount_to_receive, signature_expiration_timestamp]
    ).hex()

    message_to_sign = messages.encode_defunct(hexstr=keccak_hex)
    signature = Account.sign_message(message_to_sign, private_key=config.private_key)

    return Response({
        'token_address': token_address_checksum,
        'amount_to_pay': str(amount_to_pay),
        'amount_to_receive': str(amount_to_receive),
        'signature_expiration_timestamp': str(signature_expiration_timestamp),
        'signature': signature.signature.hex()
    })


@swagger_auto_schema(
    method='GET',
    operation_description='Tokens view',
    responses={
        200: openapi.Response(
            description='Tokens info response',
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'symbol': openapi.Schema(type=openapi.TYPE_STRING),
                        'address': openapi.Schema(type=openapi.TYPE_STRING),
                        'decimals': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'price': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                )
            )
        ),
    }
)
@api_view(http_method_names=['GET'])
def tokens_view(request):
    response = []
    for token in config.tokens:
        try:
            price = UsdRate.objects.get(symbol=token.cryptocompare_symbol).value
        except UsdRate.DoesNotExist:
            price = None

        token_serialized = {
            'symbol': token.symbol,
            'address': token.address,
            'decimals': token.decimals,
            'price': '{:.2f}'.format(1 / price),
        }
        response.append(token_serialized)

    return Response(response)


@swagger_auto_schema(
    method='GET',
    operation_description='Token address',
    responses={
        200: openapi.Response(
            description='Token address',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'contract address': openapi.Schema(type=openapi.TYPE_STRING),
                    'token address': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )}
)
@api_view(http_method_names=['GET'])
def address_view(request):
    contract = config.carbonsale_contract_address
    address = config.address
    return Response({
        'contract address': contract,
        'token address': address
    })
