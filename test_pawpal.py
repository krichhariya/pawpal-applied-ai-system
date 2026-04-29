from datetime import datetime, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler

def test_task_mark_complete():
    """Verify that calling mark_complete() changes the task's status to True."""
    # 1. Arrange: Create a sample task
    task = Task(
        description="Morning Walk", 
        duration_mins=30, 
        priority="high", 
        frequency="Daily", 
        due_time="08:00"
    )
    
    # Verify the default state is False
    assert task.is_completed is False
    
    # 2. Act: Mark the task as complete
    task.mark_complete()
    
    # 3. Assert: Verify the state changed
    assert task.is_completed is True

def test_pet_add_task():
    """Verify that adding a task to a Pet increases that pet's task count."""
    # 1. Arrange: Create a pet and a task
    mochi = Pet(name="Mochi", species="Dog", age=3)
    task = Task(
        description="Brush Fur", 
        duration_mins=15, 
        priority="low", 
        frequency="Weekly", 
        due_time="18:00"
    )
    
    # Verify the pet starts with no tasks
    assert len(mochi.tasks) == 0
    
    # 2. Act: Add the task to the pet
    mochi.add_task(task)
    
    # 3. Assert: Verify the task list grew and contains the right task
    assert len(mochi.tasks) == 1
    assert mochi.tasks[0].description == "Brush Fur"

def test_scheduler_sort_by_time():
    """Verify tasks are returned in chronological order, with 'Any' at the end."""
    # 1. Arrange
    scheduler = Scheduler(Owner(name="Test", available_time_mins=100))
    t1 = Task(description="Evening", duration_mins=10, priority="low", frequency="Once", due_time="18:00")
    t2 = Task(description="Morning", duration_mins=10, priority="low", frequency="Once", due_time="08:00")
    t3 = Task(description="Flexible", duration_mins=10, priority="low", frequency="Once", due_time="Any")
    
    tasks = [t1, t2, t3]

    # 2. Act
    sorted_tasks = scheduler.sort_by_time(tasks)

    # 3. Assert
    assert sorted_tasks[0].description == "Morning"
    assert sorted_tasks[1].description == "Evening"
    assert sorted_tasks[2].description == "Flexible"

def test_scheduler_conflict_detection():
    """Verify the Scheduler flags duplicate or overlapping times."""
    # 1. Arrange
    owner = Owner(name="Test", available_time_mins=100)
    pet = Pet(name="Mochi", species="Dog", age=3)
    
    # Existing task from 08:00 to 08:30
    existing_task = Task(description="Walk", duration_mins=30, priority="high", frequency="Daily", due_time="08:00")
    pet.add_task(existing_task)
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)

    # 2. Act
    # New task attempting to start at 08:15 (direct overlap)
    new_task = Task(description="Meds", duration_mins=5, priority="high", frequency="Once", due_time="08:15")
    conflict_result = scheduler.check_conflicts(new_task)

    # 3. Assert
    # The result should be a warning string, not None
    assert conflict_result is not None
    assert "Conflict Warning" in conflict_result

def test_scheduler_recurrence_logic():
    """Confirm that marking a daily task complete creates a new task for the following day."""
    # 1. Arrange
    owner = Owner(name="Test", available_time_mins=100)
    pet = Pet(name="Mochi", species="Dog", age=3)
    
    # Create a daily task scheduled for today
    today_str = datetime.now().strftime("%Y-%m-%d")
    daily_task = Task(description="Walk", duration_mins=30, priority="high", frequency="Daily", due_time="08:00", due_date=today_str)
    
    pet.add_task(daily_task)
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)

    # 2. Act
    scheduler.complete_task(daily_task.id)

    # 3. Assert
    # The original task should be complete
    assert daily_task.is_completed is True
    
    # The pet should now have 2 tasks in its list (the completed one + the new one)
    assert len(pet.tasks) == 2
    
    # The new task should be incomplete and scheduled for tomorrow
    new_task = pet.tasks[1]
    assert new_task.is_completed is False
    
    expected_tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    assert new_task.due_date == expected_tomorrow
    