# Assignment Answers — HR Policy Assistant

**Project:** Project 1: HR Policy Assistant — GenAI Exam  
**Document:** Enso Group HR Policy Manual (79 pages) — `hr_manual.pdf`  
**Execution Timestamp:** 2026-10-23  
**Status:** All 5 required questions evaluated and verified against the official manual.

---

## Summary of Answers

| Q# | Question | Grounded Answer | Status | Source Page | Policy Section | Verbatim Evidence Quote |
|---|---|---|---|---|---|---|
| **1** | How many days of Privilege Leave (PL) does a permanent employee get per year? | Permanent employees are entitled to **12 days of Privilege Leave (PL)** per calendar year (1st January – 31st December). | **Found** | **Page 60** | `SECTION - IV - [G] Leave Policy` | *"Privilege Leave (PL) – 12 days... All permanent employees are eligible to avail PL. PL is calculated for a period of one calendar year (1st Jan-31st Dec). 12 days PL is allowed to each employee."* |
| **2** | What is the probation period for employees up to Senior Manager? | The probation period for all employees up to Senior Manager is **3 months** from the date of joining. | **Found** | **Page 42** | `SECTION - IV - [B] Probation Policy` | *"All employees up to Sr. Manager would be placed in Probation for a period of 3 months from the date of their joining. All employees above Sr. Manager will be treated as confirmed employees from the date of joining."* |
| **3** | What is the company's health-insurance premium amount? | **Not found** | **Not found** | *N/A* | *N/A* | The manual does not specify or establish any health-insurance premium amount. The system strictly adheres to grounding rules and outputs `Not found`. |
| **4** | What is the current GST rate in India? | **Not found** | **Not found** | *N/A* | *N/A* | External statutory GST rates are not part of the Enso Group HR Policy Manual. The system refuses external knowledge and outputs `Not found`. |
| **5** | How many days of maternity leave are given? | Eligible confirmed female staff (who worked at least 80 days in the preceding 12 months) receive **12 weeks (90 days)** of Maternity Leave with pay (of which not more than 6 weeks / 45 days should precede delivery). | **Found** | **Page 62** | `SECTION - IV - [G] Leave Policy` | *"The company will provide a total of 12 weeks(- 90days) as ML with pay, of which not more than 6 weeks(- 45days) should precede the expected date of delivery."* |

---

## Detailed Evidence & Policy Citations

### Question 1: Privilege Leave (PL)
- **Question:** How many days of Privilege Leave (PL) does a permanent employee get per year?
- **Found Answer:** Permanent employees get **12 days** of Privilege Leave (PL) per calendar year (1st Jan to 31st Dec).
- **Cited Page:** Page 60 (Document Header: `HR Manual - 60`)
- **Policy Heading:** `SECTION - IV - [G] Leave Policy`
- **Rules Cited from Document:**
  - Leave year runs from 1st January to 31st December.
  - Applicable to all permanent employees of Enso Group (not contract employees).
  - Unavailed PL cannot be carried forward to the next calendar year.
  - Accumulated leave balance can be en-cashed only upon full & final settlement at basic pay.
  - Requires email application to manager at least one week in advance.

---

### Question 2: Probation Period
- **Question:** What is the probation period for employees up to Senior Manager?
- **Found Answer:** **3 months** from the date of joining.
- **Cited Page:** Page 42 (Document Header: `HR Manual - 42`)
- **Policy Heading:** `SECTION - IV - [B] Probation Policy`
- **Rules Cited from Document:**
  - *"All employees up to Sr. Manager would be placed in Probation for a period of 3 months from the date of their joining."*
  - *"All employees above Sr. Manager will be treated as confirmed employees from the date of joining."*
  - A Probation Review Report (PRR) is submitted two weeks before the probation period ends.

---

### Question 3: Health Insurance Premium Amount
- **Question:** What is the company's health-insurance premium amount?
- **Answer:** **Not found**
- **Grounding Explanation:**
  - Complete full-text search across all 79 pages of `hr_manual.pdf` confirms zero mentions of health insurance premiums or mediclaim premium amounts.
  - The only insurance mentioned in the manual is travel insurance during company business trips (Page 71).
  - Because the document does not establish any premium amount, the pipeline returns exactly `Not found`.

---

### Question 4: GST Rate in India
- **Question:** What is the current GST rate in India?
- **Answer:** **Not found**
- **Grounding Explanation:**
  - GST (Goods and Services Tax) is an external Indian tax law, completely absent from the internal HR manual.
  - The pipeline refuses to inject external pre-trained knowledge and strictly replies `Not found`.

---

### Question 5: Maternity Leave
- **Question:** How many days of maternity leave are given?
- **Found Answer:** **12 weeks (90 days)** of paid leave.
- **Cited Page:** Page 62 (Document Header: `HR Manual - 62`)
- **Policy Heading:** `SECTION - IV - [G] Leave Policy`
- **Rules Cited from Document:**
  - *"The company will provide a total of 12 weeks(- 90days) as ML with pay, of which not more than 6 weeks(- 45days) should precede the expected date of delivery."*
  - Eligibility: Confirmed female staff who worked at least 80 days in the preceding 12 months.
  - In case of miscarriage or medical termination, four weeks of leave with pay is permitted.
  - Approval must be obtained from the HOD (Head of Department).

---

## Test Automation Results

The test suite executed via `test_questions.py` yielded:
```json
{
  "test_summary": "ALL TESTS PASSED",
  "total_tests": 5,
  "passed": 5,
  "failed": 0
}
```
All answers are directly backed by verified document excerpts.
