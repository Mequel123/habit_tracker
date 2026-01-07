from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('habits/', views.HabitListView.as_view(), name='habit_list'),
    path('habits/add/', views.HabitCreateView.as_view(), name='habit_add'),
    path('habits/<int:pk>/', views.HabitDetailView.as_view(), name='habit_detail'),
    path('habits/<int:pk>/edit/', views.HabitUpdateView.as_view(), name='habit_edit'),
    path('journal/', views.DailyLogListView.as_view(), name='daily_log_list'),
    path('journal/add/', views.DailyLogCreateView.as_view(), name='daily_log_add'),
    path('journal/<int:pk>/edit/', views.DailyLogUpdateView.as_view(), name='daily_log_edit'),
    path('log/add/', views.HabitLogCreateView.as_view(), name='habit_log_add'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
]
