import logging
from pawpal_system import Scheduler, Owner, Task

# Silence standard logging so our report card is clean
logging.getLogger().setLevel(logging.CRITICAL)

def run_evaluation():
    print("\n" + "="*40)
    print("🐾 PAWPAL+ AI EVALUATION HARNESS 🐾")
    print("="*40 + "\n")
    
    scenarios = [
        {"name": "Scenario 1: Ample Time", "budget": 180, "expected": "PASS"},
        {"name": "Scenario 2: Time Crunch", "budget": 60, "expected": "PASS (Should drop tasks)"},
        {"name": "Scenario 3: Impossible Crunch", "budget": 10, "expected": "FAIL / HEAVY DROP"}
    ]
    
    test_tasks = [
        Task(description="Vet Visit", duration_mins=60, priority="high", frequency="once", due_time="any"),
        Task(description="Morning Walk", duration_mins=30, priority="medium", frequency="daily", due_time="any"),
        Task(description="Brush Fur", duration_mins=20, priority="low", frequency="weekly", due_time="any")
    ]

    passed_tests = 0

    for idx, test in enumerate(scenarios):
        print(f"Running {test['name']} (Budget: {test['budget']}m)...")
        
        owner = Owner(name="TestUser", available_time_mins=test['budget'])
        owner.tasks = test_tasks 
        scheduler = Scheduler(owner=owner)
        scheduler.get_upcoming_tasks = lambda: test_tasks
        
        result = scheduler.generate_agentic_schedule()
        
        if "⚠️" in result and test['budget'] == 180:
            status = "❌ FAILED (Flagged ample time as an error)"
        elif test['budget'] < 110 and "Vet Visit" in result and "Brush Fur" not in result:
            status = "✅ PASSED (Correctly dropped low priority task)"
            passed_tests += 1
        elif test['budget'] == 180:
             status = "✅ PASSED (Scheduled all tasks safely)"
             passed_tests += 1
        else:
            status = "⚠️ UNCERTAIN (Review output manually)"

        print(f"Result: {status}")
        print("-" * 40)

    print(f"\nFinal Score: {passed_tests}/{len(scenarios)} Tests Passed.\n")

if __name__ == "__main__":
    run_evaluation()
