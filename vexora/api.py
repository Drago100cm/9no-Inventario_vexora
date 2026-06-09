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

        proveedores = Supplier.objects.all()

        data = []

        for proveedor in proveedores:

            data.append({
                'id': proveedor.id,
                'name': proveedor.name,
                'address': proveedor.address,
                'company': proveedor.company.id if proveedor.company else None,
                'company_name': proveedor.company.name if proveedor.company else None
                
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

    if request.method != 'GET':
        return JsonResponse({
            'error': 'Método no permitido'
        }, status=405)

    # Obtener todos los productos con su proveedor relacionado
    productos = Product.objects.select_related('supplier').all()

    data = []

    for producto in productos:
        data.append({
            'id': producto.id,
            'name': producto.name,  
            'purchase_date': producto.purchase_date,  
            'price': str(producto.price),  
            'supplier': producto.supplier.name,
            'supplier_id': producto.supplier.id,
            'company': producto.company.id if producto.company else None,
            'company_name': producto.company.name if producto.company else None
        })

    return JsonResponse(data, safe=False)

# =========================================
# CREAR PRODUCTO
# =========================================

@csrf_exempt
def api_crear_producto(request):

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

    name = data.get('name')
    purchase_date = data.get('purchase_date')
    price = data.get('price')
    supplier_id = data.get('supplier')
    company_id = data.get('company')

    if not all([name, purchase_date, price, supplier_id]):
        return JsonResponse({
            'error': 'Faltan campos requeridos (name, purchase_date, price, supplier)'
        }, status=400)

    # Validar proveedor
    try:
        supplier = Supplier.objects.get(id=supplier_id)
    except Supplier.DoesNotExist:
        return JsonResponse({
            'error': 'Proveedor no encontrado'
        }, status=404)

    # Validar company si se envía
    company = None
    if company_id:
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return JsonResponse({
                'error': 'Empresa no encontrada'
            }, status=404)

    producto = Product.objects.create(
        name=name,
        purchase_date=purchase_date,
        price=price,
        supplier=supplier,
        company=company
    )

    return JsonResponse({
        'success': True,
        'message': 'Producto creado correctamente',
        'producto': {
            'id': producto.id,
            'name': producto.name,
            'purchase_date': producto.purchase_date,
            'price': str(producto.price),
            'supplier': producto.supplier.name,
            'supplier_id': producto.supplier.id,
            'company': producto.company.id if producto.company else None,
            'company_name': producto.company.name if producto.company else None
        }
    }, status=201)


# =========================================
# EDITAR PRODUCTO
# =========================================

@csrf_exempt
def api_product_update(request, producto_id):

    if request.method != 'PUT':
        return JsonResponse({
            'error': 'Método no permitido. Use PUT'
        }, status=405)

    try:
        producto = Product.objects.get(id=producto_id)
    except Product.DoesNotExist:
        return JsonResponse({
            'error': 'Producto no encontrado'
        }, status=404)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({
            'error': 'JSON inválido'
        }, status=400)

    # Actualizar campos
    if 'name' in data:
        producto.name = data['name']
    if 'purchase_date' in data:
        producto.purchase_date = data['purchase_date']
    if 'price' in data:
        producto.price = data['price']
    if 'supplier' in data:
        try:
            producto.supplier = Supplier.objects.get(id=data['supplier'])
        except Supplier.DoesNotExist:
            return JsonResponse({
                'error': 'Proveedor no encontrado'
            }, status=404)
    if 'company' in data:
        company_id = data['company']
        if company_id:
            try:
                producto.company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                return JsonResponse({
                    'error': 'Empresa no encontrada'
                }, status=404)
        else:
            producto.company = None

    producto.save()

    return JsonResponse({
        'success': True,
        'message': 'Producto actualizado correctamente',
        'producto': {
            'id': producto.id,
            'name': producto.name,
            'purchase_date': producto.purchase_date,
            'price': str(producto.price),
            'supplier': producto.supplier.name,
            'supplier_id': producto.supplier.id,
            'company': producto.company.id if producto.company else None,
            'company_name': producto.company.name if producto.company else None
        }
    })



# =========================================
# CREAR PROVEEDOR
# =========================================

@csrf_exempt
def api_crear_proveedor(request):

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

    name = data.get('name')
    address = data.get('address')
    company_id = data.get('company')

    if not all([name, address]):
        return JsonResponse({
            'error': 'Faltan campos requeridos (name, address)'
        }, status=400)

    company = None

    if company_id:
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return JsonResponse({
                'error': 'Empresa no encontrada'
            }, status=404)

    proveedor = Supplier.objects.create(
        name=name,
        address=address,
        company=company
    )

    return JsonResponse({
        'success': True,
        'message': 'Proveedor creado correctamente',
        'proveedor': {
            'id': proveedor.id,
            'name': proveedor.name,
            'address': proveedor.address,
            'company': proveedor.company.id if proveedor.company else None,
            'company_name': proveedor.company.name if proveedor.company else None
        }
    }, status=201)

# =========================================
# EDITAR PROVEEDOR
# =========================================

@csrf_exempt
def api_supplier_update(request, supplier_id):

    if request.method != 'PUT':
        return JsonResponse({
            'error': 'Método no permitido. Use PUT'
        }, status=405)

    try:
        proveedor = Supplier.objects.get(id=supplier_id)
    except Supplier.DoesNotExist:
        return JsonResponse({
            'error': 'Proveedor no encontrado'
        }, status=404)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({
            'error': 'JSON inválido'
        }, status=400)

    if 'name' in data:
        proveedor.name = data['name']

    if 'address' in data:
        proveedor.address = data['address']

    if 'company' in data:

        company_id = data['company']

        if company_id:
            try:
                proveedor.company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                return JsonResponse({
                    'error': 'Empresa no encontrada'
                }, status=404)
        else:
            proveedor.company = None

    proveedor.save()

    return JsonResponse({
        'success': True,
        'message': 'Proveedor actualizado correctamente',
        'proveedor': {
            'id': proveedor.id,
            'name': proveedor.name,
            'address': proveedor.address,
            'company': proveedor.company.id if proveedor.company else None,
            'company_name': proveedor.company.name if proveedor.company else None
        }
    })

