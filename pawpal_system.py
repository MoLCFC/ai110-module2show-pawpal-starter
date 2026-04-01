"""PawPal+ domain model and scheduling logic."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Iterable, Literal, Optional

PriorityLevel = Literal["low", "medium", "high"]
Frequency = Literal["once", "daily", "weekly"]

PRIORITY_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}


def _time_to_minutes(hhmm: str) -> int:
    """Convert 'HH:MM' to minutes since midnight for sorting."""
    parts = hhmm.strip().split(":")
    h, m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
    return h * 60 + m


def _new_task_id() -> str:
    """Return a short unique id for tasks."""
    return uuid.uuid4().hex[:10]


@dataclass
class Task:
    """A single care activity for a pet."""

    title: str
    time_str: str
    duration_minutes: int
    priority: PriorityLevel = "medium"
    frequency: Frequency = "once"
    completed: bool = False
    task_date: date = field(default_factory=date.today)
    pet_name: str = ""
    task_id: str = field(default_factory=_new_task_id)

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True


@dataclass
class Pet:
    """A pet owned by an owner, with its own task list."""

    name: str
    species: str = "other"
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet (sets pet_name)."""
        task.pet_name = self.name
        self.tasks.append(task)

    def mark_task_complete(self, task_id: str) -> Optional[Task]:
        """Mark a task complete; for recurring tasks, append the next occurrence."""
        for t in self.tasks:
            if t.task_id != task_id:
                continue
            t.mark_complete()
            if t.frequency == "once":
                return None
            delta = timedelta(days=1) if t.frequency == "daily" else timedelta(weeks=1)
            next_task = Task(
                title=t.title,
                time_str=t.time_str,
                duration_minutes=t.duration_minutes,
                priority=t.priority,
                frequency=t.frequency,
                completed=False,
                task_date=t.task_date + delta,
                pet_name=self.name,
            )
            self.tasks.append(next_task)
            return next_task
        return None


@dataclass
class Owner:
    """Pet owner; holds multiple pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, name: str, species: str = "other") -> Pet:
        """Register a new pet."""
        pet = Pet(name=name, species=species)
        self.pets.append(pet)
        return pet

    def get_pet(self, name: str) -> Optional[Pet]:
        """Find a pet by name (case-sensitive)."""
        for p in self.pets:
            if p.name == name:
                return p
        return None

    def all_tasks(self) -> list[Task]:
        """Flatten tasks from every pet."""
        out: list[Task] = []
        for pet in self.pets:
            out.extend(pet.tasks)
        return out


class Scheduler:
    """Plans and analyzes tasks across an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler bound to an owner."""
        self.owner = owner

    def collect_all_tasks(self) -> list[Task]:
        """Return every task from every pet."""
        return self.owner.all_tasks()

    def tasks_for_date(self, day: date) -> list[Task]:
        """Tasks scheduled on a given calendar day."""
        return [t for t in self.collect_all_tasks() if t.task_date == day]

    @staticmethod
    def sort_by_time(tasks: Iterable[Task]) -> list[Task]:
        """Sort tasks by clock time (HH:MM)."""
        return sorted(tasks, key=lambda t: _time_to_minutes(t.time_str))

    @staticmethod
    def sort_by_priority_then_time(tasks: Iterable[Task]) -> list[Task]:
        """Sort by priority (high first), then by time."""
        return sorted(
            tasks,
            key=lambda t: (PRIORITY_ORDER.get(t.priority, 99), _time_to_minutes(t.time_str)),
        )

    @staticmethod
    def filter_tasks(
        tasks: Iterable[Task],
        *,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> list[Task]:
        """Filter by completion status and/or pet name."""
        out = list(tasks)
        if completed is not None:
            out = [t for t in out if t.completed == completed]
        if pet_name is not None:
            out = [t for t in out if t.pet_name == pet_name]
        return out

    @staticmethod
    def detect_conflicts(tasks: Iterable[Task]) -> list[str]:
        """Report tasks that share the same date and start time (lightweight check)."""
        by_key: dict[tuple[date, str], list[Task]] = {}
        for t in tasks:
            key = (t.task_date, t.time_str)
            by_key.setdefault(key, []).append(t)

        warnings: list[str] = []
        for (d, tm), group in by_key.items():
            if len(group) < 2:
                continue
            labels = ", ".join(f"{t.pet_name}: {t.title}" for t in group)
            warnings.append(
                f"Same start time {tm} on {d.isoformat()}: {labels}. "
                "Consider staggering these tasks."
            )
        return warnings

    def generate_daily_plan(
        self,
        day: date,
        minutes_available: int,
    ) -> tuple[list[Task], list[str], list[str]]:
        """
        Build an ordered plan for one day with explanations.

        Returns (ordered_tasks, reason_lines, extra_warnings).
        """
        candidates = [
            t
            for t in self.tasks_for_date(day)
            if not t.completed
        ]
        ordered = self.sort_by_priority_then_time(candidates)
        reasons: list[str] = []
        for t in ordered:
            pr = t.priority
            tm = t.time_str
            reasons.append(
                f"{t.pet_name} - {t.title} at {tm} ({t.duration_minutes} min, {pr} priority): "
                f"placed after higher-priority or earlier-time items for that day."
            )

        total_min = sum(t.duration_minutes for t in ordered)
        extra: list[str] = []
        if total_min > minutes_available:
            extra.append(
                f"Total planned time ({total_min} min) exceeds available time "
                f"({minutes_available} min); consider dropping low-priority items or rescheduling."
            )

        return ordered, reasons, extra
