from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests

def home(request):
    return JsonResponse({'message': 'Welcome to API!'})

@csrf_exempt
def login(request):
    if request.method == 'POST':
        token = request.POST.get('token')

        if not token:
            return JsonResponse({'error': 'No token provided'}, status=400)
        
        headers = {'Authorization': f'PersonalAccessToken {token}'}
        response = requests.get('https://api.angelcam.com/v1/me', headers=headers)
        if response.status_code != 200:
            print('Error response:', response.json())
            return JsonResponse({'error': 'Invalid token', 'details': response.json()}, status=401)

        return JsonResponse({'message': 'Login successful', 'data': response.json()})
    
    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def get_cameras(request):
    if request.method == 'GET':
        token = request.headers.get('Authorization', '').split(' ')[-1]
        if not token:
            return JsonResponse({'error': 'No token provided'}, status=400)

        headers = {'Authorization': f'PersonalAccessToken {token}'}
        response = requests.get('https://api.angelcam.com/v1/shared-cameras', headers=headers)

        if response.status_code != 200:
            return JsonResponse({'error': 'Failed to fetch cameras', 'details': response.json()}, status=401)

        return JsonResponse({'cameras': response.json()})

    return JsonResponse({'error': 'Only GET requests are allowed'}, status=405)