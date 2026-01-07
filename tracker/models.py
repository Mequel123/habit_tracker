from django.db import models
from django.contrib.auth.models import User

class Habit(models.Model):
    CATEGORY_CHOICES = [
        ('health', 'Health'),
        ('productivity', 'Productivity'),
        ('mindfulness', 'Mindfulness'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='health')
    target_value = models.FloatField(help_text="Target goal")
    # unit = models.CharField(max_length=50) # TODO: Add unit later
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

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
