# Implementation Plan - Persistent User Storage & Admin Export

## Goal
Store user details (name, roll number, email) and quiz scores in a database so the event organizer can download them easily. Ensure users stay logged in.

## Proposed Changes

### Backend (`backend/app.py`)
1.  **Database Setup**:
    *   Use `sqlite3` to create a local `participants.db`.
    *   Table `users`:
        *   `rollno` (Primary Key - assuming unique per student)
        *   `username`
        *   `email`
        *   `phase1_score` (default 0)
        *   `phase2_score` (default 0)
        *   `phase3_score` (default 0)
        *   `total_score` (default 0)
        *   `login_time`

2.  **New Endpoints**:
    *   `POST /api/login`: Receives user details, saves to DB (UPSERT), sets session.
    *   `GET /api/admin/export`: Generates a CSV file of all users and scores.

3.  **Modified Endpoints**:
    *   `submit_quiz` / `complete_phase_x`: Update the corresponding score columns for the current user in the DB.

### Frontend (`static/js/login.js`)
1.  **Login Logic**:
    *   On form submit, send `POST` request to `/api/login`.
    *   On success, redirect to `phases.html`.

### Admin
*   Since there is no admin UI requested, I will provide the URL `/api/admin/export` for the organizer to use directly, or create a simple hidden button if needed. For now, just the endpoint.

## Verification Plan

### Automated Tests
*   Verify `participants.db` is created.
*   Verify `/api/login` adds a row.
*   Verify `/api/admin/export` returns a CSV with correct headers.

### Manual Verification
1.  Open Login Page, enter details.
2.  Check if redirected to Phases.
3.  Complete a quiz.
4.  Hit `/api/admin/export` in browser and check the CSV content.
