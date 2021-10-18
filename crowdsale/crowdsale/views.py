from rest_framework.decorators import api_view
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from .settings import config
from web3 import Web3
from eth_account import Account, messages
from .models import UsdRate, Investor
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.core.validators import validate_email


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

    contract = config.crowdsale_contract

    current_price = contract.functions.price().call() * 10 ** 9
    usd_rate = UsdRate.objects.get(symbol=token.cryptocompare_symbol)
    usd_amount_to_pay = amount_to_pay / usd_rate.value
    decimals = 10 ** (config.token_decimals - token.decimals)
    amount_to_receive = int(usd_amount_to_pay / current_price * decimals)
    if usd_amount_to_pay > 10000000:
        amount_to_receive = amount_to_receive * 1.04
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
    operation_description='Price',
    responses={
        200: openapi.Response(
            description='Token price',
            schema=openapi.Schema(
                type=openapi.TYPE_STRING,
            )
        )}
)
@api_view(http_method_names=['GET'])
def stage_view(request):
    contract = config.carbonless_contract

    current_price_usd = contract.functions.price.call()

    return Response({
        'current_price_usd': current_price_usd,
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
    method='POST',
    operation_description='Whitelist view',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'address': openapi.Schema(type=openapi.TYPE_STRING),
            'email': openapi.Schema(type=openapi.TYPE_STRING),
        },
        required=['address', 'email']
    ),
    responses={
        200: openapi.Response(
            description='Whitelist success reponse',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(type=openapi.TYPE_STRING),
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
def whitelist_view(request):
    data = request.data
    address = data['address']
    email = data['email']

    try:
        validate_email(email)
    except ValidationError:
        return Response({'detail': 'INVALID_EMAIL'}, status=400)

    try:
        address = Web3.toChecksumAddress(address)
    except ValueError:
        return Response({'detail': 'INVALID_ADDRESS'}, status=400)

    try:
        Investor(address=address, email=email).save()
    except IntegrityError:
        return Response({'detail': 'ALREADY_REGISTERED'}, status=400)

    return Response({'detail': 'OK'})


@swagger_auto_schema(
    method='GET',
    operation_description='Is whitelisted view',
    responses={
        200: openapi.Response(
            description='Is address whitelisted',
            schema=openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
            )
        ),
        400: openapi.Response(
            description='Invalid address response',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(type=openapi.TYPE_STRING),
                },
            )
        )
    }
)
@api_view(http_method_names=['GET'])
def is_whitelisted_view(request, address):

    try:
        address = Web3.toChecksumAddress(address)
    except ValueError:
        return Response({'detail': 'INVALID_ADDRESS'}, status=400)

    is_whitelisted = Investor.objects.filter(address=address).exists()
    return Response(is_whitelisted)
