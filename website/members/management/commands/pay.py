import datetime
import decimal

from django.core.management.base import BaseCommand, CommandError

from members import logic
from members.models import Person, PaymentStrategy, Organization

PLATFORMS = {
    'todopago': PaymentStrategy.TODO_PAGO,
    'transfer': PaymentStrategy.TRANSFER,
}


class Command(BaseCommand):
    help = "Helper to create payments"

    def add_arguments(self, parser):
        parser.add_argument('--first-month', type=str, nargs='?')
        parser.add_argument('dni-cuit', type=str)
        parser.add_argument('date', type=str)
        parser.add_argument('platform', type=str)
        parser.add_argument('amount', type=str)

    def handle(self, *args, **options):
        if options['dni-cuit'] is None:
            raise CommandError('You must specify the DNI (person) or CUIT (organization).')

        # process the first month indication, if there
        first_unpaid = options.get('first_month')
        if first_unpaid is not None:
            if len(first_unpaid) != 6 or not first_unpaid.isdigit():
                raise CommandError("The first-month indication must be of format YYYYMM")
            first_unpaid = int(first_unpaid[:4]), int(first_unpaid[4:])

        try:
            person = Person.objects.get(document_number=options['dni-cuit'])
            member = person.membership
        except Person.DoesNotExist:
            print("============= not a person! organization?")
            try:
                organiz = Organization.objects.get(document_number=options['dni-cuit'])
                member = organiz.membership
            except Organization.DoesNotExist:
                print("============= not an organization either!")
                print("============= FAILED")
                return

        print("======= Member:", member)

        timestamp = datetime.datetime.strptime(options['date'], "%Y-%m-%d")
        print("======= Timestamp:", timestamp)

        amount = decimal.Decimal(options['amount'])
        print("======= Amount:", amount)

        platform = PLATFORMS[options['platform']]
        print("======= Platform:", platform)

        strategy, _ = PaymentStrategy.objects.get_or_create(
            platform=platform, id_in_platform='', patron=member.patron)
        print("======= Strategy:", strategy)

        logic.create_payment(member, timestamp, amount, strategy, first_unpaid=first_unpaid)
        print("======= Done")
