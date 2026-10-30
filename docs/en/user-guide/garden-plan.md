# Garden Plan

The garden plan shows your garden from above: beds and garden objects such as paths, fences and trees, drawn to scale. Here you draw, move and plant beds, see at a glance where something needs doing, and back up or print the plan.

---

## Prerequisites

- A site in your garden. How to create one is described under [Locations and Substrates](locations-substrates.md).
- Any role lets you view the plan. To draw and save you need at least the "grower" role, see [Who may do what](#who-may-do-what).
- A plan that has a garden boundary (see [The garden boundary](#the-garden-boundary)).

## Opening the garden plan

Open the site under **Locations** and click **Open garden plan**. The page has the address `/standorte/sites/<key>/plan`. On a narrow screen (under 600 pixels wide) it opens directly in [field mode](#field-mode-in-the-garden); otherwise planning mode starts. With **Field mode** or **Planning mode** at the top of the page you switch at any time.

Planning mode shows the toolbar, the plan in the middle, the properties panel and, below the plan, the [bed list](#bed-list-on-the-garden-plan). With the **Show as list** button you switch to a list view of the same plan that needs neither a mouse nor the drawing area.

### The garden boundary {#the-garden-boundary}

Every plan has a garden boundary: the outline of your garden as a rectangle or polygon. Beds and garden objects must lie completely inside it. A site with no boundary and no placed objects shows the notice **No garden plan yet** instead of the editor.

!!! note "Partially available: garden boundary"
    The interface does not yet have a tool for drawing the garden boundary. You create the first plan through the API (see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters)) or you import a backup (see [Export the plan and restore a backup](#plan-export-import)). Once the boundary exists, the editor changes only its north direction: the compass field sets where geographic north lies on the plan. <!-- REQ-053 GP-FR-013, GP-FR-015 -->

### Who may do what {#who-may-do-what}

Your role always applies to the garden (tenant) you are working in.

| Task | viewer | grower | lead |
|------|:------:|:------:|:----:|
| View the plan, bed list, read field mode | yes | yes | yes |
| Export as PDF, SVG and backup (JSON) | yes | yes | yes |
| Draw, move, change, lock and save beds and objects | no | yes | yes |
| Delete beds and objects | no | no | yes |
| Plant, complete tasks | no | yes | yes |
| Create and change irrigation zones, log a watering round | no | yes | yes |
| Delete an irrigation zone | no | no | yes |
| Save a bed template, set or remove the underlay | no | yes | yes |
| Delete a bed template | no | no | yes |
| Import a backup, restore an earlier state, create a new season | no | no | yes |

!!! note "Note"
    The editor does not hide tools your role may not use. The server checks when you save. A batch of changes that contains even one deletion is refused as a whole unless you have the "lead" role; you then see the message **Saving is not allowed** and undo the change. Delete only as a lead if you need to.

## Drawing and editing

### Tools and shapes

The toolbar offers four tools and the template picker:

| Tool | What it does |
|------|--------------|
| **Select** | Clicking selects an object, a frame selects several, with the Shift key you add objects. Dragging moves the selected objects. |
| **Pan view** | Drags the view without changing anything. |
| **Draw bed** | Draws a new bed. |
| **Object: draw garden object** | Draws a garden object such as a path, fence or tree. |
| **From template** | Places a bed from a [template](#bed-templates). |

As **shape** you choose rectangle, circle, polygon or line. You drag out the rectangle (with Shift it becomes a square) and the circle from its centre outwards. For the polygon and the line you click point by point; **Finish**, the Enter key or a click on the first point closes the polygon, **Finish** or Enter ends the line. Backspace takes back the last point, **Esc** discards the shape.

For every object the plan shows width, length (diameter for a circle) and area. **Add with dimensions** creates a bed or object from typed-in dimensions, without drawing.

A selected object has handles: the corners change the size, the rotation handle turns the object. The **rotation step** snaps the rotation every 15, 45 or 90 degrees; hold the Alt key to rotate freely. On a polygon you add a point with **Insert point** and remove one with **Delete point**.

### With the mouse

- Clicking selects, dragging moves, a frame over free space selects everything that lies completely inside the frame (locked objects excluded).
- With **Ctrl** (**Cmd** on a Mac) and the mouse wheel you zoom smoothly around the pointer; when the plan has the focus, the wheel alone is enough. A plain mouse wheel scrolls the page.
- A right-click on an object (on a touchscreen the **⋯** button in the properties panel) opens the actions of the object: Edit, Duplicate, Bring to front, Send to back, Lock.
- Hold the **Alt** key to switch snapping off briefly.

### On a touchscreen

- With **two fingers** you move and zoom the plan.
- You select an object with a tap. To move it, hold your finger on the object for about half a second; a ring shows that it is now being moved. If you swipe earlier, you move the view instead.
- You switch **multi-select** on as a button. Then you tap objects or drag a frame over free space.
- When drawing, you move the plan with two fingers until the crosshair is on the point you want, and tap **Set point**. **Undo** takes back the point, **Finish** closes the shape, **Cancel** discards it. The plan ignores very wide touches (a palm) and a second finger that lands right after the first.

### With the keyboard

You can operate the plan without a mouse. The **Keyboard help** button (or the **?** key) lists all keys. The most important ones:

| Key | Effect |
|-----|--------|
| Arrow keys | Move the selection by one grid step; without a selection they scroll the view |
| Shift + arrow keys | Ten steps at once |
| Page Down / Page Up | Focus the next or previous object |
| Enter / Space | Select the focused object; Enter also closes a polygon |
| Delete | Deletes the selection after a confirmation |
| Esc | Cancels what is in progress, then clears the selection |
| Ctrl + A | Selects all unlocked objects |
| Ctrl + Z | Undo |
| Ctrl + Shift + Z or Ctrl + Y | Redo |
| Ctrl + S | Save |
| + / − / 0 | Zoom in, zoom out, show the whole plan |
| G | Show or hide the grid |

Tab leaves the plan; you reach all objects and actions in the list view. You can switch off the single keys **?**, **G**, **+**, **−** and **0** in the keyboard help if they get in your way. At the top of the page there are skip links to the object list, the plan and the properties panel.

### Grid, snapping, zoom and compass

- **Grid:** The grid steps are 1 cm, 5 cm, 10 cm, 25 cm, 50 cm and 1 m. At a low zoom the plan draws only the steps whose lines are far enough apart. With **Show grid** (or **G**) you hide the lines; snapping is not affected.
- **Snapping:** The **Snap** switch makes objects snap to the grid and to corners and edges of other objects when you move, draw or drag handles.
- **Length unit:** You choose metres or centimetres for all dimensions in the editor. Storage is always in metres.
- **Zoom:** The fixed levels are 25, 50, 100, 200 and 400 percent; **Fit** shows the whole plan. The scale bar shows how long a distance is on the plan.
- **Compass:** Set the **north angle** so the plan knows where geographic north lies: turn the dial, use the arrow keys or type a value (0 up to but not including 360 degrees, clockwise; 0 means north is up). The compass in a phone gives magnetic north, so Kamerplanter never takes it over automatically.
- **Mini-map:** see [Working faster in the garden plan](#plan-comfort).

### Properties and list view

The **Properties** panel shows name, type, position (x to the right, y upwards, in metres), dimensions and rotation counter-clockwise for the selected bed or object. You change the values directly; **Lock** protects an object from being moved by accident. For a bed you also find **Plant it**, the sun tiles and the number of open and overdue tasks with a jump to the care tab. For a polygon the panel lists the points.

The list view shows the same objects as a list of areas, beds and garden objects. Each entry has move buttons, an input for a target position and Delete. It is the alternative for screen readers and for everyone who does not want to draw.

## Working faster in the garden plan {#plan-comfort}

This section describes the aids that save you manual work in planning mode.

**A bed from a template.** In the tool bar, **From template** puts a bed on the plan with one click. You pick a template, turn it in 90-degree steps with **Rotate** if needed, and click where the bed should go (the lower-left corner of a rectangle, the centre of a circle). A dashed preview shows where it lands; it turns red where the bed would not fit completely into the garden. Without a mouse, **Place at view centre** puts the middle of the bed in the middle of the view. The bed gets the template's name, type, shape and height and is saved at once; Kamerplanter saves your unsaved changes first. This step cannot be taken back with **Undo**. If you do not want the bed, delete it. **Esc** or another tool ends the template choice.

**Standard sizes.** In the **Add with dimensions** dialog, a standard size fills shape, size, bed type and height in one go, for example the raised bed 1.2 × 2.4 m, the raised bed 2 × 1 × 0.8 m or a planter. You can still change every value afterwards. The height is optional.

**Save as template.** With exactly one bed selected, **Save as template** stores its shape, type and height as a template of your garden. Plants, tasks and notes are not part of it, and the template only carries planting distances or soil values if you enter them yourself. Growers and leads create templates.

**Snapping to other objects.** When you move or draw, the plan snaps to corners and edges of other objects before it snaps to the grid. When you move a bed, every corner of it snaps, even when the bed is rotated, not just the spot under the pointer: this lets you put the right edge of one bed exactly against the left edge of the next. For a round bed, the centre and the four points at the very top, bottom, left and right of its rim snap. A green ring shows the point that snaps, a green line the edge it sits on. The Alt key or the **Snap** switch turns snapping off. With a pen or a finger the catch zone is larger.

**Align and distribute.** With at least two beds or objects selected, **Align** lines them up on the left, right, top or bottom edge or on the centre. From three objects on, **Distribute evenly** spreads them with equal gaps; the two outermost objects stay where they are. Locked objects stay where they are and do not count. Objects that stand side by side or staggered are distributed even when they overlap in that direction. If two of them would end up on top of each other, for example because they stand exactly in line, or one would land on a locked object, Kamerplanter distributes nothing and tells you why. Each of these actions is a single step for **Undo**.

**Overview map.** When the garden is much larger than the visible section (more than four times), a small map appears at the bottom right of the plan with the section as a rectangle. A click on it jumps the view there. With the keyboard you keep moving the plan with the arrow keys.

**Auto-save.** The **Auto-save** switch next to **Save** saves your changes two seconds after the last change. It is off by default and applies only to you in this browser. On a conflict or a refused save it pauses and tells you so. Field mode does not have it: every action is sent at once there.

**Duplicate several times.** From the **⋯** menu or the context menu, **Duplicate several times** makes several copies of the selected beds in a row: count, direction, spacing and a naming scheme such as "Plot {n}" (up to 100 copies). You enter the spacing in the length unit you chose for the plan (m or cm). That is handy for the plots of a community garden. Kamerplanter first checks that the copies fit completely into the garden and that the limit of 500 beds and objects is enough; if not, nothing is created. If a copy does not fit into the garden, the dialog names the first one that does not fit. One **Undo** takes all copies back. Planting positions, plants and tasks are not copied; you lay out a planting grid for each bed afterwards. <!-- REQ-053 GP-FR-025, GP-FR-029, GP-FR-043, GP-FR-044, GP-FR-045, GP-FR-154, GP-UX-004, GP-UX-014 -->

## Saving, conflicts and undo

Changes in the editor are first applied only locally. The bar above the plan shows the state: **Unsaved changes (n)**, **Saving …**, **Saved**, **Conflict** or **Saving failed**. **Save** (or **Ctrl + S**) sends all open changes to the server in one step: either all are accepted or none. The **Auto-save** switch does this for you, see below.

- **Undo and redo** (Ctrl + Z, Ctrl + Shift + Z) cover the last 100 steps. The history applies to this session only: if you reload the page, it is gone.
- **Conflict:** If someone else saved the plan while you were working on it, the server does not accept your changes. A dialog names who changed it last. Before you reload you can download your changes as a copy (JSON). When you reload, your unsaved changes and the undo history are lost.
- **Rejected:** If a change breaks a rule, the server refuses the whole save and the message names the place. Common reasons: two beds overlap, an object sticks out of the garden boundary, plants still grow on a bed (clear the bed before deleting it), more than 500 changes are open, or the plan has reached its limit of 500 locations and objects together. Fix the named place or undo it; your other changes are kept.
- **Deleting:** As long as you have not saved, you can undo a deletion. After saving you cannot. The dialog first names what is deleted with it.

## Planting a bed {#planting-a-bed}

Select a bed and click **Plant it** in the properties panel. The planting dialog opens, which you also know from the bed view. You choose species and cultivar, see hints on crop rotation, neighbours and site, set the arrangement (grid, rows, staggered, area or free positions), see a preview and either plan the planting or record it at once. This works with the "grower" role; the bed must be on the plan and must not be retired. The steps are under [Planting a bed](locations-substrates.md#planting-a-bed).

Plants appear on the plan as markers. The plant state layer is described in [Plant state and filter](#plant-state-and-filter).

## Bed List on the Garden Plan {#bed-list-on-the-garden-plan}

Below the plan on the garden plan page, a table lists your beds: name (a link to the bed view), type, area, status, responsible person, plants, open tasks (including overdue ones) and next due date. Retired beds are hidden by default. The **My beds** switch filters to your own beds and requires that beds are assigned to you.

If you click a row or press Enter, the bed is selected on the plan and the view zooms to it. The number in the "Open tasks" column is a link to the bed's Care tab. From the "grower" role on, the button **Complete tasks on several beds** sits above the table (see [Care on the bed](locations-substrates.md#care-on-the-bed)).

## Field mode in the garden {#field-mode-in-the-garden}

Field mode is made for the phone at the bed: large buttons (at least 64 pixels), strong contrast for sunlight and only what you need outside. On a narrow screen (below 600 pixels wide) the garden plan page opens in field mode right away. On any device you switch with **Field mode** or **Planning mode** at the top of the page; the address then carries `?mode=field` or `?mode=plan`.

**My beds · due today.** Field mode starts with the list of your beds. Beds assigned to you come first (marked **Mine**), then beds with overdue tasks or tasks due today, then the rest by their next due date. A task is overdue when its due day lies before today; a task due today does not count as overdue yet. Retired beds are left out. The **Map** tab shows the plan without tools, grid or handles. **Zoom in**, **Zoom out** and **Whole plan** change the view. If you tap a bed, or just next to it, the map zooms to the bed and opens it.

**The bed sheet.** A tap on a bed opens a sheet at the bottom with the bed's name, the quick log, the tasks and the plants. Tasks come in the order **Overdue**, **Due today**, **Later**. Plants are grouped by species, count and phase; the phase colour always has a black outline and the phase name next to it.

- **Done** opens the short dialog with the optional fields (quantity, note). **Finish** saves. That is two taps after choosing the bed. A double tap counts once, and the buttons stay locked until the answer has arrived.
- **Quick log:** **Watered**, **Sown** and **Weeded/Mulched** save a care entry with one tap. **Harvested** and **Note** open the short form (quantity or text; for the note you can use your keyboard's voice input). **Planted** opens the planting dialog with **I have planted already** switched on; the plants are created at once. This needs a bed that is drawn on the plan.
- After **Done** and after every quick log entry you see **Undo** for eight seconds. It takes the entry back.
- **Show plants** lists the single plants of a group. **Correct position** moves a plant with the arrows in 10 cm steps; you can drag the marker only after holding it for half a second. **Photo** takes a picture for the plant's gallery.

Deleting, clearing a bed, export and import are not available in field mode; switch to planning mode for them. With the "viewer" role you see tasks and plants read-only. Your browser, not your account, remembers the tenant, site, tab and map view; if someone else signs in on the device, field mode starts fresh for them. If a remembered map view would show hardly any of the plan on the current screen – after turning the phone, for example – the map opens on the whole plan.

!!! warning "Not yet implemented"
    Without a connection field mode shows a notice and locks **Done** and the quick log; entries are not yet stored on the device and sent later. Photos are attached to a plant for now, not to the bed. **Planted** has no **Undo**. GPS help and the QR code on the bed follow later. The "last watered" layer exists only in planning mode. <!-- REQ-053 GP-UX-020…031, GP-FR-149 -->

## Layers and site conditions {#layers-and-site-conditions}

You show and hide layers in the **Layers** group of the view bar. Your browser remembers your choice; it applies only to you. The grid is not a layer of this group: it has its own switch **Show grid** in the group **Grid and snap** (on at the start, key **G**), see [Grid, snapping, zoom and compass](#grid-snapping-zoom-and-compass).

| Layer | Shows | At the start |
|-------|-------|--------------|
| **Show irrigation zones** | Zones as an outline with hatching over their beds | off |
| **Show last watered** | Days since the last recorded watering per bed, as hatching | off |
| **Show underlay** | The background picture (visible only if the site has an underlay) | on |
| **Show sun window** | When direct sun reaches a bed | off |
| **Show drainage** | How well a bed drains | off |
| **Show frost risk** | Low, normal or high per bed | off |
| **Show plant state** | Phase, ring and sign of every plant | off |

The legend below the view bar explains every layer that is switched on. The hatching of zones and of the state layers differs in pattern, not only in colour.

The **Last watered** layer shows only the distance to the last recorded watering in four steps (0 to 1, 2 to 3, 4 to 7, more than 7 days). It does not say whether a bed needs water. A bed without a recorded watering stays without hatching.

### Sun window, drainage and frost risk {#sun-window-drainage-frost-risk}

You maintain the values on the bed: sun, sun window and leaf shade in the sun tiles (see [Sun and shade of a bed](locations-substrates.md#sun-and-shade-of-a-bed)), drainage in the soil profile. The layers show these entries on the whole plan.

**Sun window, drainage and frost risk layers in the garden plan.** In the layer group of the view bar you can show three more layers: **Show sun window** (when direct sun reaches the bed), **Show drainage** (poor, moderate, good) and **Show frost risk** (low, normal, high). Every value has its own pattern, so you can tell them apart without colour. The pattern is always shown; once you zoom in far enough for the bed names to appear, a small symbol for the value joins it at the bottom edge of the bed, where the bed has room for it; the legend below the view bar explains every layer that is on. A bed without a recorded value stays without a pattern. All three layers start switched off, and your browser remembers your choice for you. The frost layer shows the stored frost risk; for overwintering, the frost exposure stays the setting that counts. <!-- REQ-053 GP-FR-169, GP-FR-047 -->

### Plant state and filter {#plant-state-and-filter}

What disc, ring and sign on a plant mean is described under [Plant state and plant info](locations-substrates.md#plant-state). In the garden plan the following applies to the layer:

**Plant state layer and filter in the garden plan.** With **Show plant state** in the same layer group you see the state of your plants without opening a bed. Once you zoom close enough to a bed for the single plants to appear, every plant carries disc, ring and sign as in the bed's **Plan** tab: the colour shows the growth phase, the ring how far the planting is, the sign at the top right the most urgent reason to act. Further out each bed sums up its plants as a circle with a number; if you have seen a bed close enough before, Kamerplanter knows its states: the circle then shows the most urgent sign, and the screen reader names the number of all plants in the bed and how many of them need attention. Next to it sits the switch **Only show plants that need attention**: it hides every plant whose state is known and that carries no sign. A plant whose state is not loaded yet stays visible. The circle of a bed then shows only the plants that remain, and it disappears only once every state of the bed is known and no plant needs attention; the bed itself stays visible, and the screen reader still names the number of all plants. While the layer is off, the switch is disabled; you still reach it with the Tab key, and the screen reader tells you why it is disabled. The legend below the view bar explains rings and signs and lists the colours of the growth phases of the plants whose states are loaded, sorted alphabetically in your language. Kamerplanter loads the states only while the layer is on, only for the beds you currently see close enough, and at most four beds at a time. Each bed loads once and again when you come back to the tab, when you save the plan or a newer version of it loads, and after you changed a zone or logged a watering round in the irrigation panel. The layer and the filter start switched off; your browser remembers your choice. The info bubble on hovering a plant stays with the bed's **Plan** tab. <!-- REQ-053 GP-UX-061, GP-UX-060 -->

!!! note "Partially available: plant state"
    **Frost danger** does not appear as a sign yet, even though the **Frost risk** layer shows the stored value. **Watering due** arises so far only from a watering task due today, not from the irrigation demand. <!-- REQ-053 GP-UX-060, GP-FR-190 -->

## Irrigation zones and the watering round {#irrigation-zones}

An **irrigation zone** groups beds of one site that are watered together, for example on a drip line or under a sprinkler. A bed belongs to at most one zone. A site can have up to 500 zones.

Click **Manage irrigation zones** to open the zone area.

1. **Create a zone:** Click **New zone**. Enter a name, choose the **type of irrigation** (By hand, Drip irrigation, Sprinkler, Soaker hose or Sub-irrigation) and a colour. Optionally enter a water source (a garden object of type water source), the flow rate in litres per minute and a schedule note.
2. **Assign beds:** Tick the beds or take over the plan selection with **Take over selection from the plan**. A bed that already lies in another zone moves to this one; the interface tells you. Beds and water sources you have not saved yet are available for selection only after you save the plan.
3. **Save the zone.** All members may read; the "grower" role and above may change; only the lead may delete. If you delete a zone, the beds stay unchanged and then belong to no zone; the watering log is kept.

**State of the zone.** For each zone Kamerplanter shows when it was last watered, the next planned watering, the **demand today** (net and gross, with the efficiency from the zone or as a guide value of the irrigation type), the **consumption of the last 30 days** with its source, and hints, for example how long the water source lasts at this daily demand.

**Log a watering round.** When you have watered a whole zone, **Log watering round** opens a dialog: you enter the **total amount in litres** (more than 0, at most 100,000) and choose the **distribution**: **By bed area** (each bed gets a share by its area; beds without an area are left out) or **Equal parts**. Kamerplanter writes one watering entry per bed into the care log. The amount is divided, not measured; the log marks it that way.

!!! info "API only: technical coupling"
    Only members with the `technical` admin scope maintain the coupling of a zone to an actuator or to a Home Assistant entity for the flow, and only through the API. Restoring a backup never takes these links over. See [For Technical Users / Self-Hosters](#for-technical-users-self-hosters).

## Bed templates {#bed-templates}

A bed template fixes shape, dimensions, bed type and height of a bed so you do not redraw the same shape every time. Kamerplanter ships standard sizes, for example bed 1 × 1 m, 2 × 1 m, 3 × 1.2 m and 4 × 1.2 m, raised bed 1.2 × 2.4 m and 2 × 1 × 0.8 m, and planters of 0.3, 0.4 and 0.5 m diameter. Your own templates belong to your garden.

- **Place:** **From template** in the toolbar, see [Working faster in the garden plan](#plan-comfort).
- **Save:** Select exactly one bed and click **Save as template**. Plants, tasks and notes are not part of it. A garden can have up to 200 own templates; when the limit is reached, delete one you no longer need first.
- **Roles:** Growers and the lead create templates; only the lead may delete.

## Underlay for tracing {#underlay}

With an **underlay** you place a photo, a sketch or an aerial view under the plan and trace the beds on it.

1. Click **Underlay** and choose an image (JPEG, PNG or WebP). The plan needs a garden boundary for this.
2. **Calibrate:** Click two points in the image whose distance you know and enter the distance in metres. From this Kamerplanter calculates the scale (pixels per metre).
3. **Position:** Set where the top left corner of the image lies on the plan, rotate the image counter-clockwise if needed and set the opacity.
4. **Save.** With **Remove underlay** you delete the image and the calibration; you would have to create both again.

A site has at most one underlay, and all members see the same one. Whether you display it is your own choice with the **Show underlay** layer. Growers and the lead may set and remove it. The underlay lies below all objects, is not part of the JSON backup and goes into the PDF print only if the API request asks for it explicitly (the export dialog does not offer this). Aerial views can reveal where you live: pass on a plan with an underlay only if you mean to.

## Change log {#change-log}

Kamerplanter keeps a change log for every plan: deletions and changes of the garden boundary with the time and the name of the editor, plus the states a replace import overwrote (see [Export the plan and restore a backup](#plan-export-import)). Entries are kept for one year. The log has no page of its own in the interface; you can read it through the API (see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters)).

What happened on a single bed is in its history: the crop rotation timeline and the list of all care entries and plantings are described in [History of the bed](locations-substrates.md#history-of-the-bed).

## Export the plan and restore a backup {#plan-export-import}

On the garden plan page, **Export & import** opens two dialogs.

**Export plan** comes as a PDF (the plan to scale, for printing), an SVG (vector graphic) and a backup (JSON). You choose paper, orientation, scale and layers (for the PDF also **Bed list as a second page**); a preview shows what you get. With **Automatic**, Kamerplanter takes the finest scale that fits the sheet and suggests A3 when A4 would get too coarse. If a fixed scale does not fit the sheet, the dialog says so and lets you choose a coarser scale or A3. On a phone there is only PDF and backup with the standard options. The export holds no member names and no assignments.

In the PDF and the SVG every plant shows its state as on the plan: the disc in the colour of its growth phase, a ring for how far it is (a thick ring means *harvesting*) and at most one sign for the most urgent matter, such as a triangle for an open finding or a drop when watering is due. The legend lists the growth phases, rings and signs that occur on the plan. Of the growth phases it names at most the six with the most plants; if there are more, one entry such as "+3 more phases" sums up the rest, so the plan still fits the page at the chosen scale. A long phase name is shortened with "…". Plants of a species with its own phase sequence carry the same colour as on the plan. From 2,000 plants on, each bed shows only the number of its plants instead. <!-- REQ-053 GP-UX-005, GP-UX-059, GP-UX-060 -->

The **backup** holds beds, garden objects, plant places, irrigation zones, soil profiles, site features and the garden boundary, but no plants and no tasks. If you have selected beds or garden objects on the plan, you can limit the backup to **Selection only** or **Selection with everything below**. Such a partial backup has no garden boundary, and references to things that are not in the file are dropped. Every role may read it.

**Restore a backup** leads through the import in three steps. Only a lead can do this.

1. **Choose file:** The file may be at most 5 MB. Kamerplanter checks it right away without writing anything.
2. **Check report:** You see how much would be created and deleted, which references are not carried over (for example an irrigation zone that does not exist here) and which problems the file has, such as overlapping beds. With problems you cannot continue.
3. **Mode:** *Add* creates the backup in addition to the existing plan. *Replace* swaps the plan of this site. For that you type the name of the site. Before that, Kamerplanter saves the previous plan as a snapshot in the change log. Download a current backup first anyway, to be safe.

In *Add* mode you can move every shape of the file by a distance (to the right and up, in metres), for example to put a bed somewhere else. **Where is the file going?** tells Kamerplanter whether the file comes from this site, another site or another garden account. For the last two, references that are not in the file are never resolved against this site: they are dropped and listed in the check report. Nothing is read from another account, the file is the transport; you need the lead role in the account you import into.

**Restore an earlier state:** In the first import step this button opens the list of plans that a *Replace* overwrote (kept for one year, at most the 20 newest per site, lead only). You pick a state, read the check report and type the name of the site. Kamerplanter first saves the current plan as a state of its own, so the restore can be undone. Irrigation zones that the state does not name are removed, and technical zone bindings (actuator, Home Assistant flow) are not restored; set them up again afterwards. *Add* does not create a state.

!!! warning "Beds with active plants"
    A bed with a plant in it is never deleted. While such beds exist, *Replace* rejects the file. If you choose the option to keep those beds, they stay together with the locations above them, and the rest is replaced.

**New season from last year:** In the **Export & import** menu, **New season from last year …** re-creates last year's places as free slots for every bed without active plants (lead only, within the same site). You enter the year of the new season; the places come from what was finished in the year before. Kamerplanter checks first and shows what happens per bed: beds with active plants and retired beds are skipped and listed in the report, and so is a bed that would pass 2,000 slots with the new places. Places that already stand as a free slot are not created twice. Zones, plants, planting runs and history stay as they are; crop rotation and companion planting hints keep using last year's occupancy. **Show "Here stood …"** adds the plant family of last year to each bed, for orientation only. Only **Create free slots** writes, in one step with an entry in the change log; if the plan changed since the check, you check again. <!-- REQ-053 GP-FR-171 -->

All keys are newly assigned on import. Links to Home Assistant and to actuators are never carried over; set them up again afterwards. If you have unsaved changes to the plan, save or discard them first. In field mode, export and import are hidden.

## For Technical Users / Self-Hosters {#for-technical-users-self-hosters}

This section is for everyone who creates the plan through the API or operates an installation. All paths are under `/api/v1/t/{slug}/`.

- **Create the first plan:** `PUT /sites/{key}/plan/boundary` with the garden boundary (rectangle or polygon), optionally `north_angle_deg`. The first call creates the plan.
- **Read the plan:** `GET /sites/{key}/plan`. **Read the change log:** `GET /sites/{key}/plan/audit`.
- **PDF with underlay:** `GET /print/garden-plan/{site_key}?underlay=true`.
- **Rate limits** and retention are listed under [Environment Variables](../reference/environment-variables.md).
- Structure, batch interface and backup format are described in [Garden Plan: Geometry and Interfaces](../architecture/garden-plan.md); the routes and error codes are in the [API Reference](../reference/api-reference.md#garden-plan-pdf-svg-json-backup).

## Frequently Asked Questions

??? question "What do I do if the plan shows **No garden plan yet**?"
    The site has no garden boundary yet. Create it through the API or import a backup, see [The garden boundary](#the-garden-boundary).

??? question "I can draw but not save."
    Saving requires at least the "grower" role. With the "viewer" role the server refuses to save.

??? question "Why can't I delete a bed?"
    Only the lead may delete. In addition, Kamerplanter refuses to delete a bed while plants grow on it; clear the bed first.

??? question "My changes are gone after reloading."
    Unsaved changes and the undo history do not survive a reload. Save regularly or switch **Auto-save** on.

??? question "Can I draw two beds overlapping?"
    No. The server refuses overlapping beds when saving; move one until they no longer touch.

## See Also

- [Locations and Substrates](locations-substrates.md) — bed view, care, history, sun and soil
- [Planting Runs](planting-runs.md)
- [Watering Log](watering-log.md)
- [Print Views and Export](print-export.md)
- [Roles and Permissions](../reference/roles-and-permissions.md)
- [Garden Plan: Geometry and Interfaces](../architecture/garden-plan.md) — technical
