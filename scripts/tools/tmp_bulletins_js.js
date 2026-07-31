
// EXACT CONFIGURATION FROM THE PROVIDED IMAGE
const DEFAULT_BRANCHES = [
  { type: 'domain', domain: 'DOMAINE DES SCIENCES', name: '', max_period_1: 0, max_exam_1: 0 },
  { type: 'subdomain', subdomain: 'Sous domaine des mathématiques', name: '', max_period_1: 0, max_exam_1: 0 },
  { type: 'branch', domain: 'DOMAINE DES SCIENCES', subdomain: 'Sous domaine des mathématiques', name: 'Algèbre', max_period_1: 30, max_exam_1: 60 },
  { type: 'branch', domain: 'DOMAINE DES SCIENCES', subdomain: 'Sous domaine des mathématiques', name: 'Arithmétique', max_period_1: 10, max_exam_1: 20 },
  { type: 'branch', domain: 'DOMAINE DES SCIENCES', subdomain: 'Sous domaine des mathématiques', name: 'Géométrie', max_period_1: 20, max_exam_1: 40 },
  { type: 'branch', domain: 'DOMAINE DES SCIENCES', subdomain: 'Sous domaine des mathématiques', name: 'Statistique', max_period_1: 10, max_exam_1: 20 },
  { type: 'branch', domain: 'DOMAINE DES SCIENCES', subdomain: 'Sous domaine des mathématiques', name: 'Sous total', max_period_1: 70, max_exam_1: 140 },
  
  { type: 'subdomain', subdomain: 'Sous domaine des sciences de la vie et de la terre', name: '', max_period_1: 0, max_exam_1: 0 },
  { type: 'branch', domain: 'DOMAINE DES SCIENCES', subdomain: 'Sous domaine des sciences de la vie', name: 'Anatomie', max_period_1: 10, max_exam_1: 20 },
  { type: 'branch', domain: 'DOMAINE DES SCIENCES', subdomain: 'Sous domaine des sciences de la vie', name: 'Botanique', max_period_1: 10, max_exam_1: 20 },
  { type: 'branch', domain: 'DOMAINE DES SCIENCES', subdomain: 'Sous domaine des sciences de la vie', name: 'Zoologie', max_period_1: 20, max_exam_1: 40 },
  { type: 'branch', domain: 'DOMAINE DES SCIENCES', subdomain: 'Sous domaine des sciences de la vie', name: 'Sous total', max_period_1: 40, max_exam_1: 80 },
  
  { type: 'subdomain', subdomain: 'Sous domaine des sciences Physiques, Technologie et Tic', name: '', max_period_1: 0, max_exam_1: 0 },
  { type: 'branch', domain: 'DOMAINE DES SCIENCES', subdomain: 'Sous domaine Physique/TIC', name: 'Sciences Physiques', max_period_1: 10, max_exam_1: 20 },
  { type: 'branch', domain: 'DOMAINE DES SCIENCES', subdomain: 'Sous domaine Physique/TIC', name: 'Technologie', max_period_1: 10, max_exam_1: 20 },
  { type: 'branch', domain: 'DOMAINE DES SCIENCES', subdomain: 'Sous domaine Physique/TIC', name: "Techno d'info & Com(TIC)", max_period_1: 10, max_exam_1: 20 },
  { type: 'branch', domain: 'DOMAINE DES SCIENCES', subdomain: 'Sous domaine Physique/TIC', name: 'Sous total', max_period_1: 30, max_exam_1: 60 },
  
  { type: 'domain', domain: 'DOMAINE DES LANGUES', name: '', max_period_1: 0, max_exam_1: 0 },
  { type: 'branch', domain: 'DOMAINE DES LANGUES', subdomain: '', name: 'Anglais', max_period_1: 30, max_exam_1: 60 },
  { type: 'branch', domain: 'DOMAINE DES LANGUES', subdomain: '', name: 'Français', max_period_1: 50, max_exam_1: 100 },
  { type: 'branch', domain: 'DOMAINE DES LANGUES', subdomain: '', name: 'Sous total', max_period_1: 80, max_exam_1: 160 },
  
  { type: 'domain', domain: "DOMAINE DE L'UNIVERS SOCIAL ET ENVIRONNEMENT", name: '', max_period_1: 0, max_exam_1: 0 },
  { type: 'branch', domain: 'DOMAINE UNIVERS SOCIAL', subdomain: '', name: 'Religion', max_period_1: 20, max_exam_1: 40 },
  { type: 'branch', domain: 'DOMAINE UNIVERS SOCIAL', subdomain: '', name: 'Éducation à la vie (1)', max_period_1: 20, max_exam_1: 40 },
  { type: 'branch', domain: 'DOMAINE UNIVERS SOCIAL', subdomain: '', name: 'Éducation civique et moral', max_period_1: 20, max_exam_1: 40 },
  { type: 'branch', domain: 'DOMAINE UNIVERS SOCIAL', subdomain: '', name: 'Géographie', max_period_1: 30, max_exam_1: 60 },
  { type: 'branch', domain: 'DOMAINE UNIVERS SOCIAL', subdomain: '', name: 'Histoire', max_period_1: 20, max_exam_1: 40 },
  { type: 'branch', domain: 'DOMAINE UNIVERS SOCIAL', subdomain: '', name: 'Sous total', max_period_1: 110, max_exam_1: 220 },
  
  { type: 'domain', domain: 'DOMAINE DES ARTS', name: '', max_period_1: 0, max_exam_1: 0 },
  { type: 'branch', domain: 'DOMAINE DES ARTS', subdomain: '', name: 'Dessin', max_period_1: 20, max_exam_1: 40 },
  { type: 'branch', domain: 'DOMAINE DES ARTS', subdomain: '', name: 'Musique', max_period_1: 20, max_exam_1: 40 },
  { type: 'branch', domain: 'DOMAINE DES ARTS', subdomain: '', name: 'Sous total', max_period_1: 40, max_exam_1: 80 },
  
  { type: 'domain', domain: 'DOMAINE DU DEVELOPPEMENT PERSONNEL', name: '', max_period_1: 0, max_exam_1: 0 },
  { type: 'branch', domain: 'DOMAINE DEV PERSONNEL', subdomain: '', name: 'Éducation Physique', max_period_1: 20, max_exam_1: 40 },
  { type: 'branch', domain: 'DOMAINE DEV PERSONNEL', subdomain: '', name: 'Sous total', max_period_1: 20, max_exam_1: 40 }
];

let currentBranches = buildPreviewBranches([...DEFAULT_BRANCHES]).branches;
const ADMIN_API_PREFIX = '{{ request.path.rsplit("/admin", 1)[0] }}/admin';

function createZeroMaxima() {
    return {
        maxPeriod: 0,
        maxExam: 0,
        semesterTotal: 0,
        generalTotal: 0
    };
}

function toNumber(value, fallback = 0) {
    const parsed = parseFloat(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}

function normalizeBranchMaxima(branch) {
    const normalized = { ...branch };

    if (normalized.type === 'branch') {
        const maxPeriod = toNumber(normalized.max_period_1);
        const maxExam = toNumber(normalized.max_exam_1);
        normalized.max_period_1 = maxPeriod;
        normalized.max_period_2 = maxPeriod;
        normalized.max_period_3 = maxPeriod;
        normalized.max_period_4 = maxPeriod;
        normalized.max_exam_1 = maxExam;
        normalized.max_exam_2 = maxExam;
    } else {
        normalized.max_period_1 = 0;
        normalized.max_period_2 = 0;
        normalized.max_period_3 = 0;
        normalized.max_period_4 = 0;
        normalized.max_exam_1 = 0;
        normalized.max_exam_2 = 0;
    }

    return normalized;
}

function addMaxima(target, source) {
    target.maxPeriod += source.maxPeriod || 0;
    target.maxExam += source.maxExam || 0;
    target.semesterTotal += source.semesterTotal || 0;
    target.generalTotal += source.generalTotal || 0;
    return target;
}

function computeBranchMaxima(branch) {
    const maxPeriod = toNumber(branch.max_period_1);
    const maxExam = toNumber(branch.max_exam_1);
    const semesterTotal = (maxPeriod * 2) + maxExam;

    return {
        maxPeriod,
        maxExam,
        semesterTotal,
        generalTotal: semesterTotal * 2
    };
}

function isSubtotalBranch(branch) {
    const name = String(branch?.name || '').trim().toLowerCase();
    return branch?.type === 'branch' && /sous[\s-]*total|subtotal/.test(name);
}

function buildPreviewBranches(branches) {
    const previewBranches = [];
    const totals = createZeroMaxima();
    let groupTotals = createZeroMaxima();
    let hasGroupBranches = false;

    branches.forEach(branch => {
        const previewBranch = normalizeBranchMaxima(branch);

        if (previewBranch.type !== 'branch') {
            previewBranches.push(previewBranch);
            return;
        }

        if (isSubtotalBranch(previewBranch)) {
            const subtotalMaxima = hasGroupBranches ? { ...groupTotals } : computeBranchMaxima(previewBranch);
            previewBranch.max_period_1 = subtotalMaxima.maxPeriod;
            previewBranch.max_period_2 = subtotalMaxima.maxPeriod;
            previewBranch.max_exam_1 = subtotalMaxima.maxExam;
            previewBranch.max_period_3 = subtotalMaxima.maxPeriod;
            previewBranch.max_period_4 = subtotalMaxima.maxPeriod;
            previewBranch.max_exam_2 = subtotalMaxima.maxExam;
            previewBranch.previewMaxima = subtotalMaxima;
            addMaxima(totals, subtotalMaxima);
            groupTotals = createZeroMaxima();
            hasGroupBranches = false;
        } else {
            previewBranch.previewMaxima = computeBranchMaxima(previewBranch);
            addMaxima(groupTotals, previewBranch.previewMaxima);
            hasGroupBranches = true;
        }

        previewBranches.push(previewBranch);
    });

    if (hasGroupBranches) {
        addMaxima(totals, groupTotals);
    }

    return { branches: previewBranches, totals };
}

async function loadLevels(preselectedLevel = '') {
    const sectionRef = document.getElementById('sectionSelect').value;
    const levelInput = document.getElementById('levelInput');
    if (!sectionRef) {
        levelInput.innerHTML = '<option value="">Niveau...</option>';
        levelInput.disabled = true;
        updateSectionSummary([]);
        return;
    }
    const schoolId = new URLSearchParams(window.location.search).get('school_id');
    const query = schoolId ? `?school_id=${encodeURIComponent(schoolId)}` : '';
    try {
        const response = await fetch(`${ADMIN_API_PREFIX}/api/bulletin-levels/${encodeURIComponent(sectionRef)}${query}`);
        if (!response.ok) {
            throw new Error(`Échec du chargement des niveaux: ${response.status}`);
        }
        const levels = await response.json();
        levelInput.innerHTML = '<option value="">Niveau...</option>';
        levels.forEach(l => {
            const selected = preselectedLevel && preselectedLevel === l.level ? ' selected' : '';
            levelInput.innerHTML += `<option value="${l.level}"${selected}>${l.level}</option>`;
        });
        updateSectionSummary(levels);
        levelInput.disabled = false;
        if (preselectedLevel) {
            levelInput.value = preselectedLevel;
        } else if (levels.length === 1) {
            levelInput.value = levels[0].level;
        } else {
            levelInput.value = '';
        }
        const currentLevel = levelInput.value || '';
        updateUrlQueryParams({ section_name: sectionRef, level: currentLevel, school_id: schoolId || '' });
        if (levelInput.value) {
            loadConfig();
        }
    } catch (e) {
        console.error(e);
        updateSectionSummary([]);
    }
}

function updateUrlQueryParams(params) {
    const url = new URL(window.location.href);
    Object.keys(params).forEach(key => {
        const value = params[key];
        if (value === null || value === undefined || value === '') {
            url.searchParams.delete(key);
        } else {
            url.searchParams.set(key, value);
        }
    });
    window.history.replaceState({}, '', url.toString());
}

function updateSectionSummary(levels) {
    const summaryLevels = levels.map(l => l.level).join(', ') || 'Aucun';
    const classesSet = new Set();
    levels.forEach(l => {
        if (Array.isArray(l.classes)) {
            l.classes.forEach(c => classesSet.add(c));
        }
    });
    const summaryClasses = Array.from(classesSet).sort().join(', ') || 'Aucune';
    document.getElementById('sectionLevelsSummary').textContent = summaryLevels;
    document.getElementById('sectionClassesSummary').textContent = summaryClasses;

    const detailsEl = document.getElementById('sectionLevelDetails');
    if (!levels.length) {
        detailsEl.innerHTML = '<em>Sélectionnez une section pour afficher les niveaux et classes.</em>';
        return;
    }

    const lines = levels.map(l => {
        const classes = Array.isArray(l.classes) && l.classes.length ? l.classes.join(', ') : 'Aucune classe configurée';
        return `<div><strong>${l.level}:</strong> ${classes}</div>`;
    });
    detailsEl.innerHTML = lines.join('');
}

function isLevel4Bulletin() {
    const levelInput = document.getElementById('levelInput');
    return levelInput && String(levelInput.value).trim() === '4';
}

function updateValidationStatus(data) {
    const statusText = document.getElementById('validationStatusText');
    const validateButton = document.getElementById('validateButton');
    if (!data || !data.id) {
        statusText.textContent = 'Aucune configuration chargée';
        if (validateButton) validateButton.disabled = true;
        return;
    }

    if (data.validated) {
        statusText.textContent = `Validé le ${new Date(data.validated_at).toLocaleString()} par ${data.validated_by || 'utilisateur'}`;
        if (validateButton) validateButton.disabled = true;
    } else {
        statusText.textContent = 'Non validé';
        if (validateButton) validateButton.disabled = false;
    }
}

async function loadConfig() {
    const sectionId = document.getElementById('sectionSelect').value;
    const level = document.getElementById('levelInput').value;
    if (!sectionId || !level) return;
    const schoolId = new URLSearchParams(window.location.search).get('school_id');
    const query = schoolId ? `?school_id=${encodeURIComponent(schoolId)}` : '';
    updateUrlQueryParams({ section_name: sectionId, level, school_id: schoolId || '' });
    try {
        const response = await fetch(`${ADMIN_API_PREFIX}/api/bulletin-config/${encodeURIComponent(sectionId)}/${encodeURIComponent(level)}${query}`);
        if (response.ok) {
            const data = await response.json();
            currentBranches = buildPreviewBranches(data.branches || []).branches;
            updateValidationStatus(data);
        } else {
            currentBranches = buildPreviewBranches([...DEFAULT_BRANCHES]).branches;
            updateValidationStatus(null);
        }
        renderTable();
        updatePreview();
    } catch (e) { 
        currentBranches = buildPreviewBranches([...DEFAULT_BRANCHES]).branches;
        renderTable();
        updatePreview();
        updateValidationStatus(null);
    }
}

function renderTable() {
    const tbody = document.getElementById('branchRows');
    tbody.innerHTML = '';
    currentBranches.forEach((b, idx) => {
        const tr = document.createElement('tr');
        const isDomain = b.type === 'domain';
        const isSub = b.type === 'subdomain';
        
        tr.innerHTML = `
            <td class="text-muted small">${idx + 1}</td>
            <td>
                <input type="text" class="branch-input ${isDomain ? 'fw-bold bg-dark text-white' : (isSub ? 'fst-italic bg-light' : '')}" 
                       value="${isDomain ? b.domain : (isSub ? b.subdomain : b.name)}" 
                       onchange="updateBranchData(${idx}, this.value)">
            </td>
            <td><input type="number" class="branch-input max-input" value="${b.max_period_1}" onchange="updateBranchField(${idx}, 'max_period_1', this.value)"></td>
            <td><input type="number" class="branch-input max-input" value="${b.max_exam_1}" onchange="updateBranchField(${idx}, 'max_exam_1', this.value)"></td>
            <td class="text-end" style="width: 240px;">
                <div class="d-flex flex-wrap gap-1 justify-content-end align-items-center">
                    ${b.entry_state === 'ns' ? '<span class="badge bg-danger" title="Cours non saisi">NS</span>' : ''}
                    <button class="btn btn-sm btn-outline-success" title="Insérer au-dessus" aria-label="Insérer au-dessus" onclick="insertRow(${idx}, -1)">
                        <i class="fas fa-arrow-up"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-success" title="Insérer en dessous" aria-label="Insérer en dessous" onclick="insertRow(${idx}, 1)">
                        <i class="fas fa-arrow-down"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-primary" title="Monter" aria-label="Monter" onclick="moveRow(${idx}, -1)">
                        <i class="fas fa-angle-double-up"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-primary" title="Descendre" aria-label="Descendre" onclick="moveRow(${idx}, 1)">
                        <i class="fas fa-angle-double-down"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" title="Supprimer" aria-label="Supprimer" onclick="removeRow(${idx})">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function updateBranchData(idx, val) {
    if (currentBranches[idx].type === 'domain') currentBranches[idx].domain = val;
    else if (currentBranches[idx].type === 'subdomain') currentBranches[idx].subdomain = val;
    else currentBranches[idx].name = val;
    updatePreview();
}

function updateBranchField(idx, field, val) {
    const numericValue = parseFloat(val) || 0;
    currentBranches[idx][field] = numericValue;
    if (field === 'max_period_1') {
        currentBranches[idx].max_period_2 = numericValue;
        currentBranches[idx].max_period_3 = numericValue;
        currentBranches[idx].max_period_4 = numericValue;
    }
    if (field === 'max_exam_1') {
        currentBranches[idx].max_exam_2 = numericValue;
    }
    updatePreview();
}

function createRowLike(referenceRow = {}) {
    const type = referenceRow.type || 'branch';

    if (type === 'domain') {
        return {
            type: 'domain',
            domain: referenceRow.domain || 'Nouveau domaine',
            name: '',
            max_period_1: 0,
            max_exam_1: 0
        };
    }

    if (type === 'subdomain') {
        return {
            type: 'subdomain',
            subdomain: referenceRow.subdomain || 'Nouveau sous-domaine',
            name: '',
            max_period_1: 0,
            max_exam_1: 0
        };
    }

    return {
        type: 'branch',
        domain: referenceRow.domain || '',
        subdomain: referenceRow.subdomain || '',
        name: 'Nouvelle Branche',
        max_period_1: Number(referenceRow.max_period_1 ?? 10),
        max_period_2: Number(referenceRow.max_period_1 ?? 10),
        max_exam_1: Number(referenceRow.max_exam_1 ?? 20),
        max_period_3: Number(referenceRow.max_period_1 ?? 10),
        max_period_4: Number(referenceRow.max_period_1 ?? 10),
        max_exam_2: Number(referenceRow.max_exam_1 ?? 20)
    };
}

function insertRow(idx, direction) {
    const referenceRow = currentBranches[idx] || {};
    const newRow = createRowLike(referenceRow);
    const insertIndex = direction < 0 ? idx : idx + 1;
    currentBranches.splice(insertIndex, 0, newRow);
    renderTable();
    updatePreview();
}

// Add custom functions
function addRow() {
    const referenceRow = currentBranches[currentBranches.length - 1] || {};
    currentBranches.push(createRowLike({ ...referenceRow, type: 'branch' }));
    renderTable();
    updatePreview();
}

function addDomain() {
    const referenceRow = currentBranches[currentBranches.length - 1] || {};
    currentBranches.push(createRowLike({ ...referenceRow, type: 'domain' }));
    renderTable();
    updatePreview();
}

function addSubdomain() {
    const referenceRow = currentBranches[currentBranches.length - 1] || {};
    currentBranches.push(createRowLike({ ...referenceRow, type: 'subdomain' }));
    renderTable();
    updatePreview();
}

function addSubtotal() {
    const referenceRow = currentBranches[currentBranches.length - 1] || {};
    const newSubtotal = {
        type: 'branch',
        domain: referenceRow.domain || '',
        subdomain: referenceRow.subdomain || '',
        name: 'Sous total',
        max_period_1: 0,
        max_period_2: 0,
        max_period_3: 0,
        max_period_4: 0,
        max_exam_1: 0,
        max_exam_2: 0
    };
    currentBranches.push(newSubtotal);
    renderTable();
    updatePreview();
}

function removeRow(idx) {
    currentBranches.splice(idx, 1);
    renderTable();
    updatePreview();
}

// Re-order rows
function moveRow(idx, dir) {
    const newIdx = idx + dir;
    if (newIdx < 0 || newIdx >= currentBranches.length) return;
    const temp = currentBranches[idx];
    currentBranches[idx] = currentBranches[newIdx];
    currentBranches[newIdx] = temp;
    renderTable();
    updatePreview();
}

async function saveConfiguration() {
    const sectionValue = document.getElementById('sectionSelect').value;
    const level = document.getElementById('levelInput').value.trim();
    if (!sectionValue || !level) { alert('Sélectionnez une section et un niveau'); return; }
    try {
        const branchesToSave = buildPreviewBranches(currentBranches).branches.map(branch => {
            const { previewMaxima, ...cleanBranch } = branch;
            return cleanBranch;
        });
        const body = { level: level, branches: branchesToSave };
        const parsedSectionId = Number.parseInt(sectionValue, 10);
        if (!Number.isNaN(parsedSectionId)) {
            body.section_id = parsedSectionId;
        } else {
            body.section_name = sectionValue;
        }
        const res = await fetch(`${ADMIN_API_PREFIX}/api/bulletin-config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (res.ok) {
            const data = await res.json();
            alert('Configuration sauvegardée !');
            if (data.courses_url) {
                window.location.href = data.courses_url;
                return;
            }
        }
    } catch (e) { alert('Erreur lors de la sauvegarde'); }
}

async function validateConfiguration() {
    const sectionValue = document.getElementById('sectionSelect').value;
    const level = document.getElementById('levelInput').value.trim();
    if (!sectionValue || !level) { alert('Sélectionnez une section et un niveau avant de valider'); return; }

    try {
        const body = { level: level };
        const parsedSectionId = Number.parseInt(sectionValue, 10);
        if (!Number.isNaN(parsedSectionId)) {
            body.section_id = parsedSectionId;
        } else {
            body.section_name = sectionValue;
        }
        const res = await fetch(`${ADMIN_API_PREFIX}/api/bulletin-config/validate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (res.ok) {
            const data = await res.json();
            updateValidationStatus(data);
            alert('Configuration validée avec succès.');
        } else {
            const error = await res.text();
            alert(`Échec de la validation : ${error}`);
        }
    } catch (e) {
        console.error(e);
        alert('Erreur lors de la validation');
    }
}

function updatePreview() {
    const area = document.getElementById('previewArea');
    const level = document.getElementById('levelInput').value || '7';
    
    const sectionSelect = document.getElementById('sectionSelect');
    const selectedOption = sectionSelect.options[sectionSelect.selectedIndex];
    const sectionName = selectedOption ? selectedOption.text : '';
    
    let cycleTitle = "CYCLE TERMINAL DE L'EDUCATION DE BASE (CTEB)";
    if (sectionName && !sectionName.toLowerCase().includes('education de base') && !sectionName.toLowerCase().includes('éducation de base')) {
        cycleTitle = "HUMANITES / " + sectionName.toUpperCase();
    }
    
    const currentAcademicYear = "{{ current_academic_year }}";
    const currentMinistry = {{ ((school.ministry if school else None) or "MINISTERE DE L'ENSEIGNEMENT PRIMAIRE, SECONDAIRE ET TECHNIQUE")|tojson }};
    const currentProvince = {{ ((school.province if school else None) or "")|tojson }};
    const currentCity = {{ ((school.city if school else None) or "")|tojson }};
    const currentCommune = {{ ((school.commune if school else None) or "")|tojson }};
    const currentSchoolForBulletin = {{ ((school.bulletin_school_name if school else None) or (school.name if school else ""))|tojson }};
    const currentSchoolCode = {{ ((school.school_code if school else None) or "")|tojson }};
    
    let html = `
        <div id="bulletin-container">
            <!-- OUTER BORDER WRAPPER -->
            <div style="border: 1px solid #000; overflow: hidden;">
            <!-- TOP HEADER -->
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #000; padding: 4px;">
                    <img src="/static/img/drapeau.png" style="height: 50px;">
                    <div style="text-align: center; padding: 2px;">
                        <h5 style="font-size: 11px; margin: 0; font-weight: 900; text-transform: uppercase;">République Démocratique du Congo</h5>
                        <p style="font-size: 11px; margin: 0; font-weight: bold; text-transform: uppercase;">${currentMinistry}</p>
                    </div>
                    <img src="/static/img/embleme.png" style="height: 50px;">
            </div>
 
            <!-- ID SECTION -->
            <div style="border-bottom: 1px solid #000; padding: 2px;">
                <div style="display: flex; align-items: center; border-bottom: 1px solid #000; padding-bottom: 2px; margin-bottom: 2px;">
                    <span class="meta-label">N° ID</span>
                    <div style="margin-left: 10px;">${Array(15).fill('<div class="id-box"></div>').join('')}</div>
                </div>
                <div style="display: flex; align-items: center;">
                    <span class="meta-label">PROVINCE :</span>
                    <div class="meta-value">${currentProvince || ''}</div>
                </div>
            </div>
 
            <!-- PERSONAL INFO GRID -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; border-bottom: 1px solid #000; padding: 4px;">
                <div style="display: flex; flex-direction: column; gap: 2px;">
                    <div style="display: flex;"><span class="meta-label">VILLE :</span><div class="meta-value">${currentCity || ''}</div></div>
                    <div style="display: flex;"><span class="meta-label">COMMUNE :</span><div class="meta-value">${currentCommune || ''}</div></div>
                    <div style="display: flex;"><span class="meta-label">ECOLE :</span><div class="meta-value">${currentSchoolForBulletin || ''}</div></div>
                    <div style="display: flex; align-items: center;">
                        <span class="meta-label">CODE :</span>
                        <div style="margin-left: 5px;">${currentSchoolCode ? `<strong>${currentSchoolCode}</strong>` : Array(10).fill('<div class="id-box"></div>').join('')}</div>
                    </div>
                </div>
                <div style="display: flex; flex-direction: column; gap: 2px;">
                    <div style="display: flex;"><span class="meta-label">ELEVE :</span><div class="meta-value"></div><span class="meta-label" style="margin-left: 5px;">SEXE :</span><div class="meta-value" style="width: 30px;"></div></div>
                    <div style="display: flex;"><span class="meta-label">NE(E) A :</span><div class="meta-value">..../..../....</div><span class="meta-label" style="margin-left: 5px;">LE :</span><div class="meta-value" style="width: 120px;">Lieu de naissance</div></div>
                    <div style="display: flex;"><span class="meta-label">CLASSE :</span><div class="meta-value"></div></div>
                    <div style="display: flex; align-items: center;">
                        <span class="meta-label">N°PERM :</span>
                        <div style="margin-left: 5px;">${Array(8).fill('<div class="id-box"></div>').join('')}</div>
                    </div>
                </div>
            </div>
 
            <div style="text-align: center; font-size: 11px; font-weight: bold !important; padding: 2px; text-transform: uppercase;">
                <strong>BULLETIN DE LA ${level}<sup>ème</sup> ANNEE ${cycleTitle}<span style="margin-left: 8rem; font-weight: bold !important;">ANNEE SCOLAIRE ${currentAcademicYear}</span></strong>
            </div>
 
            <!-- MAIN TABLE -->
            <table class="bulletin-table">
                <thead>
                    <tr>
                        <th rowspan="3" class="branch-col">BRANCHES</th>
                        <th colspan="7">PREMIER SEMESTRE</th>
                        <th colspan="7">SECOND SEMESTRE</th>
                        <th colspan="2" rowspan="3" class="totg-col">TOT.<br>G</th>
                        ${isLevel4Bulletin() ?
                            `<th colspan="2" rowspan="3" class="rep-col" style="white-space: normal; font-size: 9px; text-align: center; vertical-align: middle;">EXAMEN<br>DE REP.</th>` :
                            `<th colspan="2" style="white-space: normal; font-size: 9px; text-align: center; vertical-align: middle;">EXAMEN<br>DE REP.</th>`
                        }
                    </tr>
                    <tr>
                        <th colspan="3">TRAVAUX<br>JOURNAL</th>
                        <th colspan="2" rowspan="2" class="exam-col">MAX<br>EXAM</th>
                        <th colspan="2" rowspan="2" class="tot-col">MAX<br>TOT</th>
                        <th colspan="3">TRAVAUX<br>JOURNAL</th>
                        <th colspan="2" rowspan="2" class="exam-col">MAX<br>EXAM</th>
                        <th colspan="2" rowspan="2" class="tot-col">MAX<br>TOT</th>
                        ${isLevel4Bulletin() ? '' : `<th rowspan="2" class="rep-col" style="width: 30px;">%</th><th rowspan="2" class="rep-col" style="white-space: normal; font-size: 9px; text-align: center; vertical-align: middle;">SIG.<br>PRF</th>`}
                    </tr>
                    <tr>
                        <th class="narrow-col">MAX</th><th class="narrow-col">1 P</th><th class="narrow-col">2 P</th>
                        <th class="narrow-col">MAX</th><th class="narrow-col">3 P</th><th class="narrow-col">4 P</th>
                    </tr>
                </thead>
                <tbody>
    `;
 
    const previewData = buildPreviewBranches(currentBranches);
    const previewBranches = previewData.branches;
    const totals = previewData.totals;

    let currentDomain = null, currentSubdomain = null;

    previewBranches.forEach((b, idx) => {
        if (b.type === 'domain') {
            const isSci = b.domain.toUpperCase().includes('SCIENCES');
            html += `<tr class="domain-row"><td colspan="17">${b.domain}</td><td colspan="2" style="background:#fff !important;"></td></tr>`;
            currentDomain = b.domain;
        } else if (b.type === 'subdomain') {
            const isMath = b.subdomain.toLowerCase().includes('mathématiques');
            html += `<tr class="subdomain-row"><td colspan="17">${b.subdomain}</td><td colspan="2" style="background:#fff !important;"></td></tr>`;
        } else {
            const maxima = b.previewMaxima || computeBranchMaxima(b);
            const maxPeriod = maxima.maxPeriod;
            const maxExam = maxima.maxExam;
            const semesterTotal = maxima.semesterTotal;
            const generalTotal = maxima.generalTotal;
            const isTotal = b.name.toLowerCase().includes('total');
            html += `
                <tr class="${isTotal?'total-row':''}">
                    <td class="branch-name-cell" style="text-align: left; padding-left: 5px;">${b.name}</td>
                    <td class="narrow-col">${maxPeriod || ''}</td><td class="narrow-col"></td><td class="narrow-col"></td><td class="exam-col">${maxExam || ''}</td><td class="exam-col"></td><td class="tot-col" style="background:#f2f2f2"><strong>${semesterTotal || ''}</strong></td><td class="tot-col"></td>
                    <td class="narrow-col">${maxPeriod || ''}</td><td class="narrow-col"></td><td class="narrow-col"></td><td class="exam-col">${maxExam || ''}</td><td class="exam-col"></td><td class="tot-col" style="background:#f2f2f2"><strong>${semesterTotal || ''}</strong></td><td class="tot-col"></td>
                    <td class="totg-col" style="background:#e6e6e6"><strong>${generalTotal || ''}</strong></td><td class="totg-col"></td>${isLevel4Bulletin() ? '<td class="rep-col" colspan="2"></td>' : '<td class="rep-col"></td><td class="rep-col"></td>'}
                </tr>
            `;
        }
    });
 
    // SUMMARY ROWS
    html += `
        <tr class="total-row summary-row">
            <td style="text-align: left; padding-left: 5px;">MAXIMA GENERAUX</td>
            <td class="narrow-col">${totals.maxPeriod || ''}</td><td class="narrow-col"></td><td class="narrow-col"></td><td class="exam-col">${totals.maxExam || ''}</td><td class="exam-col"></td><td class="tot-col" style="background:#f2f2f2">${totals.semesterTotal || ''}</td><td class="tot-col"></td>
            <td class="narrow-col">${totals.maxPeriod || ''}</td><td class="narrow-col"></td><td class="narrow-col"></td><td class="exam-col">${totals.maxExam || ''}</td><td class="exam-col"></td><td class="tot-col" style="background:#f2f2f2">${totals.semesterTotal || ''}</td><td class="tot-col"></td>
            <td class="totg-col" style="background:#e6e6e6">${totals.generalTotal || ''}</td>
            <td colspan="3" rowspan="6" class="decision-box">
                <div style="margin-bottom: 2px;">- Passe (1)</div>
                <div style="margin-bottom: 2px;">- Double (1)</div>
                <div style="margin-bottom: 6px;">- A échoué (1)</div>
                <div style="font-size: 11px;">Le ....../....../20....</div>
                <div style="text-align: center; font-weight: bold; margin-top: 12px;">
                    Le Chef d'Établissement<br><br>Sceau de l'École
                </div>
            </td>
        </tr>
    `;
 
    ['TOTAUX','POURCENTAGE','PLACE/NBRE ELEVES','APPLICATION','CONDUITE'].forEach((label, i) => {
        const slash = label.includes('PLACE');
        html += `<tr class="total-row summary-row"><td style="text-align: left; padding-left: 5px;">${label}</td>`;
        for(let j=0; j<15; j++) {
            let cls = 'tot-col';
            if ([0,1,2,7,8,9].includes(j)) cls = 'narrow-col';
            else if ([3,4,10,11].includes(j)) cls = 'exam-col';
            else if (j === 14) cls = 'totg-col';
             const isBlack = [0,3,5,9,10,12].includes(j);
            html += `<td class="${cls} ${isBlack?'black-cell':''}"> ${slash && [1,2,7,8,9].includes(j) ? '/' : ''} </td>`;
        }
        html += `</tr>`;
    });

    html += `
                <tr><td style="text-align: left; padding-left: 5px; height: 25px;">Signature du Responsable</td><td colspan="18"></td></tr>
                </tbody>
            </table>
            </div><!-- END OUTER BORDER WRAPPER -->

            <!-- FOOTER TEXT -->
            <div style="border: 1px solid #000; border-top: none; margin-top: 0; padding: 5px; font-size: 11px; line-height: 1.1;">
                <p style="margin: 0 0 2px 0;">- L'élève ne pourra passer dans la classe supérieure s'il n'a subi avec succès un examen de repêchage en : ................................................................</p>
                <div style="margin-top: 3px; margin-bottom: 1px;">- L'élève passe dans la classe supérieure (1)</div>
                <div style="margin-bottom: 1px;">- L'élève double sa classe (1)</div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                    <div>- L'élève a échoué (1)</div>
                    <div>Fait à ................................., le ......./......./20.....</div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 3px; font-weight: bold; text-align: center;">
                    <div style="width: 30%; text-decoration: underline;">Signature de l'élève</div>
                    <div style="width: 30%;">Sceau de l'école</div>
                    <div style="width: 30%; text-decoration: underline;">Le chef d'Etablissement</div>
                </div>
                <p style="margin-top: 8px; margin-bottom: 0; font-size: 11px;">(1) Biffer la mention inutile</p>
                <p style="margin: 0; font-size: 11px;">Note : le bulletin est sans valeur s'il est raturé ou surchargé. <span style="float: right;">IGE/PS/026</span></p>
            </div>
        </div>
    `;

    area.innerHTML = html;
}

function printBulletin() { window.print(); }

document.addEventListener('DOMContentLoaded', async () => {
    renderTable();
    updatePreview();
    const initialSectionName = {{ selected_section_name|tojson }};
    const initialLevel = {{ selected_level|tojson }};
    const sectionSelect = document.getElementById('sectionSelect');
    const levelInput = document.getElementById('levelInput');

    if (initialSectionName) {
        sectionSelect.value = initialSectionName;
        await loadLevels(initialLevel || '');
        if (initialLevel) {
            levelInput.value = initialLevel;
            await loadConfig();
        }
    } else {
        await loadLevels();
    }
});
