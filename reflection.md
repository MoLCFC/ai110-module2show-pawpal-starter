# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- **Owner**: Holds the pet list and exposes `all_tasks()` so scheduling can see every task.
- **Pet**: Owns a list of `Task` objects; `add_task` sets `pet_name`; `mark_task_complete` handles recurrence.
- **Task**: Dataclass for one activity (time, duration, priority, frequency, date, completion).
- **Scheduler**: Stateless helper bound to an `Owner`; sorts, filters, detects same-time conflicts, and builds a daily plan with explanation strings.

Relationships: Owner → many Pets → many Tasks; Scheduler uses Owner to read data.

**b. Design changes**

- **Recurrence on `Pet`**: Placing `mark_task_complete` on `Pet` keeps task lists coherent and avoids the scheduler mutating tasks without knowing which pet owns them.
- **Conflicts**: Only exact same **date + start time** are flagged (not overlapping intervals) to stay lightweight and predictable for the course; see tradeoffs below.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- **Priority** (high → medium → low) is applied first, then **clock time** within the same priority band.
- **Calendar date** scopes which tasks appear in “today’s plan.”
- **Minutes available** is compared to the **sum of durations**; if over budget, a warning is shown (tasks are not auto-dropped).

**b. Tradeoffs**

- **Exact-time conflicts only**: The scheduler does not check whether two tasks **overlap** (e.g. 08:00–08:30 vs 08:15–08:20). That keeps the implementation small and avoids false positives when durations are uncertain, but it can miss real double-bookings. A future version could merge intervals per pet and detect overlaps.

---

## 3. AI Collaboration

**a. How you used AI**

- Brainstorming class boundaries and a minimal conflict strategy.
- Scaffolding tests for sort, recurrence, and conflicts.
- Wiring Streamlit `session_state` to a single `Owner` instance.

**b. Judgment and verification**

- Rejected “drop lowest-priority tasks automatically” when over budget — instead **warn** so the human decides; clearer for a pet-care scenario.
- Verified behavior with `pytest` and `python main.py` on Windows (ASCII-safe CLI output).

---

## 4. Testing and Verification

**a. What you tested**

- Task completion, pet task counts, chronological sort, priority+time sort, daily recurrence, conflict messages, filters, and daily plan date scoping.

**b. Confidence**

- **Medium-high** for the behaviors under test. Next edge cases: **weekly** recurrence across month boundaries, invalid `HH:MM` inputs in the UI, and many tasks at identical times.

---

## 5. Reflection

**a. What went well**

- Clear split between domain (`pawpal_system`) and UI (`app.py`) made testing straightforward.

**b. What you would improve**

- Task **editing** in the UI, JSON **persistence**, and **overlap-based** conflict detection.

**c. Key takeaway**

- The “lead architect” still owns requirements, tradeoffs, and test design; AI accelerates coding once those are explicit.
