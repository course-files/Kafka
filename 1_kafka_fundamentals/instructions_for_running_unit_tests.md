# Unit Tests

## What Is a Unit Test?

A **unit test** is a small, focused piece of code that checks whether one
specific part of your program works correctly.

The word "unit" means the smallest testable piece of your code — usually a
single function. Instead of running your entire application and manually
checking whether it works, unit tests do that checking automatically.

Think of unit tests like this:

> You are baking bread. Instead of waiting until the entire loaf is done to
> find out if it tastes right, you test each ingredient separately:
> - Does the flour weigh the right amount?
> - Is the yeast still active?
> - Is the water the right temperature?
>
> If each unit is correct, the whole loaf is more likely to succeed.

---

## Why Write Unit Tests?

1. **Catch bugs early** — A bug caught during testing costs far less to fix
   than one caught in production.

2. **Confidence when changing code** — If you refactor a function, running
   the tests immediately tells you whether you broke something.

3. **Documentation** — A well-written test shows exactly what a function is
   supposed to do and what inputs it expects.

4. **Professional standard** — All serious software projects use automated
   tests. Learning to write them now prepares you for industry.

---

## What Is PyTest?

PyTest is a Python testing framework. It finds your test files automatically
and runs all your test functions, reporting which ones passed and which failed.

A test function in PyTest:
- Must start with the word `test_`
- Uses `assert` statements to check whether something is true
- Lives in a file that starts with `test_`

```python
# A simple example
def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5    # This passes
    assert add(0, 0) == 0    # This passes
    assert add(-1, 1) == 0   # This passes
```

If an `assert` statement is False, the test fails and PyTest tells you exactly
which line failed and what the actual value was.

---

## Directory Structure

```
tests/
├── README.md            ← You are reading this
├── conftest.py          ← Shared test fixtures (setup code reused across tests)
├── test_lab1.py         ← Tests for Lab 1 (Kafka Fundamentals)
├── test_lab2.py         ← Tests for Lab 2 (Containerised Microservices)
├── test_lab3.py         ← Tests for Lab 3 (CDC Data Pipeline)
└── test_lab4.py         ← Tests for Lab 4 (Data Analytics)
```

---

## How to Run the Tests

### Step 1 — Install PyTest

```bash
pip install pytest
```

### Step 2 — Run all tests

```bash
# From the tests/ directory
pytest

# With detailed output (shows each test name)
pytest -v

# With even more detail (shows print statements inside tests)
pytest -v -s
```

### Step 3 — Run tests for one lab only

```bash
pytest test_producer_order_old.py -v
pytest test_lab2.py -v
pytest test_lab3.py -v
pytest test_lab4.py -v
```

### Step 4 — Run a single test function

```bash
pytest test_lab3.py::test_bulk_order_flag_is_set_when_quantity_exceeds_five -v
```

---

## Reading the Test Output

When all tests pass:
```
=================== 12 passed in 0.45s ===================
```

When a test fails:
```
FAILED test_lab3.py::test_bulk_order_flag - AssertionError: assert 0 == 1
```

PyTest shows you:
- Which test failed
- Which line the failure occurred on
- What the actual value was vs what you expected

---

## Key Vocabulary

| Term | Meaning |
|------|---------|
| **Test function** | A function starting with `test_` that checks one behaviour |
| **Assertion** | An `assert` statement — the actual check |
| **Fixture** | Shared setup code that multiple tests can reuse (in conftest.py) |
| **Pass** | The assertion was True — the code works as expected |
| **Fail** | The assertion was False — the code has a bug |
| **Test suite** | The full collection of all your tests |
