"""
Setup inicial do banco de produção.
Cria superusuários, carrega dados geográficos e popula o CRM.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Setup completo: usuários + dados geográficos + população do CRM"

    def handle(self, *args, **options):
        from apps.accounts.models import User

        # Superusuários
        self.stdout.write("==> Criando usuários...")
        for username, password, first, last in [
            ("peterson", "peterson5544", "Peterson", "Vivan"),
            ("gefferson", "gefferson5544", "Gefferson", "Vivan"),
        ]:
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(
                    username=username,
                    email="",
                    password=password,
                    role="admin",
                    first_name=first,
                    last_name=last,
                )
                self.stdout.write(f"  Criado: {username}")
            else:
                self.stdout.write(f"  Já existe: {username}")

        # Dados geográficos
        self.stdout.write("==> Carregando regiões e macro-regiões...")
        call_command("load_initial_data")

        self.stdout.write("==> Carregando cidades de SC...")
        call_command("load_sc_cities")

        # Popular CRM
        self.stdout.write("==> Populando CRM com dados de teste...")
        call_command("populate_crm")

        self.stdout.write(self.style.SUCCESS("\nSetup concluído! Acesse com peterson/peterson5544 ou gefferson/gefferson5544"))
