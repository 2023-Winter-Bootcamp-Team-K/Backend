from django.urls import path
from .views import json_response_view

urlpatterns = [
    path('', json_response_view, name='json_response'),
]

