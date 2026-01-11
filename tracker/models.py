from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, RegexValidator
from datetime import timedelta
from django.utils import timezone

class Habit(models.Model):
    # Default categories for suggestions, but field is free text
    DEFAULT_CATEGORIES = ['Health', 'Productivity', 'Mindfulness', 'Learning', 'Fitness', 'Finance']
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, default='Health')
    target_value = models.FloatField(help_text="Target goal for the habit (e.g. 8 for hours, 2000 for ml)")
    unit = models.CharField(
        max_length=50, 
        help_text="Unit of measurement (e.g. hours, ml, pages)",
        validators=[
            MinLengthValidator(1, message="Unit cannot be empty."),
            RegexValidator(r'^[a-zA-Z\s/%]+$', message="Unit must contain only letters, spaces, or symbols like / and %.")
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    @property
    def streaks(self):
        dates = sorted(list(self.logs.values_list('entry__date', flat=True).distinct()))
        if not dates:
            return {'current': 0, 'longest': 0}

        # Longest streak calculation
        longest = 1
        current_seq = 1
        for i in range(1, len(dates)):
            if dates[i] - dates[i-1] == timedelta(days=1):
                current_seq += 1
            else:
                longest = max(longest, current_seq)
                current_seq = 1
        longest = max(longest, current_seq)

        # Current streak calculation
        today = timezone.now().date()
        last_log_date = dates[-1]
        
        # If last log was before yesterday, current streak is 0
        if last_log_date < today - timedelta(days=1):
            current = 0
        else:
            current = 1
            # Count backwards from the end
            for i in range(len(dates) - 2, -1, -1):
                if dates[i+1] - dates[i] == timedelta(days=1):
                    current += 1
                else:
                    break
        
        return {'current': current, 'longest': longest}

class DailyEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_entries')
    date = models.DateField()
    productivity_score = models.IntegerField(choices=[(i, str(i)) for i in range(1, 11)], default=5)
    mood_score = models.IntegerField(choices=[(i, str(i)) for i in range(1, 11)], default=5)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"Entry {self.date} - {self.user.username}"

class HabitLog(models.Model):
    entry = models.ForeignKey(DailyEntry, on_delete=models.CASCADE, related_name='habit_logs')
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='logs')
    value = models.FloatField(help_text="Actual value achieved")
    
    class Meta:
        unique_together = ('entry', 'habit')

    def __str__(self):
        return f"{self.habit.name}: {self.value} {self.habit.unit}"
