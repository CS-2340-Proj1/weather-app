# weather/urls.py
from django.urls import path
from .views import index, forecast, summary

urlpatterns = [
    path('', index, name='weather.index'),
    path('forecast/', forecast, name='weather.forecast'),
    path('summary/',  summary,  name='weather.summary'),
]
