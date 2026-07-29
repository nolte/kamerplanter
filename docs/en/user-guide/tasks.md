# Tasks

Kamerplanter combines manually created tasks, automatically generated care reminders, and task packages created from workflow templates into a single shared queue. You retain full control at all times: tasks can be adjusted, edited in bulk, and managed flexibly.

---

## Prerequisites

- At least one plant or an active planting run
- For automatic care reminders: a care profile (created automatically on first access) — see [Care Reminders](care-reminders.md)

---

## Tasks at a Glance

Open **Tasks** in the navigation (`/aufgaben/queue`). The overview groups all entries by urgency:

- **Overdue**: Past the due date (marked red)
- **Today**: Due today
- **This Week**: Due within the next 7 days
- **Future**: Everything else without a fixed due date, or due later

Use the **Source** filter (All / Tasks / Care) to show only manually or workflow-created tasks, only automatic care reminders, or both together.

Each task shows:

- Title and category
- Associated plant or planting run
- Priority (Low / Medium / High / Critical), if it differs from "Medium"
- Due date

---

## Task Categories

Kamerplanter has twelve task categories:

| Category | Description |
|----------|-------------|
| Maintenance | General care work |
| Feeding | Fertilization events |
| Training | High-/low-stress training (HST/LST) measures |
| Pruning | Cutting back |
| Defoliation (ausgeizen) | Removing side shoots (mainly tomatoes) |
| Transplant | Repotting appointments |
| Plant Protection | Integrated Pest Management (IPM) measures |
| Harvest | Harvest appointments |
| Observation | Maturity observation, inspection rounds |
| Care Reminder | Automatically generated from the care profile |
| Seasonal Task | Tasks tied to the season |
| Phenological Task | Tasks tied to natural events |

<!-- Source: src/backend/app/common/enums.py (TaskCategory) -->

!!! note "No dedicated \"Watering\" task type"
    There is no dedicated "Watering" category. Automatic watering reminders run under the **Care Reminder** category; manual watering tasks are created under **Maintenance** or **Observation**, depending on context.

---

## Where Tasks Come From

- **Created manually**: via the **Create Task** button
- **From workflow templates**: by applying a workflow template (see below)
- **Automatically as a care reminder**: from a plant's care profile (watering, fertilizing, repotting, pest check, location check, humidity check) — see [Care Reminders](care-reminders.md)

---

## Creating a Manual Task

### Step 1: Add a New Task

Click **Create Task** in the task overview.

### Step 2: Describe the Task

| Field | Description |
|-------|-------------|
| Name | Short, clear description of the task (required) |
| Instruction | Step-by-step guidance for carrying out the task |
| Category | One of the twelve task categories |
| Due Date | When must the task be completed? |
| Priority | Low / Medium / High / Critical |
| Estimated Duration (min) | For time planning |
| Plant | Assignment to a plant |

Additional fields — **Skill Level**, **Recurrence**, **Assigned To**, **Timer Duration/Label**, and **Tags** — only appear from the "Intermediate" experience level onward (Settings → Experience Level).

### Step 3: Checklist (Optional)

Add as many checklist items as you like (press Enter to confirm). The checklist is for your own overview while carrying out the task — it does not block completion.

### Step 4: Save

The task appears immediately in the task overview and in the calendar.

---

## Marking a Task as Complete

### Completing a Single Task

1. Open the task by clicking its title.
2. Click **Start** to set it to in progress (optional, activates the timer if configured).
3. Click **Complete**. Optionally enter notes, the actual duration, and a difficulty and quality rating (1–5).
4. Confirm.

!!! warning "Photo required"
    If **Photo Required** is enabled for the task, Kamerplanter blocks completion until at least one photo has been uploaded.

### Ticking Off a Task from the List View

Click the checkmark icon next to a task in the list. The task is immediately marked as complete (unless a photo is required).

### Timer

If a task has a timer duration set (e.g. for mixing protocols: "stir and wait"), the countdown timer appears once you start the task.

---

## Changing a Task Afterwards

Open the task and switch to the **Edit** tab. There you adjust the same fields you filled in when creating it, and save with **Save**.

!!! tip "Error hints appear directly on the field"
    If an entry is invalid — an empty **Name**, an estimated duration below one minute — saving is aborted and the reason appears as red helper text underneath the affected field. The same applies to the **Complete** tab. Previously the browser's own check ran first in these cases: it showed a briefly displayed bubble in the browser's language, disappeared on the next click, and left the form unsaved without marking anything on the field itself. <!-- REQ-006 -->

---

## Editing Multiple Tasks at Once

When many tasks pile up, you can handle them in bulk instead of touching each one individually.

1. In the task overview, click **Select multiple** in the top right. (The button appears as soon as there is at least one task.)
2. A selection checkbox appears next to each task. Tick the tasks you want — or use **Select all** in the action bar.
3. Choose the bulk action in the action bar:
    - **Complete** — marks all selected tasks as done.
    - **Skip** — skips all selected tasks.
    - **Delete** — removes all selected tasks.
4. Use **Cancel** to leave selection mode without making any changes.

---

## Using Workflow Templates

Workflow templates are predefined task packages for recurring care scenarios. Applying a template means the system creates a set of concrete tasks from it for your plant, run, site, or tank.

### Step 1: Select a Template

Navigate to **Tasks → Workflow Templates** (`/aufgaben/workflows`). Kamerplanter ships four system templates:

| Template | Target Entity | Category | Description |
|----------|---------------|----------|-------------|
| Cannabis SOG | Plant | Harvest | Sea of Green workflow for cannabis, from transplanting into SOG positions through harvest (6 tasks across the vegetative and flowering phases) |
| Tomato Standard | Plant | Maintenance | Standard tomato growing: transplanting, staking, deshooting, weekly feeding, ripeness observation, harvest |
| General Maintenance | Plant | Maintenance | General recurring inspection and care tasks, independent of plant species |
| Tank Anmischen (Tank Mixing) | Tank | Feeding | Step-by-step mixing protocol for nutrient solutions in the correct mixing order, including stir-and-wait timers |

<!-- Source: src/backend/app/migrations/seed_data/workflows.yaml -->

!!! tip "Tasks adapt to the growth phase"
    Tasks tied to a specific growth phase (e.g. "Flip to 12/12" in Cannabis SOG) are created with status **Dormant** when applying the template and only activate once the plant actually reaches that phase.

### Step 2: Apply the Template to an Entity

1. Click **Apply Template** next to the desired template.
2. Select the matching target entity (plant, planting run, site, or tank — depending on the template).
3. Confirm — all tasks are created immediately. Due dates are calculated from today according to the day offsets stored in the template.

### Creating Your Own Templates

If you use a sequence of tasks repeatedly, you can create your own template:

1. Navigate to **Tasks → Workflow Templates → New Template**.
2. Provide a name, description, category, and target entity/entities.
3. Open the newly created template and use **Add Task** to add individual task templates with title, instruction, category, trigger, and day offset.
4. The template is then available for all your plants or target entities.

!!! note "Best suited for experienced users"
    The workflow editor targets experienced users — some dropdown fields use technical labels. For getting started, the four system templates are usually a better fit than building a template from scratch.

---

## Activity Plans

For an individual planting run, you can additionally apply an **activity plan** — a task suggestion list derived from the activities defined for the plant species. You will find it in the **Activity Plan** tab on the planting run's detail page. More: [Planting Runs](planting-runs.md).

---

## Care Reminders

Automatically generated watering, fertilizing, and other care reminders are not a separate area — they appear in the same task overview (Source filter "Care"). For how the care profile works, which reminder types exist, and how escalation works, see [Care Reminders](care-reminders.md).

When you complete a watering reminder here in the queue, Kamerplanter creates the next watering task right away — see [The next watering task is created immediately](care-reminders.md#naechste-giess-aufgabe).

---

## Filtering Tasks

The task overview provides these filters:

- **Source**: All / Tasks / Care
- **Category**: one of the twelve task categories (only for the "Tasks" source)
- **Plant**: narrow down to a specific plant

!!! note "No filter by location, priority, or tags"
    These filters do not currently exist in the task overview.

---

## Frequently Asked Questions

??? question "Can I delete an automatically created task?"
    Yes, as long as it is in status Pending, Skipped, or Dormant. Tasks already started or completed can no longer be deleted. If you delete an open care reminder, Kamerplanter creates a new one on the next daily planning run if needed — provided the care profile is still active.

??? question "What happens to the tasks when I remove a plant?"
    When you remove a plant, its still-open tasks (pending, in progress, dormant) are automatically removed from the queue. Tasks that were already completed, skipped, or failed are kept as history. Removed plants also no longer generate new automatic care reminders.

??? question "Does Kamerplanter automatically escalate overdue tasks?"
    Only for **watering reminders**: if a watering reminder remains unconfirmed, the system raises the notification urgency to "High" after 2 days and to "Critical" after 4 days; a final warning follows after 7 days. There is no automatic escalation for other task types — the red overdue marking is purely a visual indicator there.

??? question "Can I create recurring tasks?"
    Yes, directly when creating a task via the **Recurrence** field (daily/weekly/biweekly/monthly) — visible from the "Intermediate" experience level onward. As soon as you complete a recurring task, Kamerplanter automatically creates the next instance.

??? question "Can I assign tasks to other members of my tenant?"
    Yes, if you are working in a shared garden (with multiple members). Open the task and enter the appropriate user in the **Assigned To** field (visible from the "Intermediate" experience level).

---

## See Also

- [Calendar](calendar.md)
- [Care Reminders](care-reminders.md)
- [Planting Runs](planting-runs.md)
- [Pest Management (IPM)](pest-management.md)
