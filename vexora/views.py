from pyexpat.errors import messages
from django.contrib.auth.decorators import login_required
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
from django.db.models import Q
from datetime import datetime

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
class GroupListView(LoginRequiredMixin, ListView):

    model = Role
    template_name = "vexora/groups/list.html"
    context_object_name = "groups"

    def get_queryset(self):

        user = self.request.user
    
        # 🔥 Superusuario ve TODO
        if user.is_superuser:
            return Role.objects.filter(active=True).order_by("name")

        # 🏢 Empresa del usuario
        membership = user.memberships.select_related("company").first()

        if not membership:
            return Role.objects.none()

        return Role.objects.filter(
            company=membership.company,
            active=True
        ).order_by("name")
        
class GroupCreateView(LoginRequiredMixin, CreateView):
    template_name = "vexora/groups/create.html"
    form_class = GroupForm

    def get(self, request, *args, **kwargs):

        company = request.user.company

        if not company:
            messages.error(request, "No perteneces a ninguna empresa.")
            return redirect("vexora:dashboard")

        subscription = getattr(company, "subscription", None)

        if not subscription or not subscription.active:
            messages.error(request, "Necesitas una suscripción activa.")
            return redirect("vexora:plans")

        plan = subscription.plan
        total_roles = company.roles.count()

        if plan.max_groups != 0 and total_roles >= plan.max_groups:
            messages.error(
                request,
                f"Tu plan permite crear únicamente {plan.max_groups} roles."
            )
            return redirect("vexora:group_list")

        return render(request, self.template_name, {
            "form": self.form_class(),
            "group_permissions": []
        })

    def post(self, request, *args, **kwargs):

        company = request.user.company

        if not company:
            messages.error(request, "No perteneces a ninguna empresa.")
            return redirect("vexora:dashboard")

        subscription = getattr(company, "subscription", None)

        if not subscription or not subscription.active:
            messages.error(request, "Necesitas una suscripción activa.")
            return redirect("vexora:plans")

        plan = subscription.plan
        total_roles = company.roles.count()

        if plan.max_groups != 0 and total_roles >= plan.max_groups:
            messages.error(
                request,
                f"Has alcanzado el límite de {plan.max_groups} roles."
            )
            return redirect("vexora:group_list")

        form = self.form_class(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {
                "form": form,
                "group_permissions": request.POST.getlist("permissions")
            })

        # Validar duplicado
        if Role.objects.filter(
            company=company,
            name=form.cleaned_data["name"]
        ).exists():

            messages.warning(
                request,
                f'El rol "{form.cleaned_data["name"]}" ya existe.'
            )

            return redirect("vexora:group_list")

        role = form.save(commit=False)
        role.company = company
        role.save()

        permissions = Permission.objects.filter(
            codename__in=request.POST.getlist("permissions")
        )

        role.permissions.set(permissions)

        messages.success(request, "Rol creado correctamente.")
        return redirect("vexora:group_list")
class GroupUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "vexora/groups/edit.html"

    def get_role(self, request, pk):
        user = request.user

        # 🔥 Superusuario puede ver todo
        if user.is_superuser:
            return get_object_or_404(Role, pk=pk)

        # 🏢 Usuario normal solo su empresa
        membership = user.memberships.select_related("company").first()

        if not membership:
            return None

        return get_object_or_404(
            Role,
            pk=pk,
            company=membership.company
        )

    def get(self, request, pk):
        role = self.get_role(request, pk)

        if not role:
            return redirect("vexora:group_list")

        form = GroupForm(instance=role)

        permissions = Permission.objects.all()

        context = {
            "group": role,
            "form": form,
            "permissions": permissions,
            "group_permissions": role.permissions.values_list("codename", flat=True),
        }

        return render(request, self.template_name, context)

    def post(self, request, pk):
        role = self.get_role(request, pk)

        if not role:
            return redirect("vexora:group_list")

        form = GroupForm(request.POST, instance=role)

        if form.is_valid():

            user = request.user

            # 🔥 Validación duplicado por empresa
            if not user.is_superuser:
                membership = user.memberships.select_related("company").first()
                company = membership.company if membership else None

                if Role.objects.filter(
                    company=company,
                    name=form.cleaned_data["name"]
                ).exclude(pk=role.pk).exists():

                    messages.warning(
                        request,
                        f'El rol "{form.cleaned_data["name"]}" ya existe.'
                    )

                    return redirect("vexora:group_list")

                role.company = company

            role = form.save()

            permissions = Permission.objects.filter(
                codename__in=request.POST.getlist("permissions")
            )

            role.permissions.set(permissions)

            messages.success(request, "Rol actualizado correctamente.")

            return redirect("vexora:group_list")

        permissions = Permission.objects.all()

        context = {
            "group": role,
            "form": form,
            "permissions": permissions,
            "group_permissions": request.POST.getlist("permissions"),
        }

        return render(request, self.template_name, context)
def delete_group(request, pk):
    group = get_object_or_404(Role, id=pk)
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

        user = self.object

        login(self.request, user)

        return response
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

class PlanListView(LoginRequiredMixin, ListView):
    model = Plan
    template_name = 'vexora/subscriptions/plans.html'
    context_object_name = 'plans'
    ordering = ['id']  # o 'name', según prefieras

    def get_queryset(self):
        ensure_default_plans()  # Crea los planes por defecto si no existen
        return Plan.objects.filter(active=True).order_by('id')
    

class PlanCreateView(LoginRequiredMixin, CreateView):
    model = Plan
    form_class = PlanesForm
    template_name = 'vexora/subscriptions/plan_create.html'
    success_url = reverse_lazy('vexora:plan_list')

    def form_valid(self, form):
        messages.success(self.request, "✅ Plan creado correctamente!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear nuevo plan'
        return context
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if self.request.user.company:
            form.instance.company = self.request.user.company
            messages.success(self.request, f"✅ Proveedor '{form.instance.name}' creado correctamente!")
            return super().form_valid(form)
        else:
            messages.error(self.request, "❌ No tienes una empresa asignada.")
            return redirect('vexora:list_suppliers')

    def get_success_url(self):
        return reverse('vexora:list_suppliers')
    
class PlanUpdateView(LoginRequiredMixin,UpdateView):
    model = Plan
    form_class = PlanesForm
    template_name = "vexora/subscriptions/plan_edit.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "✅ Plan actualizado correctamente!")
        return response

    def get_success_url(self):
        return reverse('vexora:plan_list')

def delete_plan(request, pk):
    plan = get_object_or_404(Plan, id=pk)
    plan.delete()
    messages.success(request, "✅ Plan eliminado correctamente!")
    return redirect('vexora:plan_list')  # ruta a la lista de planes
    
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

        user = request.user
        company = user.company

        if not company:
            messages.error(
                request,
                'Necesitas crear una empresa antes de elegir un plan.'
            )
            return redirect('vexora:company_create')

        plan = get_object_or_404(
            Plan,
            id=plan_id,
            active=True
        )

        # Ahora la suscripción pertenece a la empresa
        current_subscription = getattr(company, "subscription", None)

        start_date = timezone.now().date()
        end_date = subscription_end_date(
            start_date,
            plan.billing_type
        )

        # Ya tiene ese plan
        if (
            current_subscription
            and current_subscription.plan_id == plan.id
            and current_subscription.active
        ):
            messages.info(request, "Ya tienes ese plan seleccionado.")
            return redirect("vexora:subscription_detail")

        # Actualizar suscripción existente
        if current_subscription:

            current_subscription.plan = plan
            current_subscription.status = "active"
            current_subscription.start_date = start_date
            current_subscription.end_date = end_date
            current_subscription.trial = False
            current_subscription.active = True
            current_subscription.save()

            subscription = current_subscription

        # Crear nueva suscripción
        else:

            subscription = Subscription.objects.create(
                company=company,
                plan=plan,
                status="active",
                start_date=start_date,
                end_date=end_date,
                trial=False,
                active=True,
            )

        payment.objects.create(
            company=company,
            subscription=subscription,
            amount=plan.price,
            payment_method="cash",
            status="completed",
            transaction_id=f"PAY-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            paid_at=timezone.now(),
        )

        messages.success(
            request,
            f"Suscripción a {plan.name} activada correctamente."
        )

        return redirect("vexora:subscription_detail")
class SubscriptionDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'vexora/subscriptions/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        company = getattr(user, 'company', None)

        context['company'] = company

        # Si no hay empresa, no hay suscripción
        if not company:
            context['subscription'] = None
            context['payments'] = None
            return context

        try:
            # AHORA es por company, no por user
            subscription = Subscription.objects.get(company=company)

            context['subscription'] = subscription

            context['payments'] = payment.objects.filter(
                subscription=subscription
            ).order_by('-paid_at')

        except Subscription.DoesNotExist:
            context['subscription'] = None
            context['payments'] = None

        return context
#---------------------User List----------------------
class UserListView(LoginRequiredMixin, ListView):
    template_name = "vexora/users/list.html"

    def get(self, request):

        if request.user.is_superuser:
            list_user = CustomUser.objects.all()

        else:
            companies = Company.objects.filter(
                Q(owner=request.user) |
                Q(members=request.user)
            ).distinct()

            list_user = CustomUser.objects.filter(
                companies__in=companies
            ).distinct()

        data = {
            "list_user": list_user
        }

        if request.user.is_superuser or request.user.has_perm("vexora.view_customuser"):
            return render(request, self.template_name, data)

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
    if Company.objects.filter(owner=user).exists():
        messages.error(request, "No puedes eliminar este usuario porque es propietario de una empresa.")
        return redirect("vexora:user_list")
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
    
#==================== Company Views (Empresas) ====================
class CompanyListView(LoginRequiredMixin, ListView):
    template_name = "vexora/companies/list.html"

    def get(self, request):

        user = request.user

        # Superusuario ve todas las empresas
        if user.is_superuser:
            list_company = Company.objects.all()

        # Usuario normal solo ve las empresas que creó
        else:
            list_company = Company.objects.filter(owner=user)

        data = {
            "list_company": list_company
        }

        return render(request, self.template_name, data)


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
        form = CompanyForm(request.POST, request.FILES)

        if form.is_valid():
            company = form.save(commit=False)
            company.owner = request.user
            company.save()

            admin_role = Role.objects.create(
                company=company,
                name="Administrador",
                description="Administrador de la empresa"
            )

            admin_role.permissions.set(Permission.objects.all())

            CompanyMember.objects.create(
                company=company,
                user=request.user,
                role=admin_role
            )

            messages.success(request, "✅ ¡Empresa creada correctamente!")

            return redirect("vexora:subscription_list")

        messages.error(request, "❌ Error al crear la empresa.")
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

@login_required
def delete_company(request, pk):

    company = get_object_or_404(Company, id=pk)

    # Validación básica de seguridad
    if request.user.company != company and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para eliminar esta empresa.")
        return redirect("vexora:company_list")

    # 🔥 SOFT DELETE (RECOMENDADO)
    company.is_active = False
    company.deleted_at = timezone.now()
    company.save()

    messages.success(request, "✅ Empresa desactivada correctamente!")

    return redirect("vexora:company_list")
# ============================================
# CATEGORY VIEWS (Categorías)
# ============================================

class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'vexora/category/list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        if self.request.user.company:
            return Category.objects.filter(company=self.request.user.company).order_by('name')
        return Category.objects.all().order_by('name')

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'vexora/category/create.html'

    def form_valid(self, form):
        if self.request.user.company:
            form.instance.company = self.request.user.company
        messages.success(self.request, "✅ Categoria creada correctamente!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:list_categories')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'New Category'
        return context
    
class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'vexora/category/update.html'
    pk_url_kwarg = 'id'

    def form_valid(self, form):
        messages.success(self.request, "✅ Categoria actualizada correctamente!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:list_categories')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Category'
        return context

def delete_category(request, pk):
    category = get_object_or_404(Category, id=pk)
    category.delete()
    messages.success(request, "✅ Categoria eliminada correctamente!")
    return redirect('vexora:list_categories') 


# ============================================
# SUPPLIER VIEWS (Proveedores)
# ============================================

class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'vexora/supplier/list.html'
    context_object_name = 'suppliers'

    def get_queryset(self):
        if self.request.user.company:
            return Supplier.objects.filter(company=self.request.user.company).order_by('name')
        return Supplier.objects.none()  # Si no tiene empresa, no muestra nada

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas
        if self.request.user.company:
            suppliers = Supplier.objects.filter(company=self.request.user.company)
            context['stats'] = {
                'total': suppliers.count(),
            }
        else:
            context['stats'] = {
                'total': 0,
            }
        
        return context


class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'vexora/supplier/create.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if self.request.user.company:
            form.instance.company = self.request.user.company
            messages.success(self.request, f"✅ Proveedor '{form.instance.name}' creado correctamente!")
            return super().form_valid(form)
        else:
            messages.error(self.request, "❌ No tienes una empresa asignada.")
            return redirect('vexora:list_suppliers')

    def get_success_url(self):
        return reverse('vexora:list_suppliers')


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'vexora/supplier/update.html'
    pk_url_kwarg = 'id'

    def get_queryset(self):
        if self.request.user.company:
            return Supplier.objects.filter(company=self.request.user.company)
        return Supplier.objects.none()

    def get_form_kwargs(self):
        # 👇 PASAR EL USUARIO AL FORMULARIO
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"✅ Proveedor '{form.instance.name}' actualizado correctamente!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:list_suppliers')


def delete_supplier(request, pk):
    supplier = get_object_or_404(Supplier, id=pk, company=request.user.company)
    supplier_name = supplier.name
    supplier.delete()
    messages.success(request, f"✅ Proveedor '{supplier_name}' eliminado correctamente!")
    return redirect('vexora:list_suppliers')

# ===========================================
# PRODUCT VIEWS (Productos)
# ===========================================

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'vexora/products/list.html'
    context_object_name = 'products'

    def get_queryset(self):
        # Mostrar productos de la empresa del usuario
        if self.request.user.company:
            queryset = Product.objects.filter(company=self.request.user.company)
        else:
            queryset = Product.objects.all()

        # Filtro por proveedor
        supplier = self.request.GET.get('supplier')
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)

        # Filtro por categoría
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        # Filtro por disponibilidad
        disponibilidad = self.request.GET.get('disponibilidad')
        if disponibilidad == 'disponibles':
            queryset = queryset.filter(is_active=True, stock__gt=0)
        elif disponibilidad == 'no_disponibles':
            queryset = queryset.filter(Q(is_active=False) | Q(stock=0))

        # Filtro por rango de fechas
        fecha_inicio = self.request.GET.get('fecha_inicio')
        fecha_fin = self.request.GET.get('fecha_fin')
        if fecha_inicio and fecha_fin:
            try:
                from datetime import datetime
                fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
                queryset = queryset.filter(purchase_date__range=[fecha_inicio_dt, fecha_fin_dt])
            except ValueError:
                pass

        # Búsqueda global
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(barcode__icontains=search)
            )

        return queryset.order_by('-purchase_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Base para estadísticas
        if self.request.user.company:
            base_queryset = Product.objects.filter(company=self.request.user.company)
        else:
            base_queryset = Product.objects.all()

        # Estadísticas
        context['stats'] = {
            'total': base_queryset.count(),
            'disponibles': base_queryset.filter(is_active=True, stock__gt=0).count(),
            'no_disponibles': base_queryset.filter(Q(is_active=False) | Q(stock=0)).count(),
        }

        # Proveedores para el filtro
        if self.request.user.company:
            context['suppliers'] = Supplier.objects.filter(
                Q(company=self.request.user.company) | Q(company__isnull=True)
            )
            context['categories'] = Category.objects.filter(company=self.request.user.company)
        else:
            context['suppliers'] = Supplier.objects.all()
            context['categories'] = Category.objects.all()

        return context
    
class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'vexora/products/create.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if self.request.user.company:
            form.instance.company = self.request.user.company
        messages.success(self.request, "✅ Producto creado correctamente!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:list_products')


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'vexora/products/update.html'
    pk_url_kwarg = 'id'

    def get_queryset(self):
        return Product.objects.all()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Mantener la empresa original si no viene en el form
        if not form.instance.company and self.object:
            form.instance.company = self.object.company
        # O asignar la empresa del usuario
        elif self.request.user.company:
            form.instance.company = self.request.user.company
        
        # 👇 NUEVA LÓGICA PARA EL STOCK
        product = form.save(commit=False)
        
        # Obtener la cantidad a agregar
        stock_addition = form.cleaned_data.get('stock_addition', 0)
        
        # Si se agregó stock, sumarlo al stock actual
        if stock_addition and stock_addition > 0:
            # Mantener el stock actual y sumarle la adición
            product.stock = self.object.stock + stock_addition
            messages.success(
                self.request, 
                f'✅ Se agregaron {stock_addition} unidades al stock. Nuevo stock total: {product.stock}'
            )
        else:
            # Si no se agregó stock, mantener el stock actual
            product.stock = self.object.stock
        
        # Guardar el producto
        product.save()
        
        # Guardar los campos ManyToMany (tags)
        form.save_m2m()
        
        messages.success(self.request, "✅ Producto actualizado correctamente!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:list_products')


def delete_product(request, pk):
    product = get_object_or_404(Product, id=pk)
    product.delete()
    messages.success(request, "✅ Producto eliminado correctamente!")
    return redirect('vexora:list_products')


# =====================================
# SALES VIEWS (Ventas)
# =====================================

class SalesListView(LoginRequiredMixin, ListView):
    model = Sale
    template_name = 'vexora/sales/list.html'
    context_object_name = 'sales'

    def get_queryset(self):
        return Sale.objects.all().order_by('-date')


class SalesCreateView(LoginRequiredMixin, CreateView):
    model = Sale
    form_class = SalesForm
    template_name = 'vexora/sales/create.html'

    def form_valid(self, form):
        messages.success(self.request, "✅ Sale created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:list_sales')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'New Sale'
        return context


class SalesUpdateView(LoginRequiredMixin, UpdateView):
    model = Sale
    form_class = SalesForm
    template_name = 'vexora/sales/update.html'
    pk_url_kwarg = 'id'

    def form_valid(self, form):
        messages.success(self.request, "✅ Sale updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:list_sales')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Sale'
        return context
    
#=====================================MEMBERS VIEW========================================
class MembersView(LoginRequiredMixin, ListView):
    model = CompanyMember
    template_name = 'vexora/members/list.html'
    context_object_name = 'members'

    def get_queryset(self):
        if self.request.user.company:
            return CompanyMember.objects.filter(company=self.request.user.company)
        return CompanyMember.objects.none()  # Si no tiene empresa, no muestra nada



# =====================================
# SALES MAIN (CRUD Frontend)
# =====================================

class SalesMainListView(LoginRequiredMixin, TemplateView):
    template_name = "vexora/sales_main/list.html"


class SalesMainCreateView(LoginRequiredMixin, TemplateView):
    template_name = "vexora/sales_main/create.html"


class SalesMainUpdateView(LoginRequiredMixin, TemplateView):
    template_name = "vexora/sales_main/update.html"
