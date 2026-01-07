from django import forms
from .models import Habit, DailyEntry, HabitLog

class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ['name', 'category', 'target_value', 'unit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded mb-4'}),
            'category': forms.Select(attrs={'class': 'w-full p-2 border rounded mb-4'}),
            'target_value': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded mb-4'}),
            'unit': forms.TextInput(attrs={'class': 'w-full p-2 border rounded mb-4'}),
        }

class DailyEntryForm(forms.ModelForm):
    class Meta:
        model = DailyEntry
        fields = ['date', 'productivity_score', 'mood_score', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-2 border rounded mb-4'}),
            'productivity_score': forms.Select(attrs={'class': 'w-full p-2 border rounded mb-4'}),
            'mood_score': forms.Select(attrs={'class': 'w-full p-2 border rounded mb-4'}),
            'notes': forms.Textarea(attrs={'class': 'w-full p-2 border rounded mb-4', 'rows': 3}),
        }

class HabitLogForm(forms.ModelForm):
    class Meta:
        model = HabitLog
        fields = ['habit', 'value']
        widgets = {
            'habit': forms.Select(attrs={'class': 'w-full p-2 border rounded mb-4'}),
            'value': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded mb-4'}),
        }
