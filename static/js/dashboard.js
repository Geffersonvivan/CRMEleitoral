// Dashboard App - Alpine.js + D3.js Map
function dashboardApp() {
    return {
        data: {},
        currentLevel: 'state',
        regionName: '',
        scMap: null,
        mapMode: 'eleicoes_2022',
        showMapHelp: false,
        showCompletedRoutes: false,
        doacoesData: null,

        async init() {
            // Evitar inicializacao dupla
            if (this.scMap) return;

            // Carregar dados do dashboard
            try {
                this.data = await API.dashboard.overview();
            } catch (e) {
                console.log('Dashboard API nao disponivel');
                this.data = {};
            }

            // Inicializar mapa SVG com D3.js
            this.scMap = new SCMap('map-container').init();
            this.scMap.onRegionClick = (slug) => {
                this.currentLevel = 'region';
                const region = (this.data.regions || []).find(r => r.slug === slug);
                this.regionName = region ? region.name : slug.toUpperCase();
            };
            await this.scMap.loadState();

            // Restaurar modo de mapa da URL ou carregar padrao (eleicoes_2022)
            const urlMapa = new URLSearchParams(window.location.search).get('mapa');
            await this.setMapMode(urlMapa || 'eleicoes_2022');

        },

        strategicData: null,
        strategicFilter: '',
        strategicSort: 'score_desc',

        plNetworkData: null,
        plNetworkFilter: '',
        plNetworkSort: 'score_desc',

        zoneData: null,
        zoneFilter: '',
        zoneSort: 'ranking_asc',

        transferData: null,
        transferFilter: '',
        transferSort: 'score_desc',
        transferCitySort: 'penetration_desc',

        deputiesData: null,
        deputiesFilter: '',
        deputiesSort: 'best_dep_desc',

        elections2022Data: null,
        elections2022Filter: '',
        elections2022Sort: 'position_asc',

        async setMapMode(mode) {
            const wasTransfer = this.mapMode === 'transferencia';
            this.mapMode = mode;
            if (this.scMap) this.scMap.mapMode = mode;
            if (this.scMap) {
                // Se está saindo do modo transferência, recarregar mapa de estado primeiro
                if (wasTransfer && mode !== 'transferencia') {
                    this.scMap.voteTransferEnabled = false;
                    await this.scMap.loadState();
                }
                if (mode === 'calor') {
                    this.scMap.setHeatmap(true);
                } else if (mode === 'demandas') {
                    this.scMap.setDemands(true);
                } else if (mode === 'roteiros') {
                    this.scMap.setItineraries(true, this.showCompletedRoutes);
                } else if (mode === 'estrategico') {
                    this.scMap.setStrategic(true).then(() => {
                        this.strategicData = this.scMap._strategicData;
                    });
                } else if (mode === 'rede_pl') {
                    this.scMap.setPLNetwork(true).then(() => {
                        this.plNetworkData = this.scMap._plNetworkData;
                    });
                } else if (mode === 'zonas') {
                    this.scMap.setZoneRanking(true).then(() => {
                        this.zoneData = this.scMap._zoneRankingData;
                    });
                } else if (mode === 'transferencia') {
                    this.scMap.setVoteTransfer(true).then(() => {
                        this.transferData = this.scMap._voteTransferData;
                    });
                } else if (mode === 'deputados') {
                    this.scMap.setNeighborDeputies(true).then(() => {
                        this.deputiesData = this.scMap._neighborDeputiesData;
                    });
                } else if (mode === 'eleicoes_2022') {
                    this.scMap.setElections2022(true).then(() => {
                        this.elections2022Data = this.scMap._elections2022Data;
                    });
                } else if (mode === 'doacoes') {
                    this.scMap.setDoacoes(true).then(() => {
                        this.doacoesData = this.scMap._doacoesData;
                    });
                } else {
                    this.scMap.setHeatmap(false);
                    this.scMap.setDemands(false);
                    this.scMap.setItineraries(false);
                    this.scMap.setStrategic(false);
                    this.scMap.setPLNetwork(false);
                    this.scMap.setZoneRanking(false);
                    this.scMap.setVoteTransfer(false);
                    this.scMap.setNeighborDeputies(false);
                    this.scMap.setElections2022(false);
                }
            }
        },

        get strategicFiltered() {
            if (!this.strategicData) return [];
            let cities = this.strategicData.cities || [];
            if (this.strategicFilter) {
                cities = cities.filter(c => c.classification === this.strategicFilter);
            }
            const [field, dir] = this.strategicSort.split('_');
            const mul = dir === 'desc' ? -1 : 1;
            cities = [...cities].sort((a, b) => {
                if (field === 'score') return (a.score - b.score) * mul;
                if (field === 'name') return a.name.localeCompare(b.name) * mul;
                if (field === 'penetration') return (a.penetration - b.penetration) * mul;
                if (field === 'votes') return ((a.votes_2022||0) - (b.votes_2022||0)) * mul;
                return 0;
            });
            return cities;
        },

        get transferFiltered() {
            if (!this.transferData) return [];
            let opps = this.transferData.opportunities || [];
            // transferFilter pode ser prioridade (alta/media/baixa) ou opp_class
            if (this.transferFilter && ['alta', 'media', 'baixa'].includes(this.transferFilter)) {
                opps = opps.filter(o => o.priority === this.transferFilter);
            }
            const [field, dir] = this.transferSort.split('_');
            const mul = dir === 'desc' ? -1 : 1;
            opps = [...opps].sort((a, b) => {
                if (field === 'score') return (a.score - b.score) * mul;
                if (field === 'potential') return (a.potential_votes - b.potential_votes) * mul;
                if (field === 'diff') return (a.pen_diff - b.pen_diff) * mul;
                if (field === 'distance') return (a.distance_km - b.distance_km) * mul;
                if (field === 'source') return a.source.name.localeCompare(b.source.name) * mul;
                return 0;
            });
            return opps;
        },

        get transferCitiesFiltered() {
            if (!this.transferData) return [];
            let cities = this.transferData.cities || [];
            if (this.transferFilter) {
                cities = cities.filter(c => c.opp_class === this.transferFilter);
            }
            const [field, dir] = this.transferCitySort.split('_');
            const mul = dir === 'desc' ? -1 : 1;
            cities = [...cities].sort((a, b) => {
                if (field === 'penetration') return (a.penetration - b.penetration) * mul;
                if (field === 'jorginho') return (a.jorginho_pct - b.jorginho_pct) * mul;
                if (field === 'carol') return (a.carol_pct - b.carol_pct) * mul;
                if (field === 'voters') return (a.voters - b.voters) * mul;
                if (field === 'name') return a.name.localeCompare(b.name) * mul;
                return 0;
            });
            return cities;
        },

        transferCount(pri) {
            if (!this.transferData) return 0;
            return this.transferData.summary[pri] || 0;
        },

        transferPriorityLabel(pri) {
            const map = { alta: 'Alta', media: 'Média', baixa: 'Baixa' };
            return map[pri] || pri;
        },

        transferPriorityColor(pri) {
            const map = { alta: '#dc2626', media: '#f97316', baixa: '#9ca3af' };
            return map[pri] || '#9ca3af';
        },

        transferOppCount(cls) {
            if (!this.transferData) return 0;
            return this.transferData.opp_summary[cls] || 0;
        },

        transferOppLabel(cls) {
            const map = {
                zona_ouro: 'Zona de Ouro',
                buscar_ambos: 'Buscar Ambos',
                buscar_jorginho: 'Buscar Jorginho',
                buscar_carol: 'Buscar Carol',
                polo_ls: 'Polo LS',
                baixa_prioridade: 'Baixa Prioridade',
            };
            return map[cls] || cls;
        },

        transferOppColor(cls) {
            const map = {
                zona_ouro: '#fbbf24',
                buscar_ambos: '#7c3aed',
                buscar_jorginho: '#2563eb',
                buscar_carol: '#ec4899',
                polo_ls: '#15803d',
                baixa_prioridade: '#d1d5db',
            };
            return map[cls] || '#d1d5db';
        },

        get zoneFiltered() {
            if (!this.zoneData) return [];
            let zones = this.zoneData.zones || [];
            if (this.zoneFilter) {
                zones = zones.filter(z => z.performance === this.zoneFilter);
            }
            const [field, dir] = this.zoneSort.split('_');
            const mul = dir === 'desc' ? -1 : 1;
            zones = [...zones].sort((a, b) => {
                if (field === 'ranking') return (a.ranking - b.ranking) * mul;
                if (field === 'votes') return (a.ls_votes - b.ls_votes) * mul;
                if (field === 'position') return (a.ls_position - b.ls_position) * mul;
                if (field === 'percentage') return (a.ls_percentage - b.ls_percentage) * mul;
                if (field === 'gap') return (a.gap_to_first - b.gap_to_first) * mul;
                if (field === 'zone') return a.zone_number.localeCompare(b.zone_number, undefined, {numeric: true}) * mul;
                return 0;
            });
            return zones;
        },

        zoneCount(perf) {
            if (!this.zoneData) return 0;
            return this.zoneData.summary[perf] || 0;
        },

        zonePerfLabel(perf) {
            const map = { lider: '1º Lugar', competitivo: 'Top 3', medio: 'Top 5', baixo: '6º+', ausente: 'Sem dados' };
            return map[perf] || perf;
        },

        zonePerfColor(perf) {
            const map = { lider: '#15803d', competitivo: '#22c55e', medio: '#eab308', baixo: '#f97316', ausente: '#d1d5db' };
            return map[perf] || '#d1d5db';
        },

        get plNetworkFiltered() {
            if (!this.plNetworkData) return [];
            let cities = this.plNetworkData.cities || [];
            if (this.plNetworkFilter) {
                cities = cities.filter(c => c.level === this.plNetworkFilter);
            }
            const [field, dir] = this.plNetworkSort.split('_');
            const mul = dir === 'desc' ? -1 : 1;
            cities = [...cities].sort((a, b) => {
                if (field === 'score') return (a.score - b.score) * mul;
                if (field === 'name') return a.name.localeCompare(b.name) * mul;
                if (field === 'contacts') return ((a.contacts||0) - (b.contacts||0)) * mul;
                if (field === 'vereadores') return ((a.num_vereadores_pl||0) - (b.num_vereadores_pl||0)) * mul;
                return 0;
            });
            return cities;
        },

        plNetworkCount(level) {
            if (!this.plNetworkData) return 0;
            return this.plNetworkData.summary[level] || 0;
        },

        plNetworkLevelLabel(level) {
            const labels = { forte: 'Forte', moderada: 'Moderada', fraca: 'Fraca', ausente: 'Ausente' };
            return labels[level] || level;
        },

        plNetworkLevelColor(level) {
            const map = { forte: '#1e3a8a', moderada: '#2563eb', fraca: '#93c5fd', ausente: '#d1d5db' };
            return map[level] || '#d1d5db';
        },

        strategicCount(cls) {
            if (!this.strategicData) return 0;
            return this.strategicData.summary[cls] || 0;
        },

        strategicClassLabel(cls) {
            const labels = { base_forte: 'Base Forte', aliado_fraco: 'Aliado Fraco', potencial_oculto: 'Potencial Oculto', territorio_hostil: 'Território Hostil', neutro: 'Neutro' };
            return labels[cls] || cls;
        },

        strategicClassColor(cls) {
            const map = { base_forte: '#15803d', aliado_fraco: '#86efac', potencial_oculto: '#eab308', territorio_hostil: '#dc2626', neutro: '#9ca3af' };
            return map[cls] || '#d1d5db';
        },

        get deputiesFiltered() {
            if (!this.deputiesData) return [];
            let cities = this.deputiesData.cities || [];
            if (this.deputiesFilter) {
                cities = cities.filter(c => c.classification === this.deputiesFilter);
            }
            const [field, dir] = this.deputiesSort.split('_');
            const mul = dir === 'desc' ? -1 : 1;
            cities = [...cities].sort((a, b) => {
                if (field === 'best_dep') return (a.best_dep_pct - b.best_dep_pct) * mul;
                if (field === 'ls') return (a.ls_pct - b.ls_pct) * mul;
                if (field === 'total') return (a.total_dep_votes - b.total_dep_votes) * mul;
                if (field === 'name') return a.name.localeCompare(b.name) * mul;
                return 0;
            });
            return cities;
        },

        deputiesCount(cls) {
            if (!this.deputiesData) return 0;
            return this.deputiesData.summary[cls] || 0;
        },

        deputiesClassLabel(cls) {
            const map = {
                ponte_forte: 'Ponte Forte',
                base_conjunta: 'Base Conjunta',
                territorio_dep: 'Território Dep.',
                territorio_ls: 'Território LS',
                sem_presenca: 'Sem Presença',
            };
            return map[cls] || cls;
        },

        deputiesClassColor(cls) {
            const map = {
                ponte_forte: '#f59e0b',
                base_conjunta: '#15803d',
                territorio_dep: '#2563eb',
                territorio_ls: '#86efac',
                sem_presenca: '#d1d5db',
            };
            return map[cls] || '#d1d5db';
        },

        get elections2022Filtered() {
            if (!this.elections2022Data) return [];
            let cities = this.elections2022Data.cities || [];
            if (this.elections2022Filter) {
                cities = cities.filter(c => c.performance === this.elections2022Filter);
            }
            const [field, dir] = this.elections2022Sort.split('_');
            const mul = dir === 'desc' ? -1 : 1;
            cities = [...cities].sort((a, b) => {
                if (field === 'position') return (a.ls_position - b.ls_position) * mul;
                if (field === 'votes') return (a.ls_votes - b.ls_votes) * mul;
                if (field === 'pct') return (a.ls_pct - b.ls_pct) * mul;
                if (field === 'name') return a.name.localeCompare(b.name) * mul;
                if (field === 'region') return a.region.localeCompare(b.region) * mul;
                return 0;
            });
            return cities;
        },

        elections2022Count(perf) {
            if (!this.elections2022Data) return 0;
            return this.elections2022Data.perf_summary[perf] || 0;
        },

        elections2022PerfLabel(perf) {
            const map = { primeiro: '1º Lugar', top3: 'Top 3', top5: 'Top 5', top10: 'Top 10', abaixo: '11º+' };
            return map[perf] || perf;
        },

        elections2022PerfColor(perf) {
            const map = { primeiro: '#15803d', top3: '#22c55e', top5: '#eab308', top10: '#f97316', abaixo: '#ef4444' };
            return map[perf] || '#d1d5db';
        },

        backToState() {
            this.scMap.backToState();
            this.currentLevel = 'state';
            this.regionName = '';
        },

        zoomToRegion(slug) {
            this.scMap.zoomToRegion(slug);
            this.currentLevel = 'region';
            const region = (this.data.regions || []).find(r => r.slug === slug);
            this.regionName = region ? region.name : slug.toUpperCase();
        },

    };
}
