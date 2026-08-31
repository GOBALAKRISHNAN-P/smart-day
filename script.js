/**
 * SmartDay – Personal Priority Planner
 * Vanilla JavaScript Frontend Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    initHeaderDate();
    initDefaultDeadline();
});

/**
 * Format and display the current date in the header
 */
function initHeaderDate() {
    const dateEl = document.getElementById('currentDateDisplay');
    if (!dateEl) return;

    const options = { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' };
    const today = new Date();
    dateEl.textContent = `📅 ${today.toLocaleDateString('en-US', options)}`;
}

/**
 * Set the default value of the deadline input to tomorrow
 */
function initDefaultDeadline() {
    const deadlineInput = document.getElementById('taskDeadline');
    if (!deadlineInput || deadlineInput.value) return;

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    const yyyy = tomorrow.getFullYear();
    const mm = String(tomorrow.getMonth() + 1).padStart(2, '0');
    const dd = String(tomorrow.getDate()).padStart(2, '0');
    
    deadlineInput.value = `${yyyy}-${mm}-${dd}`;
}

/**
 * Open the "What If I Delay?" simulation modal
 * Fetches simulated score from the backend API without altering the database.
 */
async function openWhatIfModal(taskId) {
    const modal = document.getElementById('whatIfModal');
    const taskNameEl = document.getElementById('modalTaskName');
    const currentScoreEl = document.getElementById('modalCurrentScore');
    const currentLevelEl = document.getElementById('modalCurrentLevel');
    const simulatedScoreEl = document.getElementById('modalSimulatedScore');
    const simulatedLevelEl = document.getElementById('modalSimulatedLevel');
    const diffEl = document.getElementById('modalScoreDiff');
    const explanationEl = document.getElementById('modalExplanationText');

    // Reset modal content while fetching
    taskNameEl.textContent = 'Simulating...';
    currentScoreEl.textContent = '--';
    currentLevelEl.textContent = '';
    simulatedScoreEl.textContent = '--';
    simulatedLevelEl.textContent = '';
    diffEl.textContent = '+0';
    diffEl.style.backgroundColor = 'var(--priority-critical)';
    explanationEl.textContent = 'Calculating priority shift after a 1-day delay...';

    modal.style.display = 'flex';

    try {
        const response = await fetch(`/api/tasks/${taskId}/what-if`);
        if (!response.ok) {
            throw new Error('Failed to fetch what-if calculation');
        }

        const data = await response.json();
        
        taskNameEl.textContent = data.task_name;
        currentScoreEl.textContent = data.current_score;
        currentLevelEl.textContent = data.current_level.label;
        currentLevelEl.style.color = data.current_level.color;

        simulatedScoreEl.textContent = data.simulated_score;
        simulatedLevelEl.textContent = data.simulated_level.label;
        simulatedLevelEl.style.color = data.simulated_level.color;

        const diff = data.difference;
        if (diff > 0) {
            diffEl.textContent = `+${diff} pts`;
            diffEl.style.backgroundColor = 'var(--priority-critical)';
        } else if (diff === 0) {
            diffEl.textContent = `No Change`;
            diffEl.style.backgroundColor = 'var(--text-muted)';
        } else {
            diffEl.textContent = `${diff} pts`;
            diffEl.style.backgroundColor = 'var(--priority-low)';
        }

        explanationEl.textContent = data.message;

    } catch (err) {
        console.error('What-if error:', err);
        explanationEl.textContent = 'Could not load simulation. Please try again.';
    }
}

/**
 * Close the What-If simulation modal
 */
function closeWhatIfModal() {
    const modal = document.getElementById('whatIfModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Close modal when clicking on the backdrop
 */
function closeWhatIfModalOnBackdrop(event) {
    if (event.target.id === 'whatIfModal') {
        closeWhatIfModal();
    }
}

// Close modal on ESC key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeWhatIfModal();
    }
});

/**
 * Handle Add Task Form Submission asynchronously
 */
async function handleAddTask(event) {
    event.preventDefault();
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');

    const name = document.getElementById('taskName').value.trim();
    const deadline = document.getElementById('taskDeadline').value;
    const importance = document.getElementById('taskImportance').value;
    const estimated_hours = parseFloat(document.getElementById('taskHours').value) || 1.0;

    if (!name || !deadline) {
        alert('Please provide both task name and deadline.');
        return;
    }

    if (submitBtn) submitBtn.disabled = true;

    try {
        const response = await fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, deadline, importance, estimated_hours })
        });

        if (response.ok) {
            window.location.reload();
        } else {
            const err = await response.json();
            alert(err.error || 'Failed to add task.');
        }
    } catch (err) {
        console.error('Add task error:', err);
        form.submit(); // fallback to standard form submit
    } finally {
        if (submitBtn) submitBtn.disabled = false;
    }
}

/**
 * Handle Complete/Undo action asynchronously
 */
async function handleFormAction(event, form) {
    event.preventDefault();
    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            window.location.reload();
        } else {
            form.submit();
        }
    } catch (e) {
        form.submit();
    }
}

/**
 * Handle Task Delete action with confirmation
 */
async function handleDeleteAction(event, form) {
    event.preventDefault();
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            window.location.reload();
        } else {
            form.submit();
        }
    } catch (e) {
        form.submit();
    }
}
