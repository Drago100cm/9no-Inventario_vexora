from pyexpat.errors import messages
from urllib import request
from django.contrib.auth import  login, logout
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.urls import reverse, reverse_lazy
from .forms import *
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView,RedirectView, DetailView, TemplateView
from vexora.models import *
from django.contrib import messages
from django.core.mail import send_mail
import logging
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import Group, Permission
# Create your views here.

class HomeView(TemplateView):
    template_name = 'Home/home.html'

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from .models import SiteConfiguration
from .forms import SiteConfigurationForm

#--------------------Configuración del sitio-------------------
class SiteConfigurationUpdateView(
    LoginRequiredMixin,
    UpdateView
):

    model = SiteConfiguration
    form_class = SiteConfigurationForm
    template_name = 'vexora/configuration/site_configuration.html'
    success_url = reverse_lazy('vexora:site_configuration')

    def dispatch(self, request, *args, **kwargs):

        if not request.user.company:
            return redirect('vexora:company_create')

        return super().dispatch(request, *args, **kwargs)

    def get_object(self):

        obj, created = SiteConfiguration.objects.get_or_create(
            company=self.request.user.company
        )

        return obj
#--------------------Grupos y permisos-------------------
class GroupListView(LoginRequiredMixin,ListView):

    model = Group

    template_name = 'vexora/groups/list.html'

    context_object_name = 'groups'





from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.models import Group, Permission
from django.contrib import messages


class GroupCreateView(View):

    template_name = 'vexora/groups/create.html'

    def get(self, request):

        return render(
            request,
            self.template_name
        )

    def post(self, request):

        group_name = request.POST.get(
            'group_name'
        )

        group = Group.objects.create(
            name=group_name
        )

        permission_codenames = request.POST.getlist(
            'permissions'
        )

        permissions = Permission.objects.filter(
            codename__in=permission_codenames
        )

        group.permissions.set(
            permissions
        )

        messages.success(
            request,
            'Grupo creado correctamente'
        )

        return redirect(
            'vexora:group_list'
        )
#---------------------Login----------------------
class CustomLoginView(FormView):
    form_class = CustomAuthenticationForm
    template_name = "Accounts/login.html"
    success_url = settings.LOGIN_REDIRECT_URL

    def dispatch(self, request, *args, **kwargs):
        print("🔹 Entrando a dispatch")
        if request.user.is_authenticated:
            print("✅ Usuario ya autenticado:", request.user)
            return redirect(self.success_url)
        print("❌ Usuario no autenticado, mostrando formulario")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        print("👤 Usuario autenticado:", user)  # debug
        login(self.request, user)
        return super().form_valid(form)

    def get_success_url(self):
        # Buscar 'next' tanto en POST como en GET (formularios pueden enviarlo por POST)
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        url = next_url or self.success_url
        print("📌 get_success_url ->", url)
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Iniciar sesión'
        print("📝 Contexto agregado:", context)
        return context
#---------------------Logout----------------------
class LogoutRedirectView(RedirectView):
    pattern_name = 'vexora:login'  # URL a la que se redirige después de cerrar sesión

    def dispatch(self, request, *args, **kwargs):
        logout(request)
        return super().dispatch(request, *args, **kwargs)
#---------------------Registro----------------------
class RegisterView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "Accounts/register.html"
    success_url = reverse_lazy("vexora:home")

    def form_valid(self, form):
        form.instance.is_active = True
        response = super().form_valid(form)
        # Loguear automáticamente al usuario después del registro
        login(self.request, self.object)
        return response
    def form_invalid(self, form):
        form.instance.is_active = True
        print("❌ Registro inválido")
        print("Errores:", form.errors)
        return super().form_invalid(form)
    
#---------------------User List----------------------
class UserListView(LoginRequiredMixin,ListView):
    #template_name = "logamex/departments/departaments.html"
    template_name = "vexora/users/list.html"

    def get(self, request):
        
        list_user = CustomUser.objects.all()

        data = {
            'list_user': list_user
        }

        permisos = request.user.get_all_permissions()

        if "vexora.view_customuser" in permisos:
            return render(request, self.template_name, data)
        else:
            return redirect("vexora:home")

       
#--------------------Crear usuario -------------------
class UserCreateView(LoginRequiredMixin,CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "vexora/users/create.html"   # 👈 plantilla para crear usuarios
    success_url = reverse_lazy("vexora:user_list")
    
    def get_form_kwargs(self):
        kwargs = super(UserCreateView, self).get_form_kwargs()
        return kwargs

    def post(self, request, *args, **kwargs):
        form = CustomUserCreationForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ ¡Usuario creado correctamente!")
        else:
            messages.error(request, "❌ Error al crear el usuario. Verifica los datos.")
        return redirect("vexora:user_list")
#--------------------Actualizar Usuario -------------------
class UserUpdateView(LoginRequiredMixin,UpdateView):
    model = CustomUser
    form_class = CustomUserUpdateForm
    template_name = "vexora/users/update.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["current_user"] = self.request.user   # 👈 se lo pasamos al form
        return kwargs
    
    def form_valid(self, form):
        promesa = self.get_object()
        promesa.save()
        messages.success(self.request, "✅ Usuario actualizado correctamente!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:user_list')

def delete_user(request, pk):
    user = get_object_or_404(CustomUser, id=pk)
    user.delete()
    messages.success(request, "✅ Usuario eliminado correctamente!")
    return redirect('vexora:user_list')  # ruta a la lista de clientes

#-----------------perfil usuario----------------------
class ProfileView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = "accounts/profile/profile.html"
    context_object_name = "profile"

    def get_object(self, queryset=None):
        # Siempre devuelve el usuario autenticado
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user



        # Destinos visitados (por reservas confirmadas)


        # Puntos de fidelidad simple (ejemplo: 100 puntos por reserva confirmada)

        context.update({

       
            # Próximos viajes: reservas pendientes o confirmadas (máx 4)
        })
        return context
    
#---------------------Company----------------------
class CompanyListView(LoginRequiredMixin,ListView):
    #template_name = "logamex/departments/departaments.html"
    template_name = "vexora/companies/list.html"

    def get(self, request):
        
        list_company = Company.objects.all()

        data = {
            'list_company': list_company
        }

        permisos = request.user.get_all_permissions()

        if "vexora.view_company" in permisos:
            return render(request, self.template_name, data)
        else:
            return redirect("vexora:home")

       
#--------------------Crear empresa -------------------
class CompanyCreateView(LoginRequiredMixin,CreateView):
    model = Company
    form_class = CompanyForm
    template_name = "vexora/companies/create.html"   # 👈 plantilla para crear empresas
    success_url = reverse_lazy("vexora:company_list")
    
    def get_form_kwargs(self):
        kwargs = super(CompanyCreateView, self).get_form_kwargs()
        return kwargs

    def post(self, request, *args, **kwargs):
        form = CompanyForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            company = form.save(commit=False)

            company.owner = self.request.user

            company.save()

            # Vincular usuario
            user = self.request.user
            user.company = company
            user.save()
            messages.success(request, "✅ ¡Empresa creada correctamente!")
        else:
            messages.error(request, "❌ Error al crear la empresa. Verifica los datos.")
        return redirect("vexora:company_list")
#--------------------Actualizar Empresa -------------------
class CompanyUpdateView(LoginRequiredMixin,UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = "vexora/companies/update.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs
    
    def form_valid(self, form):
        promesa = self.get_object()
        promesa.save()
        messages.success(self.request, "✅ Empresa actualizada correctamente!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:company_list')

def delete_company(request, pk):
    company = get_object_or_404(Company, id=pk)
    company.delete()
    messages.success(request, "✅ Empresa eliminada correctamente!")
    return redirect('vexora:company_list')  # ruta a la lista de empresas
