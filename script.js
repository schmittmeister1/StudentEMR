// PTA EMR Playground JS

// Global dataset
let patients = [];
let currentIndex = null;

// Load initial data from JSON or localStorage
async function loadData() {
  const stored = localStorage.getItem('pta_emr_patients');
  if (stored) {
    try {
      patients = JSON.parse(stored);
      renderPatientList();
      return;
    } catch (e) {
      console.error('Error parsing localStorage data', e);
    }
  }
  // Fetch JSON file
  const resp = await fetch('patients.json');
  const data = await resp.json();
  // Initialize progress_notes arrays where null
  patients = data.map(p => {
    if (!p.progress_notes || p.progress_notes === null) {
      p.progress_notes = [];
    }
    return p;
  });
  saveData();
  renderPatientList();
}

// Save data to localStorage
function saveData() {
  localStorage.setItem('pta_emr_patients', JSON.stringify(patients));
}

// Render patient list with search filtering
function renderPatientList() {
  const list = document.getElementById('patient-list');
  list.innerHTML = '';
  const search = document.getElementById('patient-search').value.toLowerCase();
  patients.forEach((patient, idx) => {
    const fullName = `${patient.first_name} ${patient.last_name}`;
    if (fullName.toLowerCase().includes(search)) {
      const li = document.createElement('li');
      li.textContent = `${fullName} — ${patient.category}`;
      li.dataset.index = idx;
      if (idx === currentIndex) li.classList.add('active');
      li.addEventListener('click', () => selectPatient(idx));
      list.appendChild(li);
    }
  });
}

// Select a patient and show details
function selectPatient(idx) {
  currentIndex = idx;
  renderPatientList();
  const patient = patients[idx];
  document.getElementById('patient-name').textContent = `${patient.first_name} ${patient.last_name}`;
  document.getElementById('empty-state').classList.add('hidden');
  document.getElementById('patient-details').classList.remove('hidden');
  // Populate evaluation form
  populateEvaluation(patient);
  // Render progress notes
  renderProgressNotes(patient);
}

// Populate evaluation form fields
function populateEvaluation(patient) {
  const e = patient.evaluation;
  // Date fields
  setValue('eval-date', e.evaluation_date);
  setValue('recert-date', e.recertification_date);
  // ICD codes
  setValue('icd10-med', patient.icd10_med || '');
  setValue('icd10-tx', patient.icd10_tx || '');
  // Account and insurance
  setValue('account-number', e.account_number);
  setValue('insurance', e.insurance);
  setValue('policy-number', e.policy_number);
  setValue('referring-physician', e.referring_physician);
  setValue('eval-therapist', e.evaluation_therapist);
  setValue('dob', e.dob);
  setValue('clinical-assessment', e.clinical_assessment);
  setValue('functional-progress', e.functional_progress);
  setValue('medications', e.medications);
  // Objective measures
  setValue('mmt', e.objective_measures.MMT);
  setValue('rom', e.objective_measures.ROM);
  setValue('berg', e.objective_measures.BergBalance);
  setValue('hr', e.objective_measures.HR);
  setValue('bp', e.objective_measures.BP);
  setValue('spo2', e.objective_measures.SpO2);
  // Goals
  renderGoals('st-goals', e.short_term_goals, patient, true);
  renderGoals('lt-goals', e.long_term_goals, patient, false);
  // Other fields
  setValue('contraindications', e.contraindications);
  document.getElementById('patient-consent').checked = !!e.patient_consent;
  document.getElementById('informed-consent').checked = !!e.informed_consent;
  setValue('required-cpt', e.required_cpt_codes ? e.required_cpt_codes.join(', ') : '');
  setValue('plan-frequency', e.plan_frequency);
  setValue('therapist-signature', e.therapist_signature);
  setValue('physician-signature', e.physician_signature);
  // Attach change listeners to update patient data
  attachEvaluationListeners(patient);
}

// Helper to set input/textarea value
function setValue(id, value) {
  const el = document.getElementById(id);
  if (!el) return;
  el.value = value || '';
}

// Render goals table; stFlag indicates short-term or long-term
function renderGoals(tableId, goals, patient, isShort) {
  const tbody = document.querySelector(`#${tableId} tbody`);
  tbody.innerHTML = '';
  goals.forEach((goalObj, idx) => {
    const tr = document.createElement('tr');
    // Goal description cell
    const tdGoal = document.createElement('td');
    const goalInput = document.createElement('input');
    goalInput.type = 'text';
    goalInput.value = goalObj.goal;
    goalInput.addEventListener('input', () => {
      goalObj.goal = goalInput.value;
      saveData();
    });
    tdGoal.appendChild(goalInput);
    // Due date
    const tdDate = document.createElement('td');
    const dateInput = document.createElement('input');
    dateInput.type = 'date';
    dateInput.value = goalObj.due_date;
    dateInput.addEventListener('change', () => {
      goalObj.due_date = dateInput.value;
      saveData();
    });
    tdDate.appendChild(dateInput);
    // Status
    const tdStatus = document.createElement('td');
    const select = document.createElement('select');
    ['Continue', 'Completed'].forEach(status => {
      const opt = document.createElement('option');
      opt.value = status;
      opt.textContent = status;
      if (goalObj.status === status) opt.selected = true;
      select.appendChild(opt);
    });
    select.addEventListener('change', () => {
      goalObj.status = select.value;
      saveData();
    });
    tdStatus.appendChild(select);
    // Append row
    tr.appendChild(tdGoal);
    tr.appendChild(tdDate);
    tr.appendChild(tdStatus);
    tbody.appendChild(tr);
  });
}

// Attach listeners on evaluation form fields to update data
function attachEvaluationListeners(patient) {
  const e = patient.evaluation;
  // Map of form id to property path
  const map = {
    'eval-date': val => e.evaluation_date = val,
    'recert-date': val => e.recertification_date = val,
    'icd10-med': val => patient.icd10_med = val,
    'icd10-tx': val => patient.icd10_tx = val,
    'account-number': val => e.account_number = val,
    'insurance': val => e.insurance = val,
    'policy-number': val => e.policy_number = val,
    'referring-physician': val => e.referring_physician = val,
    'eval-therapist': val => e.evaluation_therapist = val,
    'dob': val => e.dob = val,
    'clinical-assessment': val => e.clinical_assessment = val,
    'functional-progress': val => e.functional_progress = val,
    'medications': val => e.medications = val,
    'mmt': val => e.objective_measures.MMT = val,
    'rom': val => e.objective_measures.ROM = val,
    'berg': val => e.objective_measures.BergBalance = parseInt(val) || 0,
    'hr': val => e.objective_measures.HR = parseInt(val) || 0,
    'bp': val => e.objective_measures.BP = val,
    'spo2': val => e.objective_measures.SpO2 = val,
    'contraindications': val => e.contraindications = val,
    'required-cpt': val => e.required_cpt_codes = val.split(',').map(s => s.trim()).filter(Boolean),
    'plan-frequency': val => e.plan_frequency = val,
    'therapist-signature': val => e.therapist_signature = val,
    'physician-signature': val => e.physician_signature = val
  };
  Object.keys(map).forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    // Use appropriate event
    const eventName = el.tagName === 'INPUT' && el.type === 'date' ? 'change' : 'input';
    el.oninput = null; // Reset previous handler
    el.onchange = null;
    el.addEventListener(eventName, (ev) => {
      const val = el.type === 'checkbox' ? el.checked : el.value;
      map[id](val);
      saveData();
    });
  });
  // Checkbox listeners
  document.getElementById('patient-consent').addEventListener('change', ev => {
    e.patient_consent = ev.target.checked;
    saveData();
  });
  document.getElementById('informed-consent').addEventListener('change', ev => {
    e.informed_consent = ev.target.checked;
    saveData();
  });
}

// Render progress notes for a patient
function renderProgressNotes(patient) {
  const container = document.getElementById('progress-notes-list');
  container.innerHTML = '';
  patient.progress_notes.forEach((note, noteIdx) => {
    const noteEl = createNoteElement(note, patient, noteIdx);
    container.appendChild(noteEl);
  });
}

// Create DOM element for a progress note
function createNoteElement(note, patient, noteIdx) {
  const template = document.getElementById('progress-note-template');
  const clone = template.content.cloneNode(true);
  const noteEl = clone.querySelector('.progress-note');
  const dateInput = noteEl.querySelector('.note-date');
  dateInput.value = note.date || '';
  dateInput.addEventListener('change', () => {
    note.date = dateInput.value;
    saveData();
  });
  // Subjective/objective/assessment/plan
  const subj = noteEl.querySelector('.note-subjective');
  subj.value = note.subjective || '';
  subj.addEventListener('input', () => {
    note.subjective = subj.value;
    saveData();
  });
  const obj = noteEl.querySelector('.note-objective');
  obj.value = note.objective || '';
  obj.addEventListener('input', () => {
    note.objective = obj.value;
    saveData();
  });
  const assess = noteEl.querySelector('.note-assessment');
  assess.value = note.assessment || '';
  assess.addEventListener('input', () => {
    note.assessment = assess.value;
    saveData();
  });
  const plan = noteEl.querySelector('.note-plan');
  plan.value = note.plan || '';
  plan.addEventListener('input', () => {
    note.plan = plan.value;
    saveData();
  });
  // CPT codes
  const cptTableBody = noteEl.querySelector('.cpt-table tbody');
  const addCptBtn = noteEl.querySelector('.add-cpt-btn');
  const totalMinSpan = noteEl.querySelector('.total-min');
  const totalUnitsSpan = noteEl.querySelector('.total-units');
  function updateTotals() {
    let totalMin = 0;
    note.cpt_codes.forEach(item => {
      const m = parseInt(item.minutes) || 0;
      totalMin += m;
    });
    note.total_minutes = totalMin;
    note.units = Math.floor(totalMin / 15);
    totalMinSpan.textContent = totalMin;
    totalUnitsSpan.textContent = note.units;
    saveData();
  }
  // Render CPT rows
  function renderCptRows() {
    cptTableBody.innerHTML = '';
    note.cpt_codes.forEach((item, idx) => {
      const rowTemplate = document.getElementById('cpt-row-template');
      const rowClone = rowTemplate.content.cloneNode(true);
      const tr = rowClone.querySelector('tr');
      const codeInput = tr.querySelector('.cpt-code');
      const minInput = tr.querySelector('.cpt-min');
      codeInput.value = item.code;
      minInput.value = item.minutes;
      codeInput.addEventListener('input', () => {
        item.code = codeInput.value;
        saveData();
      });
      minInput.addEventListener('input', () => {
        item.minutes = parseInt(minInput.value) || 0;
        updateTotals();
      });
      tr.querySelector('.remove-cpt-btn').addEventListener('click', () => {
        note.cpt_codes.splice(idx, 1);
        renderCptRows();
        updateTotals();
      });
      cptTableBody.appendChild(tr);
    });
  }
  // Initial render of CPT rows
  if (!note.cpt_codes) note.cpt_codes = [];
  renderCptRows();
  updateTotals();
  // Add CPT code handler
  addCptBtn.addEventListener('click', () => {
    note.cpt_codes.push({ code: '', minutes: 0 });
    renderCptRows();
    updateTotals();
  });
  // Sign & Lock / Unlock
  const signBtn = noteEl.querySelector('.sign-lock-btn');
  const unlockBtn = noteEl.querySelector('.unlock-btn');
  const therapistSigInput = noteEl.querySelector('.note-therapist-signature');
  therapistSigInput.value = note.therapist_signature || '';
  therapistSigInput.addEventListener('input', () => {
    note.therapist_signature = therapistSigInput.value;
    saveData();
  });
  function setLockedState(locked) {
    note.locked = locked;
    // Toggle disabled state of inputs
    const inputs = noteEl.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
      if (input.classList.contains('note-date') || input.classList.contains('note-therapist-signature')) {
        // date and signature remain editable only until locked
      }
      input.disabled = locked;
    });
    if (locked) {
      signBtn.classList.add('hidden');
      unlockBtn.classList.remove('hidden');
    } else {
      signBtn.classList.remove('hidden');
      unlockBtn.classList.add('hidden');
    }
    saveData();
  }
  signBtn.addEventListener('click', () => {
    // sign: fill therapist signature with form value if blank
    if (!note.therapist_signature) {
      // if there is a therapist signature in evaluation, use that
      note.therapist_signature = patients[currentIndex].evaluation.therapist_signature || 'Signed';
      therapistSigInput.value = note.therapist_signature;
    }
    setLockedState(true);
  });
  unlockBtn.addEventListener('click', () => {
    setLockedState(false);
  });
  // Set initial locked state
  if (note.locked) {
    setLockedState(true);
  } else {
    setLockedState(false);
  }
  return noteEl;
}

// Add new progress note
function addNewProgressNote() {
  if (currentIndex === null) return;
  const patient = patients[currentIndex];
  const newNote = {
    date: new Date().toISOString().split('T')[0],
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
  patient.progress_notes.push(newNote);
  saveData();
  renderProgressNotes(patient);
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
  // Load data
  loadData();
  // Search filter
  document.getElementById('patient-search').addEventListener('input', () => {
    renderPatientList();
  });
  // Add note button
  document.getElementById('add-note-btn').addEventListener('click', addNewProgressNote);
});