from django.urls import path
from .views import *
from . import views
from .api import api_register, api_login
from .views import SubscriptionPlanListView, SubscriptionChooseView, SubscriptionDetailView
app_name = 'vexora'
urlpatterns = [
    
    #----------------------Home----------------------
    path('', HomeView.as_view(), name='home'),

    #----------------------Autenticación----------------------
    path("login/", CustomLoginView.as_view(), name="login"),
    path('logout/', LogoutRedirectView.as_view(), name='logout'),
    path("Registro/", RegisterView.as_view(), name="registro"),
    #----------------------Configuración del sitio----------------------
    path('configuration/',SiteConfigurationUpdateView.as_view(),name='site_configuration'),
    path('smtp_configuration/', SMTPConfigurationUpdateView.as_view(), name='smtp_configuration'),
    path('smtp_test/',SMTPTestView.as_view(),name='smtp_test'),
    #----------------------Grupos y permisos----------------------
    path('groups/',GroupListView.as_view(),name='group_list'),
    path('group_create/',GroupCreateView.as_view(),name='group_create'),
    
    #----------------------Suscripciones----------------------
    path('subscription_list/', SubscriptionPlanListView.as_view(), name='subscription_list'),
    path('subscriptions/choose/<int:plan_id>/', SubscriptionChooseView.as_view(), name='subscription_choose'),
    path('subscriptions/detail/', SubscriptionDetailView.as_view(), name='subscription_detail'),
    
    #----------------------Uuarios----------------------
    path("users/", UserListView.as_view(), name="user_list"),
    path("user_create", UserCreateView.as_view(), name="user_create"),
    path("user_edit/<int:pk>", UserUpdateView.as_view(), name="user_edit"),
    path("user_delete/<int:pk>", views.delete_user, name="user_delete"),
    path('profil/<int:pk>/', ProfileView.as_view(), name='profil'),
    #----------------------Empresas----------------------
    path("companies/", CompanyListView.as_view(), name="company_list"),
    path("company_create", CompanyCreateView.as_view(), name="company_create"),
    path("company_edit/<int:pk>", CompanyUpdateView.as_view(), name="company_edit"),
    path("company_delete/<int:pk>", views.delete_company, name="company_delete"),
    
    
    # API endpoints
    path('api/register/', api_register, name='api_register'),
    path('api/login/', api_login, name='api_login'),


    # URLs para CLIENTES
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/editar/<int:id>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/eliminar/<int:id>/', views.eliminar_cliente, name='eliminar_cliente'),
    
    # URLs para PROVEEDORES
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/crear/', views.crear_proveedor, name='crear_proveedor'),
    path('proveedores/editar/<int:id>/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<int:id>/', views.eliminar_proveedor, name='eliminar_proveedor'),
    
    # URLs para PRODUCTOS
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
]