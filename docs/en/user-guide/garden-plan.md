# Garden Plan

The garden plan shows your garden from above: beds and garden objects such as paths, fences and trees, drawn to scale. Here you draw, move and plant beds, see at a glance where something needs doing, and back up or print the plan.

---

## Prerequisites

- A site in your garden. How to create one is described under [Locations and Substrates](locations-substrates.md).
- Any role lets you view the plan. To draw and save you need at least the "grower" role, see [Who may do what](#who-may-do-what).
- A plan that has a garden boundary (see [The garden boundary](#the-garden-boundary)).

## Opening the garden plan

Open the site under **Locations** and click **Open garden plan**. The page has the address `/standorte/sites/<key>/plan`. On a narrow screen (under 600 pixels wide) it opens directly in [field mode](#field-mode-in-the-garden); otherwise planning mode starts. With **Field mode** or **Planning mode** at the top of the page you switch at any time.

Planning mode is a workspace like a drawing program. The drawing area gets as much room as possible:

- **Header bar:** a single row above the plan. It holds **Back** to the site, **Undo** and **Redo**, the save state with **Save**, the tabs **Plan**, **List** and **Beds**, the switch to field mode and the switch for the side panel. Rare actions sit in the **⋮** menu (More): keyboard help, underlay, drawing or unlocking the garden boundary, select all, export and import and, while exactly one bed is selected, **Save as template**. When the window gets narrower, first the **Auto-save** switch, then the field-mode switch, the panel switch and last the tabs move into the menu. **Save** always stays visible.
- **Tabs Plan · List · Beds:** **Plan** shows the drawing area, **List** the same plan as a list (usable without a mouse or drawing area), **Beds** the [bed list](#bed-list-on-the-garden-plan). The selected tab is part of the address (`?tab=plan`, `list` or `beds`), so a link opens the right tab directly and the browser's **Back** returns to the previous tab. Switching tabs keeps unsaved changes, the selection and the view, and asks nothing.
- **Tool rail:** vertical, to the left of the drawing area (see [Tools and shapes](#tools-and-shapes)).
- **Drawing area:** fills the height of the window. Zoom, **Fit**, the scale bar and the mini-map sit in its corners on top of the plan.
- **Side panel:** on the right, with the tabs **Properties**, **View**, **Layers** and **Zones** (see [Properties, side panel and list view](#properties-and-list-view)). Without a selection it is collapsed and takes no room.

**On tablet and phone.** From 768 pixels wide the side panel stands beside the plan; the plan gets narrower and moves a selected bed into view. Below 768 pixels the tool rail becomes a bar below the plan and the side panel opens as a sheet from the bottom (half or full height). The header bar then keeps only **Back**, the save state, **Save** and **⋮**; **Undo** and **Redo** sit in the bar below the plan. With a touchscreen you see the touch bar (set point, multi-select) at every width. <!-- REQ-053 GP-UX-063, GP-UX-064, GP-UX-065, GP-UX-067, GP-UX-068, GP-UX-069 -->

### The garden boundary {#the-garden-boundary}

Every plan has a garden boundary: the outline of your garden as a rectangle or polygon. Beds and garden objects must lie completely inside it. A site with no boundary and no placed objects shows the notice **No garden plan yet** instead of the editor.

**Drawing the boundary.** Choose **Draw garden boundary** in the **⋮** menu (in a [flat plan](#flat-plan) **Draw floor plan**). A notice appears above the plan, and in the tool rail you pick **Rectangle** or **Polygon**. You drag out a rectangle; a polygon you place point by point and close with **Done** or Enter, just like a bed. On a touchscreen you place the points with **Set point**. Afterwards the boundary shows handles: drag corners and edges, rotate, move, insert or delete points. Every change is one step for **Undo**; the north direction stays as it is.

**Locked once saved.** A saved boundary is locked against accidental changes: you can neither select nor move it. To change it, choose **Unlock and edit garden boundary** in the **⋮** menu. **Lock** in the notice above the plan, Esc or the next save lock it again.

**Beds and objects stay inside.** A boundary that would leave a bed or garden object outside is drawn red and not applied; Kamerplanter clips nothing. Move the bed inside first or draw the boundary wider. Objects marked "Outside the property" do not count.

!!! note "Partially available: garden boundary"
    A garden without a plan shows **No garden plan yet** with **Add the first bed**. You draw the boundary afterwards through the **⋮** menu. The compass field in the **View** tab sets the north direction only once a boundary exists. <!-- REQ-053 UC-01, GP-FR-019, GP-FR-032, GP-FR-013, GP-FR-015, GP-FR-182 -->

### Who may do what {#who-may-do-what}

Your role always applies to the garden (tenant) you are working in.

| Task | viewer | grower | lead |
|------|:------:|:------:|:----:|
| View the plan, bed list, read field mode | yes | yes | yes |
| Export as PDF, SVG, backup (JSON) and bed list (CSV) | yes | yes | yes |
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

### Tools and shapes {#tools-and-shapes}

The tool rail to the left of the plan offers five tools. Each has a tooltip; on wide screens its name stands next to it.

| Tool | What it does |
|------|--------------|
| **Select** | Clicking selects an object, a frame selects several, with the Shift key you add objects. Dragging moves the selected objects. |
| **Pan view** | Drags the view without changing anything. |
| **Draw bed** ▸ | Draws a new bed. The small menu next to it offers **From template** (place a bed from a [template](#bed-templates)) and **Add with dimensions**. |
| **Object: draw garden object** ▸ | Draws a garden object such as a path, fence, tree, trellis, compost or, in a flat plan, window, door, furniture and lamp. The menu next to it offers **Add with dimensions**. |
| **Measure** | Measures a distance on the plan, point by point. Nothing is saved, see [Measuring distances](#measuring-distances). |

Below the tools, the **selection group** appears only while something is selected: **rotation step** (15°, 45°, 90°), **Align** and **Delete**.

!!! note "Partially available: tools"
    Three more tools are planned but not built yet: **Area**, **Place plant** and **Label**. Until then you create areas through the API or a backup and plant beds with **Plant it**. <!-- REQ-053 GP-UX-001, GP-UX-066, GP-UX-071, #2913 -->

As **shape** you choose rectangle, circle, polygon or line. You drag out the rectangle (with Shift it becomes a square) and the circle from its centre outwards. For the polygon and the line you click point by point; **Finish**, the Enter key or a click on the first point closes the polygon, **Finish** or Enter ends the line. Backspace takes back the last point, **Esc** discards the shape.

For every object the plan shows width, length (diameter for a circle) and area. **Add with dimensions** creates a bed or object from typed-in dimensions, without drawing.

The name of a bed or object sits in its middle; on a polygon it sits where it has the most room to every edge, so it stays inside an L-shaped bed. A name that is too long is shortened with "…". When two names overlap, the larger object keeps its name. The PDF and the SVG put the name in the same place. <!-- REQ-053 GP-UX-047 -->

A selected object has handles: the corners change the size, the rotation handle turns the object. The **rotation step** snaps the rotation every 15, 45 or 90 degrees; hold the Alt key to rotate freely. On a polygon you add a point with **Insert point** and remove one with **Delete point**.

The dimensions of the selected object stand outside, above its top edge, and keep clear of the handles. When an object is too small on screen for handles, a hint offers **Zoom in to edit**: the plan zooms in around the object until all handles appear. <!-- REQ-053 GP-UX-047, GP-UX-048 -->

### Measuring distances {#measuring-distances}

With **Measure** you check how far apart two spots are, for example whether a path fits between two beds. Click the start point; as you move the mouse, a line with its length follows. The next click sets the point. Keep clicking to measure a polyline: the plan shows the length of every segment and the total at its end. The points snap like drawn points, to the grid and to corners and edges of other objects; hold Alt to place them freely.

Press Enter or double-click to finish the measurement; it stays until you press **Esc**, start the next measurement with a new click or change the tool. Backspace takes back the last point. The lengths use the unit you chose in the **View** tab (metres or centimetres). Above the plan the measured distance is also shown as text, which a screen reader reads out too.

Measuring changes nothing in the plan: there is no unsaved change and no step for **Undo**. <!-- REQ-053 GP-UX-071, #2913 -->

### With the mouse

- Clicking selects, dragging moves, a frame over free space selects everything that lies completely inside the frame (locked objects excluded).
- With **Ctrl** (**Cmd** on a Mac) and the mouse wheel you zoom smoothly around the pointer; when the plan has the focus, the wheel alone is enough. A plain mouse wheel scrolls the page.
- A right-click on an object (on a touchscreen the **⋯** button in the properties panel) opens the actions of the object: Edit, Duplicate, Bring to front, Send to back, Lock. Duplicate has no keyboard shortcut; the copy of a bed has no planting positions.
- Hold the **Alt** key to switch snapping off briefly.
- You move the view in every tool by dragging with the **middle mouse button** held down, or by holding **Space** and dragging with the left mouse button. While you hold Space, the pointer shows a hand; the selection stays, nothing is drawn or moved. When you release Space, your tool applies again. In a text field Space types a space as usual, on a button it activates the button.

### On a touchscreen

- With **two fingers** you move and zoom the plan.
- You select an object with a tap. To move it, hold your finger on the object for about half a second; a ring shows that it is now being moved. If you swipe earlier, you move the view instead.
- You switch **multi-select** on as a button. Then you tap objects or drag a frame over free space.
- When drawing, you move the plan with two fingers until the crosshair is on the point you want, and tap **Set point**. **Undo** takes back the point, **Finish** closes the shape, **Cancel** discards it. With **Measure** you set the points the same way; **Finish** ends the measurement, **Clear** discards it. The plan ignores very wide touches (a palm) and a second finger that lands right after the first.

### With the keyboard

You can operate the plan without a mouse. **Keyboard help** in the **⋮** menu (or the **?** key) lists all keys. The most important ones:

| Key | Effect |
|-----|--------|
| Arrow keys | Move the selection by one grid step; without a selection they scroll the view |
| Shift + arrow keys | Ten grid steps at once; without a selection they scroll ten times as far |
| Space + drag | Moves the view in every tool |
| Page Down / Page Up | Focus the next or previous object |
| Enter / Space | Select the focused object (Space on release); Enter also closes a polygon |
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

Grid, snapping, length unit and compass are in the side panel's **View** tab. Zoom and **Fit** sit at the top right of the drawing area.

- **Grid:** The grid steps are 1 cm, 5 cm, 10 cm, 25 cm, 50 cm and 1 m; a new garden plan starts at 10 cm, a flat plan at 5 cm. At a low zoom the plan draws only the steps whose lines are far enough apart. With **Show grid** (or **G**) you hide the lines; snapping is not affected.
- **Snapping:** The **Snap** switch makes objects snap to the grid and to corners and edges of other objects when you move, draw or drag handles.
- **Length unit:** You choose metres or centimetres for all dimensions in the editor. Storage is always in metres.
- **Zoom:** The fixed levels are 25, 50, 100, 200 and 400 percent; **Fit** shows the whole plan. The scale bar shows how long a distance is on the plan.
- **Compass:** Set the **north angle** so the plan knows where geographic north lies: turn the dial, use the arrow keys or type a value (0 up to but not including 360 degrees, clockwise; 0 means north is up). The compass in a phone gives magnetic north, so Kamerplanter never takes it over automatically. If the site has GPS coordinates, the compass marks today's sunrise and sunset directions (filled dot and ring, with time and degrees below, shading not considered); from the north angle and the rotation Kamerplanter also derives each bed's long axis, which you see in its properties and which is stored as its orientation as long as no slope direction is entered. <!-- REQ-053 GP-FR-016, GP-FR-017 -->
- **Mini-map:** see [Working faster in the garden plan](#plan-comfort).

### Properties, side panel and list view {#properties-and-list-view}

The **side panel** has four tabs:

| Tab | Content |
|-----|---------|
| **Properties** | The selected bed or object (see below). |
| **View** | Grid step, grid, snapping, length unit and compass. |
| **Layers** | The [layers](#layers-and-site-conditions) with their switches, the attention filter, the legend and the zone legend. |
| **Zones** | Manage the [irrigation zones](#irrigation-zones). |

When you select something, the panel opens on **Properties**. When you clear the selection, it collapses again if the selection opened it. If you opened it yourself with the panel switch in the header bar, it stays open; if you closed it yourself, it stays closed until you open it or select something new. Without a selection it opens on the tab used last, the first time on **View**. You reach the tabs with the keyboard too: the arrow keys move from tab to tab, Enter or Space opens the tab. So you can move across the tabs without the content changing.

The **Properties** tab shows name, type, position (x to the right, y upwards, in metres), dimensions and rotation counter-clockwise for the selected bed or object. You change the values directly; **Lock** protects an object from being moved by accident. For a bed you also find **Plant it**, the sun tiles and the number of open and overdue tasks with a jump to the care tab. For a polygon the panel lists the points.

For a garden object the tab shows the **object properties** of its kind: for a **trellis** the height, for a **window** sill height, glazing and the compass direction Kamerplanter derives from its position in the wall and the north angle (read only), for a **door** the swing, for a **lamp** kind, mounting height and a reference light intensity (Kamerplanter does not calculate anything from it yet). The **Outside the property** switch marks an object such as a neighbour's tree: it may stick out of the garden boundary and is drawn as scenery. You can switch it off only when the object lies completely inside the garden. The object legend in the **Layers** tab explains the symbols of all object kinds on the plan. **Compost**, **water source** and **storage** also get the [Tasks](#tasks-on-garden-objects) section. <!-- REQ-053 GP-FR-180 -->

The **List** tab shows the same objects as a list of areas, beds and garden objects. Each entry has move buttons, an input for a target position and Delete. It is the alternative for screen readers and for everyone who does not want to draw.

## Working faster in the garden plan {#plan-comfort}

This section describes the aids that save you manual work in planning mode.

**A bed from a template.** In the tool bar, **From template** puts a bed on the plan with one click. You pick a template, turn it in 90-degree steps with **Rotate** if needed, and click where the bed should go (the lower-left corner of a rectangle, the centre of a circle). A dashed preview shows where it lands; it turns red where the bed would not fit completely into the garden. Without a mouse, **Place at view centre** puts the middle of the bed in the middle of the view. The bed gets the template's name, type, shape and height and is saved at once; Kamerplanter saves your unsaved changes first. This step cannot be taken back with **Undo**. If you do not want the bed, delete it. **Esc** or another tool ends the template choice. When the template brings recurring tasks, ticking **Create recurring tasks** creates them on the new bed, each recurring yearly; without the tick (the default) you get the bed only.

**Standard sizes.** In the **Add with dimensions** dialog, a standard size fills shape, size, bed type and height in one go, for example the raised bed 1.2 × 2.4 m, the raised bed 2 × 1 × 0.8 m or a planter. You can still change every value afterwards. The height is optional.

**Save as template.** With exactly one bed selected, **Save as template** stores its shape, type and height as a template of your garden. Plants, tasks and notes are not part of it, and the template only carries planting distances or soil values if you enter them yourself. Growers and leads create templates.

**Snapping to other objects.** When you move or draw, the plan snaps to corners and edges of other objects before it snaps to the grid. When you move a bed, every corner of it snaps, even when the bed is rotated, not just the spot under the pointer: this lets you put the right edge of one bed exactly against the left edge of the next. For a round bed, the centre and the four points at the very top, bottom, left and right of its rim snap. A green ring shows the point that snaps, a green line the edge it sits on. The Alt key or the **Snap** switch turns snapping off. With a pen or a finger the catch zone is larger.

**Align and distribute.** With at least two beds or objects selected, **Align** lines them up on the left, right, top or bottom edge or on the centre. From three objects on, **Distribute evenly** spreads them with equal gaps; the two outermost objects stay where they are. Locked objects stay where they are and do not count. Objects that stand side by side or staggered are distributed even when they overlap in that direction. If two of them would end up on top of each other, for example because they stand exactly in line, or one would land on a locked object, Kamerplanter distributes nothing and tells you why. Each of these actions is a single step for **Undo**.

**Overview map.** When the garden is much larger than the visible section (more than four times), a small map appears at the bottom right of the plan with the section as a rectangle. A click on it jumps the view there. With the keyboard you keep moving the plan with the arrow keys.

**Auto-save.** The **Auto-save** switch next to **Save** saves your changes two seconds after the last change. It is off by default and applies only to you in this browser. On a conflict or a refused save it pauses and tells you so. Field mode does not have it: every action is sent at once there.

**Duplicate several times.** From the **⋯** menu or the context menu, **Duplicate several times** makes several copies of the selected beds in a row: count, direction, spacing and a naming scheme such as "Plot {n}" (up to 100 copies). You enter the spacing in the length unit you chose for the plan (m or cm). That is handy for the plots of a community garden. Kamerplanter first checks that the copies fit completely into the garden and that the limit of 500 beds and objects is enough; if not, nothing is created. If a copy does not fit into the garden, the dialog names the first one that does not fit. One **Undo** takes all copies back. Planting positions, plants and tasks are not copied; you lay out a planting grid for each bed afterwards. <!-- REQ-053 GP-FR-025, GP-FR-029, GP-FR-043, GP-FR-044, GP-FR-045, GP-FR-154, GP-UX-004, GP-UX-014 -->

## Saving, conflicts and undo

Changes in the editor are first applied only locally. The header bar shows the state (on narrow screens as an icon with a counter): **Unsaved changes (n)**, **Saving …**, **Saved**, **Conflict** or **Saving failed**. **Save** (or **Ctrl + S**) sends all open changes to the server in one step: either all are accepted or none. The **Auto-save** switch does this for you, see below.

- **Undo and redo** (Ctrl + Z, Ctrl + Shift + Z) cover the last 100 steps. The history applies to this session only: if you reload the page, it is gone.
- **Conflict:** If someone else saved the plan while you were working on it, the server does not accept your changes. A dialog names who changed it last. Before you reload you can download your changes as a copy (JSON). When you reload, your unsaved changes and the undo history are lost.
- **Rejected:** If a change breaks a rule, the server refuses the whole save and the message names the place. Common reasons: two beds overlap, an object sticks out of the garden boundary, plants still grow on a bed (clear the bed before deleting it), more than 500 changes are open, or the plan has reached its limit of 500 locations and objects together. Fix the named place or undo it; your other changes are kept.
- **Deleting:** As long as you have not saved, you can undo a deletion. After saving you cannot. The dialog first names what is deleted with it.

## Planting a bed {#planting-a-bed}

Select a bed and click **Plant it** in the properties panel. The planting dialog opens, which you also know from the bed view. You choose species and cultivar, see hints on crop rotation, neighbours and site, set the arrangement (grid, rows, staggered, area or free positions), see a preview and either plan the planting or record it at once. This works with the "grower" role; the bed must be on the plan and must not be retired. The steps are under [Planting a bed](locations-substrates.md#planting-a-bed).

Plants appear on the plan as markers. The plant state layer is described in [Plant state and filter](#plant-state-and-filter).

**Succession sowing in a bed.** When you generate the batches of a succession plan for a bed with planting positions, every batch still to come reserves free positions for its time in the bed, and the plan shows these positions dashed with the day from which they are taken. <!-- REQ-053 GP-FR-074, #2896 -->

**Trellis.** If a species needs a support (such as peas or pole beans), the planting dialog tells you which trellises are drawn in the bed or on its edge, with their height. If none is drawn, it says so; you can still plant. Species without this information get no hint. <!-- REQ-053 W-005 -->

### Sowing, thinning and replanting {#sowing-thinning-replanting}

In the **Planting** tab of the bed view, rows and areas you sow directly work like this:

1. **Record sowing:** on a planned row or area you record the day of sowing (at most a year back, not in the future). No single plants exist yet; the row is listed under **Sown** with its date, and the plant state shows it with seed dots.
2. **Thin out:** once the seedlings stand, you pull the surplus ones and tap **Thin out**. The dialog takes the spacing from the planting plan, which you can change, and calculates the number of plants from it and the row length or area. If no spacing is stored, it asks for the spacing or directly for the number of seedlings left standing; Kamerplanter never fills in a value on its own. For an area the dialog also asks for the row spacing and prefills it from the planting plan or the species profile (naming the source); with a row spacing it calculates row spacing × spacing in the row, without one (broadcast sowing) it estimates on a square grid and tells you which calculation it used. Afterwards the plants are recorded one by one, the row no longer counts as sown, and the care log gets a "thinning" entry.
3. **Replant:** if a plant died (recorded as "died" when it was removed), its place is listed under **Failed**. **Replant** opens the planting dialog with the same crop and its spacing. A plant that was cleared at the natural end of its life ("senesced") does not count as failed and gets no **Replant**.

!!! note "Partially available: sowing"
    Sown rows and areas appear in the **Planting** tab, in the plant state and in the legend, but not yet as a line or area on the drawing area and not in the PDF or SVG. <!-- REQ-053 W-015 -->

**Crop rotation hint when replanting.** The dialog knows which plant you are replacing and no longer holds its family against you as "already stood here this year". Instead, a residual hint depends on the cause you recorded when you removed the plant:

| Recorded cause | Hint in the dialog |
|----------------|--------------------|
| Disease or pests | Warning: if the pathogen or pest lives in the soil, the new plant of the same family can fail the same way. **Plant anyway** needs a short reason; nothing is ever blocked. |
| Cause unknown or not recorded | Soft info hint with the same consideration. |
| Frost, heat, drought, waterlogging, neglect or mechanical damage | No hint. |

Other plants in the bed and earlier years count as before. If you recorded a soil change on the bed, the hint is gone entirely.

!!! tip "Tip"
    Record the cause when you mark a plant as "died". Without a cause you see the info hint even if frost was the reason. <!-- REQ-053 §11.3, GP-FR-131, #2888 -->

## Bed List on the Garden Plan {#bed-list-on-the-garden-plan}

The **Beds** tab (in a flat plan **Planting spots**) lists your beds in a table: name (a link to the bed view), type, area, status, responsible person, plants, open tasks (including overdue ones) and next due date. Retired beds are hidden by default. The **My beds** switch filters to your own beds and requires that beds are assigned to you.

If you click a row or press Enter, the page switches to the **Plan** tab, the bed is selected and the view zooms to it. After every save the list shows the saved state. The number in the "Open tasks" column is a link to the bed's Care tab. From the "grower" role on, the button **Complete tasks on several beds** sits above the table (see [Care on the bed](locations-substrates.md#care-on-the-bed)).

## Tasks on garden objects {#tasks-on-garden-objects}

A compost heap, a water source or a storage shed needs work too: turning the compost, winterising the rain barrel, tidying the shed. When you select such an object on the plan, the **Properties** tab shows the **Tasks** section with the object's open tasks, sorted by due date. **Add task** opens the task dialog with the object as its target; you choose among the kinds that suit an object: maintenance, cleaning, observation, covering and uncovering. Tasks "for every plant" do not exist here because an object carries no plants. Other objects such as paths, fences or trellises get no tasks. An object must be saved before it gets tasks, and you cannot add any without a connection. Members from the "grower" role on may add them. <!-- REQ-053 R-7.2, W-008 -->

## Flat plan: windowsill, shelf and tent {#flat-plan}

For a site in your home (site type indoor, windowsill or grow tent) the garden plan is a **flat plan**. You draw and plan with the same tools as in the garden; a few things are set up for indoors:

- **Empty plan:** instead of "No garden plan yet" you see **No flat plan yet** with two ways in: **Draw the floor plan** opens the drawing area and starts drawing the outline of your flat right away (see [The garden boundary](#the-garden-boundary)), **Load a photo as a template** opens it with the [underlay](#underlay) dialog. A photo or sketch of the floor plan, calibrated to real dimensions with two points, is the easiest start.
- **Grid:** a new flat plan starts at 5 cm instead of 10 cm.
- **Indoor objects:** under **Garden object** you find **Window** (a line in the wall), **Door**, **Furniture** (windowsill, shelf, table) and **Lamp**. Their properties are described under [Properties, side panel and list view](#properties-and-list-view).
- **What indoors leaves out:** Kamerplanter hides frost, cold-air pocket, heat storage and wind for indoor sites, and the frost layer too. Stored values are kept.
- **Planting spots:** the **Beds** tab is called **Planting spots** here (the address keeps `tab=beds`) and lists everything you can lay out plants in: tents and shelves as well as tubs and planters. A room itself is not a planting spot.

**Suggest the sun from the windows.** A window knows its compass direction as soon as it sits in the wall: Kamerplanter derives it from its position on the plan and the north angle and shows it in the window's properties, for example "South-east, 135°". When you select a planting spot, its sun section offers **Suggest from windows**. A dialog shows the windows within the radius (1.5 m by default; you set the radius per site), the suggested value for the sun at the bed (morning, midday, afternoon, all day or changing) and notes, for example that shading by neighbouring buildings or trees is not considered. Windows facing away from the sun only bring diffuse light and do not count. **Cancel** changes nothing. Only **Take over** writes the value; if a value is already set, the button reads **Replace** and the dialog tells you beforehand what gets replaced. Hours and foliage shade stay unchanged. Without GPS coordinates for the site Kamerplanter assumes the northern hemisphere; between the tropics there is no suggestion. <!-- REQ-053 GP-FR-180, GP-FR-181, GP-FR-182, GP-FR-183 -->

**Tent rules.** On the page of a tent or shelf you enter, under **Tent rules**, an own **adjacency factor** (it overrides the garden's value, for example when plants grow into each other on purpose) and the **lighting**: lamp height and distance to the plants. Kamerplanter stores the lighting for a later light calculation and does not calculate anything from it yet. If plants in the same tent need different day lengths in their current phase according to their phase profiles, the page warns you: a lamp has only one schedule. If no light duration is stored for a phase, the page says so instead of guessing. When you plant, the dialog warns if a pot is smaller than the species' recommended pot volume. <!-- REQ-053 W-016 -->

!!! note "Partially available: flat plan"
    The light-need warning currently names the phases by their English name, also in the German interface. Some labels still talk about the "garden" indoors. <!-- REQ-053 GP-FR-182, #2889 -->

## Field mode in the garden {#field-mode-in-the-garden}

Field mode is made for the phone at the bed: large buttons (at least 64 pixels), strong contrast for sunlight and only what you need outside. On a narrow screen (below 600 pixels wide) the garden plan page opens in field mode right away. On any device you switch with **Field mode** or **Planning mode** at the top of the page; the address then carries `?mode=field` or `?mode=plan`.

**My beds · due today.** Field mode starts with the list of your beds. Beds assigned to you come first (marked **Mine**), then beds with overdue tasks or tasks due today, then the rest by their next due date. A task is overdue when its due day lies before today; a task due today does not count as overdue yet. Retired beds are left out. The **Map** tab shows the plan without tools, grid or handles. **Zoom in**, **Zoom out** and **Whole plan** change the view. If you tap a bed, or just next to it, the map zooms to the bed and opens it.

**My position.** Above the map you switch on **My position**. Only then does your browser ask whether Kamerplanter may use your location. A dot with a circle shows roughly where you stand in the garden; the circle is at least 3 m wide and grows when your device locates less precisely. The dot moves with you while the switch is on and the map is open. This needs GPS coordinates on the site and a north direction on the plan; the coordinates count as the middle of your garden. If they are missing, if you declined access, or if you are more than 500 m away from the plan, you see a hint instead of the dot. **Your position stays on your device:** Kamerplanter does not send it to the server and stores it nowhere; even the switch is off again the next time you open field mode. <!-- REQ-053 GP-UX-026 -->

**The bed sheet.** A tap on a bed opens a sheet at the bottom with the bed's name (its cover photo beside it, if it has one), the quick log, the tasks and the plants. Tasks come in the order **Overdue**, **Due today**, **Later**. Plants are grouped by species, count and phase; the phase colour always has a black outline and the phase name next to it.

- **Done** opens the short dialog with the optional fields (quantity, note). **Finish** saves. That is two taps after choosing the bed. A double tap counts once, and the buttons stay locked until the answer has arrived.
- **Quick log:** **Watered**, **Sown** and **Weeded/Mulched** save a care entry with one tap. **Harvested** and **Note** open the short form (quantity or text; for the note you can use your keyboard's voice input). **Planted** opens the planting dialog with **I have planted already** switched on; the plants are created at once. This needs a bed that is drawn on the plan.
- After **Done** and after every quick log entry you see **Undo** for eight seconds. It takes the entry back.
- **Show plants** lists the single plants of a group. **Correct position** moves a plant with the arrows in 10 cm steps; you can drag the marker only after holding it for half a second. While you drag, the plant snaps to the garden plan's grid within the bed; hold Alt to place it freely to the centimetre. **Photo** takes a picture for the plant's gallery.
- **Photo of the bed** takes a picture for the gallery of the whole bed (see [Photos of the bed](locations-substrates.md#photos-of-the-bed)). The first photo of a bed becomes its cover photo. Without a connection Kamerplanter keeps the photo on your device and uploads it as soon as you are back online (see [What works offline](#what-works-offline)).

Deleting, clearing a bed, export and import are not available in field mode; switch to planning mode for them. With the "viewer" role you see tasks and plants read-only. Your browser, not your account, remembers the tenant, site, tab and map view; if someone else signs in on the device, field mode starts fresh for them. If a remembered map view would show hardly any of the plan on the current screen – after turning the phone, for example – the map opens on the whole plan.

Without a connection field mode keeps **Done**, the **Note** and photos on your device and sends them as soon as you are back online; the other quick log buttons need a connection. What exactly works offline is described under [What works offline](#what-works-offline).

**QR label on the bed.** In the bed view, **Print label** creates a PDF label with the bed name, site, type, area and a QR code; you choose the size of the code (25, 40 or 60 mm). Scanning the code with your phone opens field mode with the sheet of exactly this bed. If you are not signed in, you go through the sign-in first and come straight back to the bed. The code holds only the address of the bed, no password and no access: someone who is not a member of your garden sees nothing. If you are a member of several gardens, switch to the bed's garden first.

!!! warning "Not yet implemented"
    **Planted** will get an **Undo**. The "last watered" layer will exist only in planning mode. <!-- REQ-053 GP-UX-020…031, GP-FR-149 -->

## What works offline {#what-works-offline}

In the garden the network is often weak. Kamerplanter therefore remembers on your device what you loaded last, and keeps what you capture in field mode without a connection. The bar at the top always shows whether you are **Online** or **Offline**.

### Reading offline

Without a connection Kamerplanter shows you the last loaded state of these pages:

- the garden plan of a site,
- the site list,
- in field mode the list of your beds and the bed sheet with tasks and plants,
- the bed view with the bed head and the **Plan** tab; the other tabs, such as the master data under **Details**, need a connection.

A banner tells you how old the data is: "Offline: you are looking at the state as of 14:05." A state is remembered for at most 15 minutes. If you have not opened a page with a connection within that time, Kamerplanter shows a notice instead of the data, for example "This plan is not available offline". Open the page once with a connection then.

Without a connection you can only look at the plan: drawing, moving and relocating are locked, unsaved changes are kept. On the bed, status, sun, soil, rotation and photos are locked until the connection is back.

### Capturing offline

In field mode you can capture three things without a connection:

- **Done** for a task,
- a **Note** from the quick log,
- a **Photo of the bed** and the **Photo** of a plant.

Kamerplanter stores each entry on your device with the time you captured it. As soon as you are back online, the app sends the entries in order, the oldest first, and shows the progress ("Sending 2/5 entries …"), then something like "5 entries sent." An entry arrives only once, even if the app sends it again after a dropped connection. **Undo** takes an entry back out within the eight seconds after it.

- Per account your device keeps at most 500 entries. When the store is full, the app tells you and takes nothing more until you have been online.
- Before storing a photo, the app scales it down to at most 1,920 pixels on the longer side and stores it without location (GPS) and camera data.
- While entries are waiting, the bar at the top shows how many, for example **"3 not sent"**. If sending fails, the app tries again with a growing pause. After five attempts, when the server refuses the entry, or when the task has been completed or deleted in the meantime, it no longer sends the entry by itself and tells you so. A tap on the count opens **Entries not sent**: there you choose per entry between **Try again**, **Keep** (the entry stays on the device for reading and is not sent again) and **Discard**.
- What is not sent, the device deletes by itself at some point: waiting entries older than one year are no longer accepted by the server; entries not sent and kept entries disappear 90 days after capture. The app tells you how many there were.

### Online only

**Watered**, **Sown**, **Weeded/Mulched**, **Harvested** and **Planted**, **Correct position**, sun and site features, all drawing and moving on the plan, deleting, export, import and bed templates need a connection. Without a connection these buttons are locked; nothing gets lost.

### Reload once the first time

When you open Kamerplanter on a device for the first time, or after you have cleared the site data, reload the page once while you still have a connection. Only then does your browser have everything that capturing offline needs.

### Signing out and switching gardens

When you sign out, Kamerplanter deletes the remembered state on this device. If you still have entries that are not sent, the app asks first: **Send now**, **Discard and sign out** or **Cancel**. Without a connection **Send now** does not work; the dialog tells you why. When you switch to another garden, Kamerplanter deletes the remembered state as well; your entries of the previous garden that are not sent stay on the device and are sent as soon as you return there. What exactly is on your device and when it is deleted is described under [Data on your device](privacy.md#data-on-your-device).

## Kamerplanter on the home screen {#home-screen}

You can put Kamerplanter on the home screen of your phone or into the app list of your computer like an app. It then opens in its own window without an address bar. Kamerplanter shows no install prompt of its own; you use your browser's menu:

- **Chrome or Edge** (Android, Windows, macOS, Linux): menu → **Install app** or **Add to home screen**.
- **Safari on iPhone and iPad:** **Share** → **Add to Home Screen**.

When there is a new version, the banner **New version available** appears at the bottom. **Update now** loads it in all open windows; with **Later** you keep working for now.

## Layers and site conditions {#layers-and-site-conditions}

You show and hide layers in the side panel's **Layers** tab; every switch carries its name. Your browser remembers your choice; it applies only to you. The grid is not a layer of this group: it has its own switch **Show grid** in the **View** tab (on at the start, key **G**), see [Grid, snapping, zoom and compass](#grid-snapping-zoom-and-compass).

| Layer | Shows | At the start |
|-------|-------|--------------|
| **Show irrigation zones** | Zones as an outline with hatching over their beds | off |
| **Show last watered** | Days since the last recorded watering per bed, as hatching | off |
| **Show underlay** | The background picture (visible only if the site has an underlay) | on |
| **Show sun window** | When direct sun reaches a bed | off |
| **Show drainage** | How well a bed drains | off |
| **Show frost risk** | Low, normal or high per bed | off |
| **Show plant state** | Phase, ring and sign of every plant | off |
| **Show companion planting** | Lines between neighbouring plants: good, bad or unknown neighbours | off |

The legend in the **Layers** tab explains every layer that is switched on; it appears as soon as at least one layer is on. A flat plan has no frost layer. The hatching of zones and of the state layers differs in pattern, not only in colour.

The **Last watered** layer shows only the distance to the last recorded watering in four steps (0 to 1, 2 to 3, 4 to 7, more than 7 days). It does not say whether a bed needs water. A bed without a recorded watering stays without hatching.

### Sun window, drainage and frost risk {#sun-window-drainage-frost-risk}

You maintain the values on the bed: sun, sun window and leaf shade in the sun tiles (see [Sun and shade of a bed](locations-substrates.md#sun-and-shade-of-a-bed)), drainage in the soil profile. The layers show these entries on the whole plan.

**Sun window, drainage and frost risk layers in the garden plan.** In the **Layers** tab you can show three more layers: **Show sun window** (when direct sun reaches the bed), **Show drainage** (poor, moderate, good) and **Show frost risk** (low, normal, high). Every value has its own pattern, so you can tell them apart without colour. The pattern is always shown; once you zoom in far enough for the bed names to appear, a small symbol for the value joins it at the bottom edge of the bed, where the bed has room for it; the legend in the **Layers** tab explains every layer that is on. A bed without a recorded value stays without a pattern. All three layers start switched off, and your browser remembers your choice for you. The frost layer shows the stored frost risk; for overwintering, the frost exposure stays the setting that counts. <!-- REQ-053 GP-FR-169, GP-FR-047 -->

### Plant state and filter {#plant-state-and-filter}

What disc, ring and sign on a plant mean is described under [Plant state and plant info](locations-substrates.md#plant-state). In the garden plan the following applies to the layer:

**Plant state layer and filter in the garden plan.** With **Show plant state** in the same tab you see the state of your plants without opening a bed. Once you zoom close enough to a bed for the single plants to appear, every plant carries disc, ring and sign as in the bed's **Plan** tab: the colour shows the growth phase, the ring how far the planting is, the sign at the top right the most urgent reason to act. Further out each bed sums up its plants as a circle with a number; if you have seen a bed close enough before, Kamerplanter knows its states: the circle then shows the most urgent sign, and the screen reader names the number of all plants in the bed and how many of them need attention. Next to it sits the switch **Only show plants that need attention**: it hides every plant whose state is known and that carries no sign. A plant whose state is not loaded yet stays visible. The circle of a bed then shows only the plants that remain, and it disappears only once every state of the bed is known and no plant needs attention; the bed itself stays visible, and the screen reader still names the number of all plants. While the layer is off, the switch is disabled; you still reach it with the Tab key, and the screen reader tells you why it is disabled. The legend in the **Layers** tab explains rings and signs and lists the colours of the growth phases of the plants whose states are loaded, sorted alphabetically in your language. Kamerplanter loads the states only while the layer is on, only for the beds you currently see close enough, and at most four beds at a time. Each bed loads once and again when you come back to the tab, when you save the plan or a newer version of it loads, and after you changed a zone or logged a watering round in the irrigation panel. The layer and the filter start switched off; your browser remembers your choice. The info bubble on hovering a plant stays with the bed's **Plan** tab. <!-- REQ-053 GP-UX-061, GP-UX-060 -->

!!! note "Partially available: plant state"
    **Frost danger** does not appear as a sign yet, even though the **Frost risk** layer shows the stored value. **Watering due** arises so far only from a watering task due today, not from the irrigation demand. <!-- REQ-053 GP-UX-060, GP-FR-190 -->

### Companion planting on the plan {#companion-planting-on-the-plan}

**Companion planting layer in the garden plan.** With **Show companion planting** in the **Layers** tab you see whether neighbouring plants get along. The plan draws a line between two neighbouring occupied places of a bed. A place can hold a standing plant or a species that a running planting plans there. The kind of line says what is known:

| Line | Meaning |
|------|---------|
| Solid, green | Good neighbours: the species help each other. |
| Dashed, red | Bad neighbours: the species hinder each other. |
| Dotted, grey | Nothing known: no relation is stored for this pair. |

The lines differ in their stroke, not only in their colour, so you can tell them apart in greyscale too. Point at a line with the mouse and a card appears. It names the two species that decide the verdict, the stored reason or a short explanation, for good neighbours the score from 0.1 to 1 and, if known, the distance. On a touchscreen you tap the line. The card then stays open until you close it or tap somewhere else on the plan. A tap on a line does not select the bed below it, and a swipe that starts on a line still pans the plan. If a place holds more than eight species, the plan judges only the first eight; the card tells you so. The verdict is the same as in the planting dialog (**Plant it**): if any species pair of the two places is incompatible, the pair counts as bad neighbours.

The lines appear only once you zoom close enough to a bed for the single plants to show. Kamerplanter loads them only while the layer is on, only for the beds you currently see that close, and at most four beds at a time. Each bed loads once and again when you save the plan or a newer version of it loads. The plan shows at most 500 lines at once, bad neighbours first; if more pairs are in view, the legend tells you. Then zoom in closer. The layer starts switched off; your browser remembers your choice. <!-- REQ-053 GP-FR-134 -->

**Without mouse or touch.** The lines themselves are not reachable with the Tab key, so the plan does not get hundreds of tab stops. Open the **list of neighbouring pairs** in the layer's legend instead. For every pair in view it states the neighbourhood in words, the two species, the reason and the score, bad neighbours first. The list is a single tab stop; scroll in it with the arrow keys. <!-- REQ-053 GP-FR-134 -->

## Irrigation zones and the watering round {#irrigation-zones}

An **irrigation zone** groups beds of one site that are watered together, for example on a drip line or under a sprinkler. A bed belongs to at most one zone. A site can have up to 500 zones.

You manage zones in the side panel's **Zones** tab; **Manage irrigation zones** in the **⋮** menu opens it directly.

1. **Create a zone:** Click **New zone**. Enter a name, choose the **type of irrigation** (By hand, Drip irrigation, Sprinkler, Soaker hose or Sub-irrigation) and a colour. Optionally enter a water source (a garden object of type water source), the flow rate in litres per minute and a schedule note.
2. **Assign beds:** Tick the beds or take over the plan selection with **Take over selection from the plan**. A bed that already lies in another zone moves to this one; the interface tells you. Beds and water sources you have not saved yet are available for selection only after you save the plan.
3. **Save the zone.** All members may read; the "grower" role and above may change; only the lead may delete. If you delete a zone, the beds stay unchanged and then belong to no zone; the watering log is kept.

**State of the zone.** For each zone Kamerplanter shows when it was last watered, the next planned watering, the **demand today** (net and gross, with the efficiency from the zone or as a guide value of the irrigation type), the **consumption of the last 30 days** with its source, and hints, for example how long the water source lasts at this daily demand.

**Log a watering round.** When you have watered a whole zone, **Log watering round** opens a dialog: you enter the **total amount in litres** (more than 0, at most 100,000) and choose the **distribution**: **By bed area** (each bed gets a share by its area; beds without an area are left out) or **Equal parts**. Kamerplanter writes one watering entry per bed into the care log. The amount is divided, not measured; the log marks it that way.

A third **distribution** is **By demand**: each bed gets a share by its calculated water demand on that day; beds without a demand are left out.

**Rain — skipped.** When it has rained and you skip the round, tap **Rain — skipped** in the same dialog. Kamerplanter then writes one rain entry without an amount per bed of the zone into the care log. Open watering tasks stay open, and the entry does not count as a watered amount. <!-- REQ-053 GP-FR-117 -->

**Water source.** When you select a garden object of type water source on the plan, you enter the **Kind of water source**, the **Capacity** in litres (for a rain barrel or cistern) and the day **Last refilled** in the properties area. The zone state shows how long the water source lasts only with a capacity. <!-- REQ-053 GP-FR-111 -->

!!! info "API only: technical coupling"
    Only members with the `technical` admin scope maintain the coupling of a zone to an actuator or to a Home Assistant entity for the flow, and only through the API. Restoring a backup never takes these links over. See [For Technical Users / Self-Hosters](#for-technical-users-self-hosters).

## Bed templates {#bed-templates}

A bed template fixes shape, dimensions, bed type and height of a bed so you do not redraw the same shape every time. Kamerplanter ships standard sizes, for example bed 1 × 1 m, 2 × 1 m, 3 × 1.2 m and 4 × 1.2 m, raised bed 1.2 × 2.4 m and 2 × 1 × 0.8 m, and planters of 0.3, 0.4 and 0.5 m diameter. Your own templates belong to your garden.

- **Place:** **From template** in the toolbar, see [Working faster in the garden plan](#plan-comfort).
- **Save:** Select exactly one bed and click **Save as template**. Plants, tasks and notes are not part of it. A garden can have up to 200 own templates; when the limit is reached, delete one you no longer need first.
- **Share:** In the **Bed from template** area, **Export** downloads the chosen template as a JSON file, without your garden's key, without author and without notes. That is how you pass a template on to other gardens. **Import** takes such a file (at most 256 KB) and checks it first: the check report shows name, shape, height and planting grid, and which fields of the file are skipped. If the name exists already, Kamerplanter proposes a free one. Nothing is saved until you confirm **Import**. Kamerplanter reads files of the current and the previous version; export an older file again.
- **Roles:** Growers and the lead create and import templates; only the lead may delete.

## Underlay for tracing {#underlay}

With an **underlay** you place a photo, a sketch or an aerial view under the plan and trace the beds on it.

1. Choose **Underlay** in the **⋮** menu and pick an image (JPEG, PNG or WebP). The plan needs a garden boundary for this.
2. **Calibrate:** Click two points in the image whose distance you know and enter the distance in metres. From this Kamerplanter calculates the scale (pixels per metre).
3. **Position:** Set where the top left corner of the image lies on the plan, rotate the image counter-clockwise if needed and set the opacity.
4. **Save.** With **Remove underlay** you delete the image and the calibration; you would have to create both again.

A site has at most one underlay, and all members see the same one. Whether you display it is your own choice with the **Show underlay** layer. Growers and the lead may set and remove it. The underlay lies below all objects, is not part of the JSON backup and goes into the PDF print only if you choose it explicitly in the export dialog (see [Export the plan and restore a backup](#plan-export-import)). Aerial views can reveal where you live: pass on a plan with an underlay only if you mean to.

## Rotation matrix {#rotation-matrix}

The matrix shows at a glance what stood in all beds of a site in the last years. Open it on the site page with **Rotation matrix** (address `/standorte/sites/<key>/rotation-matrix`). Each row is a bed, each column a year, the current year is on the right. How far back the matrix reaches follows the longest rotation pauses of the families in the beds shown, at least five and at most ten years.

A cell lists one entry per planting: the plant family as a short code with colour and pattern, below it the feeder class as text and, when known, the season. Colour never carries the family alone: code and pattern tell them apart in black and white print too. The legend under the table names the full family for each code. Green manure and fallow are marked. An empty year shows a dash: nothing is recorded.

- **Fill in.** With the role "grower" or "lead" you tap a past year and fill in what grew there in the familiar **What stood here?** dialog (see [History of the bed](locations-substrates.md#history-of-the-bed)). The matrix does not take the current year; there, what is planted in the bed counts. Observers ("viewer") only read the matrix.
- **To the bed.** The name of the bed leads to the bed view.
- **Beds without the check.** A bed that is exempt from the rotation check or switched off is still in the matrix, with a note at its name. Its history stays visible.
- **Many beds.** The matrix loads 50 beds per page; **Load more beds** fetches the next ones, with the same years. It reads at most 500 beds by name; a site with more shows a note below.
- **Future years.** The matrix does not show planned follow-up crops yet; it ends in the current year.

The matrix reads the same data as the timeline of the bed and recalculates nothing: a field of the matrix is exactly the timeline entry for the same bed and year. <!-- REQ-053 GP-FR-135 -->

## Change log {#change-log}

Kamerplanter keeps a change log for every plan: deletions and changes of the garden boundary with the time and the name of the editor, plus the states a replace import overwrote (see [Export the plan and restore a backup](#plan-export-import)). Entries are kept for one year. The log has no page of its own in the interface; you can read it through the API (see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters)).

What happened on a single bed is in its history: the crop rotation timeline and the list of all care entries and plantings are described in [History of the bed](locations-substrates.md#history-of-the-bed).

## Export the plan and restore a backup {#plan-export-import}

On the garden plan page, **Export plan …** and **Restore a backup …** in the **⋮** menu open two dialogs.

**Export plan** comes as a PDF (the plan to scale, for printing), an SVG (vector graphic), a PNG (image) and a backup (JSON). You choose paper, orientation, scale and layers (for the PDF also **Bed list as a second page**); a preview shows what you get. With **Automatic**, Kamerplanter takes the finest scale that fits the sheet and suggests A3 when A4 would get too coarse. If a fixed scale does not fit the sheet, the dialog says so and lets you choose a coarser scale or A3. On a phone there is only PDF and backup with the standard options. The export holds no member names and no assignments (the parcel list in the PDF and the bed list as CSV can include them on request, see below).

**Parcel list in the PDF.** With **Parcel list as an extra page** the PDF gets one more page, for the board or the landlord, for example: every bed with a running number in plan order and its name, plus area and irrigation zone. Only when the parcel list is on does the dialog offer **Include assignments in the parcel list**. That adds a column with the names of the members a bed is assigned to; those are personal data, so pass the PDF on only to people who may see them. Notes and account data are never in it. <!-- REQ-053 GP-FR-176 -->

**Underlay in the PDF.** If the plan has an [underlay](#underlay), the dialog offers **Print the underlay** for the PDF; the switch is off, and only when you turn it on does your photo or sketch lie below the printed plan. <!-- REQ-053 GP-FR-033 -->

**PNG (image)** is made by your browser from the plan, without the server: the whole plan as an image, for sharing in messages or pasting into documents. It shows the layers you have switched on in the plan. You choose the **Resolution** 1×, 2× or 4×; 2× is preselected. 1× is at most 1,200 pixels on the longer side, 2× and 4× are sharper and the file gets bigger. The dialog tells you the size in pixels beforehand. If the image would be larger than your browser can draw, Kamerplanter takes the largest possible resolution and tells you so. The **Watermark "Kamerplanter · date"** in the bottom right corner is an option and starts off. PNG is not available on a phone. <!-- REQ-053 GP-FR-144 -->

**Bed list (CSV)** outputs the beds of the site as a table, one line per bed, for further work in your spreadsheet. Name, type, area, status, soil texture, irrigation zone and active plants are preselected; you can also tick site conditions such as sun exposure, frost risk or slope. Choose at least one column. The **Excel variant** separates columns with a semicolon and writes numbers with a decimal comma so the file opens straight as a table in a German-language Excel. The **Include assignments** switch is off: without it no member names are in the file. If you switch it on, a column with the names of the assigned members is added; this is personal data, so share the file only with people who may see it. Notes and account data are never included. The header row uses fixed English column ids (for example `name`, `area_m2`, `frost_risk`, `assigned_to`), and fields with fixed values such as status, soil texture or frost risk appear as their value code (for example `active`, `loam`, `high`); type and irrigation zone appear with their names. That way the file has the same layout whatever your language setting. A file holds at most 2,000 beds; with more, the dialog shows a message. Like SVG, the bed list is not offered on a phone; use a larger screen.

In the PDF and the SVG every plant shows its state as on the plan: the disc in the colour of its growth phase, a ring for how far it is (a thick ring means *harvesting*) and at most one sign for the most urgent matter, such as a triangle for an open finding or a drop when watering is due. The legend lists the growth phases, rings and signs that occur on the plan. Of the growth phases it names at most the six with the most plants; if there are more, one entry such as "+3 more phases" sums up the rest, so the plan still fits the page at the chosen scale. A long phase name is shortened with "…". Plants of a species with its own phase sequence carry the same colour as on the plan. From 2,000 plants on, each bed shows only the number of its plants instead. <!-- REQ-053 GP-UX-005, GP-UX-059, GP-UX-060 -->

The **backup** holds beds, garden objects, plant places, irrigation zones, soil profiles, site features and the garden boundary, but no plants and no tasks. If you have selected beds or garden objects on the plan, you can limit the backup to **Selection only** or **Selection with everything below**. Such a partial backup has no garden boundary, and references to things that are not in the file are dropped. Every role may read it.

**Restore a backup** leads through the import in three steps. Only a lead can do this.

1. **Choose file:** The file may be at most 5 MB. Kamerplanter checks it right away without writing anything. If you only have a bed list in a spreadsheet, the **Import a bed list (CSV)** link takes you to the [CSV import](#beetliste-csv-import).
2. **Check report:** You see how much would be created and deleted, which references are not carried over (for example an irrigation zone that does not exist here) and which problems the file has, such as overlapping beds. With problems you cannot continue.
3. **Mode:** *Add* creates the backup in addition to the existing plan. *Replace* swaps the plan of this site. For that you type the name of the site. Before that, Kamerplanter saves the previous plan as a snapshot in the change log. Download a current backup first anyway, to be safe.

In *Add* mode you can move every shape of the file by a distance (to the right and up, in metres), for example to put a bed somewhere else. **Where is the file going?** tells Kamerplanter whether the file comes from this site, another site or another garden account. For the last two, references that are not in the file are never resolved against this site: they are dropped and listed in the check report. Nothing is read from another account, the file is the transport; you need the lead role in the account you import into.

If you import the same file several times with *Add*, each round creates its irrigation zones again; Kamerplanter does not recognise the zones of the file. A site can have at most 500 zones; beyond that the check report rejects the file.

**Restore an earlier state:** In the first import step this button opens the list of plans that a *Replace* overwrote (kept for one year, at most the 20 newest per site, lead only). You pick a state, read the check report and type the name of the site. Kamerplanter first saves the current plan as a state of its own, so the restore can be undone. Irrigation zones that the state does not name are removed, and technical zone bindings (actuator, Home Assistant flow) are not restored; set them up again afterwards. *Add* does not create a state.

!!! warning "Beds with active plants"
    A bed with a plant in it is never deleted. While such beds exist, *Replace* rejects the file. If you choose the option to keep those beds, they stay together with the locations above them, and the rest is replaced.

**New season from last year:** In the **⋮** menu, **New season from last year …** re-creates last year's places as free slots for every bed without active plants (lead only, within the same site). You enter the year of the new season; the places come from what was finished in the year before. Kamerplanter checks first and shows what happens per bed: beds with active plants and retired beds are skipped and listed in the report, and so is a bed that would pass 2,000 slots with the new places. Places that already stand as a free slot are not created twice. Zones, plants, planting runs and history stay as they are; crop rotation and companion planting hints keep using last year's occupancy. **Show "Here stood …"** adds the plant family of last year to each bed, for orientation only. Only **Create free slots** writes, in one step with an entry in the change log; if the plan changed since the check, you check again. <!-- REQ-053 GP-FR-171 -->

All keys are newly assigned on import. Links to Home Assistant and to actuators are never carried over; set them up again afterwards. If you have unsaved changes to the plan, save or discard them first. In field mode, export and import are hidden.

## Importing a bed list from a CSV file {#beetliste-csv-import}

If you already keep your beds in a spreadsheet, a CSV file (a table as a text file, one line per bed) creates them all in the garden plan at once. Only the lead role may do this. You open the import in the **⋮** menu with **Import a bed list (CSV) …** or through the link in the first step of the backup import.

1. **Choose a file:** Pick your CSV file. **Download an example file** gives you a template to complete in your spreadsheet. Kamerplanter checks the file straight away but writes nothing yet.
2. **Check report:** You see how many lines are valid, which beds (name, size, sun) would be created, which lines have errors and which columns the import does not know and ignores. Errors and warnings name the line and column. Lines with an error are skipped; you can still apply the remaining lines. If no line is valid, fix the file and choose it again.
3. **Create:** **Create … beds** adds the valid beds. They are then selected in the plan so you can arrange them right away.

!!! note "Did the plan change?"
    If someone changed the plan since you checked the file, Kamerplanter stops and writes nothing. Click **Check again** and then apply once more.

### How the file must be built

- The first line is the header with the column names. Separate the columns with a semicolon (`;`).
- Required columns: `Name`, `Typ`, `Breite_m` and `Länge_m` (also `Laenge_m`). The English names are `name`, `type`, `width_m` and `length_m`.
- Optional columns: `Sonne` (`sun`), `Bodenart` (`soil_texture`) and `Zone` (`irrigation_zone`). The import ignores any other column and names it in the report.
- Give sizes in metres, with a decimal comma or point (`2,5` or `2.5`). Thousands separators and units such as "m" are not allowed.
- `Typ` is the key of a bed type or its German or English name, for example Raised Bed. A type that is not a bed (such as the type Greenhouse) is an error.
- `Sonne` and `Bodenart` take the value or its label. Without `Bodenart` the bed gets no soil profile.
- `Zone` is the name of an irrigation zone of the same site.
- The file is UTF-8 encoded (a BOM at the start is fine), at most 1 MB in size, with at most 500 rows and 100 columns. In Excel, choose "CSV UTF-8".

If a cell starts with a formula character (`=`, `+`, `-`, `@`, tab or line break), Kamerplanter removes the character and shows a warning. That way a spreadsheet cannot smuggle a formula into your plan.

### Where the beds end up

Kamerplanter places the new beds as rectangles in rows from the top-left corner of the garden boundary, 0.5 m apart. A new row starts at the edge of the boundary, and existing beds are skipped. If a bed finds no space, that line is an error. A site holds at most 500 beds and garden objects together; if the list would exceed that, Kamerplanter rejects the whole file. You fix the exact positions afterwards in the editor.

## For Technical Users / Self-Hosters {#for-technical-users-self-hosters}

This section is for everyone who creates the plan through the API or operates an installation. All paths are under `/api/v1/t/{slug}/`.

- **Create the first plan:** `PUT /sites/{key}/plan/boundary` with the garden boundary (rectangle or polygon), optionally `north_angle_deg`. The first call creates the plan.
- **Read the plan:** `GET /sites/{key}/plan`. **Read the change log:** `GET /sites/{key}/plan/audit`.
- **PDF with underlay:** `GET /print/garden-plan/{site_key}?underlay=true`. The parcel list is requested with `parcel_list=true`, the names of the assignments additionally with `include_assignment=true`.
- **Exchange a bed template:** `GET /bed-templates/{key}/export` and `POST /bed-templates/import` (with `dry_run`).
- **Kill switch for offline work:** With `PWA_CACHING_ENABLED=false` the app unregisters its service worker (the browser's background program for offline use and push) on the next page load and deletes the remembered state **and the offline entries that are not sent yet** on every device. Use it only when offline work itself causes trouble; tell your users beforehand to go online and send their entries. See [Environment variables](../reference/environment-variables.md).
- **Bed list via API:** `POST /beds/import-csv` under `/sites/{key}` with the CSV file as the raw body (`dry_run` defaults to `true`). Routes, report fields and error codes are in the [API reference](../reference/api-reference.md#create-beds-from-a-csv-bed-list).
- **Rate limits** and retention are listed under [Environment Variables](../reference/environment-variables.md).
- Structure, batch interface and backup format are described in [Garden Plan: Geometry and Interfaces](../architecture/garden-plan.md); the routes and error codes are in the [API Reference](../reference/api-reference.md#garden-plan-pdf-svg-json-backup).

## Frequently Asked Questions

??? question "What do I do if the plan shows **No garden plan yet**?"
    The site has no plan yet. Choose **Add the first bed** and then draw the garden boundary through the **⋮** menu, or import a backup, see [The garden boundary](#the-garden-boundary).

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
