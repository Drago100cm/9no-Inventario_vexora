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
from django.utils import timezone
from django.http import JsonResponse
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
from django.views.decorators.http import require_POST
from io import BytesIO
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .models import Sale, SaleItem
# Create your views here.
logger = logging.getLogger(__name__)
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
from .models import (
    CustomUser,
    Company,
    Role,
    CompanyMember,
)
from .forms import (
    PublicUserRegistrationForm,
    CustomUserCreationForm,
)
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
# --------------------- Registro ----------------------

class RegisterView(CreateView):
    model = CustomUser
    form_class = PublicUserRegistrationForm
    template_name = "Accounts/register.html"
    success_url = reverse_lazy("vexora:home")

    def form_valid(self, form):
        form.instance.is_active = True
        form.instance.is_staff = False
        form.instance.is_superuser = False

        response = super().form_valid(form)

        user = self.object

        # Buscar la empresa activa de la tienda
        company = Company.objects.filter(
            is_active=True
        ).first()

        if company:
            # Crear o buscar el rol Cliente
            cliente_role, created = Role.objects.get_or_create(
                company=company,
                name="Cliente",
                defaults={
                    "description": "Cliente de la tienda",
                    "active": True,
                }
            )

            # Relacionar al usuario con la empresa
            CompanyMember.objects.get_or_create(
                company=company,
                user=user,
                defaults={
                    "role": cliente_role
                }
            )

        login(self.request, user)

        messages.success(
            self.request,
            "¡Tu cuenta fue creada correctamente!"
        )

        return response

    def form_invalid(self, form):
        print("========== ERROR EN EL REGISTRO ==========")

        for campo, errores in form.errors.items():
            print(f"{campo}: {errores}")

        return self.render_to_response(
            self.get_context_data(form=form)
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
    def form_invalid(self, form):

        print("ERRORES LOGIN:", form.errors)

        return super().form_invalid(form)

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)

        company = None

        # Si es propietario de una empresa
        if getattr(user, "company", None):
            company = user.company

        # Si es miembro de una empresa
        else:
            member = CompanyMember.objects.select_related("company").filter(user=user).first()
            if member:
                company = member.company

        # Guardar la empresa en la sesión
        if company:
            self.request.session["company_id"] = company.id

            messages.success(
                self.request,
                f"👋 ¡Bienvenido {user.first_name or user.username} a {company.name}!"
            )
        else:
            messages.warning(
                self.request,
                "⚠️ Tu cuenta no pertenece a ninguna empresa."
            )

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

        list_user = CustomUser.objects.all()
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
class UserCreateView(LoginRequiredMixin, CreateView):
    model = CustomUser
    form_class = PublicUserRegistrationForm
    template_name = "vexora/users/create.html"
    success_url = reverse_lazy("vexora:user_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["company"] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "✅ ¡Usuario creado correctamente!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "❌ Error al crear el usuario. Verifica los datos.")
        return super().form_invalid(form)
#--------------------Actualizar Usuario -------------------
class UserUpdateView(LoginRequiredMixin,UpdateView):
    model = CustomUser
    form_class = CustomUserUpdateForm
    template_name = "vexora/users/update.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user   # 👈 se lo pasamos al form
        kwargs["company"] = self.request.user.company   # 👈 se lo pasamos al form
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
    template_name = 'Accounts/profile/profile.html'
    context_object_name = 'profile'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company if hasattr(self.request.user, 'company') else None

        context['total_pedidos'] = Sale.objects.filter(
            company=company
        ).count() if company else 0

        context['ultimos_pedidos'] = Sale.objects.filter(
            company=company
        ).order_by('-date')[:5] if company else []

        return context
    
#==================== Company Views (Empresas) ====================
class CompanyListView(LoginRequiredMixin, ListView):
    template_name = "vexora/companies/list.html"

    def get(self, request):

        user = request.user

        # Superusuario ve todas las empresas
        if user.is_superuser:
            list_company = Company.objects.all()
            print(Permission.objects.count())

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
            
            request.session["company_id"] = company.id

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
# CATEGORY VIEWS
# ============================================

class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'vexora/category/list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        company = self.request.user.company
        if not company:
            return Category.objects.none()
        return Category.objects.filter(company=company).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        if company:
            context['stats'] = {
                'total': Category.objects.filter(company=company).count(),
            }
        else:
            context['stats'] = {'total': 0}
        return context

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'vexora/category/create.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if self.request.user.company:
            form.instance.company = self.request.user.company
            messages.success(self.request, "✅ Categoría creada correctamente!")
            return super().form_valid(form)
        else:
            messages.error(self.request, "❌ No tienes una empresa asignada.")
            return redirect('vexora:list_categories')

    def get_success_url(self):
        return reverse('vexora:list_categories')

class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'vexora/category/update.html'
    pk_url_kwarg = 'id'

    def get_queryset(self):
        company = self.request.user.company
        if not company:
            return Category.objects.none()
        return Category.objects.filter(company=company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "✅ Categoría actualizada correctamente!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:list_categories')

def delete_category(request, pk):
    company = request.user.company
    category = get_object_or_404(Category, id=pk, company=company)
    category.delete()
    messages.success(request, "✅ Categoría eliminada correctamente!")
    return redirect('vexora:list_categories')

# ============================================
# SUPPLIER VIEWS
# ============================================

class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'vexora/supplier/list.html'
    context_object_name = 'suppliers'

    def get_queryset(self):
        company = self.request.user.company
        if not company:
            return Supplier.objects.none()
        return Supplier.objects.filter(company=company).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        if company:
            context['stats'] = {
                'total': Supplier.objects.filter(company=company).count(),
            }
        else:
            context['stats'] = {'total': 0}
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
        company = self.request.user.company
        if not company:
            return Supplier.objects.none()
        return Supplier.objects.filter(company=company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"✅ Proveedor '{form.instance.name}' actualizado correctamente!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:list_suppliers')

def delete_supplier(request, pk):
    company = request.user.company
    supplier = get_object_or_404(Supplier, id=pk, company=company)
    supplier_name = supplier.name
    supplier.delete()
    messages.success(request, f"✅ Proveedor '{supplier_name}' eliminado correctamente!")
    return redirect('vexora:list_suppliers')

# ============================================
# PRODUCT VIEWS
# ============================================

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'vexora/products/list.html'
    context_object_name = 'products'

    def get_queryset(self):
        company = self.request.user.company
        if not company:
            return Product.objects.none()
        
        queryset = Product.objects.filter(company=company)

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
                fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
                queryset = queryset.filter(purchase_date__range=[fecha_inicio_dt, fecha_fin_dt])
            except ValueError:
                pass

        # Búsqueda global (incluye item_number)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(barcode__icontains=search) |
                Q(item_number__icontains=search)
            )

        return queryset.order_by('item_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        if company:
            base_queryset = Product.objects.filter(company=company)
            context['stats'] = {
                'total': base_queryset.count(),
                'disponibles': base_queryset.filter(is_active=True, stock__gt=0).count(),
                'no_disponibles': base_queryset.filter(Q(is_active=False) | Q(stock=0)).count(),
            }
            context['suppliers'] = Supplier.objects.filter(company=company)
            context['categories'] = Category.objects.filter(company=company)
        else:
            context['stats'] = {'total': 0, 'disponibles': 0, 'no_disponibles': 0}
            context['suppliers'] = Supplier.objects.none()
            context['categories'] = Category.objects.none()

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
        else:
            messages.error(self.request, "❌ No tienes una empresa asignada.")
            return redirect('vexora:list_products')

    def get_success_url(self):
        return reverse('vexora:list_products')

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'vexora/products/update.html'
    pk_url_kwarg = 'id'

    def get_queryset(self):
        company = self.request.user.company
        if not company:
            return Product.objects.none()
        return Product.objects.filter(company=company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Mantener la empresa original
        if not form.instance.company and self.object:
            form.instance.company = self.object.company
        elif self.request.user.company:
            form.instance.company = self.request.user.company
        
        product = form.save(commit=False)
        
        # Lógica para agregar stock
        stock_addition = form.cleaned_data.get('stock_addition', 0)
        if stock_addition and stock_addition > 0:
            product.stock = self.object.stock + stock_addition
            messages.success(
                self.request, 
                f'✅ Se agregaron {stock_addition} unidades al stock. Nuevo stock total: {product.stock}'
            )
        else:
            product.stock = self.object.stock
        
        # Mantener el item_number original
        product.item_number = self.object.item_number
        
        product.save()
        form.save_m2m()
        
        messages.success(self.request, "✅ Producto actualizado correctamente!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:list_products')
    
def view_product(request, pk):
    company = request.user.company
    product = get_object_or_404(Product, id=pk, company=company)
    
    # Obtener tags
    tags = product.tags.all()
    
    context = {
        'product': product,
        'tags': tags,
    }
    
    return render(request, 'vexora/products/view.html', context)

def delete_product(request, pk):
    company = request.user.company
    product = get_object_or_404(Product, id=pk, company=company)
    product.delete()
    messages.success(request, "✅ Producto eliminado correctamente!")
    return redirect('vexora:list_products')



# =====================================
# SALES VIEWS (Ventas)
# =====================================



class SalesListView(LoginRequiredMixin, ListView):
    model = Sale
    template_name = 'vexora/sales/store.html'
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
    
# ============================================
# MEMBERS VIEWS
# ============================================

class MembersView(LoginRequiredMixin, ListView):
    model = CompanyMember
    template_name = 'vexora/members/list.html'
    context_object_name = 'members'

    def get_queryset(self):
        company = self.request.user.company
        if not company:
            return CompanyMember.objects.none()
        return CompanyMember.objects.filter(company=company).select_related('user', 'role').order_by('user__username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        if company:
            context['total_users'] = CompanyMember.objects.filter(company=company).count()
        else:
            context['total_users'] = 0
        return context


class MembersCreateView(LoginRequiredMixin, CreateView):
    model = CompanyMember
    form_class = MemberCreateForm  # Usar MemberCreateForm
    template_name = 'vexora/members/create.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if self.request.user.company:
            form.instance.company = self.request.user.company
            
            response = super().form_valid(form)
            member_user = form.instance.user
            member_name = f"{member_user.first_name} {member_user.last_name}".strip() or member_user.username
            full_name = f"{member_user.first_name} {member_user.last_name}".strip()

            messages.success(
                self.request,
                f"✅ Miembro '{full_name or member_user.username}' creado correctamente!"
            )
            return response
        else:
            messages.error(self.request, "❌ No tienes una empresa asignada.")
            return redirect('vexora:list_members')

    def get_success_url(self):
        return reverse('vexora:list_members')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Miembro'
        return context


class MemberUpdateView(LoginRequiredMixin, UpdateView):
    model = CompanyMember
    form_class = MemberForm  # Usar MemberForm para edición
    template_name = 'vexora/members/update.html'
    pk_url_kwarg = 'id'

    def get_queryset(self):
        company = self.request.user.company
        if not company:
            return CompanyMember.objects.none()
        return CompanyMember.objects.filter(company=company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"✅ Miembro actualizado correctamente!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vexora:list_members')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Miembro'
        return context


def delete_member(request, pk):
    company = request.user.company
    member = get_object_or_404(CompanyMember, id=pk, company=company)
    member_name = member.user.get_full_name() or member.user.username
    member.delete()
    messages.success(request, f"✅ Miembro '{member_name}' eliminado correctamente!")
    return redirect('vexora:list_members')

# =====================================
# SALES MAIN (CRUD Frontend)
# =====================================

class SalesMainListView(LoginRequiredMixin, TemplateView):
    template_name = "vexora/sales_main/list.html"


class SalesMainCreateView(LoginRequiredMixin, TemplateView):
    template_name = "vexora/sales_main/create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(company=self.request.user.company)
        return context

class ProductQuickCreateView(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            'categories': Category.objects.filter(company=request.user.company)
        }
        return render(request, 'vexora/products/quick_create_modal.html', context)

    def post(self, request):
        name  = request.POST.get('name', '').strip()
        price = request.POST.get('price', '0')
        stock = request.POST.get('stock', '0')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')

        if not name:
            return JsonResponse({'ok': False, 'error': 'El nombre es obligatorio.'}, status=400)

        try:
            price = float(price)
        except ValueError:
            price = 0

        try:
            stock = int(stock)
        except ValueError:
            stock = 0

        company = request.user.company

        default_supplier, _ = Supplier.objects.get_or_create(
            company=company,
            name='Proveedor general',
            defaults={'address': 'N/A'}
        )

        category = None
        if category_id:
            category = Category.objects.filter(pk=category_id, company=company).first()

        product = Product.objects.create(
            name=name,
            company=company,
            supplier=default_supplier,
            category=category,
            price=price,
            sale_price=price,
            stock=stock,
            purchase_date=timezone.now().date(),
            image=image,
            is_active=True,
        )

        return JsonResponse({'ok': True, 'id': product.id, 'name': product.name})
class SalesMainUpdateView(LoginRequiredMixin, TemplateView):
    template_name = "vexora/sales_main/update.html"

# ============================================
# STORE PÚBLICA
# ============================================

class StoreHomeView(LoginRequiredMixin, View):
    template_name = 'vexora/sales/store.html'

    def get(self, request):
        productos = Product.objects.filter(
            company=request.user.company,
            is_active=True
        ).select_related('category', 'supplier').prefetch_related('variants')

        categoria_id = request.GET.get('categoria')
        query        = request.GET.get('q', '')
        talla        = request.GET.get('talla', '')
        orden        = request.GET.get('orden', 'nuevo')
        seccion      = request.GET.get('seccion', '')

        if categoria_id:
            productos = productos.filter(category_id=categoria_id)
        if query:
            productos = productos.filter(name__icontains=query)
        if talla:
            productos = productos.filter(variants__size=talla).distinct()
        if seccion == 'rebajas':
            productos = productos.filter(sale_price__isnull=False)
        if orden == 'precio_asc':
            productos = productos.order_by('sale_price')
        elif orden == 'precio_desc':
            productos = productos.order_by('-sale_price')
        else:
            productos = productos.order_by('-created_at')

        categorias  = Category.objects.filter(company=request.user.company)
        destacados  = Product.objects.filter(
            company=request.user.company, is_active=True
        ).order_by('-created_at')[:4]

        context = {
            'productos':       productos,
            'categorias':      categorias,
            'destacados':      destacados,
            'categoria_activa':categoria_id,
            'query':           query,
            'talla_activa':    talla,
            'orden':           orden,
            'seccion':         seccion,
            'tallas':          ['XS','S','M','L','XL','XXL'],
        }
        return render(request, self.template_name, context)


class StoreProductoView(LoginRequiredMixin, View):
    template_name = 'vexora/sales/store-detail.html'

    def get(self, request, pk):
        producto    = get_object_or_404(Product, pk=pk, is_active=True, company=request.user.company)
        variantes   = producto.variants.all()
        relacionados= Product.objects.filter(
            category=producto.category,
            is_active=True,
            company=request.user.company
        ).exclude(pk=pk)[:4]

        context = {
            'producto':     producto,
            'variantes':    variantes,
            'relacionados': relacionados,
        }
        return render(request, self.template_name, context)

class StoreCarritoView(LoginRequiredMixin, View):
    template_name = 'vexora/sales/store-cart.html'

    def get(self, request):
        cart = get_or_create_cart(request)
        items = cart.items.select_related('product', 'variant').all()
        return render(request, self.template_name, {'cart': cart, 'items': items})


class StoreCheckoutView(LoginRequiredMixin, View):
    template_name = "vexora/sales/store-checkout.html"

    def get(self, request):
        cart = get_or_create_cart(request)

        items = cart.items.select_related(
            "product",
            "variant",
        ).all()

        if not items.exists():
            messages.warning(
                request,
                "Tu carrito está vacío.",
            )
            return redirect("vexora:store_cart")

        return render(
            request,
            self.template_name,
            {
                "cart": cart,
                "items": items,
            },
        )

    def post(self, request):
        # Indica si el formulario fue enviado con fetch/AJAX.
        is_ajax = (
            request.headers.get("X-Requested-With")
            == "XMLHttpRequest"
        )

        cart = get_or_create_cart(request)

        items = list(
            cart.items.select_related(
                "product",
                "variant",
            ).all()
        )

        # Carrito vacío
        if not items:
            if is_ajax:
                return JsonResponse(
                    {
                        "ok": False,
                        "message": "Tu carrito está vacío.",
                    },
                    status=400,
                )

            messages.error(
                request,
                "Tu carrito está vacío.",
            )
            return redirect("vexora:store_cart")

        # Datos enviados desde el checkout
        nombre = request.POST.get(
            "nombre",
            "",
        ).strip()

        email = request.POST.get(
            "email",
            "",
        ).strip()

        telefono = request.POST.get(
            "telefono",
            "",
        ).strip()

        direccion = request.POST.get(
            "direccion",
            "",
        ).strip()

        ciudad = request.POST.get(
            "ciudad",
            "",
        ).strip()

        cp = request.POST.get(
            "cp",
            "",
        ).strip()

        estado = request.POST.get(
            "estado",
            "",
        ).strip()

        notas = request.POST.get(
            "notas",
            "",
        ).strip()

        # Validar campos obligatorios
        if (
            not nombre
            or not email
            or not telefono
            or not direccion
        ):
            mensaje_error = (
                "Completa nombre, correo, teléfono "
                "y dirección."
            )

            if is_ajax:
                return JsonResponse(
                    {
                        "ok": False,
                        "message": mensaje_error,
                    },
                    status=400,
                )

            messages.error(
                request,
                mensaje_error,
            )

            return render(
                request,
                self.template_name,
                {
                    "cart": cart,
                    "items": items,
                },
            )

        company = request.user.company

        # Crear la venta
        sale = Sale.objects.create(
            company=company,
            customer_name=nombre,
            customer_email=email,
            customer_phone=telefono,
            notes=(
                f"Dirección: {direccion}\n"
                f"Ciudad: {ciudad}\n"
                f"Estado: {estado}\n"
                f"Código postal: {cp}\n"
                f"Notas: {notas}"
            ),
            status="pending",
            user=request.user,
        )

        total = 0

        # Crear los productos de la venta
        for item in items:
            product = item.product
            price = item.unit_price
            subtotal = item.subtotal

            variant_description = ""

            if item.variant:
                variant_description = (
                    f"Talla: {item.variant.size} | "
                    f"Color: {item.variant.color}"
                )

            SaleItem.objects.create(
                sale=sale,
                product=product,
                description=variant_description,
                quantity=item.quantity,
                unit_price=price,
                total_price=subtotal,
            )

            total += subtotal

        # Guardar totales
        sale.subtotal = total
        sale.total = total

        sale.save(
            update_fields=[
                "subtotal",
                "total",
            ]
        )

        # Vaciar el carrito
        cart.items.all().delete()

        # URL de confirmación
        confirmation_url = reverse(
            "vexora:store_confirmation",
            kwargs={
                "pk": sale.pk,
            },
        )

        # URL del PDF
        pdf_url = reverse(
            "vexora:store_order_pdf",
            kwargs={
                "pk": sale.pk,
            },
        )

        # Intentar enviar el PDF por correo
        email_sent = False

        try:
            # Generar el mismo PDF que se abre en el navegador
            pdf_response = store_order_pdf(
                request,
                sale.pk,
            )

            pdf_content = pdf_response.content

            correo_pedido = EmailMessage(
                subject=(
                    f"Comprobante del pedido #{sale.pk}"
                ),
                body=(
                    f"Hola {nombre},\n\n"
                    f"Tu pedido #{sale.pk} fue registrado "
                    f"correctamente.\n\n"
                    f"Total del pedido: ${sale.total}\n\n"
                    f"Adjuntamos tu comprobante en formato "
                    f"PDF.\n\n"
                    f"Guarda, imprime o muestra el PDF en la "
                    f"tienda para validar tu compra y recibir "
                    f"tu pedido.\n\n"
                    f"Conserva el comprobante hasta recibir "
                    f"todos tus productos.\n\n"
                    f"Gracias por tu compra."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )

            correo_pedido.attach(
                filename=f"pedido_{sale.pk}.pdf",
                content=pdf_content,
                mimetype="application/pdf",
            )

            resultado_envio = correo_pedido.send(
                fail_silently=False,
            )

            email_sent = resultado_envio == 1

        except Exception:
            # El pedido no se pierde aunque el correo falle.
            logger.exception(
                "No se pudo enviar el correo del pedido %s",
                sale.pk,
            )

        # Respuesta para tu JavaScript fetch/AJAX
        if is_ajax:
            return JsonResponse(
                {
                    "ok": True,
                    "message": (
                        "Pedido registrado correctamente."
                    ),
                    "confirmation_url": confirmation_url,
                    "pdf_url": pdf_url,
                    "email_sent": email_sent,
                }
            )

        # Respuesta cuando no se utiliza JavaScript
        messages.success(
            request,
            "Tu pedido fue registrado correctamente.",
        )

        return redirect(confirmation_url)
def formato_dinero(valor):
    try:
        return f"${Decimal(valor):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


@login_required
def store_order_pdf(request, pk):
    sale = get_object_or_404(Sale, pk=pk)

    # Evita que un cliente descargue pedidos ajenos.
    if (
        not request.user.is_superuser
        and getattr(sale, "user_id", None) != request.user.id
    ):
        raise PermissionDenied(
            "No tienes permiso para consultar este pedido."
        )

    items = (
        SaleItem.objects
        .filter(sale=sale)
        .select_related("product")
    )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"Pedido {sale.pk}",
        author="Vexora",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PedidoTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=14,
    )

    subtitle_style = ParagraphStyle(
        "PedidoSubtitle",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=8,
        spaceAfter=7,
    )

    normal_style = ParagraphStyle(
        "PedidoNormal",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )

    story = []

    story.append(
        Paragraph("Comprobante de pedido", title_style)
    )

    story.append(
        Paragraph(
            f"<b>Número de pedido:</b> #{sale.pk}",
            normal_style,
        )
    )

    fecha = getattr(sale, "created_at", None)

    if fecha:
        story.append(
            Paragraph(
                f"<b>Fecha:</b> "
                f"{fecha.strftime('%d/%m/%Y %H:%M')}",
                normal_style,
            )
        )

    cliente = getattr(sale, "customer_name", "") or (
        request.user.get_full_name()
        or request.user.username
    )

    correo = getattr(sale, "customer_email", "") or (
        request.user.email
    )

    telefono = getattr(sale, "customer_phone", "")

    story.append(Spacer(1, 7))
    story.append(Paragraph("Datos del cliente", subtitle_style))

    story.append(
        Paragraph(
            f"<b>Cliente:</b> {cliente}",
            normal_style,
        )
    )

    if correo:
        story.append(
            Paragraph(
                f"<b>Correo:</b> {correo}",
                normal_style,
            )
        )

    if telefono:
        story.append(
            Paragraph(
                f"<b>Teléfono:</b> {telefono}",
                normal_style,
            )
        )

    notas = getattr(sale, "notes", "")

    if notas:
        notas_pdf = str(notas).replace("\n", "<br/>")

        story.append(
            Paragraph(
                f"<b>Información de envío:</b><br/>{notas_pdf}",
                normal_style,
            )
        )

    story.append(Spacer(1, 12))
    story.append(Paragraph("Detalles del pedido", subtitle_style))

    table_data = [
        [
            Paragraph("<b>Producto</b>", normal_style),
            Paragraph("<b>Cantidad</b>", normal_style),
            Paragraph("<b>Precio</b>", normal_style),
            Paragraph("<b>Subtotal</b>", normal_style),
        ]
    ]

    total_calculado = Decimal("0.00")

    for item in items:
        product = getattr(item, "product", None)
        product_name = getattr(
            product,
            "name",
            "Producto",
        )

        description = getattr(item, "description", "")
        quantity = getattr(item, "quantity", 0)
        unit_price = getattr(
            item,
            "unit_price",
            Decimal("0.00"),
        )

        subtotal = getattr(item, "total_price", None)

        if subtotal is None:
            subtotal = Decimal(quantity) * Decimal(unit_price)

        total_calculado += Decimal(subtotal)

        product_text = product_name

        if description:
            product_text += f"<br/><font size='7'>{description}</font>"

        table_data.append(
            [
                Paragraph(product_text, normal_style),
                str(quantity),
                formato_dinero(unit_price),
                formato_dinero(subtotal),
            ]
        )

    products_table = Table(
        table_data,
        colWidths=[
            84 * mm,
            24 * mm,
            31 * mm,
            31 * mm,
        ],
        repeatRows=1,
    )

    products_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#2563EB"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F8FAFC"),
                    ],
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(products_table)
    story.append(Spacer(1, 14))

    total = getattr(sale, "total", None)

    if total is None:
        total = total_calculado

    total_table = Table(
        [
            [
                Paragraph("<b>Total del pedido:</b>", normal_style),
                Paragraph(
                    f"<b>{formato_dinero(total)}</b>",
                    normal_style,
                ),
            ]
        ],
        colWidths=[130 * mm, 40 * mm],
    )

    total_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#E2E8F0"),
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, 0),
                    "RIGHT",
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    colors.HexColor("#94A3B8"),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
            ]
        )
    )

    story.append(total_table)
    story.append(Spacer(1, 18))

    story.append(
        Paragraph(
            "Gracias por realizar tu pedido.",
            ParagraphStyle(
                "Gracias",
                parent=normal_style,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#64748B"),
            ),
        )
    )

    document.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(
        pdf,
        content_type="application/pdf",
    )

    response["Content-Disposition"] = (
        f'inline; filename="pedido_{sale.pk}.pdf"'
    )

    return response
class CartUpdateView(LoginRequiredMixin, View):
    def post(self, request, item_id):
        cart = get_or_create_cart(request)
        item = get_object_or_404(CartItem, pk=item_id, cart=cart)
        delta = int(request.POST.get('delta', 0))
        item.quantity = max(1, item.quantity + delta)
        item.save()
        return JsonResponse({
            'ok': True,
            'quantity': item.quantity,
            'subtotal': float(item.subtotal),
            'total': float(cart.total),
            'total_items': cart.total_items,
        })


class CartRemoveView(LoginRequiredMixin, View):
    def post(self, request, item_id):
        cart = get_or_create_cart(request)
        CartItem.objects.filter(pk=item_id, cart=cart).delete()
        return JsonResponse({
            'ok': True,
            'total': float(cart.total),
            'total_items': cart.total_items,
        })

class StoreConfirmacionView(LoginRequiredMixin, View):
    template_name = 'vexora/sales/store-confirm.html'

    def get(self, request, pk):
        sale  = get_object_or_404(Sale, pk=pk, company=request.user.company)
        items = sale.items.select_related('product').all()
        return render(request, self.template_name, {'sale': sale, 'items': items})
    
    from django.utils import timezone

class ProductQuickCreateView(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            'categories': Category.objects.filter(company=request.user.company)
        }
        return render(request, 'vexora/products/quick_create_modal.html', context)

    def post(self, request):
        name  = request.POST.get('name', '').strip()
        price = request.POST.get('price', '0')
        stock = request.POST.get('stock', '0')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')

        if not name:
            return JsonResponse({'ok': False, 'error': 'El nombre es obligatorio.'}, status=400)

        try:
            price = float(price)
        except ValueError:
            price = 0

        try:
            stock = int(stock)
        except ValueError:
            stock = 0

        company = request.user.company

        default_supplier, _ = Supplier.objects.get_or_create(
            company=company,
            name='Proveedor general',
            defaults={'address': 'N/A'}
        )

        category = None
        if category_id:
            category = Category.objects.filter(pk=category_id, company=company).first()

        product = Product.objects.create(
            name=name,
            company=company,
            supplier=default_supplier,
            category=category,
            price=price,
            sale_price=price,
            stock=stock,
            purchase_date=timezone.now().date(),
            image=image,
            is_active=True,
        )

        return JsonResponse({'ok': True, 'id': product.id, 'name': product.name})
    

def get_or_create_cart(request):
    return Cart.objects.get_or_create(company=request.user.company, user=request.user)[0]

class CartCountView(LoginRequiredMixin, View):
    def get(self, request):
        cart = get_or_create_cart(request)
        return JsonResponse({'total_items': cart.total_items})
@login_required
@require_POST
def cart_add(request):
    product_id = request.POST.get("product_id")
    variant_id = request.POST.get("variant_id") or None
    quantity = int(request.POST.get("quantity", 1))

    try:
        product = Product.objects.get(pk=product_id, company=request.user.company, is_active=True)
    except Product.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Producto no encontrado"}, status=404)

    variant = None
    if variant_id:
        try:
            variant = ProductVariant.objects.get(pk=variant_id, product=product)
        except ProductVariant.DoesNotExist:
            variant = None

    cart = get_or_create_cart(request)

    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, variant=variant,
        defaults={'quantity': quantity}
    )
    if not created:
        item.quantity += quantity
        item.save()

    return JsonResponse({
        "ok": True,
        "nombre": product.name,
        "cantidad": item.quantity,
        "precio": float(product.sale_price or product.price),
        "total_items": cart.total_items,
    })
    
    