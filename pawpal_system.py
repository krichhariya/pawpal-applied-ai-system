import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List
import json
import os
from dataclasses import asdict
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# Set up logging for guardrails
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
load_dotenv() # Load the API key from the .env file

@dataclass
class Task:
    """Represents a single care activity."""
    description: str
    duration_mins: int
    priority: str 
    frequency: str
    due_time: str
    due_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    is_completed: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def mark_complete(self) -> None:
        """Updates the task status to done."""
        self.is_completed = True

    @staticmethod
    def from_dict(data):
        return Task(**data)

@dataclass
class Pet:
    """Represents a pet profile."""
    name: str
    species: str
    age: int
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Appends a new care task to the pet's list."""
        self.tasks.append(task)

    @staticmethod
    def from_dict(data):
        tasks_data = data.pop('tasks', [])
        pet = Pet(**data)
        pet.tasks = [Task.from_dict(t) for t in tasks_data]
        return pet

@dataclass
class Owner:
    """Represents the user managing the schedule."""
    name: str
    available_time_mins: int
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Links a pet profile to the owner."""
        self.pets.append(pet)

    def save_to_json(self, filename="data.json"):
        """Serializes the entire Owner tree to a JSON file."""
        with open(filename, "w") as f:
            json.dump(asdict(self), f, indent=4)

    @staticmethod
    def load_from_json(filename="data.json"):
        """Reconstructs the Owner and all sub-objects from JSON."""
        if not os.path.exists(filename):
            return None
        with open(filename, "r") as f:
            data = json.load(f)
            pets_data = data.pop('pets', [])
            owner = Owner(**data)
            owner.pets = [Pet.from_dict(p) for p in pets_data]
            return owner

class Scheduler:
    """
    Manages scheduling logic, conflict detection, and task retrieval.
    This is the 'Brain' of the system.
    """
    def __init__(self, owner: Owner):
        self.owner = owner
        self.schedule: List[Task] = []

    def get_all_tasks(self) -> List[Task]:
        all_tasks = []
        for pet in self.owner.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def get_upcoming_tasks(self) -> List[Task]:
        return [task for task in self.get_all_tasks() if not task.is_completed]

    def get_tasks_by_pet(self, pet_name: str) -> List[Task]:
        for pet in self.owner.pets:
            if pet.name.lower() == pet_name.lower():
                return pet.tasks
        return []

    def get_tasks_by_status(self, is_completed: bool) -> List[Task]:
        return [task for task in self.get_all_tasks() if task.is_completed == is_completed]

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        return sorted(tasks, key=lambda t: t.due_time if t.due_time.lower() != "any" else "24:00")

    def _time_to_mins(self, time_str: str) -> int:
        if time_str.lower() == "any":
            return 1440 
        hours, mins = map(int, time_str.split(":"))
        return hours * 60 + mins

    def check_conflicts(self, new_task: Task) -> str | None:
        if new_task.due_time.lower() == "any":
            return None

        new_start = self._time_to_mins(new_task.due_time)
        new_end = new_start + new_task.duration_mins

        for pet in self.owner.pets:
            for existing_task in pet.tasks:
                if existing_task.is_completed or existing_task.due_time.lower() == "any":
                    continue
                    
                existing_start = self._time_to_mins(existing_task.due_time)
                existing_end = existing_start + existing_task.duration_mins

                if new_start < existing_end and existing_start < new_end:
                    return (f"⚠️ Conflict Warning: '{new_task.description}' "
                            f"overlaps with {pet.name}'s '{existing_task.description}' "
                            f"(scheduled from {existing_task.due_time}).")
        return None

    def complete_task(self, task_id: str) -> None:
        target_task = None
        target_pet = None
        
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.id == task_id:
                    target_task = task
                    target_pet = pet
                    break
        
        if not target_task or target_task.is_completed:
            return

        target_task.mark_complete()

        freq = target_task.frequency.lower()
        if freq in ["daily", "weekly"]:
            current_date = datetime.strptime(target_task.due_date, "%Y-%m-%d")
            days_to_add = 1 if freq == "daily" else 7
            next_date = current_date + timedelta(days=days_to_add)
            
            new_task = Task(
                description=target_task.description,
                duration_mins=target_task.duration_mins,
                priority=target_task.priority,
                frequency=target_task.frequency,
                due_time=target_task.due_time,
                due_date=next_date.strftime("%Y-%m-%d")
            )
            target_pet.add_task(new_task)

    def generate_daily_schedule(self) -> List[Task]:
        pending_tasks = self.get_upcoming_tasks()
        priority_map = {"high": 1, "medium": 2, "low": 3}

        pending_tasks.sort(key=lambda x: (
            priority_map.get(x.priority.lower(), 4), 
            x.duration_mins
        ))

        daily_plan = []
        time_used = 0

        for task in pending_tasks:
            if time_used + task.duration_mins <= self.owner.available_time_mins:
                daily_plan.append(task)
                time_used += task.duration_mins

        self.schedule = daily_plan
        return self.schedule

    def generate_agentic_schedule(self) -> str:
        """
        Agentic Workflow: The AI drafts a schedule, evaluates its own work 
        against the time budget, and retries if it fails.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logging.error("No API key found. Falling back to basic Python logic.")
            self.generate_daily_schedule()
            return "⚠️ **System Notice:** API key missing. Displaying standard schedule below."

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        pending_tasks = self.get_upcoming_tasks()
        if not pending_tasks:
            return "No tasks pending for today!"

        task_details = [f"- {t.description} ({t.duration_mins}m, {t.priority.upper()} priority)" for t in pending_tasks]
        budget = self.owner.available_time_mins
        
        draft_prompt = f"""
        You are an expert pet care assistant. The owner has {budget} minutes available today.
        Here are the pending tasks:
        {chr(10).join(task_details)}
        
        Create a chronological daily schedule. Prioritize HIGH priority tasks first. 
        If the total time of tasks exceeds the {budget} minute budget, you MUST drop the lowest priority tasks.
        Format the output nicely using Markdown, including a brief, empathetic explanation of your choices.
        """

        max_retries = 3
        for attempt in range(max_retries):
            try:
                logging.info(f"Agent generating schedule... (Attempt {attempt + 1})")
                draft_response = model.generate_content(draft_prompt).text
                
                verify_prompt = f"""
                Look at this schedule you just generated:
                {draft_response}
                
                The owner only has {budget} minutes. Did you include tasks that total MORE than {budget} minutes?
                Answer strictly with exactly one word: YES or NO.
                """
                
                eval_response = model.generate_content(verify_prompt).text.strip().upper()
                logging.info(f"Agent self-evaluation returned: {eval_response}")
                
                if "NO" in eval_response:
                    return draft_response 
                else:
                    logging.warning("AI exceeded time budget. Prompting it to try again.")
                    draft_prompt += "\nCRITICAL RULE REMINDER: You failed the time check. You MUST drop tasks to stay under budget!"
                    
            except Exception as e:
                logging.error(f"AI API Error: {e}")
                self.generate_daily_schedule() 
                return "⚠️ **System Notice:** AI generation failed. Using standard logic."
                
        return "⚠️ **Warning: This schedule may exceed your time budget.**\n\n" + draft_response

    def find_next_available_slot(self, duration_mins: int) -> str:
        day_start = 8 * 60 
        day_end = 20 * 60
        
        busy_blocks = []
        for task in self.get_tasks_by_status(is_completed=False):
            if task.due_time.lower() != "any":
                start = self._time_to_mins(task.due_time)
                busy_blocks.append((start, start + task.duration_mins))
        
        busy_blocks.sort()

        current_time = day_start
        for start, end in busy_blocks:
            if start - current_time >= duration_mins:
                return f"{current_time // 60:02d}:{current_time % 60:02d}"
            current_time = max(current_time, end)

        if day_end - current_time >= duration_mins:
            return f"{current_time // 60:02d}:{current_time % 60:02d}"

        return "No slots available today."
    
    def sort_by_priority_and_time(self, tasks: List[Task]) -> List[Task]:
        priority_map = {"high": 0, "medium": 1, "low": 2}
        return sorted(tasks, key=lambda t: (
            priority_map.get(t.priority.lower(), 3),
            t.due_time if t.due_time.lower() != "any" else "23:59"
        ))
