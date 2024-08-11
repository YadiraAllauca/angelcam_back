from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from django.conf import settings

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

@csrf_exempt
def get_camera_stream(request, camera_id):
    if request.method == 'GET':
        token = request.headers.get('Authorization', '').split(' ')[-1]

        if not token:
            return JsonResponse({'error': 'Authorization token is required'}, status=400)

        url = f"https://api.angelcam.com/v1/shared-cameras/{camera_id}/"
        headers = {'Authorization': f'PersonalAccessToken {token}'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            stream_details = [
                {'url': stream['url'], 'format': stream['format']}
                for stream in data.get('streams', [])
                if 'url' in stream and 'format' in stream
            ]

            if stream_details:
                return JsonResponse({'stream_details': stream_details})
            else:
                return JsonResponse({'error': 'No streams available'}, status=404)
        else:
            return JsonResponse({'error': 'Could not fetch camera data', 'details': response.json()}, status=response.status_code)

    return JsonResponse({'error': 'Only GET requests are allowed'}, status=405)

@csrf_exempt
def get_recording_info(request, camera_id):
    if request.method == 'GET':
        token = request.headers.get('Authorization', '').split(' ')[-1]
        if not token:
            return JsonResponse({'error': 'Authorization token is required'}, status=400)

        url = f"https://api.angelcam.com/v1/shared-cameras/{camera_id}/recording/"
        headers = {'Authorization': f'PersonalAccessToken {token}'}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return JsonResponse({'recording_info': data})
        else:
            return JsonResponse({'error': 'Could not fetch recording information', 'details': response.json()}, status=response.status_code)

    return JsonResponse({'error': 'Only GET requests are allowed'}, status=405)

@csrf_exempt
def get_recording_stream(request, camera_id):
    start = request.GET.get('start')
    end = request.GET.get('end')

    if not start:
        return JsonResponse({'error': 'Start time is required'}, status=400)
    
    token = request.headers.get('Authorization', '').split(' ')[-1]
    if not token:
        return JsonResponse({'error': 'Authorization token is required'}, status=400)

    url = f"https://api.angelcam.com/v1/shared-cameras/{camera_id}/recording/stream/"
    headers = {'Authorization': f'PersonalAccessToken {token}'}
    params = {'start': start, 'end': end}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        return JsonResponse({'stream': data})
    else:
        return JsonResponse({'error': 'Could not fetch recording stream', 'details': response.json()}, status=response.status_code)

@csrf_exempt
def get_recording_timeline(request, camera_id):
    start = request.GET.get('start')
    end = request.GET.get('end')

    if not start or not end:
        return JsonResponse({'error': 'Start and end times are required'}, status=400)
    
    token = request.headers.get('Authorization', '').split(' ')[-1]
    if not token:
        return JsonResponse({'error': 'Authorization token is required'}, status=400)

    url = f"https://api.angelcam.com/v1/shared-cameras/{camera_id}/recording/timeline/"
    headers = {'Authorization': f'PersonalAccessToken {token}'}
    params = {'start': start, 'end': end}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        return JsonResponse({'timeline': data})
    else:
        return JsonResponse({'error': 'Could not fetch recording timeline', 'details': response.json()}, status=response.status_code)
