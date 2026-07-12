// --- КОНФИГУРАЦИЯ URL (Ваши данные) ---
const SHEET_URL_1 = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=164268489&single=true&output=csv';
const SHEET_URL_2 = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=306922452&single=true&output=csv';
const NEWS_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=30512158&single=true&output=csv';
const STREAMS_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=781157227&single=true&output=csv';
const LEADERBOARD_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTCNytbZ_R5TV-BfA1M2m0HiEe_C5FwfMlOCWWIu7gK9iOB48uKOnohrv6xTMqVmmjtB3d5XrISE4p9/pub?gid=299902186&single=true&output=csv';

// --- ДАННЫЕ РЕЙТИНГА ---
const officialScores = [350, 331.71, 313.42, 291.7, 271.78, 252.88, 235.0, 218.14, 202.3, 187.49, 173.69, 160.91, 149.15, 138.41, 128.69, 119.99, 112.31, 105.65, 99.01, 93.39, 87.79, 83.21, 78.65, 75.11, 71.59, 68.09, 65.61, 63.15, 60.71, 58.29, 56.89, 55.51, 54.15, 52.81, 51.49, 50.19, 48.91, 47.65, 46.41, 45.19, 44.99, 43.81, 42.65, 41.51, 40.39, 39.29, 38.21, 37.15, 36.11, 35.09, 34.09, 33.11, 32.15, 31.21, 30.29, 29.39, 28.51, 27.65, 26.81, 25.99, 25.19, 24.41, 23.65, 22.91, 22.19, 21.49, 20.81, 20.15, 19.51, 18.89, 18.29, 17.71, 17.15, 16.61, 16.09, 15.59, 15.11, 14.65, 14.21, 13.79, 13.39, 13.01, 12.65, 12.31, 11.99, 11.69, 11.41, 11.15, 10.91, 10.69, 10.49, 10.31, 10.15, 10.01, 9.89, 9.79, 9.71, 9.65, 9.61, 9.59, 9.59, 9.61, 9.65, 9.71, 9.79, 9.89, 10.01, 10.15, 10.31, 10.49, 10.69, 10.91, 11.15, 11.41, 11.69, 11.99, 12.31, 12.65, 13.01, 13.39, 13.79, 14.21, 14.65, 15.11, 15.59, 16.09, 16.61, 17.15, 17.71, 18.29, 18.89, 19.51, 20.15, 20.81, 21.49, 22.19, 22.91, 23.65, 24.41, 25.19, 25.99, 26.81, 27.65, 28.51, 29.39, 30.29, 31.21, 32.15, 33.11, 34.09];
const officialScoresh = [1000, 750, 500, 291.7, 271.78, 252.88, 235.0, 218.14, 202.3, 187.49, 173.69, 160.91, 149.15, 138.41, 128.69, 119.99, 112.31, 105.65, 99.01, 93.39, 87.79, 83.21, 78.65, 75.11, 71.59, 68.09, 65.61, 63.15, 60.71, 58.29, 56.89, 55.51, 54.15, 52.81, 51.49, 50.19, 48.91, 47.65, 46.41, 45.19, 44.99, 43.81, 42.65, 41.51, 40.39, 39.29, 38.21, 37.15, 36.11, 35.09, 34.09, 33.11, 32.15, 31.21, 30.29, 29.39, 28.51, 27.65, 26.81, 25.99, 25.19, 24.41, 23.65, 22.91, 22.19, 21.49, 20.81, 20.15, 19.51, 18.89, 18.29, 17.71, 17.15, 16.61, 16.09, 15.59, 15.11, 14.65, 14.21, 13.79, 13.39, 13.01, 12.65, 12.31, 11.99, 11.69, 11.41, 11.15, 10.91, 10.69, 10.49, 10.31, 10.15, 10.01, 9.89, 9.79, 9.71, 9.65, 9.61, 9.59, 9.59, 9.61, 9.65, 9.71, 9.79, 9.89, 10.01, 10.15, 10.31, 10.49, 10.69, 10.91, 11.15, 11.41, 11.69, 11.99, 12.31, 12.65, 13.01, 13.39, 13.79, 14.21, 14.65, 15.11, 15.59, 16.09, 16.61, 17.15, 17.71, 18.29, 18.89, 19.51, 20.15, 20.81, 21.49, 22.19, 22.91, 23.65, 24.41, 25.19, 25.99, 26.81, 27.65, 28.51, 29.39, 30.29, 31.21, 32.15, 33.11, 34.09];

let currentMode = 'pointercrate';

// --- ЭКСПОРТ ФУНКЦИЙ В WINDOW ---
// Это гарантирует, что HTML-кнопки их увидят
window.changeRatingSystem = function(mode) {
    currentMode = mode;
    console.log("Режим:", mode);
    loadLevels(SHEET_URL_1, 'levels-list-tab1');
    loadLevels(SHEET_URL_2, 'levels-list-tab2');
};

window.switchTab = function(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    document.querySelectorAll('button[id^="btn-"]').forEach(btn => {
        btn.classList.remove('border-orange-500', 'text-orange-600');
        btn.classList.add('border-transparent', 'text-gray-500');
    });
    document.getElementById(tabId).classList.remove('hidden');
    document.getElementById('btn-' + tabId).classList.add('border-orange-500', 'text-orange-600');
};

window.toggleDropdown = function() {
    const dropdown = document.getElementById('dropdown-menu');
    dropdown.classList.toggle('hidden');
};

// --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
function getFlag(country) {
    // Простая заглушка для флагов, можно дополнить логикой
    return country ? `🏳️ ${country}` : '';
}

async function loadLevels(url, elementId) {
    const container = document.getElementById(elementId);
    if (!container) return;
    
    try {
        const response = await fetch(url);
        const data = await response.text();
        const rows = data.split('\n').slice(1); // Пропускаем заголовок
        
        let html = '';
        rows.forEach((row, index) => {
            const cols = row.split(',');
            if (cols.length < 3) return;
            
            const name = cols[0];
            const creator = cols[1];
            const pos = index + 1;
            
            // Расчет очков
            const scoreSystem = (currentMode === 'pointercrate') ? officialScores : officialScoresh;
            const points = (pos <= scoreSystem.length) ? scoreSystem[pos - 1] : 0;
            
            html += `<div class="p-2 border-b">#${pos} - ${name} (${creator}) - <b>${points.toFixed(2)} pts</b></div>`;
        });
        
        container.innerHTML = html;
    } catch (e) {
        console.error("Ошибка загрузки данных:", e);
        container.innerHTML = 'Ошибка загрузки...';
    }
}

// Заглушки для других разделов, чтобы скрипт не падал при вызове
function loadNews() { console.log("News loaded"); }
function loadStreams() { console.log("Streams loaded"); }
function loadLeaderboard() { console.log("Leaderboard loaded"); }

// --- ИНИЦИАЛИЗАЦИЯ ---
document.addEventListener('DOMContentLoaded', () => {
    loadNews();
    loadStreams();
    loadLeaderboard();
    loadLevels(SHEET_URL_1, 'levels-list-tab1');
    loadLevels(SHEET_URL_2, 'levels-list-tab2');
});