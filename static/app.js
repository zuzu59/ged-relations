/**
 * GED Relations — Frontend JavaScript
 *
 * Gère :
 * - Menu hamburger
 * - Recherche avec autocomplétion
 * - Prévisualisation des individus
 */

// =====================
// Menu Hamburger
// =====================

const menuBtn = document.getElementById('menuBtn');
const menuOverlay = document.getElementById('menuOverlay');
const menuClose = document.getElementById('menuClose');

function openMenu() {
    menuOverlay.classList.add('active');
    menuBtn.setAttribute('aria-expanded', 'true');
    menuClose.focus();
    document.body.style.overflow = 'hidden';
}

function closeMenu() {
    menuOverlay.classList.remove('active');
    menuBtn.setAttribute('aria-expanded', 'false');
    menuBtn.focus();
    document.body.style.overflow = '';
}

if (menuBtn) {
    menuBtn.addEventListener('click', () => {
        if (menuOverlay.classList.contains('active')) {
            closeMenu();
        } else {
            openMenu();
        }
    });
}

if (menuClose) {
    menuClose.addEventListener('click', closeMenu);
}

if (menuOverlay) {
    menuOverlay.addEventListener('click', (e) => {
        if (e.target === menuOverlay) {
            closeMenu();
        }
    });
}

// Fermer avec Échap
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menuOverlay.classList.contains('active')) {
        closeMenu();
    }
});

// =====================
// Recherche autocomplétion
// =====================

let searchTimeout = null;

function initSearch(inputId, resultsId, onSelected) {
    const input = document.getElementById(inputId);
    const results = document.getElementById(resultsId);
    const clearBtn = document.getElementById('clear' + inputId.slice(-1));

    if (!input || !results) return;

    // Afficher/masquer le bouton clear
    input.addEventListener('input', () => {
        if (clearBtn) {
            clearBtn.classList.toggle('visible', input.value.length > 0);
        }
    });

    // Debounce search
    input.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        const query = input.value.trim();

        if (query.length < 1) {
            hideResults(results);
            return;
        }

        searchTimeout = setTimeout(() => doSearch(query, results, inputId, onSelected), 200);
    });

    // Navigation clavier dans les résultats
    input.addEventListener('keydown', (e) => {
        const items = results.querySelectorAll('.search-result-item');
        const visibleItems = [...items].filter(i => !i.hidden);
        if (visibleItems.length === 0) return;

        const activeIdx = visibleItems.indexOf(document.activeElement);

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const next = activeIdx < visibleItems.length - 1 ? activeIdx + 1 : 0;
            visibleItems[next].focus();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            const prev = activeIdx > 0 ? activeIdx - 1 : visibleItems.length - 1;
            visibleItems[prev].focus();
        } else if (e.key === 'Enter' && activeIdx >= 0) {
            e.preventDefault();
            visibleItems[activeIdx].click();
        }
    });

    // Cacher les résultats quand on clique ailleurs
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !results.contains(e.target)) {
            hideResults(results);
        }
    });
}

function doSearch(query, resultsContainer, inputId, onSelected) {
    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(resp => resp.json())
        .then(data => {
            if (!data || data.length === 0) {
                hideResults(resultsContainer);
                return;
            }
            renderResults(data, resultsContainer, onSelected);
        })
        .catch(() => {
            hideResults(resultsContainer);
        });
}

function renderResults(data, container, onSelected) {
    container.innerHTML = '';

    data.forEach(ind => {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.tabIndex = 0;
        item.setAttribute('role', 'option');
        item.dataset.id = ind.id;

        const dateInfo = [];
        if (ind.birth_date) dateInfo.push(ind.birth_date);
        if (ind.death_date) dateInfo.push(ind.death_date);

        const parentInfo = [];
        if (ind.father_name) parentInfo.push('père: ' + ind.father_name);
        if (ind.mother_name) parentInfo.push('mère: ' + ind.mother_name);

        item.innerHTML = `
            <div class="search-result-item__name">${escapeHtml(ind.full_name)}</div>
            <div class="search-result-item__info">
                ${dateInfo.map(d => `<span>📅 ${escapeHtml(d)}</span>`).join('')}
                ${parentInfo.map(p => `<span>👨‍👩‍👧 ${escapeHtml(p)}</span>`).join('')}
            </div>
        `;

        item.addEventListener('click', () => {
            // Remplir l'input avec le nom complet
            const input = document.getElementById(
                inputId === 'results1' ? 'person1' :
                inputId === 'results2' ? 'person2' : inputId
            );
            if (input) {
                input.value = ind.full_name;
            }
            hideResults(container);
            onSelected(ind);
        });

        item.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                item.click();
            }
        });

        container.appendChild(item);
    });

    container.hidden = false;
}

function hideResults(container) {
    container.innerHTML = '';
    container.hidden = true;
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
