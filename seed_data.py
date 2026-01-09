import os
import django
import random
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from tracker.models import Habit, DailyEntry, HabitLog

def run_seed():
    print("Seeding data...")
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("Superuser 'admin' created.")
    
    user, created = User.objects.get_or_create(username='testuser')
    if created:
        user.set_password('testpass')
        user.save()
        print("User 'testuser' created.")

    # Create Habits
    habits_data = [
        ('Sleep', 'health', 8.0, 'hours'),
        ('Drink Water', 'health', 2500, 'ml'),
        ('Reading', 'productivity', 30, 'pages'),
        ('Coding', 'productivity', 4, 'hours'),
        ('Meditation', 'mindfulness', 15, 'minutes'),
    ]
    
    habits = []
    for name, cat, target, unit in habits_data:
        h, _ = Habit.objects.get_or_create(
            user=user, 
            name=name, 
            defaults={'category': cat, 'target_value': target, 'unit': unit}
        )
        habits.append(h)
    
    # Create Daily Entries for last 14 days
    today = date.today()
    for i in range(14):
        d = today - timedelta(days=i)
        productivity = random.randint(3, 10)
        mood = random.randint(3, 10)
        
        # Correlate sleep (habit 0) with productivity
        # We'll generate sleep value first
        sleep_val = random.uniform(5, 9)
        # Higher sleep -> higher productivity (simplistic correlation logic for demo)
        if sleep_val > 7.5:
            productivity = max(productivity, random.randint(8, 10))
        elif sleep_val < 6:
            productivity = min(productivity, random.randint(1, 5))

        entry, created = DailyEntry.objects.get_or_create(
            user=user,
            date=d,
            defaults={
                'productivity_score': productivity,
                'mood_score': mood,
                'notes': f"Log for {d}"
            }
        )
        
        # Log Habits
        # Sleep
        HabitLog.objects.get_or_create(entry=entry, habit=habits[0], defaults={'value': round(sleep_val, 1)})
        # Water
        HabitLog.objects.get_or_create(entry=entry, habit=habits[1], defaults={'value': random.randint(1000, 3000)})
        # Reading
        if random.random() > 0.3:
            HabitLog.objects.get_or_create(entry=entry, habit=habits[2], defaults={'value': random.randint(10, 50)})

    print("Seeding complete.")

if __name__ == '__main__':
    run_seed()
