---
name: openproject-task-manager
description: Manages the full lifecycle of a task in OpenProject including investigation, planning, creation/retrieval, status tracking, and time logging.
---

# OpenProject Task Manager Skill

## Purpose
This skill ensures that every task received from the user is properly investigated, planned, tracked, and timed in OpenProject. It guarantees transparency and session recovery capability without user intervention.

## When to Use This Skill
- **IMMEDIATELY** upon receiving a new task or request from the user.
- When resuming a session to check for existing in-progress tasks.

---

## Workflow Steps

### Step 1: Investigation & Planning
**Goal**: Understand *what* needs to be done before touching the code.

1.  **Analyze Request**: Read the user's prompt carefully.
2.  **Investigate Context**: Use tools (`grep`, `glob`, `read`) to understand the codebase state relevant to the request.
3.  **Formulate Plan**: Create a detailed, step-by-step plan of action. This will be the "Description" of your OpenProject work package.

### Step 2: OpenProject Task Management
**Goal**: Ensure the task exists in the system and handle interruptions.

1.  **Select Project**:
    - Use `openproject_get_projects`.
    - Choose the most relevant project ID (e.g., "Web app backend", "DevOps"). If unsure, ask or use a default like "Scrum project".

2.  **Check for Existing Task (Recovery)**:
    - Use `openproject_search_work_packages` with keywords from the user's request.
    - **IF FOUND**:
        - Retrieve details (`openproject_get_work_packages` or from search result).
        - If status is "Closed" (ID 12), confirm with user before reopening.
        - If status is "In progress" (ID 7) or "New" (ID 1), resume this task.
    - **IF NOT FOUND**:
        - Create a new work package (`openproject_create_work_package`).
        - **Subject**: Concise summary of the request.
        - **Description**: The detailed plan from Step 1.
        - **Type**: 1 (Task) or 7 (Bug) as appropriate.
        - **Note the ID** of this new work package.

### Step 3: Start Work (In Progress)
**Goal**: Signal that work has begun.

1.  **Update Status**:
    - Use `openproject_update_work_package`.
    - Set `status` to **7** ("In progress").
2.  **Record Start Time**:
    - Note the current wall-clock time internally (e.g., "Started at 14:00").

### Step 4: Execute Task
**Goal**: Implement the plan.

1.  Perform the coding, testing, and verification steps as planned.
2.  Use standard tools (`edit`, `bash`, etc.) to modify the codebase.

### Step 5: Completion & Time Tracking
**Goal**: Close the loop and log effort.

1.  **Record End Time**: Note the current time (e.g., "Finished at 15:30").
2.  **Close Task**:
    - Use `openproject_update_work_package`.
    - Set `status` to **12** ("Closed").
3.  **Log Time**:
    - Calculate duration in decimal hours (e.g., 1.5 for 1h 30m).
    - Use `openproject_log_time_entry`.
    - **Payload**:
        - `work_package_id`: The ID of your task.
        - `hours`: Calculated duration.
        - `spent_on`: Today's date (YYYY-MM-DD).
        - `comment`: "Worked from [Start Time] to [End Time]. Total: [Duration]. [Brief summary of outcome]."

---

## Checklist for Every Task

- [ ] **Plan Created**: Detailed steps formulated.
- [ ] **Project Identified**: Correct project ID found.
- [ ] **Task Exists**: Checked for existing task (found or created).
- [ ] **Status -> In Progress**: Updated status to ID 7.
- [ ] **Work Done**: Implementation complete.
- [ ] **Status -> Closed**: Updated status to ID 12.
- [ ] **Time Logged**: Time entry created with start/end times in comment.
