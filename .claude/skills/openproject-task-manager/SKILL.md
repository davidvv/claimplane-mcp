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
4.  **Estimate Effort**: Estimate the time required to complete the task in hours (e.g., 0.5, 2.0).

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
        - **Share the task URL with the user** (e.g., "Task #123: http://...")
    - **IF NOT FOUND**:
        - Create a new work package (`openproject_create_work_package`).
        - **Subject**: Concise summary of the request.
        - **Description**: The detailed plan from Step 1.
        - **Type**: 1 (Task) or 7 (Bug) as appropriate.
        - **estimated_hours**: The effort estimate from Step 1.
        - **Note the ID** of this new work package.
        - **IMPORTANT**: Share the task URL with the user immediately (from the `url` field in the response)

### Step 3: Start Work (In Progress)
**Goal**: Signal that work has begun and inform the user.

1.  **Update Status**:
    - Use `openproject_update_work_package`.
    - Set `status` to **7** ("In progress").
2.  **Record Start Time**:
    - Note the current wall-clock time internally (e.g., "Started at 14:00").
3.  **Inform User**:
    - Tell the user which task you're working on with the task link.
    - Example: "Starting work on Task #137: Setup Vertex AI (http://...)"

### Step 4: Execute Task
**Goal**: Implement the plan.

1.  Perform the coding, testing, and verification steps as planned.
2.  Use standard tools (`edit`, `bash`, etc.) to modify the codebase.

### Step 5: Completion & Time Tracking
**Goal**: Close the loop, log effort, and confirm completion with user.

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
4.  **Inform User**:
    - Tell the user the task is complete with the task link.
    - Example: "✅ Completed Task #138: Add dependencies (http://...)"

---

## Checklist for Every Task

- [ ] **Plan Created**: Detailed steps formulated.
- [ ] **Project Identified**: Correct project ID found.
- [ ] **Task Exists**: Checked for existing task (found or created).
- [ ] **Task URL Shared**: User informed of task link when created/found.
- [ ] **Status -> In Progress**: Updated status to ID 7.
- [ ] **User Informed of Start**: Told user which task is being worked on.
- [ ] **Work Done**: Implementation complete.
- [ ] **Status -> Closed**: Updated status to ID 12.
- [ ] **Time Logged**: Time entry created with start/end times in comment.
- [ ] **User Informed of Completion**: Told user task is complete with link.
