from django.shortcuts import render, redirect
from django.views import View
import json
from django.http import JsonResponse
from django.contrib.auth.models import User


# Create your views here.

class UsernameValidationView(View):
    def post(self, request):
        data=json.loads(request.body)
        username=data['username']
        if not str(username).isalnum():
            return JsonResponse({'username_error': 'username should only containt alphanumeric characters'})
        return JsonResponse({'username_valid': ''})
class RegistrationView(View):
    def get(self, request):
        return render(request, 'authentication/register.html')