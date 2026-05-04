# PawPal+ System Reflection & Model Card

## 🧪 Reliability and Evaluation

To prove this system is robust and not just a fragile AI wrapper, PawPal+ relies on a multi-layered testing and reliability strategy:

* **Automated Unit Tests:** A complete `pytest` suite guarantees the underlying deterministic Python logic (conflict detection, time conversion, recurring tasks) is mathematically sound before the AI ever interacts with it.
* **Automated AI Evaluation:** The Agentic Workflow acts as its own internal tester. The Evaluator Agent actively reviews the Generator Agent's output against the user's hard time budget constraint. 
* **Logging & Error Handling:** The API calls are wrapped in `try/except` blocks utilizing Python's built-in `logging` module. If the API times out or the AI fails its math check three times, the system logs the error (`logging.error`) and automatically triggers the standard Python scheduling algorithm as a safe fallback.
* **Human Verification:** The AI is instructed to explain its scheduling choices in the UI, allowing the pet owner to quickly verify that the triage logic makes sense for their pet's specific needs.

**Testing Summary:**
All automated `pytest` functions passed for the core scheduling engine. During Agentic integration, the AI struggled initially when asked to drop tasks, resulting in budget overruns. Reliability and adherence to constraints improved drastically after adding the strict `"CRITICAL RULE REMINDER"` to the self-correction loop. Simulated API outages were successfully caught by the error handlers, ensuring 100% uptime for the user via the Python fallback.

## 🧠 Reflection and Ethics

**Limitations and Biases**
The primary limitation of PawPal+ is its lack of physical context. The AI operates on a bias toward "productivity" and schedule optimization, assuming that as long as a task fits mathematically within a time block, it should be scheduled. In reality, pet care is highly contextual; a dog might be too tired for a 30-minute walk even if the owner has 30 minutes available. The system also biases toward the owner's constraints rather than evaluating the pet's behavioral or emotional state.

**Potential Misuse and Prevention**
A significant risk is that a user might over-rely on the AI for critical triage, inputting a severe medical symptom alongside routine tasks to see how the AI schedules it. If the AI hallucinates or misprioritizes, it could delay urgent veterinary care. 
* **Prevention:** To prevent this, the system's core prompt should be updated with a hardcoded ethical guardrail: *“If any task mentions bleeding, trauma, or severe illness, you must clear the entire schedule, prioritize the Vet Visit immediately, and output a medical disclaimer.”*

**Surprises During Reliability Testing**
During testing, I was surprised by how poorly the underlying LLM handled strict arithmetic. When given a 60-minute budget and 90 minutes of tasks, the AI initially tried to "squeeze" tasks in by hallucinating shorter durations or simply ignoring the constraint entirely to please the user. It required engineering a multi-step Agentic Workflow—where a second prompt acts as a "Critic" to explicitly verify the math—and adding aggressive `"CRITICAL RULE REMINDER"` prompts to force the AI to reliably drop tasks.

**AI Collaboration**
* **Helpful Suggestion:** AI was instrumental in helping me architect the "Slot Finder" algorithm and writing the `timedelta` logic required to accurately calculate and spawn future dates for recurring daily and weekly tasks.
* **Flawed Suggestion:** When building the initial task-filtering logic, the AI suggested a highly complex, nested "one-liner" utilizing `next()` and generator expressions. While technically "Pythonic," it was incredibly difficult to read and impossible to easily debug. I ultimately rejected the suggestion, opting to write a standard `for` loop to ensure the code remained maintainable and clear.
