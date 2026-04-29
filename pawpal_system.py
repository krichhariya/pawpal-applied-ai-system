import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List
import json
import os
from dataclasses import asdict

@dataclass
class Task:
    """Represents a single care activity."""
    description: str
    duration_mins: int
    priority: str 
    frequency: str
    due_time: str
    # Defaults to today's date formatted as YYYY-MM-DD
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
        """Helper: Retrieves a flattened list of all tasks across all pets."""
        all_tasks = []
        for pet in self.owner.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def get_upcoming_tasks(self) -> List[Task]:
        """Returns tasks that are not yet completed."""
        return [task for task in self.get_all_tasks() if not task.is_completed]

    def get_tasks_by_pet(self, pet_name: str) -> List[Task]:
        """Filters all tasks across the owner's profile by a specific pet's name."""
        for pet in self.owner.pets:
            if pet.name.lower() == pet_name.lower():
                return pet.tasks
        return []

    def get_tasks_by_status(self, is_completed: bool) -> List[Task]:
        """Filters all tasks to return only completed or incomplete tasks."""
        return [task for task in self.get_all_tasks() if task.is_completed == is_completed]

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sorts a list of tasks chronologically by their due_time ('HH:MM')."""
        return sorted(tasks, key=lambda t: t.due_time if t.due_time.lower() != "any" else "24:00")

    def _time_to_mins(self, time_str: str) -> int:
        """Helper: Converts 'HH:MM' to total minutes for overlap math."""
        if time_str.lower() == "any":
            return 1440  # Represents 24:00 (end of day)
        hours, mins = map(int, time_str.split(":"))
        return hours * 60 + mins

    def check_conflicts(self, new_task: Task) -> str | None:
        """
        Lightweight conflict detection.
        Returns a warning message if an overlap is found, otherwise returns None.
        """
        if new_task.due_time.lower() == "any":
            return None  # Flexible tasks don't conflict

        new_start = self._time_to_mins(new_task.due_time)
        new_end = new_start + new_task.duration_mins

        # Check against all tasks across all pets
        for pet in self.owner.pets:
            for existing_task in pet.tasks:
                if existing_task.is_completed or existing_task.due_time.lower() == "any":
                    continue
                    
                existing_start = self._time_to_mins(existing_task.due_time)
                existing_end = existing_start + existing_task.duration_mins

                # Lightweight overlap check
                if new_start < existing_end and existing_start < new_end:
                    return (f"⚠️ Conflict Warning: '{new_task.description}' "
                            f"overlaps with {pet.name}'s '{existing_task.description}' "
                            f"(scheduled from {existing_task.due_time}).")
                    
        return None

    def complete_task(self, task_id: str) -> None:
        """Marks a task complete and generates the next occurrence if recurring."""
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
        """Sorts tasks by priority and fits them into the day based on available time."""
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

    def find_next_available_slot(self, duration_mins: int) -> str:
        """
        Scans the day (08:00 to 20:00) to find the first gap 
        that fits the requested duration.
        """
        # Define the 'active' day in minutes (8 AM to 8 PM)
        day_start = 8 * 60 
        day_end = 20 * 60
        
        # Get all busy blocks
        busy_blocks = []
        for task in self.get_tasks_by_status(is_completed=False):
            if task.due_time.lower() != "any":
                start = self._time_to_mins(task.due_time)
                busy_blocks.append((start, start + task.duration_mins))
        
        # Sort busy blocks by start time
        busy_blocks.sort()

        current_time = day_start
        for start, end in busy_blocks:
            # Is there enough gap between current_time and the next task?
            if start - current_time >= duration_mins:
                # Found a slot! Convert minutes back to HH:MM
                return f"{current_time // 60:02d}:{current_time % 60:02d}"
            # Move current_time to the end of this busy block
            current_time = max(current_time, end)

        # Check if there is space after the last task
        if day_end - current_time >= duration_mins:
            return f"{current_time // 60:02d}:{current_time % 60:02d}"

        return "No slots available today."
    
    def sort_by_priority_and_time(self, tasks: List[Task]) -> List[Task]:
        """
        Sorts tasks by priority (High > Medium > Low), 
        then chronologically for tasks of the same priority.
        """
        priority_map = {"high": 0, "medium": 1, "low": 2}
        
        return sorted(tasks, key=lambda t: (
            priority_map.get(t.priority.lower(), 3), # Primary sort: Priority
            t.due_time if t.due_time.lower() != "any" else "23:59" # Secondary sort: Time
        ))