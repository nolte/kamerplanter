Feature: Watering log consistency across views
  A gardener records a watering once. Every view of that plant must then agree
  on that watering: the tenant-wide watering log, the plant's own watering log,
  and the plant's task history. There, the watering closes the watering task
  that was due and schedules the next one.

  Every count and every day below is a parameter of its step, never a value
  baked into the step wording — so a further case expecting a different number
  of entries, or a day other than today, reuses these steps unchanged. Days may
  be written as "today", "yesterday", "tomorrow" or as a date like 24.07.2026.

  @TC-004-092
  Scenario: A single watering is reflected consistently in every view
    Given a plant whose care profile schedules watering tasks
    And the plant has 1 watering task due
    And the plant has 0 completed watering tasks
    When the gardener records a plain watering of 1 litre for the plant
    Then the tenant-wide watering log holds 1 watering for the plant, dated today
    And that watering is recorded as a plain watering, with no fertilizer involved
    And that watering links back to the plant it was recorded for
    And the plant's own watering log has gained 1 entry of 1 litre, dated today
    And both watering logs agree on the day the plant was watered
    And 1 watering task has been completed, dated today
    And 1 follow-up watering task is due
    And the task summary bar reports 1 more done task and as many active tasks as before
