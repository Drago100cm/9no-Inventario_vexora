
# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from config import settings
from django.utils import timezone
from django.utils.text import slugify
import uuid
# models.py


class Company(models.Model):

    name = models.CharField(max_length=150,unique=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    slug = models.SlugField(unique=True)
    def save(self, *args, **kwargs):

        if not self.slug:

            self.slug = (
                f"{slugify(self.name)}"
            )

        super().save(*args, **kwargs)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='owned_companies')
    created_at = models.DateTimeField(auto_now_add=True
    )

    def __str__(self):

        return self.name
#--- Models para la configuración del sitio y el usuario personalizado
class SiteConfiguration(models.Model):
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    background_color = models.CharField(
        max_length=7,
        default="#0f172a"
    )

    card_background = models.CharField(
        max_length=7,
        default="#1e293b"
    )

    text_color = models.CharField(
        max_length=7,
        default="#ffffff"
    )
    primary_color = models.CharField(
        max_length=7,
        default="#2563EB"
    )

    secondary_color = models.CharField(
        max_length=7,
        default="#1E293B"
    )

    accent_color = models.CharField(
        max_length=7,
        default="#F59E0B"
    )

    logo = models.ImageField(
        upload_to='logos/',
        blank=True,
        null=True
    )

    favicon = models.ImageField(
        upload_to='favicons/',
        blank=True,
        null=True
    )

    dark_mode = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.company.name if self.company else "Sin empresa"#--------Planes de suscripcion------

#--- Modelo para representar una empresa, con un propietario y un slug único para URLs amigables


    
class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, first_name, last_name, phone=None, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a username")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            is_active=True,  # 👈 Muy importante
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            **extra_fields
        )
        

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)  # login field
    username = models.CharField(max_length=50, unique=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    birthdate = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    cover = models.ImageField(upload_to='vexora/user/profile/', null=True, blank=True)
    avatar = models.ImageField(upload_to='vexora/user/avatar/', null=True, blank=True)
    # Evitar conflictos con auth.User
    groups = models.ManyToManyField(Group,related_name="customuser_set",blank=True,help_text="The groups this user belongs to.",verbose_name="groups",)
    user_permissions = models.ManyToManyField(Permission,related_name="customuser_set",blank=True,help_text="Specific permissions for this user.",verbose_name="user permissions",)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    objects = CustomUserManager()

    USERNAME_FIELD = "email"  # login con email
    REQUIRED_FIELDS = ["username","first_name", "last_name"]

    def __str__(self):
        return self.email

#--------------------Plan de suscripción-------------------
class Plan(models.Model):

    PLAN_TYPES = (
        ('monthly', 'Mensual'),
        ('yearly', 'Anual'),
    )

    name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    billing_type = models.CharField(
        max_length=20,
        choices=PLAN_TYPES,
        default='monthly'
    )

    max_users = models.IntegerField(
        default=1
    )

    max_products = models.IntegerField(
        default=100
    )

    max_branches = models.IntegerField(
        default=1
    )

    custom_domain = models.BooleanField(
        default=False
    )

    priority_support = models.BooleanField(
        default=False
    )

    active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,

    )

    def __str__(self):

        return self.name
    
class Subscription(models.Model):

    STATUS_CHOICES = (
        ('active', 'Activa'),
        ('expired', 'Expirada'),
        ('cancelled', 'Cancelada'),
        ('pending', 'Pendiente'),
    )

    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE
    )

    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    start_date = models.DateField()

    end_date = models.DateField()

    trial = models.BooleanField(
        default=False
    )

    active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return f"{self.company.name} - {self.plan.name}"
#--------------------Pagos-------------------
class payment(models.Model):

    PAYMENT_METHODS = (
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('mercadopago', 'MercadoPago'),
        ('cash', 'Efectivo'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('refunded', 'Reembolsado'),
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE
    )

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
#--------------------Features-------------------
class Feature(models.Model):

    name = models.CharField(max_length=100)

    code = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
#--------------------Relación entre planes y features-------------------
class PlanFeature(models.Model):

    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE
    )

    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE
    )

    enabled = models.BooleanField(default=True)

#--------------------Invitaciones a empresas-------------------
class CompanyInvitation(models.Model):

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE
    )

    email = models.EmailField()

    token = models.UUIDField()

    accepted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    
#--------------------Logs de suscripción-------------------
class SubscriptionLog(models.Model):

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE
    )

    action = models.CharField(max_length=100)

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    
#--------------------Configuración SMTP para envíos de email-------------------
    
class SMTPConfiguration(models.Model):

    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE, null=True, blank=True
    )

    email_host = models.CharField(
        max_length=255,
        default='smtp.gmail.com'
    )

    email_port = models.IntegerField(
        default=587
    )

    email_host_user = models.EmailField()

    email_host_password = models.CharField(
        max_length=255
    )

    use_tls = models.BooleanField(
        default=True
    )

    use_ssl = models.BooleanField(
        default=False
    )

    active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )