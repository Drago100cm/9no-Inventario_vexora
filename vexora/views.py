from pyexpat.errors import messages
from urllib import request
from django.contrib.auth import  login, logout
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
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
from django.utils import timezone
from datetime import timedelta
from django.views import View
from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import (EmailBackend)
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.models import Group, Permission
from django.contrib import messages
from .models import Plan, Subscription, payment, PlanFeature
from vexora.services.email_service import (send_welcome_email)
from .services.ai_service import get_ai_response
from .models import SiteConfiguration, SMTPConfiguration
from .forms import SiteConfigurationForm, SMTPConfigurationForm
# Create your views here.

class HomeView(TemplateView):
    template_name = 'Home/home.html'
#======Home de la empresa (con slug)======
def company_home(request, slug):
    company = get_object_or_404(Company, slug=slug)
    context = {
        'company': company,
        'slug': slug
    }
    return render(request, 'vexora/companies/home.html', context)



class AIChatView(LoginRequiredMixin, FormView):
    template_name = 'vexora/assistant/chat.html'
    form_class = AIChatForm
    success_url = reverse_lazy('vexora:ai_assistant')

    def form_valid(self, form):
        prompt = form.cleaned_data['prompt']

        try:
            answer = get_ai_response(prompt)

        except Exception as e:
            answer = f'Error al generar la respuesta: {e}'

        return self.render_to_response(
            self.get_context_data(
                form=form,
                answer=answer,
                prompt=prompt
            )
        )


# views.py


#--------------------Configuración del sitio-------------------
class SiteConfigurationUpdateView(LoginRequiredMixin,UpdateView):

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

#--------------------Configuración SMTP-------------------
class SMTPConfigurationUpdateView(LoginRequiredMixin,UpdateView):

    model = SMTPConfiguration
    form_class = SMTPConfigurationForm
    template_name = 'vexora/configuration/smtp_configuration.html'
    success_url = reverse_lazy('vexora:smtp_configuration')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.company:
            return redirect('vexora:company_create')
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        obj, created = SMTPConfiguration.objects.get_or_create(
            company=self.request.user.company
        )
        return obj
class SMTPTestView(LoginRequiredMixin, View):

    def post(self, request):

        smtp = get_object_or_404(
            SMTPConfiguration,
            company=request.user.company
        )

        try:

            connection = EmailBackend(

                host=smtp.email_host,

                port=smtp.email_port,

                username=smtp.email_host_user,

                password=smtp.email_host_password,

                use_tls=smtp.use_tls,
                    
                use_ssl=smtp.use_ssl,

                timeout=10
            )

            email = EmailMessage(

                subject='Prueba SMTP Vexora 🚀',

                body='Tu configuración SMTP funciona correctamente.',

                from_email=smtp.email_host_user,

                to=[request.user.email],

                connection=connection

            )

            email.send()

            messages.success(
                request,
                'Correo de prueba enviado.'
            )

        except Exception as e:

            messages.error(
                request,
                f'Error SMTP: {str(e)}'
            )

        return redirect(
            'vexora:smtp_configuration'
        )

#--------------------Grupos y permisos-------------------
class GroupListView(LoginRequiredMixin,ListView):

    model = Group

    template_name = 'vexora/groups/list.html'

    context_object_name = 'groups'



class GroupCreateView(View):

    template_name = 'vexora/groups/create.html'

    def get(self, request):

        return render(request,
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
    
def delete_group(request, pk):
    group = get_object_or_404(Group, id=pk)
    group.delete()
    messages.success(request, "✅ Grupo eliminado correctamente!")
    return redirect('vexora:group_list')  # ruta a la lista de grupos

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
        #send_welcome_email(self.object)   Enviar email de bienvenida
        login(self.request, self.object)
        return response
    def form_invalid(self, form):
        form.instance.is_active = True
        print("❌ Registro inválido")
        print("Errores:", form.errors)
        return super().form_invalid(form)
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
    def form_invalid(self, form):

        print("ERRORES LOGIN:", form.errors)

        return super().form_invalid(form)

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

#==================== Subscription support ====================

def ensure_default_plans():
    plans = Plan.objects.filter(active=True)
    if not plans.exists():
        Plan.objects.create(
            name='Trial',
            description='Prueba gratuita de 14 días para empezar.',
            price=0.00,
            billing_type='monthly',
            max_users=2,
            max_products=50,
            max_branches=1,
            custom_domain=False,
            priority_support=False,
            active=True,
        )
        Plan.objects.create(
            name='Básico',
            description='Ideal para equipos pequeños y proyectos iniciales.',
            price=19.99,
            billing_type='monthly',
            max_users=5,
            max_products=200,
            max_branches=2,
            custom_domain=False,
            priority_support=False,
            active=True,
        )
        Plan.objects.create(
            name='Pro',
            description='Para organizaciones con más usuarios y soporte prioritario.',
            price=49.99,
            billing_type='monthly',
            max_users=20,
            max_products=1000,
            max_branches=5,
            custom_domain=True,
            priority_support=True,
            active=True,
        )
        plans = Plan.objects.filter(active=True)
    return plans


def subscription_end_date(start_date, billing_type):
    if billing_type == 'yearly':
        return start_date + timedelta(days=365)
    return start_date + timedelta(days=30)


class SubscriptionPlanListView(LoginRequiredMixin, TemplateView):
    template_name = 'vexora/subscriptions/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = ensure_default_plans()
        context['company'] = self.request.user.company
        context['subscription'] = None
        if context['company']:
            context['subscription'] = getattr(context['company'], 'subscription', None)
        return context


class SubscriptionChooseView(LoginRequiredMixin, View):
    def post(self, request, plan_id, *args, **kwargs):
        company = request.user.company
        if not company:
            messages.error(request, 'Necesitas crear una empresa antes de elegir un plan.')
            return redirect('vexora:company_create')

        plan = get_object_or_404(Plan, id=plan_id, active=True)
        current_subscription = getattr(company, 'subscription', None)
        start_date = timezone.now().date()
        end_date = subscription_end_date(start_date, plan.billing_type)

        if current_subscription and current_subscription.plan_id == plan.id and current_subscription.active:
            messages.info(request, 'Ya tienes ese plan seleccionado.')
            return redirect('vexora:subscription_detail')

        if current_subscription:
            current_subscription.plan = plan
            current_subscription.status = 'active'
            current_subscription.start_date = start_date
            current_subscription.end_date = end_date
            current_subscription.trial = False
            current_subscription.active = True
            current_subscription.save()
            subscription = current_subscription
        else:
            subscription = Subscription.objects.create(
                company=company,
                plan=plan,
                status='active',
                start_date=start_date,
                end_date=end_date,
                trial=False,
                active=True,
            )

        payment.objects.create(
            company=company,
            subscription=subscription,
            amount=plan.price,
            payment_method='cash',
            status='completed',
            transaction_id=f'PAY-{timezone.now().strftime("%Y%m%d%H%M%S")}',
            paid_at=timezone.now(),
        )

        messages.success(request, f'Suscripción a {plan.name} activada correctamente.')
        return redirect('vexora:subscription_detail')


class SubscriptionDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'vexora/subscriptions/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.request.user.company
        context['subscription'] = None
        context['payments'] = None
        if context['company']:
            context['subscription'] = getattr(context['company'], 'subscription', None)
            context['payments'] = payment.objects.filter(company=context['company']).order_by('-paid_at')
        return context


    
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
        print("[UserUpdateView] cleaned_data:", form.cleaned_data)
        response = super().form_valid(form)
        messages.success(self.request, "✅ Usuario actualizado correctamente!")
        return response

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

#--------------------Detalle Empresa -------------------
class CompanyDetailView(LoginRequiredMixin,DetailView):
    model = Company
    template_name = "vexora/companies/detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "company"

    def get(self, request, *args, **kwargs):
        permisos = request.user.get_all_permissions()
        if "vexora.view_company" not in permisos:
            return redirect("vexora:home")
        return super().get(request, *args, **kwargs)

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
            return redirect("vexora:subscription_list")
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
        response = super().form_valid(form)
        messages.success(self.request, "✅ Empresa actualizada correctamente!")
        return response

    def get_success_url(self):
        return reverse('vexora:company_list')

def delete_company(request, pk):
    company = get_object_or_404(Company, id=pk)
    company.delete()
    messages.success(request, "✅ Empresa eliminada correctamente!")
    return redirect('vexora:company_list')  # ruta a la lista de empresas

# ============================================
# SUPPLIER VIEWS (Proveedores)
# ============================================

class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'vexora/supplier/list.html'
    context_object_name = 'suppliers'

    def get_queryset(self):
        return Supplier.objects.all().order_by('name')


class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'vexora/supplier/create.html'

    def form_valid(self, form):
        messages.success(self.request, "✅ Supplier created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:list_suppliers')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'New Supplier'
        return context


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'vexora/supplier/update.html'
    pk_url_kwarg = 'id'

    def form_valid(self, form):
        messages.success(self.request, "✅ Supplier updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:list_suppliers')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Supplier'
        return context

def SupplierDeleteView(request, pk):
    supplier = get_object_or_404(Supplier, id=pk)
    supplier.delete()
    messages.success(request, "✅ Proveedor eliminado correctamente!")
    return redirect('vexora:list_suppliers')  # ruta a la lista de proveedores


# ============================================
# PRODUCT VIEWS (Productos)
# ============================================

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'vexora/products/list.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.all().order_by('-purchase_date')


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'vexora/products/form.html'

    def form_valid(self, form):
        messages.success(self.request, "✅ Product created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:list_products')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'New Product'
        return context


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'vexora/products/form.html'
    pk_url_kwarg = 'id'

    def form_valid(self, form):
        messages.success(self.request, "✅ Product updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:list_products')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Product'
        return context


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'vexora/products/confirm_delete.html'
    pk_url_kwarg = 'id'

    def get_success_url(self):
        messages.success(self.request, "✅ Product deleted successfully!")
        return reverse('vexora:list_products')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = 'product'
        return context