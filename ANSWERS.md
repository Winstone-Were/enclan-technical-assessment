# Enclan Africa Technical Assessment

**Winstone Were**
GitHub: [github.com/Winstone-Were](https://github.com/Winstone-Were)

This file contains my answers to all four questions. Runnable code for Question 1 is in `question1/`, the full Django project for Question 2 is in `question2/`, and the SQL script for Question 4 is in `question4/`. Setup and run instructions are in the [README](README.md).

---

## Question 1: Programming Fundamentals

**Code:** `question1/unique_sort.py`

```python
def quicksort_unique(nums):
    if len(nums) <= 1:
        return nums

    pivot = nums[0]
    smaller = [x for x in nums if x < pivot]
    larger  = [x for x in nums if x > pivot]

    return quicksort_unique(smaller) + [pivot] + quicksort_unique(larger)

numbers = [12, 7, 12, 3, 5, 7, 8, 3, 9]
print(quicksort_unique(numbers))
```

**Output:** `[3, 5, 7, 8, 9, 12]`

### My approach

I implemented quicksort in a way that removes duplicates as part of the sorting itself instead of as a separate step. In a normal quicksort, elements equal to the pivot are kept. Here the partition only keeps values strictly smaller than the pivot and strictly larger than the pivot. Any copies of the pivot are dropped, and the pivot itself appears exactly once in the result. Since every element eventually becomes a pivot at some level of the recursion, every duplicate gets eliminated.

The simplest solution in Python would be `sorted(set(numbers))`, which also runs in O(n log n). I chose the quicksort version to show the sorting and deduplication logic explicitly rather than relying on built-ins.

---

## Question 2: Django API Development

**Code:** `question2/blogapi/`

### Overview

I built a Blog API with two Django apps:

- `accounts` handles registration, login, logout and account deletion
- `posts` handles blog post CRUD

Authentication uses JWT through `djangorestframework-simplejwt`. Authorization is enforced at two levels: every endpoint requires a valid token, and write operations on posts additionally require ownership. The API is documented with an interactive Swagger UI at `/api/docs/` (drf-spectacular).

### Data model

`BlogPost` has a title, content, created/updated timestamps, and a foreign key to Django's built-in `User` model. I used the built-in User instead of a custom model because it already handles password hashing securely and integrates with Django's auth system. The foreign key means one user can have many posts, and `on_delete=CASCADE` means deleting an account also removes that user's posts, so no orphaned data is left behind.

### Authentication

Login works by exchanging a username and password for a JWT token pair at `/api/auth/login/`. The access token (30 minute lifetime) is attached to every request as a Bearer header. The refresh token (1 day) is used to get new access tokens without re-entering credentials.

JWTs are stateless, which creates a problem for logout: the server does not store tokens, so it cannot simply forget one. I solved this with SimpleJWT's token blacklist app. Logout submits the refresh token and the server records it as revoked, so it can no longer be used to obtain new access tokens.

Passwords are hashed by `User.objects.create_user()` before being stored, and the password field on the register serializer is `write_only` so it never appears in any API response. Registration also runs Django's password validators (minimum length, not entirely numeric, not a common password, not too similar to the username or email) and returns a 400 with per-rule error messages if the password is weak.

### Authorization

Authorization happens at two levels:

1. `@permission_classes([IsAuthenticated])` on every view rejects requests without a valid token with a 401.
2. For updates and deletes on posts, the view compares `post.author` to `request.user` and returns a 403 if they differ.

The distinction matters: 401 means "I do not know who you are" (authentication failed), while 403 means "I know who you are, but this is not yours" (authorization failed).

Two design decisions back this up:

- The author of a post is never taken from the request body. It is set from the authenticated token in the view (`serializer.save(author=request.user)`), so a client cannot create posts as someone else.
- Account deletion takes no user ID. It deletes `request.user`, whoever the token belongs to, so a user cannot delete any account except their own.

I required authentication on all endpoints, including reads, since the requirement was that users can see all blogs. If the blog were meant to have a public audience, making reads open would be a one line change (swap `IsAuthenticated` for `IsAuthenticatedOrReadOnly`).

### Design choices

**Function-based views with `@api_view`.** I chose function-based views over ViewSets because every step (auth check, ownership check, status code) is explicit in the function body, which makes the logic easy to review and explain. The trade-off is more boilerplate, and the schema generator cannot introspect function bodies, so I documented the endpoints explicitly with `@extend_schema`. At a larger scale I would move to ViewSets, which do the same things declaratively.

**PUT vs PATCH.** PUT is a full update and requires all fields. PATCH is a partial update, implemented with the serializer's `partial=True` flag, so a client can send only the fields that changed.

**Errors.** Requesting a post that does not exist returns a 404 with a clear message. Validation failures return 400 with per-field errors from the serializer.

### Endpoints

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/register/` | No | Create account |
| POST | `/api/auth/login/` | No | Get access and refresh tokens |
| POST | `/api/auth/token/refresh/` | Refresh token | New access token |
| POST | `/api/auth/logout/` | Yes | Blacklist refresh token |
| DELETE | `/api/auth/delete/` | Yes | Delete own account |
| GET | `/api/posts/` | Yes | List all blogs |
| POST | `/api/posts/` | Yes | Create blog |
| GET | `/api/posts/{id}/` | Yes | View one blog |
| PUT / PATCH | `/api/posts/{id}/` | Author only | Update own blog |
| DELETE | `/api/posts/{id}/` | Author only | Delete own blog |

### How to test

Interactive docs at `http://127.0.0.1:8000/api/docs/`. Register, login, click Authorize and paste the access token, then use the post endpoints. To verify authorization, register a second user and attempt to PATCH the first user's post. It returns 403. A request with no token returns 401.

---

## Question 3: Mobile App Design

### Design decision: online, account-based

I chose an online design where the shop's data lives on a server tied to an account, not on the phone. The sales records are the business's books. If everything lived on the device and the phone was stolen, broke, or was reset, the owner would lose their records. Phone theft is a real risk here. With an account, any phone plus a login recovers everything, so a lost phone costs the owner a phone, not their business history.

The honest weakness of this choice is that no network means no recording sales. The practical fix I would add later is a small local queue: sales made during an outage are held on the phone and uploaded automatically when the connection returns.

### 1. Screens

1. **Register** (one time): name, shop name, email, password
2. **Login**: email, password. The app stays logged in after the first time so the owner does not type a password every morning
3. **Home / Today's Sales**: the screen the app opens on
4. **Record Sale**: a bottom sheet that slides up over Home
5. **Products**: list, edit and add products

I used bottom sheets for recording a sale and editing a product so the owner stays anchored on one screen instead of navigating a stack of pages. Fewer places to get lost.

### 2. Information on each screen

**Home / Today's Sales**
- Today's total in KSh in large text at the top, since this is the number the owner cares about most
- Stat cards: number of sales today, top selling product
- A list of today's individual sales (time, product, amount), most recent first
- A large Record Sale button, since the most frequent action should be one tap away

**Record Sale (bottom sheet)**
- Product list with a search box
- Quantity selected with plus and minus buttons instead of a text field
- The total for the sale calculated and shown automatically
- A confirmation line before saving, for example "1 x Soda, KSh 50", then a Save button

**Products**
- List of all products with name and selling price
- Tapping a product opens a bottom sheet to edit its name or price
- An add button at the bottom with a plus icon, opening a sheet with two fields: product name and selling price

### 3. Two things to make it easy for a non-technical owner

**Design for taps, not typing.** Recording a sale involves zero keyboard use: pick the product from a list, adjust quantity with plus and minus buttons, tap save. Typing is slow and error-prone, especially while a customer is waiting. Buttons and text are large because the owner may be using a small, older phone in a bright, busy shop. The only typing in daily use is the search box, and even that is optional for a small product list.

**Soft errors in plain language.** When something goes wrong the app says what happened and what to do next in simple words, for example "No connection. This sale is saved and will upload when you are back online." Never a crash, never a technical error code, never a dead end. Labels use everyday words like Record Sale and Today's Total rather than terms like Transaction or Revenue.

### 4. A mistake when recording a sale, and how the app handles it

**The mistake:** entering an invalid or wrong amount, such as a negative quantity, zero, or an accidental extra digit (recording 10 sodas instead of 1).

**Prevention:** quantity uses a plus/minus stepper that starts at 1, so a negative or zero quantity is impossible by construction. Jumping from 1 to 10 requires nine deliberate taps rather than one slipped keystroke. Before saving, the sheet shows a plain confirmation of exactly what will be recorded.

**Correction:** mistakes will still happen, so each sale in today's list has an undo/delete option with a confirmation. Deleting a wrong sale keeps the daily total honest, because the total always equals the sum of the sales shown in the list, so the owner can trust the number.

---

## Question 4: Relational Databases

**Code:** `question4/school.sql`

### 1. Tables

Three tables: `students`, `courses`, and `enrollments`. The first two hold the entities. The third exists because a student can take many courses and a course has many students, a many-to-many relationship, which relational databases model with a junction table.

### 2 and 3. Columns and primary keys

**students**

| Column | Type | Notes |
|---|---|---|
| `student_id` | INTEGER | Primary key, auto-increment |
| `first_name` | TEXT | |
| `last_name` | TEXT | |
| `email` | TEXT | UNIQUE |
| `date_of_birth` | DATE | |

**courses**

| Column | Type | Notes |
|---|---|---|
| `course_id` | INTEGER | Primary key, auto-increment |
| `course_name` | TEXT | e.g. "Introduction to Programming" |
| `course_code` | TEXT | UNIQUE, e.g. "CS101" |

**enrollments** (junction table)

| Column | Type | Notes |
|---|---|---|
| `enrollment_id` | INTEGER | Primary key, auto-increment |
| `student_id` | INTEGER | Foreign key to `students.student_id` |
| `course_id` | INTEGER | Foreign key to `courses.course_id` |
| `enrollment_date` | DATE | |

The enrollments table also has a `UNIQUE(student_id, course_id)` constraint so the same student cannot be enrolled in the same course twice. An alternative design uses the pair `(student_id, course_id)` as a composite primary key. I used a surrogate key plus the unique constraint, which is the convention ORMs like Django follow.

### 4. How students connect to courses

Through the `enrollments` table. Each row in it records one fact: this student is enrolled in this course, expressed as a pair of foreign keys. Neither `students` nor `courses` references the other directly. To answer "which students take course X", you join across all three tables using the foreign keys.

### 5. SQL query

List all students enrolled in "Introduction to Programming":

```sql
SELECT s.student_id, s.first_name, s.last_name
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses c     ON e.course_id  = c.course_id
WHERE c.course_name = 'Introduction to Programming';
```

Reading it in order: find the course row by name, follow `enrollments` to get the student IDs linked to that course, then follow those IDs into `students` to get the names.

The full schema, sample data and this query are in `question4/school.sql`. The repo also includes `question4/run_query.py`, which executes the script with plain Python (using the built-in `sqlite3` module), so no SQLite installation is needed to verify the result. With the sample data, the query returns the two students enrolled in the course and correctly excludes the student who is enrolled in a different course.
