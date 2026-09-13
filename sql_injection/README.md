# SQL Injection

## 1. Objective

Learn how SQL Injection works by attacking an intentionally vulnerable Flask application.

This scenario follows the following workflow:

1. Confirm normal login behavior
2. Perform SQL Injection
3. Inspect the vulnerable source code
4. Identify the root cause
5. Fix the vulnerability
6. Perform the same attack again
7. Verify that the vulnerability has been mitigated

## 2. Architecture

```text
┌─────────────────────────────────────────────┐
│ Docker                                      │
│                                             │
│  internal_nw                                │
│  ┌─────────────────┐                        │
│  │ attacker        │                        │
│  │ curl            │                        │
│  └────────┬────────┘                        │
│           │ HTTP                            │
│           ↓                                 │
│  ┌─────────────────┐                        │
│  │ app             │                        │
│  │ Flask           │                        │
│  └────────┬────────┘                        │
│           │ SQLite                          │
│           ↓                                 │
│  ┌─────────────────┐                        │
│  │ SQLite Database │                        │
│  └─────────────────┘                        │
│                                             │
│  Network: internal_nw                       │
│  External access: Disabled                  │
└─────────────────────────────────────────────┘
```

The application does not publish any port to the host.

The attacker accesses the application from inside the Docker network using:

```text
http://app:8000
```

## 3. Directory Structure

```text
sql_injection/
├── docker-compose.yaml
├── README.md
└── app/
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py
    └── init_db.py
```

The common Docker Compose configuration is located at:

```text
config/
└── docker-compose.default.yaml
```

The common network is:

```text
internal_nw
```

## 4. Docker Compose Configuration

This scenario includes the common Compose configuration:

```yaml
include:
  - ../config/docker-compose.default.yaml
```

The common configuration defines the isolated network:

```yaml
networks:
  internal_nw:
    driver: bridge
    internal: true
```

The scenario's containers join this network:

```yaml
networks:
  - internal_nw
```

This prevents the intentionally vulnerable application from being directly exposed to the external network.

## 5. Start the Lab

Move to the scenario directory:

```bash
cd sql_injection
```

Start the containers:

```bash
docker compose up --build -d
```

Check the container status:

```bash
docker compose ps
```

Both `app` and `attacker` should be running.

## 6. Enter the Attacker Container

Enter the attacker container:

```bash
docker compose exec attacker sh
```

The application can be accessed from this container using:

```text
http://app:8000
```

The service name `app` is resolved by Docker's internal DNS.

## 7. Confirm Normal Login

The application provides a login endpoint:

```text
POST /login
```

Use the following credentials:

```text
username: alice
password: password123
```

Execute:

```bash
curl -X POST http://app:8000/login \
  -d 'username=alice&password=password123'
```

Expected result:

```text
Login successful: alice
```

Now verify that an incorrect password fails:

```bash
curl -X POST http://app:8000/login \
  -d 'username=alice&password=wrong'
```

Expected result:

```text
Login failed
```

The HTTP status should be `401`.

## 8. Perform SQL Injection

The login functionality is intentionally vulnerable to SQL Injection.

Try the following payload:

```bash
curl -X POST http://app:8000/login \
  --data-urlencode "username=' OR '1'='1" \
  --data-urlencode "password=password123"
```

Expected result:

```text
Login successful: alice
```

The important point is not simply that the login was bypassed.

The goal is to understand why the input changed the meaning of the SQL query.

## 9. Analyze the Vulnerability

Open:

```text
app/app.py
```

The login function constructs the SQL query as follows:

```python
query = (
    "SELECT id, username FROM users "
    f"WHERE username = '{username}' AND password = '{password}'"
)
```

The user-controlled values are directly concatenated into the SQL statement.

For normal input:

```text
username = alice
password = password123
```

the resulting query is approximately:

```sql
SELECT id, username
FROM users
WHERE username = 'alice'
AND password = 'password123'
```

However, SQL Injection payloads can introduce SQL syntax into the query.

The root cause is:

```text
User input
    ↓
String concatenation
    ↓
SQL statement
    ↓
User input becomes part of SQL syntax
```

## 10. Inspect the Database

The database is initialized by:

```text
app/init_db.py
```

The following users are created:

```text
alice / password123
bob   / qwerty123
```

The database also contains a secret value:

```text
SQLI_LAB{login_bypass_success}
```

This secret is intentionally included as the target data for this exercise.

## 11. Retrieve the Secret

The application provides:

```text
GET /secret
```

From the attacker container:

```bash
curl http://app:8000/secret
```

Expected result:

```text
flag: SQLI_LAB{login_bypass_success}
```

## 12. Root Cause

The vulnerability exists because user input is directly incorporated into an SQL statement.

### Vulnerable

```python
query = (
    "SELECT id, username FROM users "
    f"WHERE username = '{username}' AND password = '{password}'"
)
```

The application does not properly separate:

```text
SQL structure
```

from:

```text
User-provided data
```

## 13. Fix

Replace the dynamically constructed SQL statement with a parameterized query.

Example:

```python
query = (
    "SELECT id, username FROM users "
    "WHERE username = ? AND password = ?"
)

user = conn.execute(
    query,
    (username, password)
).fetchone()
```

With parameterized queries, the input is treated as data rather than SQL syntax.

## 14. Verify the Fix

Rebuild the application after applying the fix:

```bash
docker compose up --build -d
```

Repeat the previous SQL Injection attempt:

```bash
curl -X POST http://app:8000/login \
  --data-urlencode "username=' OR '1'='1" \
  --data-urlencode "password=x"
```

The attack should no longer result in:

```text
Login successful
```

The expected result is:

```text
Login failed
```

This confirms that the original SQL Injection vulnerability has been mitigated.

## 15. Cleanup

Exit the attacker container:

```bash
exit
```

Stop the containers:

```bash
docker compose down
```

To remove the database volume as well:

```bash
docker compose down -v
```

## 16. Learning Notes

After completing the exercise, document the following:

### Attack

- What input was used?
- What happened?
- Why did the attack succeed?

### Root Cause

- Which code introduced the vulnerability?
- How was user input incorporated into the SQL statement?

### Mitigation

- What was changed?
- Why does the parameterized query prevent the original attack?

### Verification

- Was the original attack repeated after the fix?
- What was the result?

The goal is to understand the relationship between the attack, the vulnerable implementation, and the mitigation rather than simply obtaining a successful payload.
