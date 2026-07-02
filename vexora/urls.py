from django.urls import path
from .views import *
from . import views
from .api import *
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
    path('group_edit/<int:pk>/',GroupUpdateView.as_view(),name='group_edit'),
    path('group_delete/<int:pk>/', views.delete_group, name='group_delete'),
    
    #----------------------Planes de suscripción----------------------
    path('plans/', PlanListView.as_view(), name='plan_list'),
    path('plans/create/', PlanCreateView.as_view(), name='plan_create'),
    path('plans/edit/<int:pk>/', PlanUpdateView.as_view(), name='plan_edit'),
    path('plans/delete/<int:pk>/', views.delete_plan, name='plan_delete'),
    
    #----------------------Suscripciones----------------------
    path('subscription_list/', SubscriptionPlanListView.as_view(), name='subscription_list'),
    path('subscriptions/choose/<int:plan_id>/', SubscriptionChooseView.as_view(), name='subscription_choose'),
    path('subscriptions/detail/', SubscriptionDetailView.as_view(), name='subscription_detail'),
    path('assistant/', AIChatView.as_view(), name='ai_assistant'),
    
    #----------------------Uuarios----------------------
    path("users/", UserListView.as_view(), name="user_list"),
    path("user_create", UserCreateView.as_view(), name="user_create"),
    path("user_edit/<int:pk>", UserUpdateView.as_view(), name="user_edit"),
    path("user_delete/<int:pk>", views.delete_user, name="user_delete"),
    path('profil/<int:pk>/', ProfileView.as_view(), name='profil'),
    #----------------------Empresas----------------------
    path("companies/", CompanyListView.as_view(), name="company_list"),
    path("company/<slug:slug>/", CompanyDetailView.as_view(), name="company_detail"),
    path("company_create", CompanyCreateView.as_view(), name="company_create"),
    path("company_edit/<int:pk>", CompanyUpdateView.as_view(), name="company_edit"),
    path("company_delete/<int:pk>", views.delete_company, name="company_delete"),


    # ============================================
    # CATEGORY URLs (Categorías)
    # ============================================
    path('categories/', views.CategoryListView.as_view(), name='list_categories'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='create_category'),
    path('categories/update/<int:id>/', views.CategoryUpdateView.as_view(), name='edit_category'),
    path('categories/delete/<int:pk>/', views.delete_category, name='delete_category'),
    
    # ============================================
    # SUPPLIER URLs (Proveedores)
    # ============================================
    path('suppliers/', views.SupplierListView.as_view(), name='list_suppliers'),
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='create_supplier'),
    path('suppliers/update/<int:id>/', views.SupplierUpdateView.as_view(), name='edit_supplier'),
    path('suppliers/delete/<int:pk>/', views.delete_supplier, name='delete_supplier'),

    # ============================================
    # PRODUCT URLs (Productos)
    # ============================================
    path('list_products/', views.ProductListView.as_view(), name='list_products'),
    path('products/create/', views.ProductCreateView.as_view(), name='create_product'),
    path('products/update/<int:id>/', views.ProductUpdateView.as_view(), name='edit_product'),
    path('products/delete/<int:id>/', views.delete_product, name='delete_product'), 

    path('products/delete/<int:pk>/', views.delete_product, name='delete_product'), 
    
    
    # API endpoints
    path('api/register/', api_register, name='api_register'),
    path('api/login/', api_login, name='api_login'),
    path('api/list_productos/',api_productos, name='api_productos'),
    path('api/list_proveedores/', api_proveedores, name='api_proveedores'),
    path('api/crear_producto/', api_crear_producto, name='api_crear_producto'),
    path('api/editar_producto/<int:id>/', api_product_update, name='api_product_update'),
    path('api/crear_proveedor/', api_crear_proveedor, name='api_crear_proveedor'),
    path('api/editar_proveedor/<int:id>/', api_supplier_update, name='api_supplier_update'),
    
    
    
    
    
    
    
    # ============================================home empresas=============
    
    path('<slug:slug>/',views.company_home,name='company_home'),
    path('<slug:slug>/register/',views.RegisterView.as_view(),name='company_register'),

    path('<slug:slug>/login/',views.CustomLoginView.as_view(),name='company_login'),
]
