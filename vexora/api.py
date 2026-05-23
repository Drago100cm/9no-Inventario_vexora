import json
import jwt
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.conf import settings

from .models import CustomUser


def _user_data(user):
    return {
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }


def _create_tokens_for_user(user):
    payload = {
        'user_id': user.id,
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    access = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    refresh_payload = {
        'user_id': user.id,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    refresh = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')

    return {'access': access, 'refresh': refresh}


@csrf_exempt
def api_register(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido, use POST'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    email = data.get('email')
    username = data.get('username')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    password = data.get('password')
    phone = data.get('phone')

    if not all([email, username, first_name, last_name, password]):
        return JsonResponse({'error': 'Faltan campos requeridos'}, status=400)

    if CustomUser.objects.filter(email=email).exists():
        return JsonResponse({'error': 'Ya existe un usuario con ese email'}, status=400)

    user = CustomUser.objects.create_user(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        password=password,
    )

    tokens = _create_tokens_for_user(user)

    # Opcional: iniciar sesión en sesión del sitio
    # login(request, user)

    return JsonResponse({'success': True, 'user': _user_data(user), 'tokens': tokens}, status=201)


@csrf_exempt
def api_login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido, use POST'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return JsonResponse({'error': 'Faltan campos requeridos'}, status=400)

    user = authenticate(request, email=email, password=password)

    if user is None:
        return JsonResponse({'error': 'Credenciales inválidas'}, status=400)

    if not user.is_active:
        return JsonResponse({'error': 'Usuario inactivo'}, status=403)

    tokens = _create_tokens_for_user(user)

    # No iniciamos sesión por defecto; la autenticación será por JWT
    return JsonResponse({'success': True, 'user': _user_data(user), 'tokens': tokens})
