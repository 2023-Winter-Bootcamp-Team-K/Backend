from django.shortcuts import render

# apps/views.py
from django.http import JsonResponse

def json_response_view(request):
    data = {'message': 'Hello, this is a simple JSON response!'}
    return JsonResponse(data)
