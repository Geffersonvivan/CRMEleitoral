"""
Mixins para aplicar filtro territorial automaticamente nos ViewSets.
"""


class TerritoryFilterMixin:
    """
    Mixin que filtra o queryset pelo território do usuário logado.
    Usa os campos `city` e `region` do model.
    Admins e coordenadores estaduais veem tudo.
    """
    territory_city_field = 'city'
    territory_region_field = 'region'

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return qs

        if not user.is_territorial():
            return qs

        territory = user.get_territory_filter()
        if not territory:
            return qs

        # Mapear os campos genéricos para os campos reais do model
        filters = {}
        if 'city_id' in territory:
            filters[f'{self.territory_city_field}_id'] = territory['city_id']
        elif 'region_id' in territory:
            filters[f'{self.territory_region_field}_id'] = territory['region_id']

        return qs.filter(**filters)
