from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg
from .models import Habit, DailyEntry, HabitLog
from .forms import HabitForm, DailyEntryForm, HabitLogForm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import urllib, base64

plt.switch_backend('Agg')

# Mixin to ensure user owns data
class UserOwnsObjectMixin:
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

class HomeView(TemplateView):
    template_name = 'tracker/home.html'

class HabitListView(ListView):
    model = Habit
    template_name = 'tracker/habit_list.html'
    context_object_name = 'habits'

    def get_queryset(self):
         # If user is auth, show their habits. Else empty or public.
         # For now, let's assume auth for demo or show all for 'guest' mode if intended.
         # TZ says: Guest sees landing. User sees own.
         if self.request.user.is_authenticated:
             return Habit.objects.filter(user=self.request.user)
         return Habit.objects.none()

class HabitDetailView(DetailView):
    model = Habit
    template_name = 'tracker/habit_detail.html'
    context_object_name = 'habit'

class HabitCreateView(LoginRequiredMixin, CreateView):
    model = Habit
    form_class = HabitForm
    template_name = 'tracker/form.html'
    success_url = reverse_lazy('habit_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class HabitUpdateView(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
    model = Habit
    form_class = HabitForm
    template_name = 'tracker/form.html'
    success_url = reverse_lazy('habit_list')

class DailyLogListView(ListView):
    model = DailyEntry
    template_name = 'tracker/daily_log_list.html'
    context_object_name = 'entries'
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return DailyEntry.objects.filter(user=self.request.user)
        return DailyEntry.objects.none()

class DailyLogCreateView(LoginRequiredMixin, CreateView):
    model = DailyEntry
    form_class = DailyEntryForm
    template_name = 'tracker/form.html'
    success_url = reverse_lazy('daily_log_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class DailyLogUpdateView(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
    model = DailyEntry
    form_class = DailyEntryForm
    template_name = 'tracker/form.html'
    success_url = reverse_lazy('daily_log_list')

class HabitLogCreateView(LoginRequiredMixin, CreateView):
    model = HabitLog
    form_class = HabitLogForm
    template_name = 'tracker/form.html'
    success_url = reverse_lazy('daily_log_list')

    def get_initial(self):
        initial = super().get_initial()
        # Pre-select habit if passed in URL or query
        if 'habit_id' in self.request.GET:
             initial['habit'] = self.request.GET.get('habit_id')
        return initial

    def form_valid(self, form):
        # Ensure the entry belongs to user or create one for today if not selected?
        # The form has 'entry'? No, HabitLogForm has 'habit' and 'value'. It needs 'entry'.
        # My HabitLogForm definition in forms.py included 'habit' and 'value'. It is missing 'entry'.
        # We need to assign 'entry'.
        # Strategy: Get or create DailyEntry for today for this user.
        
        today = pd.Timestamp.now().date()
        entry, created = DailyEntry.objects.get_or_create(
            user=self.request.user,
            date=today,
            defaults={'productivity_score': 5, 'mood_score': 5} # Default values if creating implicitly
        )
        form.instance.entry = entry
        return super().form_valid(form)


class AnalyticsView(TemplateView):
    template_name = 'tracker/analytics.html'

    def get_context_data(self, **kwargs):
        # TODO: Implement analytics
        return super().get_context_data(**kwargs)

