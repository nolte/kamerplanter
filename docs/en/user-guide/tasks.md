# Tasks and Care Reminders

Kamerplanter automatically creates tasks from workflows and care profiles and reminds you in time of all upcoming care activities. You retain full control at all times: tasks can be adjusted, recreated, and managed flexibly.

---

## Prerequisites

- At least one plant or an active planting run
- Care profiles are suggested automatically but can also be configured manually

---

## Tasks at a Glance

Find the task overview under **Tasks** in the navigation. The view shows:

- **Due Today**: Tasks that should be completed today
- **Overdue**: Tasks that have passed their due date (marked red)
- **Next Week**: Tasks for the next 7 days
- **All Tasks**: Complete list with filter and sort options

Each task displays:
- Type (watering, fertilizing, inspection, harvest, etc.)
- Associated plant(s) or planting run
- Priority (Low / Normal / High / Critical)
- Due date

---

## Task Types

Kamerplanter distinguishes between manually created tasks and automatically generated tasks:

**Automatically generated tasks are created by:**
- Watering schedule (based on configured interval or substrate moisture)
- Care profile engine (reminders for fertilizing, repotting, cleaning)
- Phase transitions (task "Check if ready for next phase")
- Tank maintenance (water changes, calibrations)
- IPM inspection plans (pest control)
- Sensor failures ("Check sensor XY")
- Seasonal triggers (frost protection, overwintering)

**Manually creatable tasks:**
- Any single task (free text)
- Tasks from workflow templates

---

## Creating a Manual Task

### Step 1: Add a New Task

Click **Create Task** (top right) in the task overview.

### Step 2: Describe the Task

| Field | Description |
|-------|-------------|
| Title | Short, clear description |
| Description | Full details and instructions |
| Type | Category (Watering, Fertilizing, Inspection, Training, Harvest, Other) |
| Priority | Low / Normal / High / Critical |
| Due Date | When must the task be completed? |
| Plant / Run | Assignment to plant(s) or planting run |
| Tags | Free keywords (e.g. "urgent", "discuss-with-partner") |

### Step 3: Optional — Set a Reminder

Enable the reminder feature to receive a notification before the due date.

### Step 4: Save

The task appears immediately in the task overview and in the calendar.

---

## Marking a Task as Complete

### Completing a Single Task

1. Open the task by clicking its title.
2. Click **Mark as Complete**.
3. Optional: enter a completion date and a note.
4. Confirm.

### Ticking Off a Task from the List View

Click the checkmark icon next to a task in the list. The task is immediately marked as complete.

!!! tip "Adaptive schedules"
    Kamerplanter learns from your completion patterns. If you consistently tick off a watering task one day early, the system adjusts the interval automatically (up to ±30 % deviation from the original interval).

---

## Using Workflow Templates

Workflow templates are predefined task packages for common care scenarios. Instantiating a template means the system creates a set of concrete tasks from the template for your plant or run.

### Step 1: Select a Template

Navigate to **Tasks → Workflow Templates**. You will see predefined system templates:

**Indoor templates:**
- Cannabis SOG (Sea of Green)
- Cannabis SCROG (Screen of Green)
- Nutrient Solution Change (hydroponics)
- Probe Calibration

**Houseplant templates:**
- Tropical Foliage Plant (Standard)
- Orchid (Phalaenopsis)
- Cactus / Succulent
- Calathea / Maranta
- Repotting Workflow
- Overwintering Workflow

**Outdoor templates:**
- Frost Protection Workflow
- Hardening-Off Workflow (indoor → outdoor)
- Spring Bed Preparation
- Propagation Workflow
- Season-End Workflow (autumn)
- Rose Annual Care

### Step 2: Apply Template to a Plant or Run

1. Click **Apply Template** next to the desired template.
2. Select the target plant(s) or planting run.
3. Choose a start date.
4. The system calculates all due dates automatically based on the template and growth phase.
5. Confirm — all tasks are created.

### Creating Your Own Templates

When you use a sequence of tasks repeatedly:

1. Navigate to **Tasks → Workflow Templates → New Template**.
2. Give the template a name and description.
3. Add tasks (title, type, days from start).
4. Save. The template is now available for all your plants.

---

## Care Profiles and Automatic Reminders

Care profiles define the basic care behaviour of a plant: how often to water? how often to fertilize? when to repot?

### Viewing and Adjusting a Care Profile

1. Open a plant and switch to the **Care** tab.
2. The system automatically suggests a care profile based on the plant species.
3. Click **Edit Profile** to adjust the intervals.

**Adjustable parameters:**
- Watering interval (days) or mode (based on substrate moisture)
- Fertilization interval (weeks)
- Repotting interval (months)
- Seasonal multipliers (e.g. water less in winter)

### Predefined Care Styles

Kamerplanter knows nine care styles, automatically derived from the plant family:

| Care Style | Typical Plants | Characteristic |
|-----------|----------------|---------------|
| Tropical | Monstera, Philodendron, Ficus | High humidity, regular watering |
| Mediterranean | Rosemary, thyme, lavender | Drought-resistant, water rarely |
| Succulent / Cactus | Cacti, echeveria, aloe | Rare watering, winter dormancy |
| Orchid | Phalaenopsis, dendrobium | Soaking instead of watering, temperature drop |
| Fern | Ferns, calathea | High humidity, no waterlogging |
| Vegetable (heavy feeder) | Tomato, courgette, pepper | Intensive fertilization, regular watering |
| Vegetable (light feeder) | Herbs, lettuce, radishes | Little fertilizer, moderate watering |
| Cannabis | Cannabis | Phase-dependent watering and feeding |
| Hydroponics | All hydro plants | EC/pH control, reservoir changes |

---

## Filtering and Sorting Tasks

The task overview provides these filters:

- **By Status**: Open / Complete / Overdue
- **By Type**: Watering, Fertilizing, Inspection, Harvest, Training, Other
- **By Plant or Run**
- **By Location**
- **By Priority**
- **By Tags**

Click the filter button at the top of the list to show or hide the filter bar.

---

## Frequently Asked Questions

??? question "How many automatic tasks does Kamerplanter create per day?"
    That depends on the number of plants and active care profiles. Kamerplanter bundles multiple tasks where possible (e.g. "Water all plants in Tent A" instead of individual watering tasks per plant). You can configure in settings whether tasks are bundled per plant or per location.

??? question "Can I delete an automatically created task?"
    Yes. You can delete any task regardless of its origin. If you delete a task from a running care plan, Kamerplanter creates a new task on the next planning run (daily) — provided the care profile is still active.

??? question "What does the red marking on overdue tasks mean?"
    A red marking means a task has passed its due date. It is a notice, not an automatic escalation. Kamerplanter escalates overdue tasks to "Critical" priority after 48 hours.

??? question "Can I assign tasks to other members of my tenant?"
    Yes, if you are working in a shared garden (with multiple members). Open the task and assign it via the **Assigned To** field.

---

## See Also

- [Calendar](calendar.md)
- [Planting Runs](planting-runs.md)
- [Pest Management (IPM)](pest-management.md)
