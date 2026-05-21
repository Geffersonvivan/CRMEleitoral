// ====================================================
// PWA Campo - Componentes Alpine.js
// ====================================================

// --- App global (usado no base_mobile.html) ---
function pwaApp() {
    return {
        online: navigator.onLine,
        pendingSync: 0,
        toast: '',
        toastType: 'success',
        _toastTimer: null,

        init() {
            window.addEventListener('online', () => this.online = true);
            window.addEventListener('offline', () => this.online = false);
            this._loadPending();
        },

        showToast(msg, type = 'success') {
            this.toast = msg;
            this.toastType = type;
            clearTimeout(this._toastTimer);
            this._toastTimer = setTimeout(() => this.toast = '', 3000);
        },

        _loadPending() {
            try {
                const queue = JSON.parse(localStorage.getItem('campo_sync_queue') || '[]');
                this.pendingSync = queue.length;
            } catch { this.pendingSync = 0; }
        },

        _addToQueue(item) {
            const queue = JSON.parse(localStorage.getItem('campo_sync_queue') || '[]');
            queue.push({ ...item, _ts: Date.now() });
            localStorage.setItem('campo_sync_queue', JSON.stringify(queue));
            this.pendingSync = queue.length;
        },

        async _syncQueue() {
            const queue = JSON.parse(localStorage.getItem('campo_sync_queue') || '[]');
            if (!queue.length || !navigator.onLine) return;

            const remaining = [];
            for (const item of queue) {
                try {
                    if (item.type === 'contact') {
                        await API.post('/api/v1/contacts/', item.data);
                    } else if (item.type === 'interaction') {
                        await API.post(`/api/v1/contacts/${item.contact_id}/interactions/`, item.data);
                    } else if (item.type === 'checkin') {
                        await API.post(`/api/v1/events/${item.event_id}/checkin/`, item.data);
                    }
                } catch {
                    remaining.push(item);
                }
            }
            localStorage.setItem('campo_sync_queue', JSON.stringify(remaining));
            this.pendingSync = remaining.length;
        }
    };
}

// --- Countdown eleições ---
function countdown() {
    return {
        days: '--', hours: '--', mins: '--',

        start() {
            this._calc();
            setInterval(() => this._calc(), 60000);
        },

        _calc() {
            const election = new Date('2026-10-04T08:00:00');
            const now = new Date();
            const diff = election - now;
            if (diff <= 0) { this.days = '0'; this.hours = '0'; this.mins = '0'; return; }
            this.days = String(Math.floor(diff / 86400000));
            this.hours = String(Math.floor((diff % 86400000) / 3600000)).padStart(2, '0');
            this.mins = String(Math.floor((diff % 3600000) / 60000)).padStart(2, '0');
        }
    };
}

// --- Home ---
function campoHome() {
    return {
        stats: { contatos_hoje: '-', interacoes_hoje: '-', demandas_pendentes: '-', eventos_hoje: '-' },
        eventos: [],
        resumo: null,
        loading: true,

        async load() {
            try {
                const data = await API.get('/api/v1/campo/home/');
                this.stats = data.stats;
                this.eventos = data.proximos_eventos || [];
                this.resumo = data.resumo || null;
            } catch (e) {
                console.warn('Erro ao carregar home:', e);
            }
            this.loading = false;
        },

        formatDate(dateStr) {
            if (!dateStr) return '';
            const d = new Date(dateStr);
            return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
        }
    };
}

// --- Novo Contato ---
function campoContato() {
    return {
        form: {
            full_name: '',
            phone: '',
            whatsapp: '',
            category: 'eleitor',
            city: '',
            notes: '',
            engagement_level: 2,
        },
        fotoPreview: null,
        fotoFile: null,
        cidades: [],
        salvando: false,

        async init() {
            try {
                const data = await API.get('/api/v1/campo/cidades/');
                this.cidades = data;
            } catch (e) {
                console.warn('Erro ao carregar cidades:', e);
            }

            // Pre-selecionar cidade se veio da URL
            const params = new URLSearchParams(window.location.search);
            if (params.get('city')) {
                this.form.city = params.get('city');
            }
        },

        onFoto(event) {
            const file = event.target.files[0];
            if (!file) return;
            this.fotoFile = file;
            const reader = new FileReader();
            reader.onload = (e) => this.fotoPreview = e.target.result;
            reader.readAsDataURL(file);
        },

        async usarGPS() {
            if (!navigator.geolocation) return;
            navigator.geolocation.getCurrentPosition(async (pos) => {
                try {
                    const data = await API.get(`/api/v1/campo/cidade-por-gps/?lat=${pos.coords.latitude}&lng=${pos.coords.longitude}`);
                    if (data.id) this.form.city = String(data.id);
                } catch (e) {
                    console.warn('GPS cidade erro:', e);
                }
            });
        },

        async salvar() {
            if (!this.form.full_name.trim()) {
                this._toast('Preencha o nome', 'error');
                return;
            }
            this.salvando = true;

            try {
                const payload = { ...this.form };
                if (payload.city) payload.city = parseInt(payload.city);
                else delete payload.city;

                if (navigator.onLine) {
                    let result;
                    if (this.fotoFile) {
                        // Enviar com FormData para incluir a foto
                        const fd = new FormData();
                        Object.entries(payload).forEach(([k, v]) => { if (v !== '' && v !== null) fd.append(k, v); });
                        fd.append('photo', this.fotoFile);
                        result = await this._postForm('/api/v1/contacts/', fd);
                    } else {
                        result = await API.post('/api/v1/contacts/', payload);
                    }
                    this._toast('Contato salvo!');
                } else {
                    // Salvar offline
                    this._addToQueue({ type: 'contact', data: payload });
                    this._toast('Salvo offline. Sincroniza quando conectar.');
                }

                this._resetForm();
            } catch (e) {
                console.error('Erro ao salvar contato:', e);
                this._toast('Erro ao salvar', 'error');
            }
            this.salvando = false;
        },

        async _postForm(url, formData) {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': API._getCsrf(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
                body: formData,
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        },

        _resetForm() {
            this.form = { full_name: '', phone: '', whatsapp: '', category: 'eleitor', city: '', notes: '', engagement_level: 2 };
            this.fotoPreview = null;
            this.fotoFile = null;
        },

        _toast(msg, type = 'success') {
            // Acessa o componente pwaApp pai
            const app = Alpine.$data(document.querySelector('[x-data="pwaApp()"]'));
            if (app) app.showToast(msg, type);
        },

        _addToQueue(item) {
            const app = Alpine.$data(document.querySelector('[x-data="pwaApp()"]'));
            if (app) app._addToQueue(item);
        }
    };
}

// --- Interação ---
function campoInteracao() {
    return {
        busca: '',
        resultados: [],
        contato: null,
        form: {
            interaction_type: 'door_to_door',
            description: '',
            outcome: '',
            next_action: '',
        },
        tipos: [
            { value: 'door_to_door', label: 'Porta a Porta' },
            { value: 'whatsapp', label: 'WhatsApp' },
            { value: 'phone_call', label: 'Telefone' },
            { value: 'meeting', label: 'Reunião' },
            { value: 'event', label: 'Evento' },
            { value: 'referral', label: 'Indicação' },
        ],
        salvando: false,

        init() {},

        async pesquisar() {
            if (this.busca.length < 2) { this.resultados = []; return; }
            try {
                const data = await API.get(`/api/v1/contacts/?search=${encodeURIComponent(this.busca)}&page_size=10`);
                this.resultados = data.results || data;
            } catch (e) {
                console.warn('Erro ao pesquisar:', e);
            }
        },

        selecionarContato(c) {
            this.contato = c;
            this.resultados = [];
            this.busca = '';
        },

        async salvar() {
            if (!this.contato) return;
            this.salvando = true;

            try {
                const payload = { ...this.form };

                if (navigator.onLine) {
                    await API.post(`/api/v1/contacts/${this.contato.id}/interactions/`, payload);
                    this._toast('Interação registrada!');
                } else {
                    this._addToQueue({ type: 'interaction', contact_id: this.contato.id, data: payload });
                    this._toast('Salvo offline. Sincroniza quando conectar.');
                }

                this.contato = null;
                this.form = { interaction_type: 'door_to_door', description: '', outcome: '', next_action: '' };
            } catch (e) {
                console.error('Erro ao salvar interação:', e);
                this._toast('Erro ao salvar', 'error');
            }
            this.salvando = false;
        },

        _toast(msg, type = 'success') {
            const app = Alpine.$data(document.querySelector('[x-data="pwaApp()"]'));
            if (app) app.showToast(msg, type);
        },

        _addToQueue(item) {
            const app = Alpine.$data(document.querySelector('[x-data="pwaApp()"]'));
            if (app) app._addToQueue(item);
        }
    };
}

// --- Check-in ---
function campoCheckin() {
    return {
        location: null,
        eventos: [],
        loading: true,
        checkingIn: false,

        async load() {
            // Obter GPS
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (pos) => this.location = { lat: pos.coords.latitude, lng: pos.coords.longitude },
                    () => console.warn('GPS indisponível')
                );
            }

            // Carregar eventos
            try {
                const data = await API.get('/api/v1/campo/eventos-checkin/');
                this.eventos = data;
            } catch (e) {
                console.warn('Erro ao carregar eventos:', e);
            }
            this.loading = false;
        },

        formatDateTime(dateStr) {
            if (!dateStr) return '';
            const d = new Date(dateStr);
            return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
        },

        async checkin(ev) {
            this.checkingIn = true;
            try {
                const payload = {
                    latitude: this.location?.lat || null,
                    longitude: this.location?.lng || null,
                };

                if (navigator.onLine) {
                    await API.post(`/api/v1/campo/checkin/${ev.id}/`, payload);
                    ev.checked_in = true;
                    this._toast('Check-in realizado!');
                } else {
                    this._addToQueue({ type: 'checkin', event_id: ev.id, data: payload });
                    ev.checked_in = true;
                    this._toast('Check-in salvo offline.');
                }
            } catch (e) {
                console.error('Erro no check-in:', e);
                this._toast('Erro no check-in', 'error');
            }
            this.checkingIn = false;
        },

        _toast(msg, type = 'success') {
            const app = Alpine.$data(document.querySelector('[x-data="pwaApp()"]'));
            if (app) app.showToast(msg, type);
        },

        _addToQueue(item) {
            const app = Alpine.$data(document.querySelector('[x-data="pwaApp()"]'));
            if (app) app._addToQueue(item);
        }
    };
}

// --- Cidade (Termômetro) ---
function campoCidade() {
    return {
        busca: '',
        resultados: [],
        cidade: null,

        init() {},

        async pesquisar() {
            if (this.busca.length < 2) { this.resultados = []; return; }
            try {
                const data = await API.get(`/api/v1/campo/cidades/?search=${encodeURIComponent(this.busca)}`);
                this.resultados = data;
            } catch (e) {
                console.warn('Erro ao pesquisar cidade:', e);
            }
        },

        async selecionarCidade(c) {
            try {
                const data = await API.get(`/api/v1/campo/cidade/${c.id}/`);
                this.cidade = data;
                this.resultados = [];
                this.busca = '';
            } catch (e) {
                console.warn('Erro ao carregar cidade:', e);
                this.cidade = c;
            }
        },

        async detectarGPS() {
            if (!navigator.geolocation) { this._toast('GPS indisponível', 'error'); return; }
            navigator.geolocation.getCurrentPosition(async (pos) => {
                try {
                    const data = await API.get(`/api/v1/campo/cidade-por-gps/?lat=${pos.coords.latitude}&lng=${pos.coords.longitude}`);
                    if (data.id) {
                        await this.selecionarCidade(data);
                    } else {
                        this._toast('Cidade não encontrada', 'error');
                    }
                } catch (e) {
                    this._toast('Erro ao detectar cidade', 'error');
                }
            }, () => this._toast('Permita acesso ao GPS', 'error'));
        },

        fmt(n) {
            if (!n && n !== 0) return '—';
            return Number(n).toLocaleString('pt-BR');
        },

        _toast(msg, type = 'success') {
            const app = Alpine.$data(document.querySelector('[x-data="pwaApp()"]'));
            if (app) app.showToast(msg, type);
        }
    };
}
