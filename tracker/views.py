from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg
from django.core.cache import cache
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

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'tracker/home.html'

class HabitListView(LoginRequiredMixin, ListView):
    model = Habit
    template_name = 'tracker/habit_list.html'
    context_object_name = 'habits'

    def get_queryset(self):
         return Habit.objects.filter(user=self.request.user)

class HabitDetailView(LoginRequiredMixin, DetailView):
    model = Habit
    template_name = 'tracker/habit_detail.html'
    context_object_name = 'habit'

class HabitCreateView(LoginRequiredMixin, CreateView):
    model = Habit
    form_class = HabitForm
    template_name = 'tracker/form.html'
    success_url = reverse_lazy('habit_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Combine default categories with user's existing ones
        user_categories = Habit.objects.filter(user=self.request.user).values_list('category', flat=True).distinct()
        defaults = set(Habit.DEFAULT_CATEGORIES)
        context['categories'] = sorted(list(defaults.union(set(user_categories))))
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class HabitUpdateView(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
    model = Habit
    form_class = HabitForm
    template_name = 'tracker/form.html'
    success_url = reverse_lazy('habit_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_categories = Habit.objects.filter(user=self.request.user).values_list('category', flat=True).distinct()
        defaults = set(Habit.DEFAULT_CATEGORIES)
        context['categories'] = sorted(list(defaults.union(set(user_categories))))
        return context

class DailyLogListView(LoginRequiredMixin, ListView):
    model = DailyEntry
    template_name = 'tracker/daily_log_list.html'
    context_object_name = 'entries'
    paginate_by = 10
    
    def get_queryset(self):
        return DailyEntry.objects.filter(user=self.request.user).order_by('-date')

    def get(self, request, *args, **kwargs):
        # Cache first page for performance
        page = request.GET.get('page', 1)
        if str(page) == '1':
            cache_key = f"daily_logs_{request.user.id}_p1"
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response
            
            response = super().get(request, *args, **kwargs)
            if hasattr(response, 'render'):
                response.render()
            
            cache.set(cache_key, response, 60 * 5) # 5 min cache
            return response
            
        return super().get(request, *args, **kwargs)

class DailyLogCreateView(LoginRequiredMixin, CreateView):
    model = DailyEntry
    form_class = DailyEntryForm
    template_name = 'tracker/form.html'
    success_url = reverse_lazy('daily_log_list')

    def form_valid(self, form):
        # Invalidate list cache
        cache.delete(f"daily_logs_{self.request.user.id}_p1")
        form.instance.user = self.request.user
        return super().form_valid(form)

class DailyLogUpdateView(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
    model = DailyEntry
    form_class = DailyEntryForm
    template_name = 'tracker/form.html'
    success_url = reverse_lazy('daily_log_list')
    
    def form_valid(self, form):
        cache.delete(f"daily_logs_{self.request.user.id}_p1")
        return super().form_valid(form)

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
        # Invalidate list cache as this affects the log count display
        cache.delete(f"daily_logs_{self.request.user.id}_p1")
        
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


class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'tracker/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get control parameters from request
        window_size = int(self.request.GET.get('window', 1))
        outlier_std = float(self.request.GET.get('std', 3.0))
        target_metric = self.request.GET.get('metric', 'productivity') # 'productivity' or 'mood'
        normalize = self.request.GET.get('normalize') == 'on'

        context['controls'] = {
            'window': window_size,
            'std': outlier_std,
            'metric': target_metric,
            'normalize': normalize
        }
        
        habits = Habit.objects.all()
        graphs = []

        for habit in habits:
            # Get logs for this habit sorted by date for rolling window
            logs = HabitLog.objects.filter(habit=habit).select_related('entry').order_by('entry__date')
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

            # 1. Rolling Window (Smoothing)
            if window_size > 1:
                df['value'] = df['value'].rolling(window=window_size, min_periods=1, center=True).mean()
                df[target_metric] = df[target_metric].rolling(window=window_size, min_periods=1, center=True).mean()

            # 2. Outlier Removal (Z-Score > threshold)
            # Remove rows where habit value is an outlier
            if len(df) > 5: # Only if enough data
                mean = df['value'].mean()
                std = df['value'].std()
                if std > 0:
                     df = df[np.abs(df['value'] - mean) <= (outlier_std * std)]
            
            if df.empty or len(df) < 2:
                continue

            # 3. Normalization (Min-Max to 0-10 scale for visual comparison)
            if normalize:
                min_val = df['value'].min()
                max_val = df['value'].max()
                if max_val > min_val:
                    df['value_scaled'] = 1 + (df['value'] - min_val) * 9 / (max_val - min_val)
                    plot_x = 'value_scaled'
                    xlabel = f"{habit.name} (Scaled 1-10)"
                else:
                    plot_x = 'value'
                    xlabel = f"{habit.name} ({habit.unit})"
            else:
                plot_x = 'value'
                xlabel = f"{habit.name} ({habit.unit})"

            # Calculate Correlation
            corr_val = df[plot_x].corr(df[target_metric])
            
            # --- Graph 1: Scatter (Correlation) ---
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Scatter Plot
            ax1.scatter(df[plot_x], df[target_metric], alpha=0.7, c='blue')
            if len(df) > 1:
                z = np.polyfit(df[plot_x], df[target_metric], 1)
                p = np.poly1d(z)
                ax1.plot(df[plot_x], p(df[plot_x]), "r--", alpha=0.8)

            ax1.set_title(f"Correlation: {corr_val:.2f}")
            ax1.set_xlabel(xlabel)
            ax1.set_ylabel(f"{target_metric.title()} Score")
            ax1.grid(True, linestyle='--', alpha=0.5)

            # --- Graph 2: Time Series Overlay ---
            # Dual axis plot
            color = 'tab:blue'
            ax2.set_xlabel('Date')
            ax2.set_ylabel(xlabel, color=color)
            ax2.plot(df['date'], df[plot_x], color=color, label='Habit', marker='o', markersize=4)
            ax2.tick_params(axis='y', labelcolor=color)
            ax2.tick_params(axis='x', rotation=45)

            ax3 = ax2.twinx()  # instantiate a second axes that shares the same x-axis
            color = 'tab:red'
            ax3.set_ylabel(f'{target_metric.title()} Score', color=color)
            ax3.plot(df['date'], df[target_metric], color=color, label='Metric', linestyle='--', marker='x', markersize=4)
            ax3.tick_params(axis='y', labelcolor=color)

            ax2.set_title(f"Time Series Trend (Window: {window_size}d)")
            fig.tight_layout()

            # Save to buffer
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            string = base64.b64encode(buf.read())
            uri = urllib.parse.quote(string)
            graphs.append({
                'habit': habit,
                'image': uri,
                'correlation': corr_val,
                'n_samples': len(df)
            })
            plt.close(fig)

        context['graphs'] = graphs
        return context

