// City View App - Alpine.js
function cityApp(slug) {
    return {
        slug: slug,
        data: {},
        s: {},
        mapaParam: new URLSearchParams(window.location.search).get('mapa') || '',

        doacoesData: null,

        mapaLabel() {
            const map = {
                regioes: 'Mapa Regiões', calor: 'Mapa Calor', demandas: 'Mapa Demandas',
                roteiros: 'Mapa Roteiros', estrategico: 'Mapa Estratégico', rede_pl: 'Mapa Rede PL',
                zonas: 'Mapa Zonas', transferencia: 'Mapa Transferência', deputados: 'Mapa Dep. Aliados',
                eleicoes_2022: 'Mapa Eleições 2022', doacoes: 'Mapa Doações',
            };
            return map[this.mapaParam] || '';
        },

        mapIs(...modes) {
            return modes.includes(this.mapaParam || 'regioes');
        },

        async init() {
            try {
                this.data = await API.dashboard.city(this.slug);
                this.s = this.data.strategic || {};
                if (this.mapIs('doacoes')) {
                    this.doacoesData = await API.fundraising.cityDetail(this.slug);
                }
            } catch (e) {
                console.error('City API erro:', e);
                this.data = { city: { name: this.slug } };
                this.s = {};
            }
        },

        classColor(cls) {
            const map = {
                base_forte: '#15803d',
                aliado_fraco: '#86efac',
                potencial_oculto: '#eab308',
                territorio_hostil: '#dc2626',
                neutro: '#9ca3af',
            };
            return map[cls] || '#d1d5db';
        },

        classBg(cls) {
            const map = {
                base_forte: 'bg-green-100 text-green-800 border-green-300',
                aliado_fraco: 'bg-green-50 text-green-600 border-green-200',
                potencial_oculto: 'bg-yellow-100 text-yellow-800 border-yellow-300',
                territorio_hostil: 'bg-red-100 text-red-800 border-red-300',
                neutro: 'bg-gray-100 text-gray-600 border-gray-300',
            };
            return map[cls] || 'bg-gray-100 text-gray-600 border-gray-300';
        },

        alignColor(alignment) {
            return { allied: 'text-green-700', adversary: 'text-red-600', neutral: 'text-gray-500' }[alignment] || 'text-gray-500';
        },

        priorityColor(p) {
            return { urgent: 'border-red-500 bg-red-50', high: 'border-orange-400 bg-orange-50', medium: 'border-yellow-400 bg-yellow-50', low: 'border-gray-300 bg-gray-50' }[p] || 'border-gray-300 bg-gray-50';
        },

        priorityLabel(p) {
            return { urgent: 'Urgente', high: 'Alta', medium: 'Média', low: 'Baixa' }[p] || p;
        },

        priorityBadge(p) {
            return { urgent: 'bg-red-600 text-white', high: 'bg-orange-500 text-white', medium: 'bg-yellow-500 text-white', low: 'bg-gray-400 text-white' }[p] || 'bg-gray-400 text-white';
        },

        iconSvg(icon) {
            const icons = {
                alert: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/>',
                calendar: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>',
                target: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>',
                'trending-up': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>',
                shield: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>',
                minus: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"/>',
                search: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>',
                clock: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>',
                users: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>',
                flag: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2z"/>',
                handshake: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3m0 0V11"/>',
            };
            return icons[icon] || icons['alert'];
        },

        scoreBarWidth(component) {
            if (!component || !component.max) return '0%';
            return Math.round(component.weighted / component.max * 100) + '%';
        },

        formatDate(dateStr) {
            if (!dateStr) return 'Sem registro';
            const d = new Date(dateStr + 'T00:00:00');
            return d.toLocaleDateString('pt-BR');
        },
    };
}
