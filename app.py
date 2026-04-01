"""PawPal+ Streamlit UI — uses pawpal_system for scheduling."""

from datetime import date, datetime

import streamlit as st

from pawpal_system import Owner, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# --- Session state: persistent owner graph ---
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(st.session_state.owner)
if "selected_pet" not in st.session_state:
    st.session_state.selected_pet = ""

owner: Owner = st.session_state.owner
sched: Scheduler = st.session_state.scheduler

st.title("🐾 PawPal+")
st.caption("Plan pet care tasks with priority-aware scheduling and conflict checks.")

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** helps you track care tasks, respect constraints, and generate a daily plan
with short explanations. Tasks are sorted by **priority** (high → medium → low), then **time**.
"""
    )

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Owner")
    new_owner = st.text_input("Owner name", value=owner.name, key="owner_name_input")
    if new_owner != owner.name:
        owner.name = new_owner

    st.subheader("Add a pet")
    np_name = st.text_input("Pet name", value="Mochi", key="new_pet_name")
    np_species = st.selectbox("Species", ["dog", "cat", "other"], key="new_pet_species")
    if st.button("Add pet"):
        if not np_name.strip():
            st.warning("Enter a pet name.")
        elif owner.get_pet(np_name.strip()):
            st.warning("A pet with that name already exists.")
        else:
            owner.add_pet(np_name.strip(), np_species)
            st.success(f"Added {np_name.strip()}!")
            st.rerun()

with col_right:
    st.subheader("Your pets")
    if not owner.pets:
        st.info("No pets yet — add one on the left.")
    else:
        pet_names = [p.name for p in owner.pets]
        st.session_state.selected_pet = st.selectbox(
            "Pet for new tasks",
            pet_names,
            index=min(
                max(0, pet_names.index(st.session_state.selected_pet))
                if st.session_state.selected_pet in pet_names
                else 0,
                len(pet_names) - 1,
            ),
        )

st.divider()
st.subheader("Add task")

c1, c2, c3, c4 = st.columns(4)
with c1:
    task_title = st.text_input("Task title", value="Morning walk")
with c2:
    task_time = st.text_input("Time (HH:MM)", value="08:00")
with c3:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with c4:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

c5, c6, c7 = st.columns(3)
with c5:
    frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
with c6:
    task_day = st.date_input("Task date", value=date.today())
with c7:
    minutes_budget = st.number_input(
        "Minutes available (for plan)",
        min_value=30,
        max_value=1440,
        value=240,
        step=30,
    )

if st.button("Add task"):
    pet_name = st.session_state.get("selected_pet") or ""
    if not owner.pets:
        st.warning("Add a pet first.")
    else:
        pet = owner.get_pet(pet_name)
        if not pet:
            st.error("Select a valid pet.")
        else:
            try:
                datetime.strptime(task_time.strip(), "%H:%M")
            except ValueError:
                st.error("Use HH:MM for time (e.g. 08:30).")
            else:
                t = Task(
                    title=task_title.strip(),
                    time_str=task_time.strip(),
                    duration_minutes=int(duration),
                    priority=priority,
                    frequency=frequency,
                    task_date=task_day,
                )
                pet.add_task(t)
                st.success(f"Added “{t.title}” for {pet.name}.")
                st.rerun()

st.divider()
st.subheader("Today’s plan")

plan_day = st.date_input("Plan for date", value=date.today(), key="plan_day")
if st.button("Generate schedule"):
    ordered, reasons, extra = sched.generate_daily_plan(plan_day, int(minutes_budget))
    conflicts = sched.detect_conflicts(sched.tasks_for_date(plan_day))

    if conflicts:
        for w in conflicts:
            st.warning(w)
    else:
        st.success("No same-start-time conflicts for this date.")

    if not ordered:
        st.info("No incomplete tasks for that date.")
    else:
        rows = []
        for t in ordered:
            rows.append(
                {
                    "Time": t.time_str,
                    "Pet": t.pet_name,
                    "Task": t.title,
                    "Min": t.duration_minutes,
                    "Priority": t.priority,
                }
            )
        st.table(rows)

        with st.expander("Why this order", expanded=True):
            for r in reasons:
                st.markdown(f"- {r}")

    for e in extra:
        st.warning(e)

st.divider()
st.subheader("All tasks (sorted)")

view_pet = st.selectbox(
    "Filter by pet",
    ["(all)"] + [p.name for p in owner.pets],
    key="filter_pet",
)
tasks = sched.collect_all_tasks()
if view_pet != "(all)":
    tasks = sched.filter_tasks(tasks, pet_name=view_pet)

tasks_sorted = sched.sort_by_priority_then_time(tasks)

if not tasks_sorted:
    st.info("No tasks yet.")
else:
    for t in tasks_sorted:
        badge = "✅" if t.completed else "⬜"
        st.markdown(
            f"{badge} **{t.pet_name}** · {t.title} — `{t.time_str}` "
            f"({t.duration_minutes} min, {t.priority}, {t.frequency}) · {t.task_date}"
        )
        if not t.completed:
            if st.button(f"Mark done: {t.title}", key=f"done_{t.task_id}"):
                pet = owner.get_pet(t.pet_name)
                if pet:
                    pet.mark_task_complete(t.task_id)
                    st.rerun()

# Global conflict overview (all dates)
all_conf = sched.detect_conflicts(sched.collect_all_tasks())
if all_conf:
    st.divider()
    st.subheader("Conflict overview")
    for w in all_conf:
        st.caption(w)
