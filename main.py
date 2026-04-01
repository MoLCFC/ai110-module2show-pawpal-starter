"""CLI demo for PawPal+ — run with: python main.py"""

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def _fmt_line(t: Task) -> str:
    status = "done" if t.completed else "pending"
    return (
        f"  [{t.time_str}] {t.pet_name}: {t.title} "
        f"({t.duration_minutes} min, {t.priority}, {status})"
    )


def main() -> None:
    today = date.today()
    owner = Owner(name="Jordan")
    mochi = owner.add_pet("Mochi", "dog")
    whiskers = owner.add_pet("Whiskers", "cat")

    mochi.add_task(
        Task(
            "Morning walk",
            "08:00",
            25,
            priority="high",
            frequency="daily",
            task_date=today,
        )
    )
    mochi.add_task(
        Task(
            "Evening feed",
            "18:00",
            10,
            priority="medium",
            frequency="once",
            task_date=today,
        )
    )
    whiskers.add_task(
        Task(
            "Medication",
            "08:00",
            5,
            priority="high",
            frequency="daily",
            task_date=today,
        )
    )

    sched = Scheduler(owner)
    all_t = sched.collect_all_tasks()

    print("=== All tasks (sorted by time only) ===")
    for t in sched.sort_by_time(all_t):
        print(_fmt_line(t))

    print("\n=== All tasks (priority, then time) ===")
    for t in sched.sort_by_priority_then_time(all_t):
        print(_fmt_line(t))

    print("\n=== Conflict warnings ===")
    for w in sched.detect_conflicts(all_t):
        print(" *", w)

    print("\n=== Today's schedule (plan) ===")
    plan, reasons, extra = sched.generate_daily_plan(today, minutes_available=180)
    for t in plan:
        print(_fmt_line(t))
    for r in reasons[:3]:
        print("  ->", r)
    if len(reasons) > 3:
        print(f"  -> ... ({len(reasons) - 3} more lines)")
    for e in extra:
        print(" !", e)

    print("\n=== Mark Mochi's walk complete (daily -> next day) ===")
    walk_id = next(
        x.task_id for x in mochi.tasks if x.title == "Morning walk" and not x.completed
    )
    new_task = mochi.mark_task_complete(walk_id)
    if new_task:
        print(f"  Next walk scheduled: {new_task.task_date} at {new_task.time_str}")

    print("\n=== Filter: incomplete only ===")
    for t in sched.filter_tasks(sched.collect_all_tasks(), completed=False):
        print(_fmt_line(t))

    # Demo: two tasks same time next week for conflict demo
    print("\n=== Same-time demo (tomorrow) ===")
    tomorrow = today + timedelta(days=1)
    mochi.add_task(
        Task("Play", "12:00", 15, priority="low", frequency="once", task_date=tomorrow)
    )
    mochi.add_task(
        Task("Training", "12:00", 20, priority="medium", frequency="once", task_date=tomorrow)
    )
    for w in sched.detect_conflicts(sched.collect_all_tasks()):
        print(" *", w)


if __name__ == "__main__":
    main()
