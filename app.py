import sqlite3
import os
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')


def get_db_connection():
    """Create and return a database connection with dict-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the SQLite database with the tasks table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            deadline TEXT NOT NULL,
            importance TEXT NOT NULL,
            estimated_hours REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def calculate_priority_score(deadline_str, importance, estimated_hours, delay_days=0):
    """
    Calculate deterministic priority score from 0 to 100 based on:
    - Deadline urgency (0 - 50 points)
    - Importance (0 - 35 points)
    - Estimated effort (0 - 15 points)
    """
    try:
        task_date = datetime.strptime(deadline_str.split('T')[0].strip(), '%Y-%m-%d').date()
        today = date.today()
        # If simulated delay is applied, days left shrinks by delay_days
        days_left = (task_date - today).days - delay_days
    except Exception:
        days_left = 3 - delay_days

    # 1. Deadline Urgency (0 - 50 points)
    if days_left < 0:
        urgency_score = 50  # Overdue
    elif days_left == 0:
        urgency_score = 46  # Due today
    elif days_left == 1:
        urgency_score = 40  # Due tomorrow
    elif days_left <= 3:
        urgency_score = 32  # Due in 2-3 days
    elif days_left <= 7:
        urgency_score = 22  # Due within a week
    elif days_left <= 14:
        urgency_score = 12  # Due within 2 weeks
    else:
        urgency_score = max(2, int(10 - (days_left - 14) * 0.5))

    # 2. Importance Score (0 - 35 points)
    importance_clean = str(importance).strip().capitalize()
    if importance_clean == 'High':
        importance_score = 35
    elif importance_clean == 'Medium':
        importance_score = 22
    else:  # Low
        importance_score = 10

    # 3. Estimated Time / Quick-win Score (0 - 15 points)
    try:
        hours = float(estimated_hours)
    except (ValueError, TypeError):
        hours = 1.0

    if hours <= 1.0:
        effort_score = 15
    elif hours <= 3.0:
        effort_score = 12
    elif hours <= 6.0:
        effort_score = 8
    else:
        effort_score = 5

    total_score = urgency_score + importance_score + effort_score
    return min(100, max(0, int(round(total_score))))


def get_priority_level(score):
    """Return priority level label and CSS styling class based on score."""
    if score >= 80:
        return {'label': 'Critical', 'category': 'critical', 'color': '#ef4444'}
    elif score >= 60:
        return {'label': 'High', 'category': 'high', 'color': '#f97316'}
    elif score >= 40:
        return {'label': 'Medium', 'category': 'medium', 'color': '#eab308'}
    else:
        return {'label': 'Low', 'category': 'low', 'color': '#22c55e'}


def generate_task_explanation(deadline_str, importance, estimated_hours, score):
    """Generate a readable explanation of why this task has its priority score."""
    try:
        task_date = datetime.strptime(deadline_str.split('T')[0].strip(), '%Y-%m-%d').date()
        today = date.today()
        days_left = (task_date - today).days
        if days_left < 0:
            urgency_text = f"overdue by {abs(days_left)} day{'s' if abs(days_left) > 1 else ''}"
        elif days_left == 0:
            urgency_text = "due today"
        elif days_left == 1:
            urgency_text = "due tomorrow"
        else:
            urgency_text = f"due in {days_left} days"
    except Exception:
        urgency_text = "upcoming deadline"

    imp_text = f"{importance.lower()} importance"
    effort_text = f"{estimated_hours}h estimated effort"

    if score >= 80:
        return f"Critical priority because the deadline is {urgency_text} and the task has {imp_text} ({effort_text})."
    elif score >= 60:
        return f"High priority because the deadline is {urgency_text} with {imp_text}."
    elif score >= 40:
        return f"Medium priority with steady progress needed ({urgency_text}, {imp_text})."
    else:
        return f"Low priority: comfortably scheduled ({urgency_text}, {imp_text})."


def enrich_task_data(task_row):
    """Convert database Row to dict and enrich with computed priority attributes."""
    task = dict(task_row)
    score = calculate_priority_score(task['deadline'], task['importance'], task['estimated_hours'])
    level_info = get_priority_level(score)
    explanation = generate_task_explanation(task['deadline'], task['importance'], task['estimated_hours'], score)

    task['priority_score'] = score
    task['priority_label'] = level_info['label']
    task['priority_category'] = level_info['category']
    task['priority_color'] = level_info['color']
    task['explanation'] = explanation
    return task


@app.route('/')
def home():
    """Main dashboard page route."""
    conn = get_db_connection()
    tasks_cursor = conn.execute('SELECT * FROM tasks ORDER BY id DESC').fetchall()
    conn.close()

    all_tasks = [enrich_task_data(t) for t in tasks_cursor]
    pending_tasks = [t for t in all_tasks if t['status'] == 'Pending']
    completed_tasks = [t for t in all_tasks if t['status'] == 'Completed']

    # Sort pending tasks by priority score descending
    pending_tasks.sort(key=lambda x: x['priority_score'], reverse=True)

    # Determine Next Best Task (highest priority pending task)
    next_best_task = pending_tasks[0] if pending_tasks else None

    # Summary Statistics
    total_tasks = len(all_tasks)
    total_completed = len(completed_tasks)
    total_pending = len(pending_tasks)
    highest_priority_score = next_best_task['priority_score'] if next_best_task else 0

    return render_template(
        'index.html',
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        next_best_task=next_best_task,
        total_tasks=total_tasks,
        total_completed=total_completed,
        total_pending=total_pending,
        highest_priority_score=highest_priority_score,
        today_date=date.today().isoformat()
    )


@app.route('/add', methods=['POST'])
@app.route('/api/tasks', methods=['POST'])
def add_task():
    """Add a new task via Form submission or JSON API."""
    is_api = request.path.startswith('/api') or request.is_json
    if request.is_json:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        deadline = data.get('deadline', '').strip()
        importance = data.get('importance', 'Medium').strip()
        estimated_hours = data.get('estimated_hours', 1.0)
    else:
        name = request.form.get('name', '').strip()
        deadline = request.form.get('deadline', '').strip()
        importance = request.form.get('importance', 'Medium').strip()
        estimated_hours = request.form.get('estimated_hours', 1.0)

    if not name or not deadline:
        if is_api:
            return jsonify({'success': False, 'error': 'Task name and deadline are required'}), 400
        return redirect(url_for('home'))

    try:
        estimated_hours = float(estimated_hours)
    except ValueError:
        estimated_hours = 1.0

    created_at = datetime.now().strftime('%Y-%m-%d %H:%M')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (name, deadline, importance, estimated_hours, status, created_at)
        VALUES (?, ?, ?, ?, 'Pending', ?)
    ''', (name, deadline, importance, estimated_hours, created_at))
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()

    if is_api:
        return jsonify({'success': True, 'task_id': task_id}), 201
    return redirect(url_for('home'))


@app.route('/complete/<int:task_id>', methods=['POST'])
@app.route('/api/tasks/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """Toggle or set task as completed."""
    is_api = request.path.startswith('/api') or request.is_json
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if not task:
        conn.close()
        if is_api:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
        return redirect(url_for('home'))

    # Toggle status if already completed or set to Completed
    new_status = 'Pending' if task['status'] == 'Completed' else 'Completed'
    conn.execute('UPDATE tasks SET status = ? WHERE id = ?', (new_status, task_id))
    conn.commit()
    conn.close()

    if is_api:
        return jsonify({'success': True, 'new_status': new_status})
    return redirect(url_for('home'))


@app.route('/delete/<int:task_id>', methods=['POST'])
@app.route('/api/tasks/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    """Delete a task."""
    is_api = request.path.startswith('/api') or request.is_json
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

    if is_api:
        return jsonify({'success': True})
    return redirect(url_for('home'))


@app.route('/api/tasks/<int:task_id>/what-if', methods=['GET'])
def what_if_delay(task_id):
    """
    Calculate simulated priority score if action is delayed by 1 day.
    Does NOT modify the database.
    """
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    conn.close()

    if not task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404

    current_score = calculate_priority_score(task['deadline'], task['importance'], task['estimated_hours'], delay_days=0)
    simulated_score = calculate_priority_score(task['deadline'], task['importance'], task['estimated_hours'], delay_days=1)
    diff = simulated_score - current_score

    current_level = get_priority_level(current_score)
    simulated_level = get_priority_level(simulated_score)

    if diff > 0:
        message = f"Delaying this task increases its priority because the deadline becomes 1 day more urgent."
    elif diff == 0:
        if current_score >= 80:
            message = "Task is already at maximum urgency level (due today or overdue)."
        else:
            message = "A 1-day delay keeps priority steady, but leaves less buffer before escalation."
    else:
        message = "Simulation calculated for delayed timeline."

    return jsonify({
        'success': True,
        'task_id': task_id,
        'task_name': task['name'],
        'deadline': task['deadline'],
        'importance': task['importance'],
        'estimated_hours': task['estimated_hours'],
        'current_score': current_score,
        'current_level': current_level,
        'simulated_score': simulated_score,
        'simulated_level': simulated_level,
        'difference': diff,
        'message': message
    })


@app.route('/api/tasks', methods=['GET'])
def list_tasks_api():
    """Return JSON list of all tasks with computed priorities."""
    conn = get_db_connection()
    tasks_cursor = conn.execute('SELECT * FROM tasks ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([enrich_task_data(t) for t in tasks_cursor])


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='127.0.0.1', port=5000)
