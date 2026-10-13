from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db.models import Count
from .utility.GetImageStressDetection import ImageExpressionDetect
from .models import *

import os
import random
import urllib.parse
import pygame

# Create your views here.
def Userregister(request):
    if request.method == 'POST':
        name = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('contact')
        form = userregistermodel(name=name, email=email, password=password, phoneno=phone,  status='waiting')
        form.save()
        messages.success(request, 'Registration Successful')
        return render(request, 'index.html')
    else:
        messages.error(request, 'Registration Un-Successful')
        return render(request, 'index.html')      
    
def userhome(request):
    email = request.session.get('email')
    if not email:
        return redirect('authpage')

    try:
        user = userregistermodel.objects.get(email=email)
    except userregistermodel.DoesNotExist:
        return redirect('authpage')

    data = userimagepredictionmodel.objects.filter(email=email).order_by('-created_at')
    emotion_counts = data.values('emotion').annotate(count=Count('emotion'))
    stats = {item['emotion']: item['count'] for item in emotion_counts}

    for record in data:
        decoded_name = urllib.parse.unquote(record.file.name)
        decoded_path = os.path.join(settings.MEDIA_ROOT, decoded_name)
        if decoded_name != record.file.name and os.path.exists(decoded_path):
            record.file.name = decoded_name
            record.save(update_fields=['file'])

    return render(request, 'user/userhome.html', {
        'data': data,
        'user_name': user.name,
        'emotion_stats': stats,
        'total_predictions': data.count(),
    })

def userlogout(request):
    request.session.flush()
    return redirect('authpage')

def UploadImageAction(request):
    image_file = request.FILES['file']
    if not image_file.name.endswith('.jpg'):
        messages.error(request, 'THIS IS NOT A JPG FILE')

    fs = FileSystemStorage()
    decoded_name = urllib.parse.unquote(image_file.name)
    image_file.name = decoded_name
    filename = fs.save(image_file.name, image_file)

    # Normalize any URL-encoded filename to the actual filesystem name.
    if '%' in filename:
        decoded_filename = urllib.parse.unquote(filename)
        encoded_path = fs.path(filename)
        decoded_path = fs.path(decoded_filename)

        if os.path.exists(decoded_path):
            if os.path.exists(encoded_path):
                fs.delete(filename)
            filename = decoded_filename
        elif os.path.exists(encoded_path):
            with fs.open(filename, 'rb') as f:
                content = f.read()
            fs.delete(filename)
            filename = fs.save(decoded_filename, content)

    filename = urllib.parse.unquote(filename)

    obj = ImageExpressionDetect()
    emotion = obj.getExpression(filename)
    print(emotion)
    music_status = play_music(emotion)
    email = request.session['email']
    stored_file = filename
    if stored_file.startswith(settings.MEDIA_URL):
        stored_file = stored_file[len(settings.MEDIA_URL):]
    userimagepredictionmodel.objects.create(
        email=email,
        emotion=emotion,
        filename=filename,
        file=stored_file,
    )
    data = userimagepredictionmodel.objects.filter(email=email)
    return render(request, 'user/userhome.html', {'data':data, 'music_playing': music_status})

def UserLiveCameDetect(request):
    obj = ImageExpressionDetect()
    most_repeated_emotion = obj.getLiveDetect()
    music_status = play_music(most_repeated_emotion)
    email = request.session['email']
    data = userimagepredictionmodel.objects.filter(email=email)
    return render(request, 'user/userhome.html', {'data':data})


def play_music(emotion):
    # Normalize emotion text for matching.
    if isinstance(emotion, str):
        emotion = emotion.strip().capitalize()

    # Map emotions to music directories with correct folder names.
    emotion_folders = {
        'Angry': 'Angry',
        'Disgusted': 'Disgusted',
        'Fear': 'Fear',
        'Happy': 'Happy',
        'Neutral': 'Neutral',
        'Surprised': 'Suprised',
        'Sad': 'Sad',
    }

    # Each emotion gets its own playlist choices.
    emotion_playlists = {
        'Angry': ['Gaaju Bomma.mp3', 'Odiyamma.mp3'],
        'Disgusted': ['Odiyamma.mp3', 'Samayama.mp3'],
        'Fear': ['Samayama.mp3', 'Gaaju Bomma.mp3'],
        'Happy': ['Ammaadi.mp3', 'Gaaju Bomma.mp3'],
        'Neutral': ['Ammaadi.mp3', 'Samayama.mp3'],
        'Surprised': ['Gaaju Bomma.mp3', 'Ammaadi.mp3'],
        'Sad': ['Odiyamma.mp3', 'Samayama.mp3'],
    }

    if emotion not in emotion_folders or emotion not in emotion_playlists:
        print(f"Invalid emotion: {emotion}. Please choose a valid emotion.")
        return False

    music_path = os.path.join(settings.BASE_DIR, 'assets', 'music', emotion_folders[emotion])
    playlist = emotion_playlists[emotion]
    available_tracks = [track for track in playlist if os.path.exists(os.path.join(music_path, track))]

    if not available_tracks:
        print(f"No available music tracks found for emotion {emotion} in {music_path}.")
        return False

    music_file = random.choice(available_tracks)
    music_full_path = os.path.join(music_path, music_file)

    try:
        pygame.mixer.init()
        pygame.mixer.music.load(music_full_path)
        pygame.mixer.music.play()

        print(f"Playing {music_file} for emotion {emotion}.")
        return True

    except FileNotFoundError:
        print(f"The directory {music_path} does not exist.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def stop_music(request):
    if request.method == 'POST':
        pygame.mixer.music.stop()
        email = request.session['email']
        data = userimagepredictionmodel.objects.filter(email=email)
        return render(request, 'user/userhome.html', {'data':data})
    else:
        email = request.session['email']
        data = userimagepredictionmodel.objects.filter(email=email)
        return render(request, 'user/userhome.html', {'data':data})