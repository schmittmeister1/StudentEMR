/*
 * PTA EMR Playground JavaScript
 *
 * This script loads the patient dataset, renders a searchable table of patient cases,
 * and provides interactive forms for evaluation details and progress notes. Students
 * can practise filling in documentation, update goal status, add progress notes,
 * and sign/lock encounters. Data is stored in localStorage so edits persist
 * between sessions.
 */

// Global variables to track state
let patients = [];
let currentPatientIndex = null;
let currentProgressNoteIndex = null;

// Load data from localStorage or fetch from JSON
async function loadData() {
    const stored = localStorage.getItem('ptaEmrData');
    if (stored) {
        try {
            patients = JSON.parse(stored);
            renderPatientList();
            return;
        } catch (e) {
            console.error('Failed to parse stored data', e);
        }
    }
    // Otherwise fetch from JSON file
    try {
        const response = await fetch('patients.json');
        patients = await response.json();
        // Initialize locked flags for evaluations if missing
        patients.forEach(p => {
            if (!p.evaluation.locked) p.evaluation.locked = false;
            // Ensure each progress note has locked property
            p.progress_notes.forEach(note => {
                if (typeof note.locked === 'undefined') note.locked = false;
            });
        });
        saveData();
        renderPatientList();
    } catch (err) {
        console.error('Error loading patient data:', err);
    }
}

// Save data to localStorage
function saveData() {
    localStorage.setItem('ptaEmrData', JSON.stringify(patients));
}

// Render the patient list table
function renderPatientList() {
    const tbody = document.querySelector('#patientTable tbody');
    tbody.innerHTML = '';
    patients.forEach((patient, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${patient.id}</td>
            <td>${patient.first_name}</td>
            <td>${patient.last_name}</td>
            <td>${patient.category}</td>
            <td>${patient.condition}</td>
            <td><button class="view-btn" data-index="${index}">View</button></td>
        `;
        tbody.appendChild(tr);
    });
    // Bind click events
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', event => {
            const idx = parseInt(event.currentTarget.getAttribute('data-index'), 10);
            showPatientDetails(idx);
        });
    });
}

// Search filter
function handleSearch() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    const rows = document.querySelectorAll('#patientTable tbody tr');
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        const match = Array.from(cells).some(cell => cell.textContent.toLowerCase().includes(query));
        row.style.display = match ? '' : 'none';
    });
}

// Populate evaluation fields for a patient
function populateEvaluation(patient) {
    document.getElementById('evalDate').value = patient.evaluation.evaluation_date;
    document.getElementById('recertDate').value = patient.evaluation.recertification_date;
    document.getElementById('icdMed').value = patient.icd10_med;
    document.getElementById('icdTx').value = patient.icd10_tx;
    document.getElementById('accountNum').value = patient.evaluation.account_number;
    document.getElementById('insurance').value = patient.evaluation.insurance;
    document.getElementById('policyNum').value = patient.evaluation.policy_number;
    document.getElementById('refPhys').value = patient.evaluation.referring_physician;
    document.getElementById('evalTherapist').value = patient.evaluation.evaluation_therapist;
    document.getElementById('dob').value = patient.evaluation.dob;
    document.getElementById('clinicalAssessment').value = patient.evaluation.clinical_assessment;
    document.getElementById('functionalProgress').value = patient.evaluation.functional_progress;
    document.getElementById('medications').value = patient.evaluation.medications;
    document.getElementById('objectiveMeasures').value = formatObjectiveMeasures(patient.evaluation.objective_measures);
    document.getElementById('contraindications').value = patient.evaluation.contraindications;
    document.getElementById('patientConsent').checked = !!patient.evaluation.patient_consent;
    document.getElementById('informedConsent').checked = !!patient.evaluation.informed_consent;
    document.getElementById('cptCodes').value = patient.evaluation.required_cpt_codes.join(', ');
    document.getElementById('planFrequency').value = patient.evaluation.plan_frequency;
    document.getElementById('therapistSignature').value = patient.evaluation.therapist_signature || '';
    document.getElementById('physicianSignature').value = patient.evaluation.physician_signature || '';
    // Render goals
    renderGoals('shortTermGoals', patient.evaluation.short_term_goals);
    renderGoals('longTermGoals', patient.evaluation.long_term_goals);
    // Update lock button text
    updateEvalLockButton(patient.evaluation.locked);
    // Disable fields if locked
    setEvaluationFieldsDisabled(patient.evaluation.locked);
}

// Convert objective measures object to text
function formatObjectiveMeasures(measures) {
    const parts = [];
    if (measures.MMT) parts.push(`MMT: ${measures.MMT}`);
    if (measures.ROM) parts.push(`ROM: ${measures.ROM}`);
    if (measures.BergBalance) parts.push(`Berg Balance: ${measures.BergBalance}`);
    if (measures.HR) parts.push(`HR: ${measures.HR}`);
    if (measures.BP) parts.push(`BP: ${measures.BP}`);
    if (measures.SpO2) parts.push(`SpO₂: ${measures.SpO2}`);
    return parts.join(', ');
}

// Render goals list with status dropdown
function renderGoals(containerId, goals) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    goals.forEach((goal, index) => {
        const div = document.createElement('div');
        div.className = 'goal-item';
        const textInput = document.createElement('input');
        textInput.type = 'text';
        textInput.value = `${goal.goal} (Due: ${goal.due_date})`;
        textInput.disabled = true;
        const select = document.createElement('select');
        ['Continue', 'Completed'].forEach(optionVal => {
            const opt = document.createElement('option');
            opt.value = optionVal;
            opt.textContent = optionVal;
            if (goal.status === optionVal) opt.selected = true;
            select.appendChild(opt);
        });
        // When status changes, update goal status in data
        select.addEventListener('change', () => {
            goal.status = select.value;
            saveData();
        });
        // Disable select if evaluation is locked
        select.disabled = patients[currentPatientIndex].evaluation.locked;
        div.appendChild(textInput);
        div.appendChild(select);
        container.appendChild(div);
    });
}

// Show patient details section
function showPatientDetails(index) {
    currentPatientIndex = index;
    const patient = patients[index];
    document.getElementById('patientName').textContent = `${patient.first_name} ${patient.last_name} – ${patient.condition}`;
    populateEvaluation(patient);
    renderProgressNotes(patient);
    document.getElementById('patient-list-section').classList.add('hidden');
    document.getElementById('patient-details-section').classList.remove('hidden');
}

// Return to patient list
function backToList() {
    document.getElementById('patient-details-section').classList.add('hidden');
    document.getElementById('patient-list-section').classList.remove('hidden');
}

// Save evaluation edits
function saveEvaluation() {
    if (currentPatientIndex === null) return;
    const patient = patients[currentPatientIndex];
    // Save signature fields (others not editable)
    patient.evaluation.therapist_signature = document.getElementById('therapistSignature').value;
    patient.evaluation.physician_signature = document.getElementById('physicianSignature').value;
    saveData();
    alert('Evaluation saved.');
}

// Toggle evaluation lock state
function toggleEvaluationLock() {
    if (currentPatientIndex === null) return;
    const patient = patients[currentPatientIndex];
    const locked = patient.evaluation.locked;
    // If unlocking, simply unlock
    if (locked) {
        patient.evaluation.locked = false;
        updateEvalLockButton(false);
        setEvaluationFieldsDisabled(false);
    } else {
        // If locking, ensure therapist signature exists
        if (!document.getElementById('therapistSignature').value) {
            alert('Please enter therapist signature before locking.');
            return;
        }
        patient.evaluation.locked = true;
        updateEvalLockButton(true);
        setEvaluationFieldsDisabled(true);
    }
    saveData();
    alert(patient.evaluation.locked ? 'Evaluation signed and locked.' : 'Evaluation unlocked.');
}

// Update evaluation lock button text
function updateEvalLockButton(isLocked) {
    const btn = document.getElementById('lockEvalBtn');
    btn.textContent = isLocked ? 'Unlock Evaluation' : 'Sign & Lock Evaluation';
}

// Enable/disable evaluation fields based on lock state
function setEvaluationFieldsDisabled(disabled) {
    const fields = ['therapistSignature','physicianSignature'];
    fields.forEach(id => {
        document.getElementById(id).disabled = disabled;
    });
    // Disable goal dropdowns
    ['shortTermGoals','longTermGoals'].forEach(cid => {
        const selects = document.getElementById(cid).querySelectorAll('select');
        selects.forEach(sel => sel.disabled = disabled);
    });
}

// Render progress notes table
function renderProgressNotes(patient) {
    const tbody = document.querySelector('#progressNotesTable tbody');
    tbody.innerHTML = '';
    if (!patient.progress_notes || patient.progress_notes.length === 0) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 3;
        td.textContent = 'No progress notes yet.';
        tr.appendChild(td);
        tbody.appendChild(tr);
        return;
    }
    patient.progress_notes.forEach((note, index) => {
        const tr = document.createElement('tr');
        const status = note.locked ? 'Locked' : 'Unlocked';
        tr.innerHTML = `
            <td>${note.date}</td>
            <td>${status}</td>
            <td><button class="view-progress-btn" data-index="${index}">View</button></td>
        `;
        tbody.appendChild(tr);
    });
    // Bind view buttons
    document.querySelectorAll('.view-progress-btn').forEach(btn => {
        btn.addEventListener('click', event => {
            const idx = parseInt(event.currentTarget.getAttribute('data-index'), 10);
            showProgressNoteDetails(idx);
        });
    });
}

// Show progress note details for current patient
function showProgressNoteDetails(noteIndex) {
    currentProgressNoteIndex = noteIndex;
    const note = patients[currentPatientIndex].progress_notes[noteIndex];
    document.getElementById('pnDate').value = note.date;
    document.getElementById('pnSubjective').value = note.subjective || '';
    document.getElementById('pnObjective').value = note.objective || '';
    document.getElementById('pnAssessment').value = note.assessment || '';
    document.getElementById('pnPlan').value = note.plan || '';
    // Format CPT codes for textarea
    const cptString = note.cpt_codes.map(item => `${item.code} (${item.minutes} min)`).join(', ');
    document.getElementById('pnCptCodes').value = cptString;
    document.getElementById('pnTotalMinutes').value = note.total_minutes || 0;
    document.getElementById('pnUnits').value = note.units || 0;
    document.getElementById('pnSignature').value = note.therapist_signature || '';
    updateProgressNoteLockButton(note.locked);
    setProgressNoteFieldsDisabled(note.locked);
    document.getElementById('progressNoteDetail').classList.remove('hidden');
}

// Close progress note detail
function closeProgressNoteDetail() {
    document.getElementById('progressNoteDetail').classList.add('hidden');
    currentProgressNoteIndex = null;
}

// Save progress note
function saveProgressNote() {
    if (currentPatientIndex === null || currentProgressNoteIndex === null) return;
    const note = patients[currentPatientIndex].progress_notes[currentProgressNoteIndex];
    note.date = document.getElementById('pnDate').value;
    note.subjective = document.getElementById('pnSubjective').value;
    note.objective = document.getElementById('pnObjective').value;
    note.assessment = document.getElementById('pnAssessment').value;
    note.plan = document.getElementById('pnPlan').value;
    // Parse CPT codes from textarea (format: code (minutes) )
    const cptInput = document.getElementById('pnCptCodes').value.split(',').map(item => item.trim()).filter(Boolean);
    const cptList = [];
    cptInput.forEach(entry => {
        const match = entry.match(/(\w+)\s*\(?\s*(\d+)\s*min\)?/i);
        if (match) {
            cptList.push({ code: match[1], minutes: parseInt(match[2], 10) });
        }
    });
    note.cpt_codes = cptList;
    // Total minutes & units
    note.total_minutes = parseInt(document.getElementById('pnTotalMinutes').value, 10) || 0;
    note.units = parseInt(document.getElementById('pnUnits').value, 10) || 0;
    note.therapist_signature = document.getElementById('pnSignature').value;
    saveData();
    renderProgressNotes(patients[currentPatientIndex]);
    alert('Progress note saved.');
}

// Toggle progress note lock
function toggleProgressNoteLock() {
    if (currentPatientIndex === null || currentProgressNoteIndex === null) return;
    const note = patients[currentPatientIndex].progress_notes[currentProgressNoteIndex];
    if (note.locked) {
        // Unlock
        note.locked = false;
        updateProgressNoteLockButton(false);
        setProgressNoteFieldsDisabled(false);
        saveData();
        renderProgressNotes(patients[currentPatientIndex]);
        alert('Progress note unlocked.');
    } else {
        // Lock; require signature
        if (!document.getElementById('pnSignature').value) {
            alert('Please enter therapist signature before locking.');
            return;
        }
        note.locked = true;
        updateProgressNoteLockButton(true);
        setProgressNoteFieldsDisabled(true);
        saveData();
        renderProgressNotes(patients[currentPatientIndex]);
        alert('Progress note signed and locked.');
    }
}

// Update progress note lock button text
function updateProgressNoteLockButton(isLocked) {
    document.getElementById('lockProgressNoteBtn').textContent = isLocked ? 'Unlock Note' : 'Sign & Lock Note';
}

// Enable/disable progress note fields based on lock state
function setProgressNoteFieldsDisabled(disabled) {
    const fields = [
        'pnDate','pnSubjective','pnObjective','pnAssessment','pnPlan',
        'pnCptCodes','pnTotalMinutes','pnUnits','pnSignature'
    ];
    fields.forEach(id => {
        document.getElementById(id).disabled = disabled;
    });
}

// Add new progress note
function addProgressNote() {
    if (currentPatientIndex === null) return;
    const today = new Date().toISOString().split('T')[0];
    const newNote = {
        date: today,
        subjective: '',
        objective: '',
        assessment: '',
        plan: '',
        cpt_codes: [],
        total_minutes: 0,
        units: 0,
        therapist_signature: '',
        locked: false
    };
    patients[currentPatientIndex].progress_notes.push(newNote);
    saveData();
    renderProgressNotes(patients[currentPatientIndex]);
    showProgressNoteDetails(patients[currentPatientIndex].progress_notes.length - 1);
}

// Event listeners setup
function setupEventListeners() {
    document.getElementById('searchInput').addEventListener('input', handleSearch);
    document.getElementById('backToListBtn').addEventListener('click', backToList);
    document.getElementById('saveEvalBtn').addEventListener('click', saveEvaluation);
    document.getElementById('lockEvalBtn').addEventListener('click', toggleEvaluationLock);
    document.getElementById('addProgressNoteBtn').addEventListener('click', addProgressNote);
    document.getElementById('saveProgressNoteBtn').addEventListener('click', saveProgressNote);
    document.getElementById('lockProgressNoteBtn').addEventListener('click', toggleProgressNoteLock);
    document.getElementById('closeProgressNoteBtn').addEventListener('click', closeProgressNoteDetail);
}

// Initialize app
window.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadData();
});