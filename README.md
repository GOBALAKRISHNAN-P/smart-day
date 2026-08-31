##live demo
[open smartDay(https://smart-day.onrender.com)
SmartDay – Personal Priority Planner

SmartDay is a simple web application that helps users decide which task they should complete first.

Instead of treating all tasks equally, SmartDay calculates a Priority Score for each task using its deadline, importance, and estimated time. The application then recommends the Next Best Task.

It also includes a simple “What If I Delay?” feature that shows how delaying a task by one day can affect its priority.

Features
Add personal tasks
Set task deadline
Set task importance
Set estimated completion time
Automatically calculate task priority
Display the highest-priority task as the Next Best Task
Mark tasks as completed
Delete tasks
Simulate the effect of delaying a task by one day
View simple task statistics
Responsive and clean user interface
How It Works

The application follows a simple process:

Add Task
   ↓
Set Deadline + Importance + Estimated Time
   ↓
Calculate Priority Score
   ↓
Display Priority
   ↓
Find Highest Priority Task
   ↓
Show Next Best Task

Priority Levels
Score	Level
80–100	🔴 Critical
60–79	🟠 High
40–59	🟡 Medium
0–39	🟢 Low

The priority score is calculated using a deterministic rule-based system. No AI or random scoring is used.

What-If Delay Simulation

SmartDay provides a simple simulation feature.

When the user selects “What If I Delay?”, the application temporarily moves the task deadline one day later and calculates the simulated priority.

The actual task data is not changed.

Example:

Current Priority:     72
Simulated Priority:   86

Result:
Delaying the task increases its priority because
the deadline becomes more urgent.

Technology Stack
Backend: Python Flask
Database: SQLite
Frontend: HTML, CSS, JavaScript
Database Access: Python SQLite3

No external APIs or AI services are required.

Project Structure
smartday/
│
├── app.py
├── database.db
│
├── templates/
│   └── index.html
│
└── static/
    ├── style.css
    └── script.js

Database

The application uses a single SQLite table called tasks.

Tasks Table
Field	Description
id	Unique task ID
name	Task name
deadline	Task deadline
importance	Low, Medium, or High
estimated_hours	Estimated completion time
status	Pending or Completed
created_at	Task creation time
Requirements

Make sure you have:

Python 3.x
Flask

Install Flask using:

pip install flask

How to Run
1. Clone or download the project

Open the project folder in your terminal.

2. Install Flask
pip install flask

3. Run the application
python app.py

4. Open the application

Open your browser and visit:

http://127.0.0.1:5000


The SQLite database will be used to store the tasks.

Example

Suppose the user adds:

Task: Complete DBMS Assignment
Deadline: Tomorrow
Importance: High
Estimated Time: 2 hours


SmartDay may display:

Priority Score: 92
Priority Level: Critical

NEXT BEST TASK:
Complete DBMS Assignment

Reason:
The task has high importance and a close deadline.

Main Objective

The main objective of SmartDay is to provide a simple decision-support tool for daily task management.

Instead of asking:

“What tasks do I have?”

SmartDay helps answer:

“What should I do next?”

Future Improvements

Possible future improvements include:

Calendar integration
User accounts
Notifications
Weekly productivity reports
Habit tracking
Mobile application
More advanced priority prediction

These features are not required for the current version.

License

This project is created for educational and academic purposes.
