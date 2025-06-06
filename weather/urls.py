# weather/urls.py
from django.urls import path
from .views import index, forecast, summary
from . import views

urlpatterns = [
    path('', index, name='weather.index'),
    path('forecast/', forecast, name='weather.forecast'),
    path('summary/',  summary,  name='weather.summary'),
    path('alerts/', views.alerts_view, name='weather.alerts'),
    path('alerts/add/', views.add_alert, name='weather.add_alert'),
    path('alerts/delete/<int:alert_id>/', views.delete_alert, name='weather.delete_alert'),
    path('alerts/dismiss/<int:alert_id>/', views.dismiss_alert, name='weather.dismiss_alert'),
    path("alerts/save/", views.save_alert, name="weather.save_alert"),
]
