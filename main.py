from pawpal_system import Task, Pet, Owner, Scheduler

def run_demo():
    # 1. Setup the environment
    owner = Owner(name="Jordan", available_time_mins=120)
    mochi = Pet(name="Mochi", species="Dog", age=3)
    luna = Pet(name="Luna", species="Cat", age=2)
    
    owner.add_pet(mochi)
    owner.add_pet(luna)
    scheduler = Scheduler(owner=owner)

    print("\n🐾 --- Scheduling Tasks --- 🐾")

    # 2. Add the first task for Mochi
    task1 = Task(description="Morning Walk", duration_mins=30, priority="high", frequency="Daily", due_time="08:00")
    mochi.add_task(task1)
    print(f"✅ Scheduled: Mochi's '{task1.description}' at {task1.due_time}")

    # 3. Try to add a conflicting task for Luna at the exact same time
    task2 = Task(description="Grooming", duration_mins=20, priority="medium", frequency="Once", due_time="08:00")
    
    # 4. Check for conflicts before adding
    conflict_warning = scheduler.check_conflicts(task2)
    
    if conflict_warning:
        print(conflict_warning)
    else:
        luna.add_task(task2)
        print(f"✅ Scheduled: Luna's '{task2.description}' at {task2.due_time}")

    # 5. Try to add a non-conflicting task
    task3 = Task(description="Give Medicine", duration_mins=5, priority="high", frequency="Daily", due_time="08:45")
    
    conflict_warning = scheduler.check_conflicts(task3)
    if conflict_warning:
        print(conflict_warning)
    else:
        luna.add_task(task3)
        print(f"✅ Scheduled: Luna's '{task3.description}' at {task3.due_time}\n")

if __name__ == "__main__":
    run_demo()