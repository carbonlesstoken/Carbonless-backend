from apscheduler.schedulers.background import BlockingScheduler
from django.core.management.base import BaseCommand
<<<<<<< HEAD:crowdsale/crowdsale/management/commands/run_scheduler.py
from .tasks import update_rates
from .settings import config
=======
from transaction.tasks import update_rates
from crowdsale.crowdsale.settings import config
>>>>>>> c7e2de8bb0712cfa60916886f1dfb5782ec86796:crowdsale/transaction/management/commands/run_scheduler.py


class Command(BaseCommand):
    help = 'Run blocking scheduler to create periodical tasks'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Preparing scheduler'))
        scheduler = BlockingScheduler()
        scheduler.add_job(update_rates.send, 'interval', seconds=60 * config.rates_update_timeout_minutes)
        self.stdout.write(self.style.NOTICE('Start scheduler'))
        scheduler.start()
