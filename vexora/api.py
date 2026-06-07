import json
import jwt

from datetime import datetime, timedelta

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate

from .models import (
    CustomUser,
)
from .models import *


# =========================================
# DATOS DEL USUARIO
# =========================================

def _user_data(user):

    return {
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': user.phone,
    }


# =========================================
# CREAR TOKENS JWT
# =========================================

def _create_tokens_for_user(user):

    payload = {
        'user_id': user.id,
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }

    access = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm='HS256'
    )

    refresh_payload = {
        'user_id': user.id,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=30)
    }

    refresh = jwt.encode(
        refresh_payload,
        settings.SECRET_KEY,
        algorithm='HS256'
    )

    return {
        'access': access,
        'refresh': refresh
    }


# =========================================
# REGISTRO DE USUARIO
# =========================================

@csrf_exempt
def api_register(request):

    if request.method != 'POST':
        return JsonResponse({
            'error': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))

    except Exception:
        return JsonResponse({
            'error': 'JSON inválido'
        }, status=400)

    email = data.get('email')
    username = data.get('username')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    password = data.get('password')
    phone = data.get('phone')

    if not all([
        email,
        username,
        first_name,
        last_name,
        password
    ]):
        return JsonResponse({
            'error': 'Faltan campos requeridos'
        }, status=400)

    if CustomUser.objects.filter(email=email).exists():

        return JsonResponse({
            'error': 'Ya existe un usuario con ese email'
        }, status=400)

    user = CustomUser.objects.create_user(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        password=password
    )

    tokens = _create_tokens_for_user(user)

    return JsonResponse({
        'success': True,
        'message': 'Usuario registrado correctamente',
        'user': _user_data(user),
        'tokens': tokens
    }, status=201)


# =========================================
# LOGIN
# =========================================

@csrf_exempt
def api_login(request):

    if request.method != 'POST':
        return JsonResponse({
            'error': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))

    except Exception:
        return JsonResponse({
            'error': 'JSON inválido'
        }, status=400)

    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):

        return JsonResponse({
            'error': 'Faltan campos requeridos'
        }, status=400)

    user = authenticate(
        request,
        email=email,
        password=password
    )

    if user is None:

        return JsonResponse({
            'error': 'Credenciales inválidas'
        }, status=400)

    if not user.is_active:

        return JsonResponse({
            'error': 'Usuario inactivo'
        }, status=403)

    tokens = _create_tokens_for_user(user)

    return JsonResponse({
        'success': True,
        'message': 'Login exitoso',
        'user': _user_data(user),
        'tokens': tokens
    })

# ========================================
# Productos y Proveedores
# ========================================


# =========================================
# LISTAR PROVEEDORES
# =========================================

@csrf_exempt
def api_proveedores(request):

    if request.method == 'GET':

        proveedores = proveedores.objects.all()

        data = []

        for proveedor in proveedores:

            data.append({
                'id': proveedor.id,
                'nombre': proveedor.nombre,
                'direccion': proveedor.direccion,
                'telefono': proveedor.telefono,
                'email': proveedor.email,
                'fecha_registro': proveedor.fecha_registro
            })

        return JsonResponse(data, safe=False)

    return JsonResponse({
        'error': 'Método no permitido'
    }, status=405)


# =========================================
# LISTAR PRODUCTOS
# =========================================

@csrf_exempt
def api_productos(request):

    if request.method != 'POST':
        return JsonResponse({
            'error': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        productos = Product.objects.select_related(
            'supplier'
        ).all()

    except Exception:
        return JsonResponse({
            'error': 'JSON inválido'
        }, status=400)

    name = data.get('name')
    purchase_price = data.get('purchase_price')
    price = data.get('price')
    supplier = data.get('supplier')

    if not all([
        name,
        purchase_price,
        price,
        supplier
    ]):
        return JsonResponse({
            'error': 'Faltan campos requeridos'
        }, status=400)
    
    
        data.append({
            'id': producto.id,
                'nombre_producto': producto.nombre_producto,
                'descripcion': producto.descripcion,
                'fecha_compra': producto.fecha_compra,
                'precio': str(producto.precio),
                'stock': producto.stock,
                'proveedor': producto.supplier.nombre,
                'fecha_registro': producto.fecha_registro
            })


