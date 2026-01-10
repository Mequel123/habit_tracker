from django.shortcuts import render, redirect
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
        # The form has 'habit' and 'value'. It needs 'entry'.
        # Strategy: Get or create DailyEntry for today for this user.
        
        today = pd.Timestamp.now().date()
        entry, created = DailyEntry.objects.get_or_create(
            user=self.request.user,
            date=today,
            defaults={'productivity_score': 5, 'mood_score': 5}
        )
        
        # Check if log already exists for this habit today to prevent IntegrityError
        habit = form.cleaned_data['habit']
        existing_log = HabitLog.objects.filter(entry=entry, habit=habit).first()
        
        if existing_log:
            # Update existing log
            existing_log.value = form.cleaned_data['value']
            existing_log.save()
            return redirect(self.success_url)
        
        form.instance.entry = entry
        return super().form_valid(form)


class AnalyticsView(TemplateView):
    template_name = 'tracker/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Prepare data for analytics
        # We want to see correlation between Habit Values and Productivity
        
        habits = Habit.objects.all()
        graphs = []

        for habit in habits:
            # Get logs for this habit
            logs = HabitLog.objects.filter(habit=habit).select_related('entry')
            if not logs.exists():
                continue
            
            data = []
            for log in logs:
                data.append({
                    'date': log.entry.date,
                    'value': log.value,
                    'productivity': log.entry.productivity_score,
                    'mood': log.entry.mood_score
                })
            
            df = pd.DataFrame(data)
            if df.empty or len(df) < 2:
                continue

            # Calculate Correlation
            corr_prod = df['value'].corr(df['productivity'])
            
            # Generate Plot
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.scatter(df['value'], df['productivity'], alpha=0.7)
            
            # Add trend line
            if len(df) > 1:
                z = np.polyfit(df['value'], df['productivity'], 1)
                p = np.poly1d(z)
                ax.plot(df['value'], p(df['value']), "r--", alpha=0.8)

            ax.set_title(f"{habit.name} vs Productivity (Corr: {corr_prod:.2f})")
            ax.set_xlabel(f"{habit.name} ({habit.unit})")
            ax.set_ylabel("Productivity Score (1-10)")
            ax.grid(True, linestyle='--', alpha=0.5)

            # Save to buffer
            buf = io.BytesIO()
            fig.tight_layout()
            fig.savefig(buf, format='png')
            buf.seek(0)
            string = base64.b64encode(buf.read())
            uri = urllib.parse.quote(string)
            graphs.append({
                'habit': habit,
                'image': uri,
                'correlation': corr_prod
            })
            plt.close(fig)

        context['graphs'] = graphs
        return context

