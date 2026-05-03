# Spec: Login and Logout

## Overview
The login and logout feature allows registered users to authenticate with their email and password, and to sign out of their session. Upon successful login, a session is established so that subsequent requests can identify the logged-in user. This feature builds on the existing users table and registration flow, completing the authentication cycle for Spendly.

## Depends on
- Step 01 — Database setup
- Step 02 — Registration

## Routes
- `GET /login` — display login form — public
- `POST /login` — process login form, set session — public
- `GET /logout` — clear session, redirect — logged-in (or public, redirects if not logged in)

## Database changes
No database changes.

## Templates
- **Create:** none (login.html already exists)
- **Modify:**
  - `templates/login.html` — ensure flash messages are displayed (already has error div, may need success messages)
  - `templates/base.html` — add conditional navigation links: show "Sign in" / "Register" when logged out, show "Profile" / "Logout" when logged in

## Files to change
- `app.py` — implement `POST /login` logic, replace placeholder `GET /logout` with proper session clearing, add `verify_user` helper or import from db
- `database/db.py` — add `verify_user(email, password)` function that checks credentials and returns user dict if valid
- `templates/base.html` — update navigation to reflect authentication state
- `templates/login.html` — minor tweaks if needed (flash messages)

## Files to create
- None

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (use `check_password_hash` for verification)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use Flask `session` object to store `user_id` upon successful login
- Clear session on logout (`session.clear()` or `session.pop('user_id', None)`)
- Redirect after actions (login success → redirect to landing or profile; logout → redirect to landing)
- Show flash messages for login errors (invalid email/password) and success (though success redirects)

## Definition of done
- [ ] `POST /login` validates email and password against the database
- [ ] Invalid credentials show a flash error and re-render login form
- [ ] Valid credentials set `session['user_id']` and redirect to landing page (or profile)
- [ ] `GET /logout` clears the session and redirects to landing page
- [ ] `base.html` shows appropriate navigation links based on `session['user_id']`
- [ ] `verify_user` function in `database/db.py` uses parameterised query and `check_password_hash`
- [ ] No new database tables or columns are created
- [ ] All templates extend `base.html` and use CSS variables
- [ ] App runs without errors after changes
