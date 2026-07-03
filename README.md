# Enclan Africa Technical Assessment

**Winstone Were**

All answers are in **[ANSWERS.md](ANSWERS.md)**.

| Question | Answer | Code |
|---|---|---|
| 1. Programming Fundamentals | ANSWERS.md | `question1/unique_sort.py` |
| 2. Django API Development | ANSWERS.md | `question2/blogapi/` |
| 3. Mobile App Design | ANSWERS.md | written answer |
| 4. Relational Databases | ANSWERS.md | `question4/school.sql` |

## Question 1: run the script

Requires Python 3.

```
cd question1
python unique_sort.py
```

Expected output: `[3, 5, 7, 8, 9, 12]`

## Question 2: run the Blog API

Requires Python 3. Instructions below are for Windows; on Linux/Mac replace the activate line with `source venv/bin/activate`.

```
cd question2
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd blogapi
python manage.py migrate
python manage.py runserver
```

Then open the interactive API docs at:

**http://127.0.0.1:8000/api/docs**

### Testing the API from the docs

1. Expand `POST /api/auth/register/` and create an account
2. Expand `POST /api/auth/login/` with the same credentials and copy the `access` token from the response
3. Click the **Authorize** button at the top right and paste the token
4. Use the `/api/posts/` endpoints to create, list, update and delete posts

To verify authorization: register a second user, login as them, and try to update or delete the first user's post. The API returns `403 Forbidden`. Any request without a token returns `401 Unauthorized`.

### Endpoints

| Method | Endpoint | Auth |
|---|---|---|
| POST | `/api/auth/register/` | No |
| POST | `/api/auth/login/` | No |
| POST | `/api/auth/token/refresh/` | Refresh token |
| POST | `/api/auth/logout/` | Yes |
| DELETE | `/api/auth/delete/` | Yes |
| GET, POST | `/api/posts/` | Yes |
| GET, PUT, PATCH, DELETE | `/api/posts/{id}/` | Yes (writes: author only) |

## Question 4: run the SQL

The schema, sample data and the answer query are in `question4/school.sql`. The `run_query.py` helper executes it with Python's built-in `sqlite3` module, so no SQLite installation is needed:

```
cd question4
python run_query.py
```

Alternatively, open [DB Browser for SQLite](https://sqlitebrowser.org/), create a new database, and paste the contents of `school.sql` into the Execute SQL tab.

Expected result: the two students enrolled in "Introduction to Programming" are returned; the student enrolled in a different course is not.
