"""
Management command para popular o CRM com dados realistas de teste.
Simula o funcionamento completo do sistema com contatos, demandas, roteiros,
eventos, empresas, interações, etc.
"""
import random
from datetime import date, datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.campaigns.models import Campaign, Content, Itinerary, ItineraryStop, Task
from apps.communications.models import MessageCampaign, MessageTemplate, WhatsAppGroup
from apps.contacts.models import CompanyPartner, Contact, Interaction, Tag
from apps.events.models import Event
from apps.fundraising.models import Donation, Expense
from apps.geography.models import City, Neighborhood, Region


class Command(BaseCommand):
    help = "Popula o CRM com dados realistas de teste"

    def handle(self, *args, **options):
        self.stdout.write("Iniciando população do CRM...")

        self.create_users()
        self.create_tags()
        self.create_contacts()
        self.create_companies()
        self.create_interactions()
        self.create_campaigns_and_tasks()
        self.create_itineraries()
        self.create_events()
        self.create_whatsapp_groups()
        self.create_message_templates()
        self.create_donations_expenses()

        self.stdout.write(self.style.SUCCESS("CRM populado com sucesso!"))
        self.print_summary()

    def print_summary(self):
        self.stdout.write("\n--- RESUMO ---")
        self.stdout.write(f"Usuários: {User.objects.count()}")
        self.stdout.write(f"Contatos: {Contact.objects.count()}")
        self.stdout.write(f"Empresas: {CompanyPartner.objects.count()}")
        self.stdout.write(f"Interações: {Interaction.objects.count()}")
        self.stdout.write(f"Campanhas: {Campaign.objects.count()}")
        self.stdout.write(f"Demandas: {Task.objects.count()}")
        self.stdout.write(f"Roteiros: {Itinerary.objects.count()}")
        self.stdout.write(f"Paradas: {ItineraryStop.objects.count()}")
        self.stdout.write(f"Eventos: {Event.objects.count()}")
        self.stdout.write(f"Grupos WhatsApp: {WhatsAppGroup.objects.count()}")
        self.stdout.write(f"Doações: {Donation.objects.count()}")
        self.stdout.write(f"Despesas: {Expense.objects.count()}")

    # ── Helpers ──────────────────────────────────────────────────────
    def random_phone(self):
        ddd = random.choice(["47", "48", "49"])
        return f"({ddd}) 9{random.randint(8000,9999)}-{random.randint(1000,9999)}"

    def random_cpf(self):
        n = [random.randint(0, 9) for _ in range(9)]
        for _ in range(2):
            val = sum((len(n) + 1 - i) * v for i, v in enumerate(n)) % 11
            n.append(0 if val < 2 else 11 - val)
        s = ''.join(str(x) for x in n)
        return f"{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}"

    def random_date_range(self, start_days_ago, end_days_ago=0):
        start = date.today() - timedelta(days=start_days_ago)
        end = date.today() - timedelta(days=end_days_ago)
        delta = (end - start).days
        if delta <= 0:
            return start
        return start + timedelta(days=random.randint(0, delta))

    def get_random_cities(self, n=1, region=None):
        qs = City.objects.all()
        if region:
            qs = qs.filter(region=region)
        ids = list(qs.values_list("id", flat=True))
        return City.objects.filter(id__in=random.sample(ids, min(n, len(ids))))

    # ── Users ────────────────────────────────────────────────────────
    def create_users(self):
        self.stdout.write("Criando usuários...")
        users_data = [
            ("coord_estadual", "Ricardo Sorgatto", "coordinator_state", None, None),
            ("coord_oeste", "Marcos Oliveira", "coordinator_region", "AMOSC", None),
            ("coord_serra", "Fernanda Lopes", "coordinator_region", "AMURES", None),
            ("coord_norte", "Carlos Mendes", "coordinator_region", "AMPLANORTE", None),
            ("coord_vale", "Ana Paula Kraus", "coordinator_region", "AMVE", None),
            ("coord_sul", "Roberto Nascimento", "coordinator_region", "AMREC", None),
            ("coord_litoral", "Juliana Costa", "coordinator_region", "GRANFPOLIS", None),
            ("coord_chapeco", "Pedro Zanella", "coordinator_city", "AMOSC", "Chapecó"),
            ("coord_floripa", "Marina Silva", "coordinator_city", "GRANFPOLIS", "Florianópolis"),
            ("coord_joinville", "Lucas Ferreira", "coordinator_city", "AMUNESC", "Joinville"),
            ("coord_blumenau", "Camila Richter", "coordinator_city", "AMVE", "Blumenau"),
            ("coord_lages", "Rodrigo Almeida", "coordinator_city", "AMURES", "Lages"),
            ("coord_criciuma", "Patrícia Santos", "coordinator_city", "AMREC", "Criciúma"),
            ("voluntario1", "Diego Machado", "volunteer", None, None),
            ("voluntario2", "Isabela Freitas", "volunteer", None, None),
            ("voluntario3", "Thiago Correia", "volunteer", None, None),
            ("assessor1", "Renata Borges", "viewer", None, None),
        ]

        for username, name, role, region_name, city_name in users_data:
            if User.objects.filter(username=username).exists():
                continue
            first, last = name.split(" ", 1)
            region = Region.objects.filter(name=region_name).first() if region_name else None
            city = City.objects.filter(name=city_name).first() if city_name else None
            User.objects.create_user(
                username=username,
                password="teste123",
                first_name=first,
                last_name=last,
                role=role,
                region=region,
                city=city,
                phone=self.random_phone(),
                whatsapp=self.random_phone(),
                is_active_campaign=True,
            )

        self.users = list(User.objects.exclude(username="admin"))
        self.stdout.write(f"  {len(self.users)} usuários criados")

    # ── Tags ─────────────────────────────────────────────────────────
    def create_tags(self):
        self.stdout.write("Criando tags...")
        tags = [
            ("Agro", "#28a745"), ("Empresário", "#007bff"), ("Saúde", "#dc3545"),
            ("Educação", "#ffc107"), ("Segurança", "#6f42c1"), ("Infraestrutura", "#fd7e14"),
            ("Jovem", "#20c997"), ("Mulher", "#e83e8c"), ("Servidor Público", "#6c757d"),
            ("Igreja", "#17a2b8"), ("Sindicalista", "#343a40"), ("PL", "#0d6efd"),
            ("Aliado", "#198754"), ("Influenciador", "#6610f2"), ("Doador", "#d63384"),
            ("Interior", "#0dcaf0"), ("Capital", "#adb5bd"),
        ]
        self.tags = []
        for name, color in tags:
            tag, _ = Tag.objects.get_or_create(name=name, defaults={"color": color})
            self.tags.append(tag)

    # ── Contatos ─────────────────────────────────────────────────────
    def create_contacts(self):
        self.stdout.write("Criando contatos...")
        regions = list(Region.objects.all())

        # Nomes realistas
        first_names_m = [
            "João", "Pedro", "Carlos", "Marcos", "Roberto", "José", "Antonio",
            "Paulo", "Rafael", "Fernando", "Bruno", "André", "Luciano", "Diego",
            "Fábio", "Eduardo", "Márcio", "Leandro", "Sérgio", "Claudio",
            "Valdir", "Nelson", "Gilberto", "Ademir", "Reginaldo", "Vanderlei",
            "Airton", "Ivo", "Darci", "Neri", "Vilmar", "Alceu", "Olívio",
        ]
        first_names_f = [
            "Maria", "Ana", "Juliana", "Fernanda", "Patrícia", "Camila",
            "Sandra", "Adriana", "Cristiane", "Luciana", "Roseli", "Márcia",
            "Cláudia", "Simone", "Eliane", "Neiva", "Ivone", "Marilene",
            "Terezinha", "Solange", "Ivanete", "Noeli", "Salete", "Lurdes",
        ]
        last_names = [
            "Silva", "Oliveira", "Santos", "Souza", "Ferreira", "Rodrigues",
            "Costa", "Pereira", "Almeida", "Nascimento", "Machado", "Lopes",
            "Martins", "Ribeiro", "Zanella", "Bortolotto", "Paganini",
            "Tozzo", "Dal Magro", "Baldissera", "Zanchett", "Perin",
            "Benvegnú", "Lunardi", "Farias", "Corrêa", "Moraes",
            "Richter", "Kraus", "Zimmermann", "Schroeder", "Muller",
            "Cardoso", "Barbosa", "Cunha", "Melo", "Azevedo",
        ]
        professions = [
            "Agricultor", "Empresário", "Professor", "Médico", "Enfermeiro",
            "Advogado", "Engenheiro", "Comerciante", "Servidor Público",
            "Pecuarista", "Dentista", "Farmacêutico", "Contador",
            "Vereador", "Funcionário Público", "Pastor", "Padre",
            "Técnico Agrícola", "Veterinário", "Motorista", "Autônomo",
            "Aposentado", "Produtor Rural", "Industrial",
        ]
        parties = ["PL", "PP", "MDB", "PSD", "UNIÃO", "PSDB", "PDT", "REPUBLICANOS", ""]

        contacts_created = 0

        # ── Coordenadores Regionais (1 por região) ──
        for region in regions:
            cities = list(City.objects.filter(region=region))
            if not cities:
                continue
            city = random.choice(cities)
            is_female = random.random() < 0.3
            first = random.choice(first_names_f if is_female else first_names_m)
            last = random.choice(last_names)
            c = Contact.objects.create(
                full_name=f"{first} {last}",
                nickname=first,
                cpf=self.random_cpf(),
                phone=self.random_phone(),
                whatsapp=self.random_phone(),
                email=f"{first.lower().replace(' ','')}.{last.lower().replace(' ','')}@email.com",
                category="coordenador_regional",
                engagement_level=5,
                city=city,
                region=region,
                birth_date=self.random_date_range(365 * 60, 365 * 30),
                profession=random.choice(["Empresário", "Advogado", "Servidor Público", "Produtor Rural"]),
                party="PL",
                notes=f"Coordenador regional da {region.full_name}. Atuante desde 2020.",
                is_active=True,
            )
            c.tags.add(*random.sample(self.tags, min(3, len(self.tags))))
            contacts_created += 1

        # ── Coordenadores Municipais (2-4 por região) ──
        for region in regions:
            cities = list(City.objects.filter(region=region))
            n = min(random.randint(2, 4), len(cities))
            selected = random.sample(cities, n)
            for city in selected:
                is_female = random.random() < 0.35
                first = random.choice(first_names_f if is_female else first_names_m)
                last = random.choice(last_names)
                c = Contact.objects.create(
                    full_name=f"{first} {last}",
                    nickname=first,
                    phone=self.random_phone(),
                    whatsapp=self.random_phone(),
                    category="coordenador_municipal",
                    engagement_level=random.choice([4, 5]),
                    city=city,
                    region=region,
                    birth_date=self.random_date_range(365 * 55, 365 * 25),
                    profession=random.choice(professions),
                    party=random.choice(["PL", "PL", "PP", "UNIÃO"]),
                    is_active=True,
                )
                c.tags.add(*random.sample(self.tags, random.randint(1, 3)))
                contacts_created += 1

        # ── Lideranças Políticas (3-5 por região) ──
        for region in regions:
            cities = list(City.objects.filter(region=region))
            for _ in range(random.randint(3, 5)):
                city = random.choice(cities)
                is_female = random.random() < 0.3
                first = random.choice(first_names_f if is_female else first_names_m)
                last = random.choice(last_names)
                cat = random.choice(["lideranca", "vereador", "prefeito"])
                c = Contact.objects.create(
                    full_name=f"{first} {last}",
                    nickname=first,
                    phone=self.random_phone(),
                    whatsapp=self.random_phone(),
                    email=f"{first.lower()}.{last.lower().replace(' ','')}@politica.com" if random.random() > 0.4 else "",
                    category=cat,
                    engagement_level=random.choice([3, 4, 5]),
                    city=city,
                    region=region,
                    birth_date=self.random_date_range(365 * 65, 365 * 28),
                    profession="Vereador" if cat == "vereador" else ("Prefeito" if cat == "prefeito" else random.choice(professions)),
                    party=random.choice(parties),
                    notes=self._generate_leadership_notes(cat, city),
                    is_active=random.random() > 0.1,
                )
                c.tags.add(*random.sample(self.tags, random.randint(1, 4)))
                contacts_created += 1

        # ── Apoiadores (8-15 por região) ──
        for region in regions:
            cities = list(City.objects.filter(region=region))
            for _ in range(random.randint(8, 15)):
                city = random.choice(cities)
                is_female = random.random() < 0.45
                first = random.choice(first_names_f if is_female else first_names_m)
                last = random.choice(last_names)
                c = Contact.objects.create(
                    full_name=f"{first} {last}",
                    phone=self.random_phone(),
                    whatsapp=self.random_phone() if random.random() > 0.2 else "",
                    category="apoiador",
                    engagement_level=random.choice([2, 3, 3, 4]),
                    city=city,
                    region=region,
                    birth_date=self.random_date_range(365 * 70, 365 * 18),
                    profession=random.choice(professions),
                    party=random.choice(["PL", "", "", ""]),
                    is_active=True,
                )
                c.tags.add(*random.sample(self.tags, random.randint(0, 3)))
                contacts_created += 1

        # ── Eleitores e indecisos (5-10 por região) ──
        for region in regions:
            cities = list(City.objects.filter(region=region))
            for _ in range(random.randint(5, 10)):
                city = random.choice(cities)
                is_female = random.random() < 0.5
                first = random.choice(first_names_f if is_female else first_names_m)
                last = random.choice(last_names)
                cat = random.choice(["eleitor", "eleitor", "indeciso"])
                c = Contact.objects.create(
                    full_name=f"{first} {last}",
                    phone=self.random_phone(),
                    category=cat,
                    engagement_level=random.choice([1, 1, 2]),
                    city=city,
                    region=region,
                    is_active=True,
                )
                contacts_created += 1

        # ── Oposição (1-2 por região, para ter no sistema) ──
        for region in regions:
            cities = list(City.objects.filter(region=region))
            for _ in range(random.randint(1, 2)):
                city = random.choice(cities)
                is_female = random.random() < 0.4
                first = random.choice(first_names_f if is_female else first_names_m)
                last = random.choice(last_names)
                Contact.objects.create(
                    full_name=f"{first} {last}",
                    phone=self.random_phone(),
                    category="oposicao",
                    engagement_level=1,
                    city=city,
                    region=region,
                    party=random.choice(["PT", "PSOL", "PCdoB", "REDE"]),
                    notes="Identificado como oposição. Monitorar posicionamento.",
                    is_active=True,
                )
                contacts_created += 1

        # ── Deputados (estaduais e federais aliados) ──
        deputados = [
            ("Dep. Jorge Kurtz", "PL", "AMVE"),
            ("Dep. Ricardo Alba", "PL", "GRANFPOLIS"),
            ("Dep. Sergio Motta", "PP", "AMOSC"),
            ("Dep. Mauro de Nadal", "MDB", "AMREC"),
            ("Dep. Celso Maldaner", "MDB", "AMAUC"),
            ("Dep. Valdir Cobalchini", "MDB", "AMEOSC"),
        ]
        for name, party, reg_name in deputados:
            region = Region.objects.filter(name=reg_name).first()
            if not region:
                continue
            city = City.objects.filter(region=region).first()
            Contact.objects.create(
                full_name=name,
                phone=self.random_phone(),
                whatsapp=self.random_phone(),
                category="deputado",
                engagement_level=random.choice([3, 4]),
                city=city,
                region=region,
                party=party,
                profession="Deputado",
                notes=f"Deputado aliado. Partido: {party}.",
                is_active=True,
            )
            contacts_created += 1

        self.contacts = list(Contact.objects.all())
        self.stdout.write(f"  {contacts_created} contatos criados")

    def _generate_leadership_notes(self, cat, city):
        notes_options = {
            "lideranca": [
                f"Liderança comunitária forte em {city.name}. Boa articulação local.",
                f"Presidente do sindicato rural de {city.name}. Muito influente.",
                f"Líder religioso com grande alcance em {city.name}.",
                f"Ex-vereador de {city.name}. Mantém boa base eleitoral.",
            ],
            "vereador": [
                f"Vereador em exercício em {city.name}. Aliado confirmado.",
                f"Vereador de {city.name}. Em negociação de apoio.",
                f"Presidente da câmara de {city.name}. Articulador importante.",
            ],
            "prefeito": [
                f"Prefeito de {city.name}. Relação institucional.",
                f"Prefeito de {city.name}. Aliado do partido.",
            ],
        }
        return random.choice(notes_options.get(cat, ["Contato político."]))

    # ── Empresas ─────────────────────────────────────────────────────
    def create_companies(self):
        self.stdout.write("Criando empresas parceiras...")
        companies_data = [
            ("Agropecuária Zanella Ltda", "Agronegócio", "Chapecó", "Patrocínio e apoio logístico", 45),
            ("Cooperativa Aurora Alimentos", "Agroindústria", "Chapecó", "Apoio institucional", 5200),
            ("Metalúrgica Bortolotto", "Indústria", "Joaçaba", "Doação e divulgação", 120),
            ("Construtora Lunardi", "Construção Civil", "Concórdia", "Apoio financeiro", 85),
            ("Supermercados Paganini", "Comércio", "Xanxerê", "Ponto de encontro e divulgação", 200),
            ("Transportadora Perin", "Transporte", "Videira", "Logística de campanha", 65),
            ("Hospital São Lucas", "Saúde", "Lages", "Parceria institucional", 350),
            ("Vinícola Dal Magro", "Agroindústria", "Tangará", "Eventos e recepções", 30),
            ("Auto Peças Floripa", "Comércio", "Florianópolis", "Patrocínio de eventos", 25),
            ("Cerâmica Portobello", "Indústria", "Tijucas", "Apoio institucional", 1800),
            ("Havan S.A.", "Comércio", "Brusque", "Apoio logístico", 15000),
            ("Weg S.A.", "Indústria", "Jaraguá do Sul", "Relação institucional", 30000),
            ("BRF S.A.", "Agroindústria", "Chapecó", "Articulação com setor produtivo", 8000),
            ("Coop. Central Oeste Catarinense", "Agronegócio", "Chapecó", "Base de apoio rural", 3000),
            ("Farmácia São João", "Comércio", "Joinville", "Ponto de divulgação", 150),
            ("Olsen Indústria", "Indústria", "Palhoça", "Apoio institucional", 500),
            ("Celulose Irani", "Indústria", "Vargem Bonita", "Parceria rural e ambiental", 900),
            ("Coamo Agroindustrial", "Agronegócio", "Campo Erê", "Base do agro", 250),
            ("Koerich Imóveis", "Imobiliário", "Florianópolis", "Networking urbano", 60),
            ("Rede Angeloni", "Comércio", "Criciúma", "Articulação com comércio", 7000),
        ]

        contacts_by_city = {}
        for c in Contact.objects.filter(category__in=["coordenador_municipal", "coordenador_regional", "lideranca"]):
            if c.city:
                contacts_by_city.setdefault(c.city.name, []).append(c)

        for name, sector, city_name, partnership, employees in companies_data:
            city = City.objects.filter(name=city_name).first()
            contact_person = None
            if city_name in contacts_by_city and contacts_by_city[city_name]:
                contact_person = random.choice(contacts_by_city[city_name])

            CompanyPartner.objects.create(
                name=name,
                cnpj=f"{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}/0001-{random.randint(10,99)}",
                contact_person=contact_person,
                city=city,
                sector=sector,
                employees_count=employees,
                partnership_type=partnership,
                notes=f"Empresa do setor de {sector.lower()} em {city_name}. {partnership}.",
            )

        self.stdout.write(f"  {len(companies_data)} empresas criadas")

    # ── Interações ───────────────────────────────────────────────────
    def create_interactions(self):
        self.stdout.write("Criando interações...")
        users = list(User.objects.all())
        contacts = list(Contact.objects.filter(
            category__in=["coordenador_regional", "coordenador_municipal", "lideranca",
                          "apoiador", "vereador", "prefeito", "deputado"]
        ))
        types = ["phone_call", "whatsapp", "meeting", "event", "door_to_door", "referral"]
        outcomes = [
            "Confirmou apoio", "Vai pensar", "Pediu mais informações",
            "Indicou outros contatos", "Agendou reunião",
            "Confirmou presença no evento", "Sem interesse no momento",
            "Muito receptivo", "Demonstrou interesse", "Quer participar ativamente",
        ]
        next_actions = [
            "Ligar novamente em 1 semana", "Enviar material de campanha",
            "Agendar visita presencial", "Incluir no grupo de WhatsApp",
            "Convidar para próximo evento", "Enviar proposta de parceria",
            "", "",
        ]

        count = 0
        for contact in contacts:
            n_interactions = random.randint(1, 5)
            for _ in range(n_interactions):
                itype = random.choice(types)
                days_ago = random.randint(1, 90)
                Interaction.objects.create(
                    contact=contact,
                    interaction_type=itype,
                    description=self._generate_interaction_desc(itype, contact),
                    performed_by=random.choice(users),
                    outcome=random.choice(outcomes),
                    next_action=random.choice(next_actions),
                    next_action_date=date.today() + timedelta(days=random.randint(1, 30)) if random.random() > 0.4 else None,
                )
                count += 1

        self.stdout.write(f"  {count} interações criadas")

    def _generate_interaction_desc(self, itype, contact):
        descs = {
            "phone_call": [
                f"Ligação para {contact.full_name} sobre articulação na região.",
                f"Retorno de ligação. {contact.full_name} demonstrou interesse.",
                f"Ligação rápida para alinhar agenda da semana.",
            ],
            "whatsapp": [
                f"Mensagem via WhatsApp sobre próximo evento.",
                f"Troca de mensagens sobre demandas da região.",
                f"Enviado material de divulgação por WhatsApp.",
            ],
            "meeting": [
                f"Reunião presencial com {contact.full_name} na cidade.",
                f"Encontro informal em almoço para articulação.",
                f"Reunião de alinhamento com lideranças locais.",
            ],
            "event": [
                f"{contact.full_name} participou do evento comunitário.",
                f"Encontro no evento regional. Boa recepção.",
            ],
            "door_to_door": [
                f"Visita presencial na residência de {contact.full_name}.",
                f"Visita ao comércio/empresa. Conversa produtiva.",
            ],
            "referral": [
                f"{contact.full_name} indicou novos contatos na região.",
                f"Indicação recebida de {contact.full_name}.",
            ],
        }
        return random.choice(descs.get(itype, ["Interação registrada."]))

    # ── Campanhas e Demandas ─────────────────────────────────────────
    def create_campaigns_and_tasks(self):
        self.stdout.write("Criando campanhas e demandas...")
        users = list(User.objects.all())
        regions = list(Region.objects.all())

        # Campanha principal já existe (id=1), criar mais
        camp2, _ = Campaign.objects.get_or_create(
            name="Articulação Partidária 2026",
            defaults={
                "description": "Campanha de articulação com diretórios municipais e lideranças do partido.",
                "start_date": date(2026, 3, 1),
                "end_date": date(2026, 8, 31),
                "responsible": User.objects.filter(role="coordinator_state").first() or users[0],
                "status": "active",
                "goal_contacts": 500,
                "achieved_contacts": 187,
            },
        )
        camp2.target_regions.set(regions)

        camp3, _ = Campaign.objects.get_or_create(
            name="Captação de Apoiadores - Agro",
            defaults={
                "description": "Foco no setor agropecuário. Visitas a cooperativas e sindicatos rurais.",
                "start_date": date(2026, 4, 1),
                "end_date": date(2026, 7, 31),
                "responsible": User.objects.filter(role="coordinator_region").first() or users[0],
                "status": "active",
                "goal_contacts": 300,
                "achieved_contacts": 92,
            },
        )

        camp4, _ = Campaign.objects.get_or_create(
            name="Mobilização Jovem SC",
            defaults={
                "description": "Campanha para engajar eleitores jovens (18-30 anos) via redes sociais e eventos.",
                "start_date": date(2026, 5, 1),
                "end_date": date(2026, 9, 30),
                "responsible": User.objects.filter(username="voluntario1").first() or users[0],
                "status": "planned",
                "goal_contacts": 1000,
                "achieved_contacts": 0,
            },
        )

        camp_old, _ = Campaign.objects.get_or_create(
            name="Pré-campanha Oeste 2025",
            defaults={
                "description": "Articulação inicial no Oeste Catarinense. Concluída.",
                "start_date": date(2025, 8, 1),
                "end_date": date(2025, 12, 31),
                "responsible": users[0],
                "status": "completed",
                "goal_contacts": 200,
                "achieved_contacts": 178,
            },
        )

        campaigns = [Campaign.objects.get(id=1), camp2, camp3, camp4]

        # ── Demandas (muitas e variadas) ──
        today = date.today()
        tasks_data = [
            # VENCIDAS (overdue) - due_date no passado, não completadas
            ("Reunião com sindicato rural de Concórdia", "meeting", "planned", "high", -15, "AMAUC", "Concórdia", camp2),
            ("Articulação com vereadores de São Miguel do Oeste", "party_work", "articulating", "urgent", -10, "AMEOSC", "São Miguel do Oeste", camp2),
            ("Visita cooperativa Videira", "field_visit", "planned", "medium", -8, "AMARP", "Videira", camp3),
            ("Captação apoiadores Joaçaba", "recruitment", "articulating", "high", -5, "AMMOC", "Joaçaba", camp3),
            ("Reunião diretório PL Itajaí", "party_work", "scheduled", "urgent", -3, "AMFRI", "Itajaí", camp2),
            ("Evento com produtores rurais Campos Novos", "event", "planned", "medium", -12, "AMPLASC", "Campos Novos", camp3),
            ("Reunião prefeito Mafra", "meeting", "articulating", "high", -7, "AMPLANORTE", "Mafra", camp2),
            ("Visita aos comerciantes de Tubarão", "field_visit", "planned", "medium", -20, "AMUREL", "Tubarão", camp3),

            # EM ANDAMENTO (active, future due dates)
            ("Articulação lideranças Chapecó", "party_work", "articulating", "urgent", 3, "AMOSC", "Chapecó", camp2),
            ("Reunião com prefeito de Joinville", "meeting", "scheduled", "urgent", 5, "AMUNESC", "Joinville", camp2),
            ("Evento comunitário Blumenau", "event", "scheduled", "high", 7, "AMVE", "Blumenau", campaigns[0]),
            ("Visita campo Xanxerê interior", "field_visit", "articulating", "medium", 10, "AMAI", "Xanxerê", campaigns[0]),
            ("Captação empresários Jaraguá do Sul", "recruitment", "planned", "high", 12, "AMVALI", "Jaraguá do Sul", camp3),
            ("Comunicação digital - Serra", "communication", "executed", "medium", 8, "AMURES", "Lages", campaigns[0]),
            ("Mobilização Jovens Florianópolis", "recruitment", "articulating", "high", 15, "GRANFPOLIS", "Florianópolis", camp4),
            ("Reunião vereadores aliados Criciúma", "meeting", "scheduled", "high", 6, "AMREC", "Criciúma", camp2),
            ("Evento agro Maravilha", "event", "planned", "medium", 14, "AMEOSC", "Maravilha", camp3),
            ("Visita cooperativa Canoinhas", "field_visit", "planned", "medium", 18, "AMPLANORTE", "Canoinhas", camp3),
            ("Articulação prefeitos Alto Irani", "party_work", "articulating", "high", 9, "AMAI", "Xanxerê", camp2),
            ("Reunião sindicato trabalhadores São Bento", "meeting", "planned", "medium", 20, "AMUNESC", "São Bento do Sul", camp2),
            ("Captação apoiadores Brusque", "recruitment", "planned", "medium", 16, "AMVE", "Brusque", camp3),
            ("Evento comunitário Rio do Sul", "event", "planned", "medium", 22, "AMAVI", "Rio do Sul", campaigns[0]),
            ("Reunião câmara de Caçador", "meeting", "scheduled", "high", 4, "AMARP", "Caçador", camp2),

            # COMPLETADAS
            ("Reunião lideranças Chapecó - Abril", "meeting", "completed", "high", -30, "AMOSC", "Chapecó", camp2),
            ("Visita cooperativa Concórdia", "field_visit", "completed", "medium", -25, "AMAUC", "Concórdia", camp3),
            ("Evento agro Xanxerê", "event", "completed", "high", -20, "AMAI", "Xanxerê", camp3),
            ("Articulação diretório PL Lages", "party_work", "completed", "medium", -18, "AMURES", "Lages", camp2),
            ("Reunião com prefeito de Florianópolis", "meeting", "completed", "urgent", -35, "GRANFPOLIS", "Florianópolis", camp2),
            ("Captação apoiadores Oeste", "recruitment", "completed", "high", -22, "AMOSC", "Chapecó", camp3),
            ("Evento jovens Blumenau", "event", "completed", "medium", -28, "AMVE", "Blumenau", camp4),
            ("Reunião sindical Joinville", "meeting", "completed", "high", -15, "AMUNESC", "Joinville", camp2),
            ("Visita produtores Curitibanos", "field_visit", "completed", "low", -40, "AMURC", "Curitibanos", camp3),

            # MAIS DEMANDAS para regiões variadas
            ("Reunião diretório Araranguá", "party_work", "planned", "medium", 25, "AMESC", "Araranguá", camp2),
            ("Captação agricultores Ibirama", "recruitment", "planned", "low", 28, "AMAVI", "Ibirama", camp3),
            ("Evento comunitário Laguna", "event", "articulating", "medium", 11, "AMUREL", "Laguna", campaigns[0]),
            ("Reunião com lideranças Barra Velha", "meeting", "planned", "medium", 30, "AMVALI", "Barra Velha", camp2),
            ("Articulação prefeitos Planalto Serrano", "party_work", "articulating", "high", 13, "AMURES", "São Joaquim", camp2),
            ("Visita cooperativas Curitibanos", "field_visit", "planned", "medium", 19, "AMURC", "Curitibanos", camp3),
            ("Mobilização digital litoral sul", "communication", "planned", "low", 21, "AMESC", "Araranguá", camp4),
            ("Captação empresários Balneário Camboriú", "recruitment", "articulating", "high", 8, "AMFRI", "Balneário Camboriú", camp3),
        ]

        created_count = 0
        for title, ttype, phase, priority, due_offset, region_name, city_name, campaign in tasks_data:
            region = Region.objects.filter(name=region_name).first()
            city = City.objects.filter(name=city_name, region=region).first() if region else None
            if not city:
                city = City.objects.filter(name=city_name).first()

            due = today + timedelta(days=due_offset)
            completed_at = due + timedelta(days=random.randint(0, 3)) if phase == "completed" else None
            assigned = random.choice(users) if random.random() > 0.15 else None

            Task.objects.create(
                campaign=campaign,
                title=title,
                description=f"Demanda: {title}. Região {region_name}.",
                task_type=ttype,
                phase=phase,
                priority=priority,
                assigned_to=assigned,
                due_date=due,
                completed_at=completed_at,
                city=city,
                region=region,
                goal_description=f"Meta: concluir {title.lower()}" if random.random() > 0.5 else "",
                goal_achieved=random.randint(50, 100) if phase == "completed" else random.randint(0, 50),
            )
            created_count += 1

        self.stdout.write(f"  {Campaign.objects.count()} campanhas, {Task.objects.count()} demandas total")

    # ── Roteiros ─────────────────────────────────────────────────────
    def create_itineraries(self):
        self.stdout.write("Criando roteiros...")
        users = list(User.objects.all())
        today = date.today()

        itineraries_data = [
            # VENCIDOS (passados, não completados)
            ("Roteiro Meio Oeste - Abril", -35, -33, "planned", ["Joaçaba", "Herval d'Oeste", "Catanduvas"]),
            ("Roteiro Extremo Oeste - Abril", -28, -26, "confirmed", ["São Miguel do Oeste", "Maravilha", "Descanso", "Guaraciaba"]),
            ("Roteiro Planalto - Maio", -15, -13, "confirmed", ["Campos Novos", "Brunópolis"]),

            # COMPLETADOS
            ("Roteiro Oeste Chapecó - Concluído", -45, -42, "completed", ["Chapecó", "Pinhalzinho", "Saudades"]),
            ("Roteiro Serra - Concluído", -40, -38, "completed", ["Lages", "São Joaquim", "Bom Jardim da Serra"]),
            ("Roteiro Norte - Concluído", -30, -28, "completed", ["Joinville", "Jaraguá do Sul"]),
            ("Roteiro Capital - Concluído", -25, -25, "completed", ["Florianópolis", "Palhoça", "São José"]),

            # FUTUROS (planejados)
            ("Roteiro Litoral Sul", 5, 7, "planned", ["Criciúma", "Tubarão", "Laguna", "Araranguá"]),
            ("Roteiro Alto Vale", 10, 12, "planned", ["Rio do Sul", "Ibirama", "Presidente Getúlio"]),
            ("Roteiro Extremo Oeste Junho", 15, 18, "confirmed", ["São Miguel do Oeste", "Itapiranga", "São João do Oeste", "Mondaí"]),
            ("Roteiro Meio Oeste Junho", 20, 22, "planned", ["Joaçaba", "Videira", "Caçador", "Fraiburgo"]),
            ("Roteiro Serra Junho", 25, 27, "planned", ["Lages", "Correia Pinto", "Otacílio Costa"]),
            ("Roteiro Grande Florianópolis", 8, 9, "confirmed", ["Florianópolis", "São José", "Biguaçu"]),

            # EM ANDAMENTO
            ("Roteiro Vale Europeu - Atual", -1, 1, "in_progress", ["Blumenau", "Gaspar", "Indaial", "Timbó"]),
        ]

        for name, start_offset, end_offset, status, city_names in itineraries_data:
            start = today + timedelta(days=start_offset)
            end = today + timedelta(days=end_offset)
            responsible = random.choice(users)

            itin = Itinerary.objects.create(
                name=name,
                start_date=start,
                end_date=end,
                responsible=responsible,
                status=status,
                notes=f"Roteiro de visitas: {', '.join(city_names)}.",
            )

            # Associar regiões
            regions_set = set()
            for cn in city_names:
                city = City.objects.filter(name=cn).first()
                if city:
                    regions_set.add(city.region)
            itin.target_regions.set(list(regions_set))

            # Criar paradas
            for idx, city_name in enumerate(city_names):
                city = City.objects.filter(name=city_name).first()
                if not city:
                    continue

                stop_date = start + timedelta(days=min(idx, (end - start).days))
                # Vincular a uma demanda da mesma cidade se existir
                task = Task.objects.filter(city=city).first()

                ItineraryStop.objects.create(
                    itinerary=itin,
                    city=city,
                    task=task,
                    date=stop_date,
                    scheduled_time=datetime.strptime(
                        f"{random.randint(8,16)}:{random.choice(['00','30'])}", "%H:%M"
                    ).time(),
                    order=idx,
                    travel_minutes=random.randint(20, 120) if idx > 0 else 0,
                    is_overnight=idx == len(city_names) - 1 and len(city_names) > 2,
                    notes=f"Parada em {city_name}." if random.random() > 0.5 else "",
                )

        self.stdout.write(f"  {Itinerary.objects.count()} roteiros, {ItineraryStop.objects.count()} paradas total")

    # ── Eventos ──────────────────────────────────────────────────────
    def create_events(self):
        self.stdout.write("Criando eventos...")
        users = list(User.objects.all())
        today = timezone.now()
        contacts = list(Contact.objects.all())

        events_data = [
            # Passados
            ("Encontro de Lideranças Oeste", "meeting", -30, 3, "Chapecó", 80, 72),
            ("Carreata Concórdia", "carreata", -25, 2, "Concórdia", 200, 180),
            ("Reunião com Empresários Joinville", "meeting", -20, 2, "Joinville", 40, 35),
            ("Encontro Jovem Florianópolis", "community", -15, 3, "Florianópolis", 150, 120),
            ("Treinamento de Voluntários - Lages", "training", -12, 4, "Lages", 30, 28),
            ("Comício Blumenau", "rally", -8, 3, "Blumenau", 500, 430),
            ("Debate Comunitário Criciúma", "debate", -5, 2, "Criciúma", 100, 88),

            # Futuros
            ("Encontro Regional Xanxerê", "meeting", 5, 3, "Xanxerê", 60, 0),
            ("Carreata Rio do Sul", "carreata", 8, 2, "Rio do Sul", 150, 0),
            ("Evento Comunitário Tubarão", "community", 12, 4, "Tubarão", 100, 0),
            ("Reunião de Planejamento - Chapecó", "meeting", 3, 2, "Chapecó", 25, 0),
            ("Treinamento Coordenadores Regionais", "training", 15, 6, "Florianópolis", 40, 0),
            ("Encontro Agro Videira", "community", 18, 3, "Videira", 80, 0),
            ("Jantar de Arrecadação Florianópolis", "fundraiser", 20, 4, "Florianópolis", 120, 0),
            ("Porta a Porta Joinville Centro", "door_to_door", 7, 5, "Joinville", 30, 0),
            ("Comício Regional Chapecó", "rally", 25, 4, "Chapecó", 1000, 0),
        ]

        for title, etype, day_offset, hours, city_name, expected, actual in events_data:
            city = City.objects.filter(name=city_name).first()
            event_date = today + timedelta(days=day_offset)

            ev = Event.objects.create(
                title=title,
                event_type=etype,
                description=f"{title}. Local: {city_name}.",
                date=event_date,
                end_date=event_date + timedelta(hours=hours),
                city=city,
                region=city.region if city else None,
                expected_attendees=expected,
                actual_attendees=actual,
                organizer=random.choice(users),
                neighborhood_name=random.choice(["Centro", "Vila Nova", "São Cristóvão", ""]),
            )

            # Adicionar convidados/participantes
            city_contacts = [c for c in contacts if c.city and c.city.name == city_name]
            region_contacts = [c for c in contacts if c.region and city and c.region == city.region]
            pool = city_contacts or region_contacts[:20]

            if pool:
                invited = random.sample(pool, min(random.randint(5, 15), len(pool)))
                ev.contacts_invited.set(invited)
                if actual > 0:
                    attended = random.sample(invited, min(len(invited), int(len(invited) * 0.8)))
                    ev.contacts_attended.set(attended)

        self.stdout.write(f"  {Event.objects.count()} eventos criados")

    # ── WhatsApp Groups ──────────────────────────────────────────────
    def create_whatsapp_groups(self):
        self.stdout.write("Criando grupos de WhatsApp...")
        regions = list(Region.objects.all())
        coordinators = list(Contact.objects.filter(category__in=["coordenador_regional", "coordenador_municipal"]))

        # Grupo de coordenação por região
        for region in regions:
            admin = next((c for c in coordinators if c.region == region), None)
            WhatsAppGroup.objects.create(
                name=f"Coordenação {region.name}",
                group_type="coordination",
                region=region,
                member_count=random.randint(5, 25),
                admin_contact=admin,
                is_active=True,
            )

        # Grupos temáticos
        groups = [
            ("Apoiadores SC - Geral", "supporters", None, None, 180),
            ("Voluntários Campanha 2026", "volunteers", None, None, 85),
            ("Coordenadores Estaduais", "coordination", None, None, 25),
            ("Campanha Digital SC", "campaign", None, None, 45),
            ("Agro Aliados SC", "supporters", None, None, 120),
            ("Jovens pela Mudança SC", "campaign", None, None, 95),
        ]
        for name, gtype, city_name, region_name, members in groups:
            WhatsAppGroup.objects.create(
                name=name,
                group_type=gtype,
                member_count=members,
                is_active=True,
            )

        # Grupos por cidade principal
        main_cities = ["Chapecó", "Florianópolis", "Joinville", "Blumenau", "Lages", "Criciúma", "Jaraguá do Sul"]
        for city_name in main_cities:
            city = City.objects.filter(name=city_name).first()
            if city:
                WhatsAppGroup.objects.create(
                    name=f"Apoiadores {city_name}",
                    group_type="supporters",
                    city=city,
                    region=city.region,
                    member_count=random.randint(30, 100),
                    is_active=True,
                )

        self.stdout.write(f"  {WhatsAppGroup.objects.count()} grupos criados")

    # ── Templates de Mensagem ────────────────────────────────────────
    def create_message_templates(self):
        self.stdout.write("Criando templates de mensagem...")
        templates = [
            ("Convite para Evento", "whatsapp",
             "Olá {nome}! Você está convidado(a) para o evento {evento} no dia {data} em {cidade}. Contamos com sua presença! 🗳️"),
            ("Agradecimento Apoio", "whatsapp",
             "Olá {nome}! Agradecemos imensamente seu apoio à nossa campanha. Juntos vamos transformar Santa Catarina! 💪"),
            ("Lembrete Reunião", "whatsapp",
             "Olá {nome}, lembrando da nossa reunião amanhã ({data}) às {horario}. Confirmamos sua presença?"),
            ("Newsletter Semanal", "email",
             "Prezado(a) {nome},\n\nConfira as novidades da semana na campanha...\n\nAtenciosamente,\nEquipe de Campanha"),
            ("Pesquisa de Opinião", "whatsapp",
             "Olá {nome}! Gostaríamos de saber sua opinião sobre as prioridades para {cidade}. Pode responder uma breve pesquisa?"),
            ("Convite Voluntariado", "whatsapp",
             "Olá {nome}! Estamos buscando voluntários para a campanha em {cidade}. Gostaria de participar?"),
        ]

        for name, channel, content in templates:
            MessageTemplate.objects.get_or_create(
                name=name,
                defaults={
                    "content": content,
                    "channel": channel,
                    "variables": ["nome", "cidade", "data"],
                },
            )

        # Criar campanhas de mensagem
        contacts = list(Contact.objects.filter(is_active=True, category__in=["apoiador", "coordenador_municipal"]))
        template = MessageTemplate.objects.first()

        msg_campaigns = [
            ("Convite Evento Chapecó - Maio", "sent", 150, 142, 98, 23),
            ("Lembrete Reunião Coordenadores", "sent", 25, 25, 20, 15),
            ("Newsletter Semana 20", "sending", 300, 180, 0, 0),
            ("Pesquisa Opinião - Oeste", "scheduled", 0, 0, 0, 0),
            ("Mobilização Junho", "draft", 0, 0, 0, 0),
        ]
        for name, status, sent, delivered, read, replied in msg_campaigns:
            mc = MessageCampaign.objects.create(
                name=name,
                template=template,
                channel="whatsapp",
                status=status,
                total_sent=sent,
                total_delivered=delivered,
                total_read=read,
                total_replied=replied,
                scheduled_at=timezone.now() + timedelta(days=random.randint(1, 10)) if status == "scheduled" else None,
                sent_at=timezone.now() - timedelta(days=random.randint(1, 15)) if status == "sent" else None,
            )
            if contacts and status in ("sent", "sending"):
                mc.target_contacts.set(random.sample(contacts, min(30, len(contacts))))

        self.stdout.write(f"  {MessageTemplate.objects.count()} templates, {MessageCampaign.objects.count()} campanhas msg")

    # ── Doações e Despesas ───────────────────────────────────────────
    def create_donations_expenses(self):
        self.stdout.write("Criando doações e despesas...")
        contacts = list(Contact.objects.filter(
            category__in=["apoiador", "lideranca", "coordenador_regional", "coordenador_municipal"]
        ))
        users = list(User.objects.all())

        # Doações
        for _ in range(35):
            donor = random.choice(contacts)
            Donation.objects.create(
                donor=donor,
                amount=random.choice([100, 200, 500, 1000, 2000, 5000, 10000]),
                date=self.random_date_range(90, 0),
                receipt_number=f"REC-{random.randint(1000,9999)}" if random.random() > 0.3 else "",
                method=random.choice(["pix", "transfer", "pix", "pix"]),
                is_verified=random.random() > 0.3,
                notes=random.choice(["", "Doação mensal", "Apoio para evento", "Contribuição voluntária"]),
            )

        # Despesas
        expense_cats = [
            ("Combustível", 200, 800),
            ("Alimentação", 100, 500),
            ("Material gráfico", 500, 5000),
            ("Aluguel de espaço", 1000, 8000),
            ("Equipamentos", 300, 3000),
            ("Comunicação digital", 500, 5000),
            ("Hospedagem", 150, 600),
            ("Transporte", 100, 1000),
        ]
        for _ in range(25):
            cat, min_val, max_val = random.choice(expense_cats)
            Expense.objects.create(
                description=f"{cat} - {random.choice(['Maio', 'Abril', 'Março'])} 2026",
                amount=random.randint(min_val, max_val),
                date=self.random_date_range(60, 0),
                category=cat,
                approved_by=random.choice(users) if random.random() > 0.3 else None,
            )

        self.stdout.write(f"  {Donation.objects.count()} doações, {Expense.objects.count()} despesas")
