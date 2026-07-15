// js/main.js
const URLS = { 
    players: './Players.csv', 
    levels: './Levels.csv', 
    rankings: './Rankings.csv', 
    streams: 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=1466784286&single=true&output=csv', 
    news: 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=30512158&single=true&output=csv' 
};
const DB = { players: {}, levels: {}, rankings: {}, streams: [], news: [], playersArr: [] };

function parseCSV(csvText) {
    const rows = csvText.split('\n').filter(r => r.trim());
    if(rows.length < 2) return [];
    const headers = rows[0].split(',').map(h => h.trim().toLowerCase());
    return rows.slice(1).map(row => { const cols = row.split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/); let obj = {}; headers.forEach((h, i) => { let val = cols[i] ? cols[i].trim() : ''; if (val.startsWith('"') && val.endsWith('"')) val = val.slice(1, -1); obj[h] = val; }); return obj; });
}

async function initApp() {
    try {
        const [pRes, lRes, rRes, sRes, nRes] = await Promise.all([
            fetch(URLS.players), fetch(URLS.levels), fetch(URLS.rankings), fetch(URLS.streams), fetch(URLS.news)
        ]);
        const texts = await Promise.all([pRes.text(), lRes.text(), rRes.text(), sRes.text(), nRes.text()]);
        
        DB.playersArr = parseCSV(texts[0]);
        DB.streams = parseCSV(texts[3]);
        DB.news = parseCSV(texts[4]);
        
        DB.playersArr.forEach(p => DB.players[String(p.player_id).trim()] = p);
        parseCSV(texts[1]).forEach(l => DB.levels[String(l.level_id).trim()] = l);
        parseCSV(texts[2]).forEach(r => { 
            const lId = String(r.level_id).trim(); 
            const pos = parseInt(r.position) || 9999; 
            if (!DB.rankings[lId] || pos < DB.rankings[lId]) DB.rankings[lId] = pos; 
        });

        renderSidebars();
        if(document.getElementById('footer')) document.getElementById('footer').style.opacity = '1';
    } catch (err) { console.error("Ошибка:", err); }
}

function renderSidebars() {
    // 1. Топ игроков
    const lContainer = document.getElementById('leaderboard-list');
    if (lContainer) {
        const leadList = DB.playersArr.filter(p => p.is_banned !== 'TRUE' && p.is_banned !== 'true')
            .sort((a,b) => (parseInt(b.points)||0) - (parseInt(a.points)||0)).slice(0, 5);
        lContainer.innerHTML = leadList.map((p, i) => `
            <a href="player.html?id=${p.player_id}" class="block stream-card mb-1.5 border border-gray-200 p-2.5 hover:border-gray-500 hover:bg-gray-50 transition-all">
                <div class="flex items-center gap-2">
                    <span class="text-sm font-bold text-gray-500 w-5">#${i+1}</span>
                    <img src="images/flags/${(p.country||'WORLD').toLowerCase()}.gif" class="w-5 h-3 hltv-border" onerror="this.src='images/flags/WORLD.gif'">
                    <span class="text-sm font-bold text-gray-900">${p.nickname}</span>
                </div>
            </a>`).join('') + `<a href="leaderboard.html" class="block w-full text-center border border-gray-200 py-2 text-xs font-bold text-orange-600 hover:bg-orange-600 hover:text-white transition-all uppercase">Полный Список</a>`;
        lContainer.classList.add('animate-list-fade');
    }

    // 2. Стримы
    const sContainer = document.getElementById('streams-list');
    if (sContainer) {
        sContainer.innerHTML = DB.streams.slice(0, 5).map(s => {
            const isLive = String(s.is_live).trim().toUpperCase() === 'LIVE';
            return `<div class="stream-card mb-3 border border-gray-200 bg-white">
                <div class="px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors" onclick="toggleDropdown(this)">
                    <div class="flex items-center mb-1.5">
                        <span class="flex items-center text-[10px] font-bold uppercase ${isLive ? 'text-red-500' : 'text-gray-400'}">
                            <span class="w-2 h-2 rounded-full mr-1.5 inline-block ${isLive ? 'bg-red-500 animate-pulse' : 'bg-gray-400'}"></span>
                            ${isLive ? 'LIVE' : 'OFFLINE'}
                        </span>
                    </div>
                    <div class="flex justify-between items-center mb-1">
                        <div class="flex items-center gap-2">
                            <span class="text-sm font-bold text-gray-900 truncate max-w-[140px]">${s.streamer_name || 'Streamer'}</span>
                        </div>
                    </div>
                    <div class="text-xs text-gray-600 font-medium truncate">${s.level_name || 'Level'} — <span class="font-bold text-gray-900">${s.progress || '0'}%</span></div>
                </div>
                <div class="dropdown-menu px-4 pb-3" style="display: none;">
                    <a href="${s.link}" target="_blank" class="block w-full bg-orange-600 text-white font-bold py-2 rounded text-[12px] uppercase text-center hover:bg-orange-700">СЛЕДИТЬ</a>
                </div>
            </div>`;
        }).join('');
        sContainer.classList.add('animate-list-fade');
    }

    // 3. Новости
    const nContainer = document.getElementById('news-list');
    if (nContainer) {
        nContainer.innerHTML = DB.news.slice(-5).reverse().map((n, i) => `
            <a href="news.html#news-${DB.news.length - 1 - i}" class="stream-card block mb-3 border border-gray-200 p-4 hover:border-gray-400 hover:bg-gray-50 transition-all">
                <div class="text-[12px] font-bold text-orange-500 uppercase tracking-wider mb-1">${n.date || 'NEWS'}</div>
                <div class="text-sm font-bold text-gray-900 leading-tight">${n.title || 'Заголовок'}</div>
            </a>`).join('');
        nContainer.classList.add('animate-list-fade');
    }
}

function toggleDropdown(el) { const menu = el.closest('.stream-card').querySelector('.dropdown-menu'); menu.style.display = menu.style.display === 'block' ? 'none' : 'block'; }
initApp();