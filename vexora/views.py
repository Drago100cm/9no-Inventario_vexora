from django.contrib.auth.decorators import login_required
from urllib import request
from django.contrib.auth import  login, logout
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from .forms import *
from xml.sax.saxutils import escape
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView,RedirectView, DetailView, TemplateView
from vexora.models import *
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import send_mail
import logging
from django.db import transaction, models
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
from django.db.models import F, Q
from datetime import datetime
from django.views.decorators.http import require_POST
from io import BytesIO
from .services.report_service import ReportService
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from io import BytesIO
import json
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
        user = form.save(commit=False)
        user.save()

        return super().form_valid(form)
        
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
    
# --------------------- Registro ----------------------

class CustomerRegisterView(CreateView):
    model = CustomUser
    form_class = CustomerRegisterForm
    template_name = "Accounts/customer_register.html"
    success_url = settings.LOGIN_REDIRECT_URL

    def dispatch(self, request, *args, **kwargs):
        self.company = get_object_or_404(
            Company,
            slug=self.kwargs["slug"]
        )

        return super().dispatch(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company"] = self.company
        return context


    def form_valid(self, form):
        user = form.save(commit=False)

        user.user_type = "customer"
        user.is_client = True
        user.save()

        customer_role, _ = Role.objects.get_or_create(
            name="Cliente"
        )

        CompanyMember.objects.create(
            company=self.company,
            user=user,
            role=customer_role
        )

        return super().form_valid(form)

class ClientsListView(LoginRequiredMixin, ListView):
    template_name = "vexora/users/client_list.html"

    def get(self, request):

        if request.user.is_superuser:
            list_user = CustomUser.objects.filter(
                is_client=True
            )

        else:
            companies = Company.objects.filter(
                Q(owner=request.user) |
                Q(members=request.user)
            ).distinct()

            list_user = CustomUser.objects.filter(
                companies__in=companies,
                is_client=True
            ).distinct()

        data = {
            "list_user": list_user
        }

        if request.user.is_superuser or request.user.has_perm("vexora.view_customuser"):
            return render(request, self.template_name, data)

        return redirect("vexora:home")
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
    template_name = "vexora/subscriptions/plans.html"
    context_object_name = "plans"
    ordering = ["id"]

    def dispatch(self, request, *args, **kwargs):
        # Solo el superusuario puede acceder
        if not request.user.is_superuser:
            messages.error(
                request,
                "❌ No tienes permisos para acceder a la administración de planes."
            )
            return redirect("vexora:home")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        ensure_default_plans()  # Crea los planes por defecto si no existen
        return Plan.objects.filter(active=True).order_by("id")

class PlanCreateView(LoginRequiredMixin, CreateView):
    model = Plan
    form_class = PlanesForm
    template_name = "vexora/subscriptions/plan_create.html"
    success_url = reverse_lazy("vexora:plan_list")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(
                request,
                "❌ No tienes permisos para crear planes."
            )
            return redirect("vexora:home")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(
            self.request,
            f"✅ Plan '{form.instance.name}' creado correctamente."
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Crear nuevo plan"
        return context
    
class PlanUpdateView(LoginRequiredMixin, UpdateView):
    model = Plan
    form_class = PlanesForm
    template_name = "vexora/subscriptions/plan_edit.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(
                request,
                "❌ No tienes permisos para editar planes."
            )
            return redirect("vexora:home")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"✅ Plan '{form.instance.name}' actualizado correctamente."
        )
        return response

    def get_success_url(self):
        return reverse("vexora:plan_list")

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

        if not self.request.user.has_perm("vexora.add_customuser"):
            messages.error(
                self.request,
                "❌ No tienes permisos para crear usuarios."
            )
            return redirect("vexora:user_list")

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

def delete_product(request, id):
    company = request.user.company
    product = get_object_or_404(Product, id=id, company=company)
    product.delete()
    messages.success(request, "✅ Producto eliminado correctamente!")
    return redirect('vexora:list_products')



# =====================================
# SALES VIEWS (Ventas)
# =====================================



class SalesListView(LoginRequiredMixin, ListView):
    model = Sale
    template_name = "vexora/sales/store.html"
    context_object_name = "sales"

    def get_queryset(self):
        return Sale.objects.filter(
            company=self.request.user.company,
            is_store=True
        ).order_by("-date")
        
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

def delete_sale(request, pk):
    company = request.user.company
    sale = get_object_or_404(Sale, id=pk, company=company)
    sale.delete()
    messages.success(request, "✅ Venta eliminada correctamente!")
    return redirect('vexora:sales_list')
    
# ============================================
# MEMBERS VIEWS
# ============================================
class MembersView(LoginRequiredMixin, ListView):
    model = CompanyMember
    template_name = "vexora/members/list.html"
    context_object_name = "members"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm("vexora.view_companymember"):
            messages.error(request, "❌ No tienes permisos para acceder a esta sección.")
            return redirect("vexora:home")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        company = self.request.user.company

        if not company:
            return CompanyMember.objects.none()

        return (
            CompanyMember.objects
            .filter(company=company)
            .select_related("user", "role")
            .order_by("user__username")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        company = self.request.user.company

        context["total_users"] = (
            CompanyMember.objects.filter(company=company).count()
            if company else 0
        )

        return context

class MembersCreateView(LoginRequiredMixin, CreateView):
    model = CompanyMember
    form_class = MemberCreateForm
    template_name = "vexora/members/create.html"

    def dispatch(self, request, *args, **kwargs):

        # Verificar permiso
        if not request.user.has_perm("vexora.add_companymember"):
            messages.error(request, "❌ No tienes permisos para crear colaboradores.")
            return redirect("vexora:list_members")

        company = request.user.company

        if not company:
            messages.error(request, "❌ No tienes una empresa asignada.")
            return redirect("vexora:list_members")

        # Verificar suscripción
        if not hasattr(company, "subscription"):
            messages.error(request, "❌ La empresa no tiene una suscripción activa.")
            return redirect("vexora:list_members")

        subscription = company.subscription
        plan = subscription.plan

        # Contar colaboradores actuales
        total_members = CompanyMember.objects.filter(company=company).count()

        # Validar límite del plan
        if total_members >= plan.max_collaborators:
            messages.error(
                request,
                f"❌ Tu plan '{plan.name}' permite un máximo de {plan.max_collaborators} colaboradores."
            )
            return redirect("vexora:list_members")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.user.company

        response = super().form_valid(form)

        member_user = form.instance.user
        full_name = (
            f"{member_user.first_name} {member_user.last_name}".strip()
            or member_user.username
        )

        messages.success(
            self.request,
            f"✅ Miembro '{full_name}' creado correctamente."
        )

        return response

    def get_success_url(self):
        return reverse("vexora:list_members")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Crear Miembro"
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


def delete_member(request, id):
    company = request.user.company
    member = get_object_or_404(CompanyMember, id=id, company=company)

    member_name = member.user.get_full_name() or member.user.username

    member.delete()

    messages.success(
        request,
        f"✅ Miembro '{member_name}' eliminado correctamente!"
    )

    return redirect("vexora:list_members")

# =====================================
# SALES MAIN (CRUD Frontend)
# =====================================

class SalesMainListView(LoginRequiredMixin, TemplateView):
    template_name = "vexora/sales_main/list.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener todas las ventas de la empresa del usuario
        context['sales'] = Sale.objects.filter(
            company=self.request.user.company
        ).order_by('-created_at')  # Ordenar por fecha de creación descendente
        return context

class SalesMainCreateView(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            'categories': Category.objects.filter(company=request.user.company),
            'products': Product.objects.filter(
                company=request.user.company,
                is_active=True
            ).select_related('category')
        }
        return render(request, 'vexora/sales_main/create.html', context)
    
    def post(self, request):
        try:
            # Log para depuración
            print("=== POST /sales-main/create/ ===")
            print("Request body:", request.body)
            
            data = json.loads(request.body)
            print("Datos parseados:", data)
            
            # Validar que haya items
            if not data.get('items'):
                return JsonResponse({'success': False, 'error': 'No hay productos en la venta'}, status=400)
            
            # Validar que items sea una lista
            if not isinstance(data['items'], list):
                return JsonResponse({'success': False, 'error': 'Formato de items inválido'}, status=400)
            
            if len(data['items']) == 0:
                return JsonResponse({'success': False, 'error': 'La lista de productos está vacía'}, status=400)
            
            # Validar cada item
            for idx, item_data in enumerate(data['items']):
                if not item_data.get('product_id'):
                    return JsonResponse({'success': False, 'error': f'Item {idx}: product_id faltante'}, status=400)
                if not item_data.get('quantity') or int(item_data.get('quantity', 0)) <= 0:
                    return JsonResponse({'success': False, 'error': f'Item {idx}: cantidad inválida'}, status=400)
            
            # Crear la venta
            sale = Sale.objects.create(
                company=request.user.company,
                customer_name=data.get('customer_name', ''),
                customer_email=data.get('customer_email', ''),
                customer_phone=data.get('customer_phone', ''),
                user=request.user,
                date=data.get('date', timezone.now()),
                status=data.get('status', 'draft'),
                subtotal=Decimal(str(data.get('subtotal', 0))),
                tax=Decimal(str(data.get('tax', 0))),
                discount=Decimal(str(data.get('discount', 0))),
                total=Decimal(str(data.get('total', 0))),
                notes=data.get('notes', '')
            )
            
            # Crear los items de la venta
            for idx, item_data in enumerate(data['items']):
                print(f"Procesando item {idx}:", item_data)
                
                try:
                    product = Product.objects.get(id=item_data['product_id'], company=request.user.company)
                except Product.DoesNotExist:
                    return JsonResponse({'success': False, 'error': f'Producto {item_data["product_id"]} no encontrado'}, status=400)
                
                quantity = int(item_data.get('quantity', 0))
                unit_price = Decimal(str(item_data.get('unit_price', 0)))
                discount = Decimal(str(item_data.get('discount', 0)))
                
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount=discount
                )
                
                # Actualizar stock del producto
                if product.stock is not None:
                    product.stock -= quantity
                    product.save()
            
            return JsonResponse({'success': True, 'sale_id': sale.id, 'invoice_number': sale.invoice_number})
            
        except json.JSONDecodeError as e:
            print("Error JSON:", e)
            return JsonResponse({'success': False, 'error': f'Error en formato JSON: {str(e)}'}, status=400)
        except Exception as e:
            print("Error general:", e)
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

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
class SalesMainUpdateView(LoginRequiredMixin, View):
    def get(self, request):
        sale_id = request.GET.get('id')
        if not sale_id:
            return JsonResponse({'success': False, 'error': 'ID de venta no proporcionado'}, status=400)
        
        try:
            sale = Sale.objects.get(id=sale_id, company=request.user.company)
        except Sale.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Venta no encontrada'}, status=404)
        
        # Obtener los items de la venta con los productos
        sale_items = sale.items.all().select_related('product')
        
        # Preparar datos para JSON
        sale_items_data = []
        for item in sale_items:
            sale_items_data.append({
                'product_id': item.product.id,
                'product_name': item.product.name,
                'sku': item.product.sku or 'Sin SKU',
                'stock': item.product.stock or 0,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'discount': float(item.discount),
                'subtotal': float(item.total_price)
            })
        
        # Obtener todos los productos activos
        products = Product.objects.filter(
            company=request.user.company,
            is_active=True
        ).select_related('category')
        
        context = {
            'sale': sale,
            'sale_items': sale_items,
            'sale_items_json': json.dumps(sale_items_data),
            'categories': Category.objects.filter(company=request.user.company),
            'products': products,  # ← Asegurar que esto está pasando
        }
        return render(request, 'vexora/sales_main/update.html', context)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            sale_id = data.get('sale_id')
            
            if not sale_id:
                return JsonResponse({'success': False, 'error': 'ID de venta no proporcionado'}, status=400)
            
            try:
                sale = Sale.objects.get(id=sale_id, company=request.user.company)
            except Sale.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Venta no encontrada'}, status=404)
            
            # Actualizar datos de la venta
            sale.customer_name = data.get('customer_name', '')
            sale.customer_email = data.get('customer_email', '')
            sale.customer_phone = data.get('customer_phone', '')
            sale.status = data.get('status', 'draft')
            sale.notes = data.get('notes', '')
            sale.subtotal = Decimal(str(data.get('subtotal', 0)))
            sale.tax = Decimal(str(data.get('tax', 0)))
            sale.discount = Decimal(str(data.get('discount', 0)))
            sale.total = Decimal(str(data.get('total', 0)))
            sale.save()
            
            # Eliminar items existentes
            sale.items.all().delete()
            
            # Crear nuevos items
            for item_data in data.get('items', []):
                product = Product.objects.get(id=item_data['product_id'], company=request.user.company)
                quantity = int(item_data['quantity'])
                unit_price = Decimal(str(item_data['unit_price']))
                discount = Decimal(str(item_data.get('discount', 0)))
                
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount=discount
                )
            
            return JsonResponse({'success': True, 'sale_id': sale.id})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
def delete_sale(request, pk):
    company = request.user.company
    sale = get_object_or_404(Sale, id=pk, company=company)
    sale.delete()
    messages.success(request, "✅ Venta eliminada correctamente!")
    return redirect('vexora:sales_main_list')
# ============================================
# STORE PÚBLICA
# ============================================

def get_or_create_cart(request):
    """
    Obtiene o crea el carrito del usuario para su empresa.
    """

    company = getattr(request.user, "company", None)

    # Respaldo para usuarios vinculados mediante CompanyMember
    if not company:
        membership = (
            CompanyMember.objects
            .select_related("company")
            .filter(user=request.user)
            .first()
        )

        if membership:
            company = membership.company

    if not company:
        raise ValueError(
            "El usuario no tiene una empresa vinculada."
        )

    cart, created = Cart.objects.get_or_create(
        company=company,
        user=request.user,
    )

    return cart

class StoreHomeView(LoginRequiredMixin, View):
    template_name = 'vexora/sales/store.html'

    def get(self, request):
        productos = Product.objects.filter(
            company=request.user.company,
            is_store=True
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


class StoreProductoView(View):
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
class StoreConfirmacionView(LoginRequiredMixin, DetailView):
    model = Sale
    template_name = "vexora/sales/store-confirm.html"
    context_object_name = "sale"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        company = getattr(
            self.request.user,
            "company",
            None,
        )

        # Buscar empresa mediante CompanyMember
        if not company:
            membership = (
                CompanyMember.objects
                .select_related("company")
                .filter(user=self.request.user)
                .first()
            )

            if membership:
                company = membership.company

        if not company:
            return Sale.objects.none()

        return Sale.objects.filter(
            company=company,
            user=self.request.user,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["items"] = (
            self.object.items
            .select_related("product")
            .all()
        )

        return context
@login_required
def store_order_pdf(request, pk):
    sale = get_object_or_404(
        Sale.objects.select_related(
            "company",
            "user",
        ),
        pk=pk,
    )

    # ==========================================
    # VALIDAR QUE EL USUARIO PUEDA VER EL PEDIDO
    # ==========================================

    if not request.user.is_superuser:
        is_owner = sale.user_id == request.user.id

        can_view_company_sales = (
            request.user.is_staff
            or request.user.has_perm("vexora.view_sale")
        )

        user_company = getattr(
            request.user,
            "company",
            None,
        )

        if not user_company:
            membership = (
                CompanyMember.objects
                .select_related("company")
                .filter(user=request.user)
                .first()
            )

            if membership:
                user_company = membership.company

        belongs_to_company = (
            user_company
            and sale.company_id == user_company.id
        )

        if not is_owner and not (
            can_view_company_sales
            and belongs_to_company
        ):
            raise PermissionDenied(
                "No tienes permiso para consultar este pedido."
            )

    items = (
        SaleItem.objects
        .filter(sale=sale)
        .select_related("product")
        .order_by("id")
    )

    # ==========================================
    # CREAR RESPUESTA PDF
    # ==========================================

    response = HttpResponse(
        content_type="application/pdf",
    )

    response["Content-Disposition"] = (
        f'inline; filename="pedido_{sale.pk}.pdf"'
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
        "OrderTitle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=15,
    )

    subtitle_style = ParagraphStyle(
        "OrderSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        spaceAfter=15,
    )

    story = []

    company_name = (
        sale.company.name
        if sale.company
        else "Vexora"
    )

    story.append(
        Paragraph(
            escape(company_name),
            title_style,
        )
    )

    story.append(
        Paragraph(
            f"Comprobante del pedido #{sale.pk}",
            subtitle_style,
        )
    )

    story.append(Spacer(1, 8))

    customer_data = [
        [
            Paragraph("<b>Cliente</b>", styles["Normal"]),
            Paragraph(
                escape(
                    sale.customer_name
                    or "Sin nombre"
                ),
                styles["Normal"],
            ),
        ],
        [
            Paragraph("<b>Correo</b>", styles["Normal"]),
            Paragraph(
                escape(
                    sale.customer_email
                    or "No registrado"
                ),
                styles["Normal"],
            ),
        ],
        [
            Paragraph("<b>Teléfono</b>", styles["Normal"]),
            Paragraph(
                escape(
                    sale.customer_phone
                    or "No registrado"
                ),
                styles["Normal"],
            ),
        ],
        [
            Paragraph("<b>Fecha</b>", styles["Normal"]),
            Paragraph(
                sale.date.strftime(
                    "%d/%m/%Y %H:%M"
                ),
                styles["Normal"],
            ),
        ],
        [
            Paragraph("<b>Estado</b>", styles["Normal"]),
            Paragraph(
                escape(
                    sale.get_status_display()
                ),
                styles["Normal"],
            ),
        ],
    ]

    customer_table = Table(
        customer_data,
        colWidths=[
            40 * mm,
            125 * mm,
        ],
    )

    customer_table.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey,
            ),
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#F3F4F6"),
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
        ])
    )

    story.append(customer_table)
    story.append(Spacer(1, 16))

    # ==========================================
    # TABLA DE PRODUCTOS
    # ==========================================

    products_data = [
        [
            Paragraph("<b>Producto</b>", styles["Normal"]),
            Paragraph("<b>Cantidad</b>", styles["Normal"]),
            Paragraph("<b>Precio</b>", styles["Normal"]),
            Paragraph("<b>Total</b>", styles["Normal"]),
        ]
    ]

    for item in items:
        product_name = (
            item.product.name
            if item.product
            else item.description
            or "Producto"
        )

        description = item.description or ""

        if description:
            product_name = (
                f"{product_name}<br/>"
                f"<font size='8'>"
                f"{escape(description)}"
                f"</font>"
            )
        else:
            product_name = escape(product_name)

        products_data.append([
            Paragraph(
                product_name,
                styles["Normal"],
            ),
            str(item.quantity),
            f"${item.unit_price:,.2f}",
            f"${item.total_price:,.2f}",
        ])

    products_table = Table(
        products_data,
        colWidths=[
            90 * mm,
            25 * mm,
            30 * mm,
            30 * mm,
        ],
        repeatRows=1,
    )

    products_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#111827"),
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
                colors.grey,
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F9FAFB"),
                ],
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                6,
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
        ])
    )

    story.append(products_table)
    story.append(Spacer(1, 16))

    totals_data = [
        [
            "Subtotal:",
            f"${sale.subtotal:,.2f}",
        ],
        [
            "Descuento:",
            f"${sale.discount:,.2f}",
        ],
        [
            "Impuesto:",
            f"${sale.tax:,.2f}",
        ],
        [
            "Total:",
            f"${sale.total:,.2f}",
        ],
    ]

    totals_table = Table(
        totals_data,
        colWidths=[
            130 * mm,
            45 * mm,
        ],
    )

    totals_table.setStyle(
        TableStyle([
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "RIGHT",
            ),
            (
                "FONTNAME",
                (0, -1),
                (-1, -1),
                "Helvetica-Bold",
            ),
            (
                "FONTSIZE",
                (0, -1),
                (-1, -1),
                12,
            ),
            (
                "LINEABOVE",
                (0, -1),
                (-1, -1),
                1,
                colors.black,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
        ])
    )

    story.append(totals_table)

    if sale.notes:
        story.append(Spacer(1, 16))
        story.append(
            Paragraph(
                "<b>Información del pedido</b>",
                styles["Heading3"],
            )
        )
        story.append(
            Paragraph(
                escape(sale.notes).replace(
                    "\n",
                    "<br/>",
                ),
                styles["Normal"],
            )
        )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "Gracias por tu compra.",
            subtitle_style,
        )
    )

    document.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    response.write(pdf)

    return response
def formato_dinero(valor):
    try:
        return f"${Decimal(valor):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"
class CartUpdateView(LoginRequiredMixin, View):

    def post(self, request, item_id):
        try:
            quantity = int(
                request.POST.get("quantity", 1)
            )

        except (TypeError, ValueError):
            return JsonResponse(
                {
                    "ok": False,
                    "error": "La cantidad no es válida.",
                },
                status=400,
            )

        if quantity < 1:
            return JsonResponse(
                {
                    "ok": False,
                    "error": (
                        "La cantidad debe ser mayor que cero."
                    ),
                },
                status=400,
            )

        try:
            cart = get_or_create_cart(request)

        except ValueError as error:
            return JsonResponse(
                {
                    "ok": False,
                    "error": str(error),
                },
                status=400,
            )

        try:
            with transaction.atomic():

                try:
                    item = (
                        CartItem.objects
                        .select_for_update()
                        .select_related(
                            "product",
                            "variant",
                        )
                        .get(
                            pk=item_id,
                            cart=cart,
                        )
                    )

                except CartItem.DoesNotExist:
                    return JsonResponse(
                        {
                            "ok": False,
                            "error": (
                                "El producto no existe "
                                "en tu carrito."
                            ),
                        },
                        status=404,
                    )

                old_quantity = item.quantity
                difference = quantity - old_quantity

                # No cambió la cantidad
                if difference == 0:
                    return JsonResponse(
                        {
                            "ok": True,
                            "quantity": item.quantity,
                            "subtotal": float(
                                item.subtotal
                            ),
                            "cart_total": float(
                                cart.total
                            ),
                            "total_items": (
                                cart.total_items
                            ),
                        }
                    )

                # ==================================
                # PRODUCTO CON VARIANTE
                # ==================================

                if item.variant_id:
                    variant = (
                        ProductVariant.objects
                        .select_for_update()
                        .get(
                            pk=item.variant_id,
                        )
                    )

                    available_stock = (
                        variant.stock
                        - variant.reserved_stock
                    )

                    if (
                        difference > 0
                        and difference > available_stock
                    ):
                        return JsonResponse(
                            {
                                "ok": False,
                                "error": (
                                    f"Solo puedes agregar "
                                    f"{available_stock} "
                                    "unidad(es) más."
                                ),
                                "stock_disponible": (
                                    available_stock
                                ),
                            },
                            status=400,
                        )

                    variant.reserved_stock += difference

                    if variant.reserved_stock < 0:
                        variant.reserved_stock = 0

                    variant.save(
                        update_fields=[
                            "reserved_stock",
                        ]
                    )

                    stock_remaining = (
                        variant.stock
                        - variant.reserved_stock
                    )

                # ==================================
                # PRODUCTO SIN VARIANTE
                # ==================================

                else:
                    product = (
                        Product.objects
                        .select_for_update()
                        .get(
                            pk=item.product_id,
                        )
                    )

                    available_stock = (
                        product.stock
                        - product.reserved_stock
                    )

                    if (
                        difference > 0
                        and difference > available_stock
                    ):
                        return JsonResponse(
                            {
                                "ok": False,
                                "error": (
                                    f"Solo puedes agregar "
                                    f"{available_stock} "
                                    "unidad(es) más."
                                ),
                                "stock_disponible": (
                                    available_stock
                                ),
                            },
                            status=400,
                        )

                    product.reserved_stock += difference

                    if product.reserved_stock < 0:
                        product.reserved_stock = 0

                    product.save(
                        update_fields=[
                            "reserved_stock",
                        ]
                    )

                    stock_remaining = (
                        product.stock
                        - product.reserved_stock
                    )

                # Actualizar cantidad del carrito
                item.quantity = quantity

                item.save(
                    update_fields=[
                        "quantity",
                    ]
                )

                return JsonResponse(
                    {
                        "ok": True,
                        "message": (
                            "Cantidad actualizada."
                        ),
                        "quantity": item.quantity,
                        "subtotal": float(
                            item.subtotal
                        ),
                        "cart_total": float(
                            cart.total
                        ),
                        "total_items": (
                            cart.total_items
                        ),
                        "stock_disponible": (
                            stock_remaining
                        ),
                        "agotado": (
                            stock_remaining <= 0
                        ),
                    }
                )

        except Exception as error:
            logger.exception(
                "Error al actualizar el carrito: %s",
                error,
            )

            return JsonResponse(
                {
                    "ok": False,
                    "error": (
                        "No fue posible actualizar "
                        "la cantidad."
                    ),
                },
                status=500,
            )
class CartRemoveView(LoginRequiredMixin, View):

    def post(self, request, item_id):
        try:
            cart = get_or_create_cart(request)

        except ValueError as error:
            return JsonResponse(
                {
                    "ok": False,
                    "error": str(error),
                },
                status=400,
            )

        try:
            with transaction.atomic():

                try:
                    item = (
                        CartItem.objects
                        .select_for_update()
                        .select_related(
                            "product",
                            "variant",
                        )
                        .get(
                            pk=item_id,
                            cart=cart,
                        )
                    )

                except CartItem.DoesNotExist:
                    return JsonResponse(
                        {
                            "ok": False,
                            "error": (
                                "El producto no existe "
                                "en tu carrito."
                            ),
                        },
                        status=404,
                    )

                quantity = item.quantity

                # Liberar reserva de una variante
                if item.variant_id:
                    variant = (
                        ProductVariant.objects
                        .select_for_update()
                        .get(pk=item.variant_id)
                    )

                    variant.reserved_stock = max(
                        variant.reserved_stock - quantity,
                        0,
                    )

                    variant.save(
                        update_fields=[
                            "reserved_stock",
                        ]
                    )

                    stock_remaining = (
                        variant.stock
                        - variant.reserved_stock
                    )

                # Liberar reserva del producto normal
                else:
                    product = (
                        Product.objects
                        .select_for_update()
                        .get(pk=item.product_id)
                    )

                    product.reserved_stock = max(
                        product.reserved_stock - quantity,
                        0,
                    )

                    product.save(
                        update_fields=[
                            "reserved_stock",
                        ]
                    )

                    stock_remaining = (
                        product.stock
                        - product.reserved_stock
                    )

                product_name = item.product.name

                # Eliminar del carrito
                item.delete()

                return JsonResponse(
                    {
                        "ok": True,
                        "message": (
                            f"{product_name} fue eliminado "
                            "del carrito."
                        ),
                        "total_items": cart.total_items,
                        "cart_total": float(cart.total),
                        "stock_disponible": stock_remaining,
                    }
                )

        except Exception as error:
            logger.exception(
                "Error al eliminar el producto del carrito: %s",
                error,
            )

            return JsonResponse(
                {
                    "ok": False,
                    "error": (
                        "No fue posible eliminar el producto "
                        "del carrito."
                    ),
                },
                status=500,
            )
class CartCountView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            cart = get_or_create_cart(request)

            return JsonResponse({
                "total_items": cart.total_items,
            })

        except ValueError:
            return JsonResponse({
                "total_items": 0,
            })

@login_required
@require_POST
def cart_add(request):
    product_id = request.POST.get("product_id")
    variant_id = request.POST.get("variant_id") or None

    # ==========================================
    # VALIDAR CANTIDAD
    # ==========================================

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        return JsonResponse(
            {
                "ok": False,
                "error": "La cantidad ingresada no es válida.",
            },
            status=400,
        )

    if quantity < 1:
        return JsonResponse(
            {
                "ok": False,
                "error": "La cantidad debe ser mayor que cero.",
            },
            status=400,
        )
    try:
        cart = get_or_create_cart(request)
        company = cart.company

    except ValueError as error:
        return JsonResponse(
        {
            "ok": False,
            "error": str(error),
        },
        status=400,
    )
   

    # ==========================================
    # TRANSACCIÓN SEGURA
    # ==========================================

    try:
        with transaction.atomic():

            # Bloqueamos el producto mientras se modifica el stock
            try:
                product = (
                    Product.objects
                    .select_for_update()
                    .get(
                        pk=product_id,
                        company=company,
                        is_active=True,
                    )
                )

            except Product.DoesNotExist:
                return JsonResponse(
                    {
                        "ok": False,
                        "error": "Producto no encontrado o no disponible.",
                    },
                    status=404,
                )

            variant = None
            product_has_variants = product.variants.exists()

            # ==========================================
            # VALIDAR VARIANTE
            # ==========================================

            if product_has_variants:

                if not variant_id:
                    return JsonResponse(
                        {
                            "ok": False,
                            "error": (
                                "Selecciona una talla y un color "
                                "antes de agregar el producto."
                            ),
                        },
                        status=400,
                    )

                try:
                    variant = (
                        ProductVariant.objects
                        .select_for_update()
                        .get(
                            pk=variant_id,
                            product=product,
                        )
                    )

                except ProductVariant.DoesNotExist:
                    return JsonResponse(
                        {
                            "ok": False,
                            "error": (
                                "La talla o el color seleccionado "
                                "no están disponibles."
                            ),
                        },
                        status=404,
                    )

                available_stock = (
                    variant.stock
                    - variant.reserved_stock
                )

            else:
                # No permitimos una variante ajena en productos simples
                if variant_id:
                    return JsonResponse(
                        {
                            "ok": False,
                            "error": (
                                "Este producto no utiliza variantes."
                            ),
                        },
                        status=400,
                    )

                available_stock = (
                    product.stock
                    - product.reserved_stock
                )

            # ==========================================
            # VALIDAR STOCK
            # ==========================================

            if available_stock <= 0:
                return JsonResponse(
                    {
                        "ok": False,
                        "error": "Este producto está agotado.",
                        "stock_disponible": 0,
                    },
                    status=400,
                )

            if quantity > available_stock:
                return JsonResponse(
                    {
                        "ok": False,
                        "error": (
                            f"Solo hay {available_stock} "
                            "unidad(es) disponibles."
                        ),
                        "stock_disponible": available_stock,
                    },
                    status=400,
                )
            # Bloquear el artículo si ya existe
            item = (
                CartItem.objects
                .select_for_update()
                .filter(
                    cart=cart,
                    product=product,
                    variant=variant,
                )
                .first()
            )

            if item:
                item.quantity += quantity
                item.save(
                    update_fields=[
                        "quantity",
                    ]
                )

            else:
                item = CartItem.objects.create(
                    cart=cart,
                    product=product,
                    variant=variant,
                    quantity=quantity,
                )

            # ==========================================
            # RESERVAR STOCK
            # ==========================================

            if variant:
                variant.reserved_stock += quantity

                variant.save(
                    update_fields=[
                        "reserved_stock",
                    ]
                )

                stock_remaining = (
                    variant.stock
                    - variant.reserved_stock
                )

            else:
                product.reserved_stock += quantity

                product.save(
                    update_fields=[
                        "reserved_stock",
                    ]
                )

                stock_remaining = (
                    product.stock
                    - product.reserved_stock
                )

            return JsonResponse(
                {
                    "ok": True,
                    "message": (
                        f"{product.name} se agregó al carrito."
                    ),
                    "nombre": product.name,
                    "cantidad_agregada": quantity,
                    "cantidad_carrito": item.quantity,
                    "precio": float(
                        product.sale_price
                        or product.price
                    ),
                    "stock_disponible": stock_remaining,
                    "agotado": stock_remaining <= 0,
                    "total_items": cart.total_items,
                }
            )

    except Exception:
        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "No fue posible agregar el producto. "
                    "Inténtalo nuevamente."
                ),
            },
            status=500,
        )

#===============================esta por verse si funciona bien========================================
from django.db.models import Count, Sum, Q
from django.core.cache import cache


class DashboardView(LoginRequiredMixin, TemplateView,):
    template_name = "partials/dashboard.html"

    def get_company(self):
        return self.request.user.company

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        company = self.get_company()

        # ==========================================
        # EMPRESA
        # ==========================================

        context["company"] = company

        # Si el usuario no tiene empresa, mostrar únicamente el botón para crearla
        if not company:
            context["subscription"] = None
            context["products_count"] = 0
            context["members_count"] = 0
            context["suppliers_count"] = 0
            context["sales_count"] = 0
            context["sales_total"] = 0
            context["categories_count"] = 0
            context["low_stock"] = 0
            context["recent_products"] = []
            context["recent_sales"] = []
            return context

        # ==========================================
        # SUSCRIPCIÓN
        # ==========================================
        try:
            subscription = company.subscription
        except Subscription.DoesNotExist:
            subscription = None

        context["subscription"] = subscription

        if subscription:
            today = timezone.now().date()
            context["subscription_expired"] = (
                subscription.status != "active"
                or (
                    subscription.end_date
                    and subscription.end_date < today
                )
            )
        else:
            context["subscription_expired"] = True

        # ==========================================
        # PRODUCTOS
        # ==========================================
        products = Product.objects.filter(company=company)

        context["products_count"] = products.count()
        context["low_stock"] = products.filter(
            stock__lte=F("min_stock"),
            is_active=True
        ).count()
        context["recent_products"] = products.order_by("-created_at")[:5]

        # ==========================================
        # CATEGORÍAS
        # ==========================================
        categories = Category.objects.filter(company=company)

        context["categories_count"] = categories.count()

        # ==========================================
        # PROVEEDORES
        # ==========================================
        suppliers = Supplier.objects.filter(company=company)

        context["suppliers_count"] = suppliers.count()

        # ==========================================
        # MIEMBROS
        # ==========================================
        members = CompanyMember.objects.filter(company=company)

        context["members_count"] = members.count()

        # ==========================================
        # VENTAS
        # ==========================================
        sales = Sale.objects.filter(company=company)
        completed_sales = sales.filter(status="completed")

        context["sales_count"] = completed_sales.count()
        context["sales_total"] = (
            completed_sales.aggregate(total=Sum("total"))["total"] or 0
        )
        context["recent_sales"] = completed_sales.order_by("-date")[:5]

        return context

# ============================================
# REPORTES VIEWS
# ============================================

class ReportsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'vexora/reports/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        if not company:
            context['error'] = 'No tienes una empresa asociada'
            return context
        
        try:
            service = ReportService(company)
            
            context.update({
                'total_products': service.get_total_products(),
                'products_status': service.get_products_by_status(),
                'inventory_value': service.get_inventory_value(),
                'total_revenue': service.get_total_revenue(days=30),
                'daily_average': service.get_daily_average_sales(),
                'best_sellers': service.get_best_selling_products(limit=5),
                'low_stock': service.get_low_stock_products(threshold=5)[:5],
                'out_of_stock': service.get_out_of_stock_products()[:5],
                'profit_summary': service.get_profit_summary(days=30),
                'sales_by_status': service.get_sales_by_status(),
                'page_title': 'Dashboard de Reportes',
            })
        except Exception as e:
            context['error'] = f'Error al generar reportes: {str(e)}'
        
        return context
    

class ProductReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'vexora/reports/product_reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        if not company:
            context['error'] = 'No tienes una empresa asociada'
            return context
        
        try:
            service = ReportService(company)
            
            context.update({
                'total_products': service.get_total_products(),
                'products_by_status': service.get_products_by_status(),
                'products_by_category': service.get_products_by_category(),
                'low_stock': service.get_low_stock_products(),
                'out_of_stock': service.get_out_of_stock_products(),
                'best_sellers': service.get_best_selling_products(),
                'worst_sellers': service.get_worst_selling_products(),
                'inventory_value': service.get_inventory_value(),
                'products_by_supplier': service.get_products_by_supplier(),
                'suppliers_summary': service.get_suppliers_summary(),
                'page_title': 'Reportes de Productos',
            })
        except Exception as e:
            context['error'] = f'Error al generar reportes: {str(e)}'
        
        return context

class SalesReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'vexora/reports/sales_reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        if not company:
            context['error'] = 'No tienes una empresa asociada'
            return context
        
        try:
            service = ReportService(company)
            
            context.update({
                'daily_sales': service.get_sales_by_period('day'),
                'weekly_sales': service.get_sales_by_period('week'),
                'monthly_sales': service.get_sales_by_period('month'),
                'yearly_sales': service.get_sales_by_period('year'),
                'total_revenue': service.get_total_revenue(),
                'daily_average': service.get_daily_average_sales(),
                'sales_by_seller': service.get_sales_by_seller(),
                'sales_by_client': service.get_sales_by_client(),
                'sales_by_status': service.get_sales_by_status(),
                'cancelled_sales': service.get_cancelled_sales(),
                'profit_summary': service.get_profit_summary(),
                'page_title': 'Reportes de Ventas',
            })
        except Exception as e:
            context['error'] = f'Error al generar reportes: {str(e)}'
        
        return context

class FinancialReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'vexora/reports/financial_reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        if not company:
            context['error'] = 'No tienes una empresa asociada'
            return context
        
        try:
            service = ReportService(company)
            
            context.update({
                'monthly_financial': service.get_financial_by_period('month'),
                'weekly_financial': service.get_financial_by_period('week'),
                'yearly_financial': service.get_financial_by_period('year'),
                'product_profitability': service.get_product_profitability(),
                'profit_summary': service.get_profit_summary(),
                'cancelled_sales': service.get_cancelled_sales(),
                'inventory_value': service.get_inventory_value(),
                'page_title': 'Reportes Financieros',
            })
        except Exception as e:
            context['error'] = f'Error al generar reportes: {str(e)}'
        
        return context
    
# ============================================
# EXPORTAR REPORTES A PDF CON REPORTLAB
# ============================================

class ExportReportsPDFView(LoginRequiredMixin, View):
    """Vista base para exportar reportes a PDF usando ReportLab con diseño profesional"""
    
    # Paleta de colores corporativa (Estilo SaaS Moderno)
    PRIMARY_COLOR = colors.HexColor('#1E293B')  # Slate 800 (Textos oscuros)
    ACCENT_COLOR = colors.HexColor('#2563EB')   # Blue 600 (Títulos, botones)
    SUCCESS_COLOR = colors.HexColor('#16A34A')  # Green 600 (Ingresos)
    DANGER_COLOR = colors.HexColor('#DC2626')   # Red 600 (Costos/Pérdidas)
    LIGHT_BG = colors.HexColor('#F8FAFC')       # Slate 50 (Fondo de tarjetas)
    BORDER_COLOR = colors.HexColor('#E2E8F0')   # Slate 200 (Bordes sutiles)
    TEXT_MUTED = colors.HexColor('#64748B')     # Slate 500 (Textos secundarios)
    
    def get_filename(self):
        return f"reporte_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    def get_data(self):
        raise NotImplementedError("Debes implementar get_data")
    
    def get_title(self):
        raise NotImplementedError("Debes implementar get_title")
    
    def _draw_header_footer(self, canvas, doc, company, title):
        """Dibuja el encabezado y pie de página en cada página del PDF"""
        canvas.saveState()
        width, height = A4
        
        # --- Encabezado ---
        # Línea de acento superior
        canvas.setFillColor(self.ACCENT_COLOR)
        canvas.rect(0, height - 10, width, 10, fill=1, stroke=0)
        
        # Nombre de la empresa (Izquierda)
        canvas.setFillColor(self.PRIMARY_COLOR)
        canvas.setFont('Helvetica-Bold', 11)
        canvas.drawString(72, height - 35, company.name.upper())
        
        # Título del reporte (Derecha)
        canvas.setFillColor(self.TEXT_MUTED)
        canvas.setFont('Helvetica', 10)
        canvas.drawRightString(width - 72, height - 35, title)
        
        # Línea separadora del encabezado
        canvas.setStrokeColor(self.BORDER_COLOR)
        canvas.setLineWidth(0.5)
        canvas.line(72, height - 45, width - 72, height - 45)

        # --- Pie de Página ---
        # Línea separadora del pie
        canvas.line(72, 50, width - 72, 50)
        
        # Texto de generador (Izquierda)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(self.TEXT_MUTED)
        canvas.drawString(72, 35, f"Generado por Vexora | {timezone.now().strftime('%d/%m/%Y %H:%M')}")
        
        # Número de página (Derecha)
        page_num = canvas.getPageNumber()
        canvas.drawRightString(width - 72, 35, f"Página {page_num}")
        
        canvas.restoreState()

    def create_pdf(self, data, title, company, user):
        """Crear el PDF usando ReportLab con diseño profesional"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=60,
            leftMargin=60,
            topMargin=70, # Más espacio para el header
            bottomMargin=60,
        )
        
        styles = getSampleStyleSheet()
        
        # Estilos tipográficos modernos
        title_style = ParagraphStyle(
            'CustomTitle', parent=styles['Heading1'], fontSize=22,
            textColor=self.PRIMARY_COLOR, alignment=TA_LEFT, spaceAfter=6, fontName='Helvetica-Bold'
        )
        subtitle_style = ParagraphStyle(
            'Subtitle', parent=styles['Normal'], fontSize=10,
            textColor=self.TEXT_MUTED, alignment=TA_LEFT, spaceAfter=2
        )
        heading_style = ParagraphStyle(
            'CustomHeading', parent=styles['Heading2'], fontSize=13,
            textColor=self.ACCENT_COLOR, spaceAfter=8, spaceBefore=20, fontName='Helvetica-Bold',
            borderPadding=0
        )
        card_label_style = ParagraphStyle(
            'CardLabel', parent=styles['Normal'], fontSize=8,
            textColor=self.TEXT_MUTED, fontName='Helvetica-Bold', alignment=TA_LEFT
        )
        card_value_style = ParagraphStyle(
            'CardValue', parent=styles['Normal'], fontSize=13,
            textColor=self.PRIMARY_COLOR, fontName='Helvetica-Bold', alignment=TA_LEFT
        )
        
        elements = []
        
        # Título principal y metadatos
        elements.append(Paragraph(title, title_style))
        elements.append(Paragraph(f"<b>Empresa:</b> {company.name} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Usuario:</b> {user.get_full_name() or user.email}", subtitle_style))
        elements.append(Paragraph(f"<b>Fecha de generación:</b> {timezone.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Resumen (estilo Cards)
        if 'summary' in data and data['summary']:
            elements.append(Paragraph("Resumen General", heading_style))
            
            summary_items = list(data['summary'].items())
            rows = []
            for i in range(0, len(summary_items), 2):
                row = []
                for j in range(2):
                    if i + j < len(summary_items):
                        key, value = summary_items[i + j]
                        label = key.replace('_', ' ').title()
                        
                        # Formatear valores
                        if isinstance(value, float) or isinstance(value, int):
                            if any(word in label.lower() for word in ['ingresos', 'ganancia', 'total', 'costo', 'valor', 'precio']):
                                val_str = f"${value:,.2f}"
                            else:
                                val_str = f"{value:,}"
                        else:
                            val_str = str(value)

                        # Crear mini-tabla para la tarjeta (Card)
                        card_data = [[Paragraph(label, card_label_style)], [Paragraph(val_str, card_value_style)]]
                        card = Table(card_data, colWidths=[3.2*inch])
                        card.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, -1), self.LIGHT_BG),
                            ('BOX', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
                            ('LEFTPADDING', (0, 0), (-1, -1), 10),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                            ('TOPPADDING', (0, 0), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                            ('LINEBEFORE', (0, 0), (0, -1), 3, self.ACCENT_COLOR), # Barra lateral azul
                        ]))
                        row.append(card)
                    else:
                        row.append("")
                rows.append(row)
            
            summary_table = Table(rows, colWidths=[3.4*inch, 3.4*inch])
            summary_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 0.2*inch))
        
        # Tablas de datos
        for table_name, table_data in data.items():
            if table_name == 'summary':
                continue
                
            if table_data and len(table_data) > 0:
                # Título de la tabla
                elements.append(Paragraph(table_name.replace('_', ' ').title(), heading_style))
                
                headers = list(table_data[0].keys())
                table_rows = []
                
                # Determinar qué columnas son numéricas para alinearlas a la derecha
                is_numeric_col = []
                for h in headers:
                    is_numeric = True
                    for row in table_data:
                        val = row.get(h, '')
                        if not isinstance(val, (int, float)):
                            is_numeric = False
                            break
                    is_numeric_col.append(is_numeric)

                # Encabezados
                header_row = [Paragraph(f"<b>{h.replace('_', ' ').title()}</b>", ParagraphStyle('h', parent=styles['Normal'], textColor=colors.white, fontSize=9, fontName='Helvetica-Bold', alignment=(TA_RIGHT if is_numeric else TA_LEFT))) for h in headers]
                table_rows.append(header_row)
                
                # Filas de datos
                for row in table_data:
                    row_data = []
                    for i, header in enumerate(headers):
                        value = row.get(header, '')
                        if value is None:
                            val_str = '-'
                        elif isinstance(value, float):
                            if any(word in header.lower() for word in ['total', 'ingreso', 'ganancia', 'costo', 'valor', 'precio', 'revenue']):
                                val_str = f'${value:,.2f}'
                            else:
                                val_str = f'{value:,.2f}'
                        elif isinstance(value, int):
                            val_str = f'{value:,}'
                        else:
                            val_str = str(value)
                        
                        # Colorear márgenes positivos/negativos si existe la palabra "Margen"
                        if 'margen' in header.lower() or 'ganancia' in header.lower():
                            color = self.SUCCESS_COLOR if not val_str.startswith('-') else self.DANGER_COLOR
                            p_style = ParagraphStyle('num', parent=styles['Normal'], fontSize=8, alignment=(TA_RIGHT if is_numeric_col[i] else TA_LEFT), textColor=color, fontName='Helvetica-Bold')
                        else:
                            p_style = ParagraphStyle('cell', parent=styles['Normal'], fontSize=8, alignment=(TA_RIGHT if is_numeric_col[i] else TA_LEFT), textColor=self.PRIMARY_COLOR)
                        
                        row_data.append(Paragraph(val_str, p_style))
                    table_rows.append(row_data)
                
                # Crear tabla con diseño minimalista (solo bordes inferiores)
                col_widths = [6.8*inch / len(headers)] * len(headers)
                table = Table(table_rows, colWidths=col_widths, repeatRows=1)
                
                style_cmds = [
                    # Encabezado
                    ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('TOPPADDING', (0, 0), (-1, 0), 10),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    
                    # Cuerpo
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LINEBELOW', (0, 0), (-1, 0), 1, self.ACCENT_COLOR), # Línea gruesa bajo el encabezado
                    ('LINEBELOW', (0, 1), (-1, -1), 0.25, self.BORDER_COLOR), # Líneas finas entre filas
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_BG]), # Filas alternadas
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ]
                
                table.setStyle(TableStyle(style_cmds))
                elements.append(table)
                elements.append(Spacer(1, 0.15*inch))
        
        # Construir documento con Header y Footer dinámicos
        # Usamos una función lambda para pasar company y title al callback
        doc.build(elements, onFirstPage=lambda c, d: self._draw_header_footer(c, d, company, title), 
                           onLaterPages=lambda c, d: self._draw_header_footer(c, d, company, title))
        
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
    
    def get(self, request, *args, **kwargs):
        try:
            company = request.user.company
            if not company:
                messages.error(request, "No tienes una empresa asociada")
                return redirect('vexora:reports_dashboard')
            
            data, title = self.get_data()
            pdf = self.create_pdf(data, title, company, request.user)
            
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{self.get_filename()}"'
            return response
            
        except Exception as e:
            messages.error(request, f"Error al generar PDF: {str(e)}")
            return redirect('vexora:reports_dashboard')

class ExportDashboardPDFView(ExportReportsPDFView):
    """Exportar Dashboard a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        data = {
            'summary': {
                'Total Productos': service.get_total_products(),
                'Productos Activos': service.get_products_by_status()['active'],
                'Productos Inactivos': service.get_products_by_status()['inactive'],
                'Ingresos (30 días)': service.get_total_revenue(days=30),
                'Ganancia Neta': service.get_profit_summary(days=30)['gross_profit'],
                'Margen': f"{service.get_profit_summary(days=30)['profit_margin']:.1f}%",
                'Sin Stock': len(service.get_out_of_stock_products()),
                'Valor Inventario': service.get_inventory_value()['total_value'],
            },
            'Productos Más Vendidos': list(service.get_best_selling_products(limit=10)),
            'Productos con Bajo Stock': list(service.get_low_stock_products(threshold=5)[:10]),
            'Ventas por Estado': list(service.get_sales_by_status()),
        }
        return data, "Dashboard de Reportes"
    
    def get_filename(self):
        return f"dashboard_reportes_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportProductsPDFView(ExportReportsPDFView):
    """Exportar Reportes de Productos a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        products_by_category = service.get_products_by_category()
        category_data = []
        for cat in products_by_category:
            category_data.append({
                'Categoría': cat['category'],
                'Cantidad': cat['count'],
                'Porcentaje': f"{cat['percentage']:.1f}%"
            })
        
        data = {
            'summary': {
                'Total Productos': service.get_total_products(),
                'Activos': service.get_products_by_status()['active'],
                'Inactivos': service.get_products_by_status()['inactive'],
                'Sin Stock': len(service.get_out_of_stock_products()),
                'Valor Inventario': service.get_inventory_value()['total_value'],
            },
            'Productos por Categoría': category_data,
            'Productos por Proveedor': list(service.get_products_by_supplier()),
            'Productos Más Vendidos': list(service.get_best_selling_products(limit=10)),
            'Productos Sin Stock': list(service.get_out_of_stock_products()[:10]),
        }
        return data, "Reporte de Productos"
    
    def get_filename(self):
        return f"reporte_productos_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportSalesPDFView(ExportReportsPDFView):
    """Exportar Reportes de Ventas a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        daily_sales = list(service.get_sales_by_period('day'))
        for sale in daily_sales:
            if sale.get('period'):
                sale['Fecha'] = sale['period'].strftime('%d/%m/%Y')
                if 'period' in sale:
                    del sale['period']
        
        weekly_sales = list(service.get_sales_by_period('week'))
        for i, sale in enumerate(weekly_sales, 1):
            sale['Semana'] = f"Semana {i}"
            if 'period' in sale:
                del sale['period']
        
        monthly_sales = list(service.get_sales_by_period('month'))
        for sale in monthly_sales:
            if sale.get('period'):
                sale['Mes'] = sale['period'].strftime('%B %Y')
                if 'period' in sale:
                    del sale['period']
        
        data = {
            'summary': {
                'Ingresos Totales': service.get_total_revenue(),
                'Promedio Diario': service.get_daily_average_sales(),
                'Ganancia Neta': service.get_profit_summary()['gross_profit'],
                'Margen': f"{service.get_profit_summary()['profit_margin']:.1f}%",
                'Ventas Canceladas': len(service.get_cancelled_sales()),
            },
            'Ventas Diarias': daily_sales[:14],
            'Ventas Semanales': weekly_sales,
            'Ventas Mensuales': monthly_sales,
            'Ventas por Vendedor': list(service.get_sales_by_seller(limit=10)),
            'Clientes con Mayor Compra': list(service.get_sales_by_client(limit=10)),
        }
        return data, "Reporte de Ventas"
    
    def get_filename(self):
        return f"reporte_ventas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportFinancialPDFView(ExportReportsPDFView):
    """Exportar Reportes Financieros a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        monthly = service.get_financial_by_period('month')
        weekly = service.get_financial_by_period('week')
        yearly = service.get_financial_by_period('year')
        
        profitability = service.get_product_profitability(limit=10)
        profit_data = []
        for p in profitability:
            profit_data.append({
                'Producto': p['product_name'],
                'Categoría': p['category'],
                'Precio': p['sale_price'],
                'Costo': p['price'],
                'Margen %': f"{p['margin_percentage']:.1f}%",
                'Vendidos': p['total_sold'],
                'Ingresos': p['total_revenue'],
            })
        
        data = {
            'summary': {
                'Ingresos Mensuales': monthly['revenue'],
                'Costos Mensuales': monthly['cost'],
                'Ganancia Mensual': monthly['profit'],
                'Margen Mensual': f"{monthly['profit_margin']:.1f}%",
                'Ventas Mensuales': monthly['sales_count'],
                'Valor Inventario': service.get_inventory_value()['total_value'],
            },
            'Resumen Semanal': [{
                'Ingresos': weekly['revenue'],
                'Costos': weekly['cost'],
                'Ganancia': weekly['profit'],
                'Margen': f"{weekly['profit_margin']:.1f}%",
                'Ventas': weekly['sales_count'],
            }],
            'Resumen Mensual': [{
                'Ingresos': monthly['revenue'],
                'Costos': monthly['cost'],
                'Ganancia': monthly['profit'],
                'Margen': f"{monthly['profit_margin']:.1f}%",
                'Ventas': monthly['sales_count'],
            }],
            'Resumen Anual': [{
                'Ingresos': yearly['revenue'],
                'Costos': yearly['cost'],
                'Ganancia': yearly['profit'],
                'Margen': f"{yearly['profit_margin']:.1f}%",
                'Ventas': yearly['sales_count'],
            }],
            'Rentabilidad por Producto': profit_data,
            'Ventas Canceladas': list(service.get_cancelled_sales()[:10]),
        }
        return data, "Reporte Financiero"
    
    def get_filename(self):
        return f"reporte_financiero_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
# ============================================
# EXPORTAR REPORTES DE PRODUCTOS POR SECCIÓN
# ============================================

class ExportProductsCategoryPDFView(ExportReportsPDFView):
    """Exportar Productos por Categoría a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        products_by_category = service.get_products_by_category()
        category_data = []
        for cat in products_by_category:
            category_data.append({
                'Categoría': cat['category'],
                'Cantidad': cat['count'],
                'Porcentaje': f"{cat['percentage']:.1f}%"
            })
        
        data = {
            'summary': {
                'Total Productos': service.get_total_products(),
                'Categorías': len(products_by_category),
            },
            'Productos por Categoría': category_data,
        }
        return data, "Productos por Categoría"
    
    def get_filename(self):
        return f"productos_por_categoria_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportProductsSupplierPDFView(ExportReportsPDFView):
    """Exportar Productos por Proveedor a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        data = {
            'summary': {
                'Total Productos': service.get_total_products(),
                'Proveedores': len(service.get_suppliers_summary()),
            },
            'Productos por Proveedor': list(service.get_products_by_supplier()),
        }
        return data, "Productos por Proveedor"
    
    def get_filename(self):
        return f"productos_por_proveedor_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportProductsBestSellersPDFView(ExportReportsPDFView):
    """Exportar Productos Más Vendidos a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        best_sellers = list(service.get_best_selling_products(limit=20))
        best_sellers_data = []
        for item in best_sellers:
            best_sellers_data.append({
                'Producto': item.get('product__name', '-'),
                'Cantidad': item.get('total_quantity', 0),
                'Ingresos': item.get('total_revenue', 0),
            })
        
        data = {
            'summary': {
                'Total Productos': service.get_total_products(),
                'Período': 'Últimos 30 días',
            },
            'Productos Más Vendidos': best_sellers_data,
        }
        return data, "Productos Más Vendidos"
    
    def get_filename(self):
        return f"productos_mas_vendidos_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportProductsWorstSellersPDFView(ExportReportsPDFView):
    """Exportar Productos Menos Vendidos a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        worst_sellers = list(service.get_worst_selling_products(limit=20))
        worst_sellers_data = []
        for item in worst_sellers:
            worst_sellers_data.append({
                'Producto': item.get('name', '-'),
                'Stock': item.get('stock', 0),
                'SKU': item.get('sku', '-'),
            })
        
        data = {
            'summary': {
                'Total Productos': service.get_total_products(),
                'Período': 'Últimos 30 días',
            },
            'Productos Menos Vendidos': worst_sellers_data,
        }
        return data, "Productos Menos Vendidos"
    
    def get_filename(self):
        return f"productos_menos_vendidos_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportProductsOutOfStockPDFView(ExportReportsPDFView):
    """Exportar Productos Sin Stock a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        out_of_stock = list(service.get_out_of_stock_products())
        out_of_stock_data = []
        for item in out_of_stock:
            out_of_stock_data.append({
                'Producto': item.get('name', '-'),
                'Categoría': item.get('category__name', '-'),
                'SKU': item.get('sku', '-'),
            })
        
        data = {
            'summary': {
                'Total Productos': service.get_total_products(),
                'Sin Stock': len(out_of_stock),
            },
            'Productos Sin Stock': out_of_stock_data,
        }
        return data, "Productos Sin Stock"
    
    def get_filename(self):
        return f"productos_sin_stock_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


# ============================================
# EXPORTAR REPORTES DE VENTAS POR SECCIÓN
# ============================================

class ExportSalesDailyPDFView(ExportReportsPDFView):
    """Exportar Ventas Diarias a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        daily_sales = list(service.get_sales_by_period('day'))
        daily_sales_data = []
        for sale in daily_sales:
            daily_sales_data.append({
                'Fecha': sale.get('period', '').strftime('%d/%m/%Y') if sale.get('period') else '',
                'Ventas': sale.get('count', 0),
                'Total': sale.get('total_sales', 0),
                'Promedio': sale.get('avg_sale', 0),
            })
        
        data = {
            'summary': {
                'Total Ingresos': service.get_total_revenue(days=1),
                'Período': 'Hoy',
            },
            'Ventas Diarias': daily_sales_data,
        }
        return data, "Ventas Diarias"
    
    def get_filename(self):
        return f"ventas_diarias_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportSalesWeeklyPDFView(ExportReportsPDFView):
    """Exportar Ventas Semanales a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        weekly_sales = list(service.get_sales_by_period('week'))
        weekly_sales_data = []
        for i, sale in enumerate(weekly_sales, 1):
            weekly_sales_data.append({
                'Semana': f"Semana {i}",
                'Ventas': sale.get('count', 0),
                'Total': sale.get('total_sales', 0),
                'Promedio': sale.get('avg_sale', 0),
            })
        
        data = {
            'summary': {
                'Total Ingresos': service.get_total_revenue(days=7),
                'Período': 'Última semana',
            },
            'Ventas Semanales': weekly_sales_data,
        }
        return data, "Ventas Semanales"
    
    def get_filename(self):
        return f"ventas_semanales_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportSalesMonthlyPDFView(ExportReportsPDFView):
    """Exportar Ventas Mensuales a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        monthly_sales = list(service.get_sales_by_period('month'))
        monthly_sales_data = []
        for sale in monthly_sales:
            monthly_sales_data.append({
                'Mes': sale.get('period', '').strftime('%B %Y') if sale.get('period') else '',
                'Ventas': sale.get('count', 0),
                'Total': sale.get('total_sales', 0),
                'Promedio': sale.get('avg_sale', 0),
            })
        
        data = {
            'summary': {
                'Total Ingresos': service.get_total_revenue(days=30),
                'Período': 'Último mes',
            },
            'Ventas Mensuales': monthly_sales_data,
        }
        return data, "Ventas Mensuales"
    
    def get_filename(self):
        return f"ventas_mensuales_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportSalesYearlyPDFView(ExportReportsPDFView):
    """Exportar Ventas Anuales a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        yearly_sales = list(service.get_sales_by_period('year'))
        yearly_sales_data = []
        for sale in yearly_sales:
            yearly_sales_data.append({
                'Año': sale.get('period', '').strftime('%Y') if sale.get('period') else '',
                'Ventas': sale.get('count', 0),
                'Total': sale.get('total_sales', 0),
                'Promedio': sale.get('avg_sale', 0),
            })
        
        data = {
            'summary': {
                'Total Ingresos': service.get_total_revenue(days=365),
                'Período': 'Último año',
            },
            'Ventas Anuales': yearly_sales_data,
        }
        return data, "Ventas Anuales"
    
    def get_filename(self):
        return f"ventas_anuales_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportSalesBySellerPDFView(ExportReportsPDFView):
    """Exportar Ventas por Vendedor a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        sales_by_seller = list(service.get_sales_by_seller(limit=20))
        sales_by_seller_data = []
        for item in sales_by_seller:
            name = item.get('user__first_name', '') or item.get('user__username', '-')
            if item.get('user__last_name'):
                name = f"{name} {item.get('user__last_name', '')}"
            sales_by_seller_data.append({
                'Vendedor': name,
                'Ventas': item.get('count', 0),
                'Total': item.get('total_sales', 0),
                'Promedio': item.get('average', 0),
            })
        
        data = {
            'summary': {
                'Total Vendedores': len(sales_by_seller_data),
                'Período': 'Últimos 30 días',
            },
            'Ventas por Vendedor': sales_by_seller_data,
        }
        return data, "Ventas por Vendedor"
    
    def get_filename(self):
        return f"ventas_por_vendedor_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportSalesByClientPDFView(ExportReportsPDFView):
    """Exportar Clientes con Mayor Compra a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        sales_by_client = list(service.get_sales_by_client(limit=20))
        sales_by_client_data = []
        for item in sales_by_client:
            sales_by_client_data.append({
                'Cliente': item.get('customer_name', '-'),
                'Compras': item.get('count', 0),
                'Total': item.get('total_purchases', 0),
                'Última Compra': item.get('last_purchase', '').strftime('%d/%m/%Y') if item.get('last_purchase') else '',
            })
        
        data = {
            'summary': {
                'Total Clientes': len(sales_by_client_data),
                'Período': 'Últimos 30 días',
            },
            'Clientes con Mayor Compra': sales_by_client_data,
        }
        return data, "Clientes con Mayor Compra"
    
    def get_filename(self):
        return f"clientes_mayor_compra_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


# ============================================
# EXPORTAR REPORTES FINANCIEROS POR SECCIÓN
# ============================================

class ExportFinancialWeeklyPDFView(ExportReportsPDFView):
    """Exportar Resumen Semanal a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        weekly = service.get_financial_by_period('week')
        
        data = {
            'summary': {
                'Ingresos': weekly['revenue'],
                'Costos': weekly['cost'],
                'Ganancia': weekly['profit'],
                'Margen': f"{weekly['profit_margin']:.1f}%",
                'Ventas': weekly['sales_count'],
                'Items Vendidos': weekly['items_sold'],
            },
        }
        return data, "Resumen Semanal"
    
    def get_filename(self):
        return f"resumen_semanal_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportFinancialMonthlyPDFView(ExportReportsPDFView):
    """Exportar Resumen Mensual a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        monthly = service.get_financial_by_period('month')
        
        data = {
            'summary': {
                'Ingresos': monthly['revenue'],
                'Costos': monthly['cost'],
                'Ganancia': monthly['profit'],
                'Margen': f"{monthly['profit_margin']:.1f}%",
                'Ventas': monthly['sales_count'],
                'Items Vendidos': monthly['items_sold'],
            },
        }
        return data, "Resumen Mensual"
    
    def get_filename(self):
        return f"resumen_mensual_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportFinancialYearlyPDFView(ExportReportsPDFView):
    """Exportar Resumen Anual a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        yearly = service.get_financial_by_period('year')
        
        data = {
            'summary': {
                'Ingresos': yearly['revenue'],
                'Costos': yearly['cost'],
                'Ganancia': yearly['profit'],
                'Margen': f"{yearly['profit_margin']:.1f}%",
                'Ventas': yearly['sales_count'],
                'Items Vendidos': yearly['items_sold'],
            },
        }
        return data, "Resumen Anual"
    
    def get_filename(self):
        return f"resumen_anual_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportFinancialProfitabilityPDFView(ExportReportsPDFView):
    """Exportar Rentabilidad por Producto a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        profitability = service.get_product_profitability(limit=30)
        profitability_data = []
        for p in profitability:
            profitability_data.append({
                'Producto': p['product_name'],
                'Categoría': p['category'],
                'Precio': p['sale_price'],
                'Costo': p['price'],
                'Margen %': f"{p['margin_percentage']:.1f}%",
                'Vendidos': p['total_sold'],
                'Ingresos': p['total_revenue'],
            })
        
        data = {
            'summary': {
                'Total Productos': service.get_total_products(),
                'Productos Analizados': len(profitability_data),
            },
            'Rentabilidad por Producto': profitability_data,
        }
        return data, "Rentabilidad por Producto"
    
    def get_filename(self):
        return f"rentabilidad_productos_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"


class ExportFinancialCancelledPDFView(ExportReportsPDFView):
    """Exportar Ventas Canceladas a PDF"""
    
    def get_data(self):
        company = self.request.user.company
        service = ReportService(company)
        
        cancelled_sales = list(service.get_cancelled_sales())
        cancelled_data = []
        for sale in cancelled_sales:
            cancelled_data.append({
                'ID': f"#{sale.get('id', '')}",
                'Cliente': sale.get('customer_name', '-'),
                'Total': sale.get('total', 0),
                'Vendedor': sale.get('user__username', '-'),
                'Fecha': sale.get('created_at', '').strftime('%d/%m/%Y %H:%M') if sale.get('created_at') else '',
            })
        
        data = {
            'summary': {
                'Total Canceladas': len(cancelled_data),
                'Período': 'Últimos 30 días',
            },
            'Ventas Canceladas': cancelled_data,
        }
        return data, "Ventas Canceladas"
    
    def get_filename(self):
        return f"ventas_canceladas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
