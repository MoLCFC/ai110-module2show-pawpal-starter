"""Tests for PawPal+ scheduling and domain behavior."""

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_status() -> None:
    t = Task("Walk", "09:00", 20, task_date=date(2026, 4, 1))
    assert t.completed is False
    t.mark_complete()
    assert t.completed is True


def test_adding_task_increases_pet_task_count() -> None:
    p = Pet("Rex", "dog")
    assert len(p.tasks) == 0
    p.add_task(Task("Feed", "07:00", 5, task_date=date(2026, 4, 1)))
    assert len(p.tasks) == 1
    p.add_task(Task("Walk", "10:00", 30, task_date=date(2026, 4, 1)))
    assert len(p.tasks) == 2


def test_sort_by_time_chronological() -> None:
    d = date(2026, 4, 1)
    a = Task("A", "14:00", 10, task_date=d)
    b = Task("B", "08:30", 10, task_date=d)
    c = Task("C", "08:00", 10, task_date=d)
    out = Scheduler.sort_by_time([a, b, c])
    assert [x.title for x in out] == ["C", "B", "A"]


def test_sort_by_priority_then_time() -> None:
    d = date(2026, 4, 1)
    low = Task("L", "09:00", 5, priority="low", task_date=d)
    high = Task("H", "10:00", 5, priority="high", task_date=d)
    med = Task("M", "09:00", 5, priority="medium", task_date=d)
    out = Scheduler.sort_by_priority_then_time([low, high, med])
    assert [x.title for x in out] == ["H", "M", "L"]


def test_weekly_recurrence_advances_by_seven_days() -> None:
    start = date(2026, 4, 1)
    pet = Pet("P", "dog")
    t = Task("Groom", "14:00", 45, frequency="weekly", task_date=start)
    pet.add_task(t)
    new_t = pet.mark_task_complete(t.task_id)
    assert new_t is not None
    assert new_t.task_date == start + timedelta(weeks=1)


def test_daily_recurrence_creates_next_day_task() -> None:
    today = date(2026, 4, 1)
    pet = Pet("P", "cat")
    t = Task(
        "Meds",
        "08:00",
        5,
        frequency="daily",
        task_date=today,
    )
    pet.add_task(t)
    tid = t.task_id
    new_t = pet.mark_task_complete(tid)
    assert t.completed is True
    assert new_t is not None
    assert new_t.task_date == today + timedelta(days=1)
    assert new_t.task_id != tid


def test_conflict_detection_duplicate_times() -> None:
    d = date(2026, 4, 1)
    t1 = Task("A", "12:00", 10, task_date=d, pet_name="X")
    t2 = Task("B", "12:00", 15, task_date=d, pet_name="Y")
    warns = Scheduler.detect_conflicts([t1, t2])
    assert len(warns) == 1
    assert "12:00" in warns[0]


def test_filter_by_completed_and_pet() -> None:
    d = date(2026, 4, 1)
    a = Task("a", "09:00", 5, task_date=d, pet_name="P1", completed=False)
    b = Task("b", "10:00", 5, task_date=d, pet_name="P1", completed=True)
    c = Task("c", "11:00", 5, task_date=d, pet_name="P2", completed=False)
    tasks = [a, b, c]
    inc = Scheduler.filter_tasks(tasks, completed=False)
    assert len(inc) == 2
    p1 = Scheduler.filter_tasks(tasks, pet_name="P1")
    assert len(p1) == 2


def test_generate_plan_respects_day() -> None:
    owner = Owner("O")
    pet = owner.add_pet("Pet", "dog")
    day = date(2026, 4, 5)
    pet.add_task(Task("Job", "10:00", 30, task_date=day))
    sched = Scheduler(owner)
    plan, _, extra = sched.generate_daily_plan(day, minutes_available=60)
    assert len(plan) == 1
    assert plan[0].title == "Job"
    plan_empty, _, _ = sched.generate_daily_plan(date(2026, 1, 1), 60)
    assert plan_empty == []
