// Region View App - Alpine.js + D3.js
function regionApp(slug) {
    return {
        slug: slug,
        data: {},
        mapaParam: new URLSearchParams(window.location.search).get('mapa') || '',

        // Dados por modo
        strategicData: null,
        plNetworkData: null,
        zoneData: null,
        transferData: null,
        deputiesData: null,
        demandsData: null,
        itinerariesData: null,

        mapaLabel() {
            const map = {
                regioes: 'Mapa Regioes', calor: 'Mapa Calor', demandas: 'Mapa Demandas',
                roteiros: 'Mapa Roteiros', estrategico: 'Mapa Estrategico', rede_pl: 'Mapa Rede PL',
                zonas: 'Mapa Zonas', transferencia: 'Mapa Transferencia', deputados: 'Mapa Dep. Aliados',
                eleicoes_2022: 'Mapa Eleicoes 2022',
            };
            return map[this.mapaParam] || '';
        },

        mapIs(...modes) {
            return modes.includes(this.mapaParam || 'regioes');
        },

        async init() {
            try {
                this.data = await API.dashboard.region(this.slug);
            } catch (e) {
                console.error('Region API erro:', e);
                this.data = { region: { name: slug.toUpperCase() }, cities: [] };
            }

            // Fetch modo-especifico
            await this._fetchModeData();

            // Mapa D3
            this._initMap();
        },

        async _fetchModeData() {
            const mode = this.mapaParam || 'regioes';
            try {
                if (mode === 'estrategico') {
                    const d = await API.dashboard.strategic();
                    this.strategicData = this._filterByRegion(d, 'cities');
                } else if (mode === 'rede_pl') {
                    const d = await API.dashboard.plNetwork();
                    this.plNetworkData = this._filterByRegion(d, 'cities');
                } else if (mode === 'zonas') {
                    const d = await API.dashboard.zoneRanking();
                    this.zoneData = this._filterZonesByRegion(d);
                } else if (mode === 'transferencia') {
                    const d = await API.dashboard.voteTransfer();
                    this.transferData = this._filterTransferByRegion(d);
                } else if (mode === 'deputados') {
                    const d = await API.dashboard.neighborDeputies();
                    this.deputiesData = this._filterByRegion(d, 'cities');
                } else if (mode === 'demandas') {
                    this.demandsData = await API.tasks.regionTasks(this.slug);
                } else if (mode === 'roteiros') {
                    const all = await API.itineraries.mapData(false);
                    this.itinerariesData = this._filterItinerariesByRegion(all);
                }
            } catch (e) {
                console.error('Erro ao carregar dados do modo:', e);
            }
        },

        _filterByRegion(data, key) {
            if (!data || !data[key]) return { cities: [], summary: {} };
            const cities = data[key].filter(c => c.region_slug === this.slug);
            const summary = {};
            // Recontar summary
            const classField = key === 'cities' ?
                (cities[0]?.classification !== undefined ? 'classification' :
                 cities[0]?.level !== undefined ? 'level' :
                 cities[0]?.performance !== undefined ? 'performance' : null) : null;
            if (classField) {
                for (const c of cities) {
                    const cls = c[classField];
                    summary[cls] = (summary[cls] || 0) + 1;
                }
            }
            return { cities, summary };
        },

        _filterZonesByRegion(data) {
            if (!data || !data.zones) return { zones: [], summary: {} };
            const zones = data.zones.filter(z =>
                z.cities && z.cities.some(c => c.region_slug === this.slug)
            );
            const summary = {};
            for (const z of zones) {
                summary[z.performance] = (summary[z.performance] || 0) + 1;
            }
            return { zones, summary };
        },

        _filterTransferByRegion(data) {
            if (!data) return { cities: [], opportunities: [], summary: {}, opp_summary: {} };
            const cities = (data.cities || []).filter(c => c.region_slug === this.slug);
            const citySlugs = new Set(cities.map(c => c.slug));
            const opportunities = (data.opportunities || []).filter(o =>
                citySlugs.has(o.source.slug) || citySlugs.has(o.target.slug)
            );
            const summary = {};
            for (const o of opportunities) {
                summary[o.priority] = (summary[o.priority] || 0) + 1;
            }
            const opp_summary = {};
            for (const c of cities) {
                opp_summary[c.opp_class] = (opp_summary[c.opp_class] || 0) + 1;
            }
            return { cities, opportunities, summary, opp_summary };
        },

        _filterItinerariesByRegion(all) {
            // Extrair visitas por cidade a partir dos roteiros
            const cityVisits = {};
            const regionCitySlugs = new Set((this.data.cities || []).map(c => c.slug));

            for (const it of (all || [])) {
                for (const stop of (it.stops || [])) {
                    if (!regionCitySlugs.has(stop.city_slug)) continue;
                    if (!cityVisits[stop.city_slug]) {
                        cityVisits[stop.city_slug] = {
                            slug: stop.city_slug,
                            name: stop.city_name,
                            visits: 0,
                            last_visit: null,
                            next_visit: null,
                            itinerary: it.name,
                        };
                    }
                    const cv = cityVisits[stop.city_slug];
                    cv.visits++;
                    const stopDate = stop.date;
                    const today = new Date().toISOString().slice(0, 10);
                    if (stopDate <= today) {
                        if (!cv.last_visit || stopDate > cv.last_visit) cv.last_visit = stopDate;
                    } else {
                        if (!cv.next_visit || stopDate < cv.next_visit) cv.next_visit = stopDate;
                    }
                }
            }
            return Object.values(cityVisits);
        },

        // Helpers de classificacao
        strategicClassLabel(cls) {
            return { base_forte: 'Base Forte', aliado_fraco: 'Aliado Fraco', potencial_oculto: 'Potencial Oculto', territorio_hostil: 'Territorio Hostil', neutro: 'Neutro' }[cls] || cls;
        },
        strategicClassColor(cls) {
            return { base_forte: '#15803d', aliado_fraco: '#86efac', potencial_oculto: '#eab308', territorio_hostil: '#dc2626', neutro: '#9ca3af' }[cls] || '#d1d5db';
        },
        plNetworkLevelLabel(level) {
            return { forte: 'Forte', moderada: 'Moderada', fraca: 'Fraca', ausente: 'Ausente' }[level] || level;
        },
        plNetworkLevelColor(level) {
            return { forte: '#1e3a8a', moderada: '#2563eb', fraca: '#93c5fd', ausente: '#d1d5db' }[level] || '#d1d5db';
        },
        zonePerfLabel(perf) {
            return { lider: '1o Lugar', competitivo: 'Top 3', medio: 'Top 5', baixo: '6o+', ausente: 'Sem dados' }[perf] || perf;
        },
        zonePerfColor(perf) {
            return { lider: '#15803d', competitivo: '#22c55e', medio: '#eab308', baixo: '#f97316', ausente: '#d1d5db' }[perf] || '#d1d5db';
        },
        deputiesClassLabel(cls) {
            return { ponte_forte: 'Ponte Forte', base_conjunta: 'Base Conjunta', territorio_dep: 'Territorio Dep.', territorio_ls: 'Territorio LS', sem_presenca: 'Sem Presenca' }[cls] || cls;
        },
        deputiesClassColor(cls) {
            return { ponte_forte: '#f59e0b', base_conjunta: '#15803d', territorio_dep: '#2563eb', territorio_ls: '#86efac', sem_presenca: '#d1d5db' }[cls] || '#d1d5db';
        },
        transferOppLabel(cls) {
            return { zona_ouro: 'Zona de Ouro', buscar_ambos: 'Buscar Ambos', buscar_jorginho: 'Buscar Jorginho', buscar_carol: 'Buscar Carol', polo_ls: 'Polo LS', baixa_prioridade: 'Baixa Prioridade' }[cls] || cls;
        },
        transferOppColor(cls) {
            return { zona_ouro: '#fbbf24', buscar_ambos: '#7c3aed', buscar_jorginho: '#2563eb', buscar_carol: '#ec4899', polo_ls: '#15803d', baixa_prioridade: '#d1d5db' }[cls] || '#d1d5db';
        },

        formatDate(dateStr) {
            if (!dateStr) return '-';
            const d = new Date(dateStr + 'T00:00:00');
            return d.toLocaleDateString('pt-BR');
        },

        // Mapa D3
        _initMap() {
            const container = document.getElementById('region-map');
            const width = container.clientWidth;
            const height = container.clientHeight || 400;

            d3.select('#region-map').select('svg').remove();

            const svg = d3.select('#region-map')
                .append('svg')
                .attr('width', '100%')
                .attr('height', '100%')
                .attr('viewBox', `0 0 ${width} ${height}`)
                .attr('preserveAspectRatio', 'xMidYMid meet')
                .style('background', '#f8fafc');

            const g = svg.append('g');

            const tip = document.createElement('div');
            tip.className = 'map-tooltip';
            document.body.appendChild(tip);

            svg.call(d3.zoom().scaleExtent([1, 6]).on('zoom', (event) => {
                g.attr('transform', event.transform);
            }));

            const self = this;

            API.maps.region(this.slug).then(geojson => {
                if (!geojson.features || geojson.features.length === 0) return;

                const projection = d3.geoMercator()
                    .fitExtent([[20, 20], [width - 20, height - 20]], geojson);
                const path = d3.geoPath().projection(projection);

                g.selectAll('path.city')
                    .data(geojson.features)
                    .enter()
                    .append('path')
                    .attr('class', 'city')
                    .attr('d', path)
                    .attr('fill', d => self._cityColor(d.properties.slug))
                    .attr('fill-opacity', 0.8)
                    .attr('stroke', d => self._cityStroke(d.properties.slug))
                    .attr('stroke-width', 1)
                    .attr('cursor', 'pointer')
                    .on('mouseenter', (event, d) => {
                        tip.innerHTML = self._cityTooltip(d.properties);
                        tip.style.transform = `translate3d(${event.pageX + 12}px, ${event.pageY - 10}px, 0)`;
                        tip.style.opacity = '1';
                    })
                    .on('mousemove', (event) => {
                        tip.style.transform = `translate3d(${event.pageX + 12}px, ${event.pageY - 10}px, 0)`;
                    })
                    .on('mouseleave', () => {
                        tip.style.opacity = '0';
                    })
                    .on('click', (event, d) => {
                        tip.style.opacity = '0';
                        const mp = self.mapaParam;
                        window.location.href = `/cidade/${d.properties.slug}/` + (mp ? `?mapa=${mp}` : '');
                    });

                // Labels
                g.selectAll('text.city-label')
                    .data(geojson.features)
                    .enter()
                    .append('text')
                    .attr('x', d => path.centroid(d)[0])
                    .attr('y', d => path.centroid(d)[1])
                    .attr('text-anchor', 'middle')
                    .attr('dy', '0.35em')
                    .attr('font-size', '9px')
                    .attr('font-weight', '600')
                    .attr('fill', '#01579b')
                    .attr('pointer-events', 'none')
                    .attr('paint-order', 'stroke')
                    .attr('stroke', '#fff')
                    .attr('stroke-width', '2px')
                    .text(d => d.properties.name);

            }).catch(e => {
                console.error('Sem GeoJSON para esta regiao:', e);
            });
        },

        _cityColor(citySlug) {
            const mode = this.mapaParam || 'regioes';

            if (mode === 'estrategico' && this.strategicData) {
                const c = this.strategicData.cities.find(x => x.slug === citySlug);
                return c ? this.strategicClassColor(c.classification) : '#d1d5db';
            }
            if (mode === 'rede_pl' && this.plNetworkData) {
                const c = this.plNetworkData.cities.find(x => x.slug === citySlug);
                return c ? this.plNetworkLevelColor(c.level) : '#d1d5db';
            }
            if (mode === 'deputados' && this.deputiesData) {
                const c = this.deputiesData.cities.find(x => x.slug === citySlug);
                return c ? this.deputiesClassColor(c.classification) : '#d1d5db';
            }
            if (mode === 'transferencia' && this.transferData) {
                const c = this.transferData.cities.find(x => x.slug === citySlug);
                return c ? this.transferOppColor(c.opp_class) : '#d1d5db';
            }
            if (mode === 'calor') {
                const c = (this.data.cities || []).find(x => x.slug === citySlug);
                if (!c || !c.population) return '#d1d5db';
                const pen = (c.votes_sorgatto_2022 || 0) / c.population * 100;
                if (pen >= 3) return '#15803d';
                if (pen >= 2) return '#22c55e';
                if (pen >= 1) return '#eab308';
                if (pen >= 0.5) return '#f97316';
                return '#ef4444';
            }
            if (mode === 'demandas' && this.demandsData) {
                const c = this.demandsData.find(x => x.slug === citySlug);
                if (!c || (c.open === 0 && c.completed === 0)) return '#d1d5db';
                if (c.overdue > 0) return '#dc2626';
                if (c.open > 0) return '#f97316';
                return '#22c55e';
            }
            return '#81d4fa';
        },

        _cityStroke(citySlug) {
            const mode = this.mapaParam || 'regioes';
            if (['estrategico', 'rede_pl', 'deputados', 'transferencia', 'calor', 'demandas'].includes(mode)) {
                return '#374151';
            }
            return '#0288d1';
        },

        _cityTooltip(props) {
            const mode = this.mapaParam || 'regioes';
            let html = `<div class="tooltip-title">${props.name}</div>`;

            if (mode === 'estrategico' && this.strategicData) {
                const c = this.strategicData.cities.find(x => x.slug === props.slug);
                if (c) {
                    html += `<div class="tooltip-row"><span class="tooltip-label">Classificacao:</span> <span class="tooltip-value">${this.strategicClassLabel(c.classification)}</span></div>`;
                    html += `<div class="tooltip-row"><span class="tooltip-label">Score:</span> <span class="tooltip-value">${c.score?.toFixed(1) || 0}</span></div>`;
                }
            } else if (mode === 'rede_pl' && this.plNetworkData) {
                const c = this.plNetworkData.cities.find(x => x.slug === props.slug);
                if (c) {
                    html += `<div class="tooltip-row"><span class="tooltip-label">Rede:</span> <span class="tooltip-value">${this.plNetworkLevelLabel(c.level)}</span></div>`;
                    html += `<div class="tooltip-row"><span class="tooltip-label">Ver. PL:</span> <span class="tooltip-value">${c.num_vereadores_pl || 0}</span></div>`;
                }
            } else if (mode === 'deputados' && this.deputiesData) {
                const c = this.deputiesData.cities.find(x => x.slug === props.slug);
                if (c) {
                    html += `<div class="tooltip-row"><span class="tooltip-label">Classificacao:</span> <span class="tooltip-value">${this.deputiesClassLabel(c.classification)}</span></div>`;
                    html += `<div class="tooltip-row"><span class="tooltip-label">Melhor Dep:</span> <span class="tooltip-value">${c.best_dep_pct?.toFixed(1)}%</span></div>`;
                }
            } else if (mode === 'transferencia' && this.transferData) {
                const c = this.transferData.cities.find(x => x.slug === props.slug);
                if (c) {
                    html += `<div class="tooltip-row"><span class="tooltip-label">Classe:</span> <span class="tooltip-value">${this.transferOppLabel(c.opp_class)}</span></div>`;
                    html += `<div class="tooltip-row"><span class="tooltip-label">LS:</span> <span class="tooltip-value">${c.penetration?.toFixed(1)}%</span></div>`;
                }
            } else if (mode === 'demandas' && this.demandsData) {
                const c = this.demandsData.find(x => x.slug === props.slug);
                if (c) {
                    html += `<div class="tooltip-row"><span class="tooltip-label">Abertas:</span> <span class="tooltip-value">${c.open}</span></div>`;
                    html += `<div class="tooltip-row"><span class="tooltip-label">Atrasadas:</span> <span class="tooltip-value">${c.overdue}</span></div>`;
                }
            } else {
                html += `<div class="tooltip-row"><span class="tooltip-label">Pop:</span> <span class="tooltip-value">${fmt.number(props.population)}</span></div>`;
                html += `<div class="tooltip-row"><span class="tooltip-label">Votos 2022:</span> <span class="tooltip-value">${fmt.number(props.votes_2022)}</span></div>`;
                html += `<div class="tooltip-row"><span class="tooltip-label">Contatos:</span> <span class="tooltip-value">${props.total_contacts || 0}</span></div>`;
            }
            return html;
        },
    };
}
