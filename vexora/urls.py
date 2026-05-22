from django.urls import path
from .views import *
from . import views
app_name = 'vexora'
urlpatterns = [
    path('configuration/',SiteConfigurationUpdateView.as_view(),name='site_configuration'),
    path('groups/',GroupListView.as_view(),name='group_list'),
    path('group_create/',GroupCreateView.as_view(),name='group_create'),
    path("login/", CustomLoginView.as_view(), name="login"),
    path('logout/', LogoutRedirectView.as_view(), name='logout'),
    path("Registro/", RegisterView.as_view(), name="registro"),
    path('', HomeView.as_view(), name='home'),
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
]