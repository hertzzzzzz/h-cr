function renderTopLevels(levelsArray) {
            const container = document.getElementById('top-levels-list');
            if (!container) return;
            
            const top5 = levelsArray
                .filter(l => (l.info || '').toLowerCase().includes('demonlist') && parseFloat(l.points) > 0)
                .sort((a, b) => parseFloat(b.points) - parseFloat(a.points))
                .slice(0, 5);

            container.innerHTML = top5.map((item, index) => {
                return `
                    <!-- ИСПРАВЛЕНА ССЫЛКА ЗДЕСЬ -->
                    <a href="level?id=${item.level_id}" class="block stream-card mb-1.5 border border-gray-200 p-2.5 hover:border-gray-500 hover:bg-gray-50 transition-all">
                        <div class="flex items-center gap-2">
                            <span class="text-sm font-bold text-gray-500 w-5">#${index + 1}</span>
                            <span class="text-sm font-bold text-gray-900 truncate">${item.name}</span>
                        </div>
                    </a>`;
            }).join('') + `<a href="top" class="block w-full text-center border border-gray-200 py-2 text-xs font-bold text-orange-600 hover:bg-orange-600 hover:text-white transition-all uppercase">Полный Список</a>`;
            
            container.classList.add('animate-list-fade');
        }