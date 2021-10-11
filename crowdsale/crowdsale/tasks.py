import dramatiq
import requests
<<<<<<< HEAD:crowdsale/crowdsale/tasks.py
from .settings import config
=======
>>>>>>> c7e2de8bb0712cfa60916886f1dfb5782ec86796:crowdsale/transaction/tasks.py
from .models import UsdRate


@dramatiq.actor(max_retries=0)
def update_rates() -> None:
    try:
        from crowdsale.settings import config
    except:
        print('error in task')
    payload = {
        'fsym': 'USD',
        'tsyms': [token.cryptocompare_symbol for token in config.tokens],
    }
    url = config.cryptocompare_api_url + '/data/price'
    response = requests.get(url, params=payload)
    print(response.json())
    if response.status_code != 200:
        raise Exception(f'Cannot get USD rates')

    data = response.json()
    for symbol, rate in data.items():
        print('new rate', symbol, rate)
        try:
            rate_obj = UsdRate.objects.get(symbol=symbol)
        except UsdRate.DoesNotExist:
            rate_obj = UsdRate(symbol=symbol)

        rate_obj.value = rate
        rate_obj.save()
