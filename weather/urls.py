# weather/urls.py
from django.urls import path
from .views import index, forecast, summary
from . import views

urlpatterns = [
    path('', index, name='weather.index'),
    path('forecast/', forecast, name='weather.forecast'),
    path('summary/',  summary,  name='weather.summary'),
    path('alerts/', views.alerts_view, name='weather.alerts'),
    path('alerts/delete/<int:alert_id>/', views.delete_alert, name='weather.delete_alert'),
]
