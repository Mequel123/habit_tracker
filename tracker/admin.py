from django.contrib import admin
from .models import Habit, DailyEntry, HabitLog

@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'category', 'target_value', 'unit')
    search_fields = ('name', 'user__username')
    list_filter = ('category',)

class HabitLogInline(admin.TabularInline):
    model = HabitLog
    extra = 1

@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'productivity_score', 'mood_score')
    list_filter = ('user', 'date')
    inlines = [HabitLogInline]

@admin.register(HabitLog)
class HabitLogAdmin(admin.ModelAdmin):
    list_display = ('habit', 'entry', 'value')

