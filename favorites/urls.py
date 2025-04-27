from django.urls import path
from .views import index, add, delete

urlpatterns = [
    path('', index, name='favorites.index'),
    path('add/', add, name='favorites.add'),
    path('delete/<int:id>/', delete, name='favorites.delete'),
]