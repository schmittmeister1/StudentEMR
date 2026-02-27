// Client-side EMR functionality and accessibility helpers

document.addEventListener('DOMContentLoaded', () => {
  // High contrast toggle
  const toggleButton = document.getElementById('toggle-contrast');
  toggleButton.addEventListener('click', () => {
    document.body.classList.toggle('high-contrast');
  });

  // Storage key for patients
  const STORAGE_KEY = 'patients';

  // Default sample patients for demonstration
  const defaultPatients = [
    { name: 'John Doe', dob: '1990-01-01', id: 'P001' },
    { name: 'Jane Smith', dob: '1985-05-12', id: 'P002' },
    { name: 'Sam Nguyen', dob: '2000-10-30', id: 'P003' }
  ];

  // Retrieve patients from localStorage or use defaults
  let patients;
  try {
    patients = JSON.parse(localStorage.getItem(STORAGE_KEY)) || defaultPatients;
  } catch (e) {
    patients = defaultPatients;
  }

  const tbody = document.getElementById('patients-body');
  const searchInput = document.getElementById('search');
  const form = document.getElementById('add-patient-form');
  const feedback = document.getElementById('patient-form-feedback');

  /**
   * Render the given list of patients into the table body.
   * @param {Array} list - array of patient objects
   */
  function renderPatients(list) {
    // Clear existing rows
    tbody.innerHTML = '';
    list.forEach(patient => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${patient.name}</td>
        <td>${patient.dob}</td>
        <td>${patient.id}</td>
        <td><button class="delete-button" data-id="${patient.id}">Delete</button></td>
      `;
      tbody.appendChild(row);
    });
  }

  // Initial render
  renderPatients(patients);

  // Search filter
  searchInput.addEventListener('input', () => {
    const term = searchInput.value.toLowerCase();
    const filtered = patients.filter(p => p.name.toLowerCase().includes(term));
    renderPatients(filtered);
  });

  // Form submission for adding a new patient
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    feedback.textContent = '';
    const name = document.getElementById('patient-name').value.trim();
    const dob = document.getElementById('patient-dob').value;
    const id = document.getElementById('patient-id').value.trim();
    const errors = [];
    if (!name) {
      errors.push('Name is required.');
    }
    if (!dob) {
      errors.push('Date of birth is required.');
    }
    if (!id) {
      errors.push('Patient ID is required.');
    } else if (patients.some(p => p.id === id)) {
      errors.push('A patient with this ID already exists.');
    }
    if (errors.length > 0) {
      feedback.textContent = errors.join(' ');
      feedback.style.color = 'red';
      return;
    }
    // Add new patient and persist
    const newPatient = { name, dob, id };
    patients.push(newPatient);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(patients));
    renderPatients(patients);
    feedback.textContent = 'Patient added successfully.';
    feedback.style.color = 'green';
    form.reset();
  });

  // Delete patient handler (event delegation)
  tbody.addEventListener('click', (event) => {
    if (event.target.classList.contains('delete-button')) {
      const idToDelete = event.target.getAttribute('data-id');
      patients = patients.filter(p => p.id !== idToDelete);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(patients));
      // Apply current search filter again
      const term = searchInput.value.toLowerCase();
      const filtered = patients.filter(p => p.name.toLowerCase().includes(term));
      renderPatients(filtered);
    }
  });
});
