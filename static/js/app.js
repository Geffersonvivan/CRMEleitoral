// CRM Eleitoral Sorgatto 26 - App principal
const API = {
    _getCsrf() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : '';
    },

    _headers(method) {
        const h = {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        };
        if (method && method !== 'GET') {
            h['Content-Type'] = 'application/json';
            h['X-CSRFToken'] = API._getCsrf();
        }
        return h;
    },

    async get(url) {
        const response = await fetch(url, {
            headers: API._headers('GET'),
            credentials: 'same-origin',
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    },

    async post(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            headers: API._headers('POST'),
            credentials: 'same-origin',
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            const e = new Error(`HTTP ${response.status}`);
            e.data = err;
            throw e;
        }
        return response.json();
    },

    async patch(url, data) {
        const response = await fetch(url, {
            method: 'PATCH',
            headers: API._headers('PATCH'),
            credentials: 'same-origin',
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    },

    async put(url, data) {
        const response = await fetch(url, {
            method: 'PUT',
            headers: API._headers('PUT'),
            credentials: 'same-origin',
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            const e = new Error(`HTTP ${response.status}`);
            e.data = err;
            throw e;
        }
        return response.json();
    },

    async delete(url) {
        const response = await fetch(url, {
            method: 'DELETE',
            headers: API._headers('DELETE'),
            credentials: 'same-origin',
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        if (response.status === 204) return null;
        return response.json();
    },

    dashboard: {
        overview: () => API.get('/api/v1/dashboard/overview/'),
        region: (slug) => API.get(`/api/v1/dashboard/region/${slug}/`),
        city: (slug) => API.get(`/api/v1/dashboard/city/${slug}/`),
        strategic: () => API.get('/api/v1/dashboard/strategic/'),
        plNetwork: () => API.get('/api/v1/dashboard/pl-network/'),
        zoneRanking: () => API.get('/api/v1/dashboard/zone-ranking/'),
        voteTransfer: () => API.get('/api/v1/dashboard/vote-transfer/'),
        neighborDeputies: () => API.get('/api/v1/dashboard/neighbor-deputies/'),
        elections2022: () => API.get('/api/v1/dashboard/elections-2022/'),
    },

    maps: {
        state: () => API.get('/api/v1/maps/state/'),
        stateCities: () => API.get('/api/v1/maps/state-cities/'),
        region: (slug) => API.get(`/api/v1/maps/region/${slug}/`),
        city: (slug) => API.get(`/api/v1/maps/city/${slug}/`),
        heatmap: (metric) => API.get(`/api/v1/maps/heatmap/${metric}/`),
    },

    tasks: {
        mapStatus: () => API.get('/api/v1/campaigns/tasks/map-status/'),
        regionTasks: (slug) => API.get(`/api/v1/campaigns/tasks/region-tasks/${slug}/`),
    },

    itineraries: {
        mapData: (showCompleted) => API.get(`/api/v1/campaigns/itineraries/map-data/?completed=${showCompleted ? 'true' : 'false'}`),
    },
};

// Countdown eleições 2026 — 1º turno 04/10/2026 19:00 BRT
function countdown() {
    const target = new Date('2026-10-04T22:00:00Z').getTime(); // 19h BRT = 22h UTC
    return {
        days: '000', hours: '00', mins: '00', secs: '00',
        start() {
            this.tick();
            setInterval(() => this.tick(), 1000);
        },
        tick() {
            const diff = Math.max(0, target - Date.now());
            const s = Math.floor(diff / 1000);
            const d = Math.floor(s / 86400);
            const h = Math.floor((s % 86400) / 3600);
            const m = Math.floor((s % 3600) / 60);
            const sec = s % 60;
            this.days = String(d).padStart(3, '0');
            this.hours = String(h).padStart(2, '0');
            this.mins = String(m).padStart(2, '0');
            this.secs = String(sec).padStart(2, '0');
        }
    };
}

// Utilidades de formatacao
const fmt = {
    number: (n) => (n || 0).toLocaleString('pt-BR'),
    percent: (n) => (n || 0).toFixed(1) + '%',
};
