# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

**Core User Actions:** Before structuring the classes, I identified the primary actions a user must be able to perform within the PawPal+ system:
    1.  **Manage Profiles:** The user can enter and store basic demographic information about themselves (the owner) and their pet (e.g., name, species).
    2.  **Manage Care Tasks:** The user can add, edit, and define specific pet care tasks, ensuring they include critical constraints like task duration and priority level.
    3.  **Generate a Daily Schedule:** The user can prompt the system to evaluate the inputted tasks against constraints to build, output, and explain a logical daily care plan.

My initial design focused on four core classes to separate the responsibilities of the system:
* **Task:** Represents a single care activity. It holds the data for what needs to be done, including constraints like `duration_mins`, `priority`, and `due_time`. It is responsible for its own completion status.
* **Pet:** Represents the animal receiving care. It acts as a container for the pet's demographic info (`name`, `species`) and holds a list of `Task` objects specific to that pet.
* **Owner:** Represents the user. It holds the user's `name`, a list of their `Pet` objects, and a critical system constraint: `available_time_mins` (how much time they have to do tasks today).
* **Scheduler:** This is the "brain" of the application. It takes in the pets (and their tasks) and evaluates them against constraints to generate a prioritized daily schedule and check for conflicts.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

* **Connecting the Time Constraint:** Initially, the `Scheduler` was entirely disconnected from the `Owner` class, meaning it had no access to the `available_time_mins` constraint needed to build a realistic schedule. I modified the design so that `generate_daily_schedule(available_time_mins: int)` explicitly takes the owner's available time as an argument.
* **Task Uniqueness:** I realized that relying on a task's `description` (e.g., "Walk") could cause bugs if a pet has multiple identical tasks in a day. I updated the `Task` class to include a unique ID (`uuid`) to ensure the scheduler can accurately track, schedule, and complete specific instances of a task.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

* **Constraints Considered:** The scheduler primarily evaluates the owner's `available_time_mins` to ensure the day isn't overbooked. It also factors in task `priority` (High, Medium, Low) and `due_time` (chronological ordering).
* **Decision Matrix:** I prioritized `available_time_mins` as a hard cap (the loop breaks if time is exceeded) and `priority` as the primary sorting mechanism, ensuring the most critical tasks are handled first before time runs out.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

* **The Tradeoff:** My `generate_daily_schedule` method relies on a "Greedy Algorithm." It sorts tasks by priority and shortest duration, then iteratively adds them until the available time is exhausted. 
* **Why it's reasonable:** A greedy approach does not mathematically guarantee the absolute optimal use of every single minute (a classic Knapsack problem), and it might leave small gaps of unused time. However, for a daily pet care scenario, mathematical perfection isn't necessary. The greedy approach is highly performant, easy to maintain, and effectively mimics how a real human prioritizes their day—knocking out the most important and quickest tasks first.
---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

* **Architectural Brainstorming:** I used AI to transition from basic classes to a centralized `Scheduler` "brain" that could handle complex interactions between owners, pets, and time-sensitive tasks.
* **Algorithmic Refinement:** AI assisted in implementing the `timedelta` math for recurring tasks and the "greedy" sorting logic used for task prioritization and time-fitting.
* **Most Helpful Prompts:** Questions such as *"What are the most common edge cases for a daily scheduler?"* and *"How can I check for overlapping time durations using start times and total minutes?"* were instrumental in building a robust backend.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

* **The Moment:** When building the task filtering logic, the AI suggested using a complex, nested "one-liner" with `next()` and generator expressions.
* **Evaluation:** While the suggestion was technically correct and "Pythonic," I modified it to use a standard `for` loop. I evaluated that **readability and maintainability** were more important for a system that might need future debugging or expansion. I verified all logic by running a `pytest` suite to ensure the human-readable code performed exactly as intended.
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

* **Chronological Sorting:** Verified that tasks appear from morning to night, regardless of the order in which they were added.
* **Conflict Detection:** Confirmed the system triggers a warning string when two tasks overlap in their time windows.
* **Recurrence Logic:** Proved that completing a "Daily" task automatically spawns a new instance for the following day with the correct date format.
* **Importance:** These tests serve as the "safety net" for the application. Without them, a user could double-book themselves or lose track of recurring care, leading to a loss of trust in the tool's reliability.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

* **Confidence Level:** 5/5. The core scheduling engine is fully covered by automated unit tests that handle both "happy paths" and common user input errors.
* **Future Edge Cases:** If I had more time, I would test "Midnight Rollover" (tasks that start at 11:30 PM and end at 12:30 AM) and add input validation for non-standard time formats (e.g., "8am" instead of "08:00").

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

* I am most satisfied with the **Conflict Detection** feature. It transforms the app from a simple to-do list into a proactive assistant that "understands" time and helps the user avoid mistakes before they happen.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

* In a future iteration, I would redesign the `Owner` class to support multiple time zones and implement a "Drag-and-Drop" interface in Streamlit to allow users to manually override the automated schedule order.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

* The most important thing I learned is that being a **"Lead Architect"** means acting as the **Editor-in-Chief** for AI. The AI provides the "building blocks," but the human must provide the logical blueprint and the final verification to ensure the system is safe, readable, and truly helpful for the end user.
