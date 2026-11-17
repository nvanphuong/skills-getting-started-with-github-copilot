# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- See signed-up participants on each activity card
- Unregister a participant using the delete icon next to their email
- Sign up for activities

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## Testing

From the repository root, install the dependencies and run the backend tests:

```bash
python -m pip install -r requirements.txt
python -m pytest tests -v
```

The tests live in `tests/` and run with `pytest`, using its support for
`unittest.TestCase` and FastAPI's `TestClient`. Requests run in-process, so no running server is required. Each test
restores the in-memory activity data to keep tests independent.
Tests follow Arrange-Act-Assert (AAA): prepare inputs and expected state, perform
requests, then verify responses and state changes.

The [Backend tests workflow](../.github/workflows/backend-tests.yml) runs the same
suite on Python 3.13 for every push and pull request.

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a participant from an activity                         |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
