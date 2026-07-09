# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.urls import reverse
from config import settings
from django.utils import timezone
from django.utils.text import slugify
import uuid
# models.py


class Company(models.Model):

    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(unique=True)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="owned_companies")

    # Información de contacto
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    # Información fiscal
    rfc = models.CharField(max_length=13, blank=True, null=True)
    tax_name = models.CharField(max_length=200, blank=True, null=True)

    # Imagen
    logo = models.ImageField(upload_to="vexora/company/logo/",blank=True,null=True)

    # Estado
    is_active = models.BooleanField(default=True)

    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("vexora:company_detail",kwargs={"slug": self.slug})

#--- Models para la configuración del sitio y el usuario personalizado
class SiteConfiguration(models.Model):
    company = models.OneToOneField(Company,on_delete=models.CASCADE,null=True,blank=True)
    background_color = models.CharField(max_length=7,default="#0f172a")
    card_background = models.CharField(max_length=7,default="#1e293b")
    text_color = models.CharField(max_length=7,default="#000000")
    primary_color = models.CharField(max_length=7,default="#2563EB")
    secondary_color = models.CharField(max_length=7,default="#1E293B")
    accent_color = models.CharField(max_length=7,default="#F59E0B")
    logo = models.ImageField(upload_to='logos/',blank=True,null=True)
    favicon = models.ImageField(upload_to='favicons/',blank=True,null=True)
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
    user_permissions = models.ManyToManyField(Permission,related_name="customuser_set",blank=True,help_text="Specific permissions for this user.",verbose_name="user permissions",)
    companies = models.ManyToManyField(Company,related_name="members",null=True,blank=True)
    @property
    def company(self):
        """Return a primary company for the user if one exists."""
        return self.owned_companies.first() or self.companies.first()

    objects = CustomUserManager()

    def get_role_permissions(self):
        company = self.company
        if not company:
            return set()

        try:
            membership = self.memberships.select_related("role").get(company=company)
        except CompanyMember.DoesNotExist:
            return set()

        return {
            f"{p.content_type.app_label}.{p.codename}"
            for p in membership.role.permissions.all()
        }
    def get_all_permissions(self, obj=None):

        if self.is_superuser:
            return {
                f"{p.content_type.app_label}.{p.codename}"
                for p in Permission.objects.all()
            }

        permissions = set()

        permissions.update(super().get_all_permissions(obj))
        permissions.update(self.get_role_permissions())

        return permissions
    def has_perm(self, perm, obj=None):

        if self.is_superuser:
            return True

        return perm in self.get_all_permissions()
    USERNAME_FIELD = "email"  # login con email
    REQUIRED_FIELDS = ["username","first_name", "last_name"]

    def __str__(self):
        return self.email
    


class Role(models.Model):

    company = models.ForeignKey(Company,on_delete=models.CASCADE,related_name="roles")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True,null=True)
    permissions = models.ManyToManyField(Permission,blank=True,related_name="roles")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ("company", "name")

    def __str__(self):
        return f"{self.company.name} - {self.name}"
    
class CompanyMember(models.Model):

    company = models.ForeignKey(Company,on_delete=models.CASCADE,related_name="memberships")
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name="memberships")
    role = models.ForeignKey(Role,on_delete=models.PROTECT,related_name="members")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("company", "user")
#--------------------Plan de suscripción-------------------
class Plan(models.Model):

    PLAN_TYPES = (
        ('monthly', 'Mensual'),
        ('yearly', 'Anual'),
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_type = models.CharField(max_length=20, choices=PLAN_TYPES)

    # Límites
    max_users = models.PositiveIntegerField(default=1)
    max_products = models.PositiveIntegerField(default=100)
    max_branches = models.PositiveIntegerField(default=1)
    max_groups = models.PositiveIntegerField(default=1)
    max_providers = models.PositiveIntegerField(default=10)
    max_collaborators = models.PositiveIntegerField(default=1)

    # Funcionalidades
    sales_module = models.BooleanField(default=True)
    users_module = models.BooleanField(default=False)
    groups_module = models.BooleanField(default=False)
    providers_module = models.BooleanField(default=True)
    custom_domain = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)

    active = models.BooleanField(default=True)
    
class Subscription(models.Model):

    STATUS_CHOICES = (
        ('active', 'Activa'),
        ('expired', 'Expirada'),
        ('cancelled', 'Cancelada'),
        ('pending', 'Pendiente'),
    )
    company = models.OneToOneField(Company,    on_delete=models.CASCADE,related_name='subscription') 
    plan = models.ForeignKey(Plan,on_delete=models.CASCADE)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='pending')
    start_date = models.DateField()
    end_date = models.DateField()
    trial = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):

        return f" - {self.plan.name}"
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='payments')
    company = models.ForeignKey(Company,on_delete=models.CASCADE,null=True,blank=True)
    subscription = models.ForeignKey(Subscription,on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    payment_method = models.CharField(max_length=20,choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='pending')
    transaction_id = models.CharField(max_length=255,blank=True,null=True)
    paid_at = models.DateTimeField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
#--------------------Features-------------------
class Feature(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100,unique=True)
    description = models.TextField(blank=True,null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
#--------------------Relación entre planes y features-------------------
class PlanFeature(models.Model):
    plan = models.ForeignKey(Plan,on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature,on_delete=models.CASCADE)
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

    company = models.OneToOneField(Company,on_delete=models.CASCADE, null=True, blank=True)
    email_host = models.CharField(max_length=255,default='smtp.gmail.com')
    email_port = models.IntegerField(default=587)
    email_host_user = models.EmailField()
    email_host_password = models.CharField(max_length=255)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

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

#==============tags=====================
class Tag(models.Model):

    name = models.CharField(max_length=50)

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='tags'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'name'],
                name='unique_tag_per_company'
            )
        ]

    def __str__(self):
        return self.name

class Category(models.Model):

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True,null=True)
    company = models.ForeignKey(Company,on_delete=models.CASCADE,related_name='categories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'name'],
                name='unique_category_per_company'
            )
        ]

    def __str__(self):
        return self.name

# ========== SUPPLIER MODEL (Proveedores) ==========
class Supplier(models.Model):
    """Supplier model - this is the "proveedores" table"""
    name = models.CharField(max_length=100, verbose_name="Supplier name")
    address = models.CharField(max_length=200, verbose_name="Address")
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='suppliers'
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'name'],
                name='unique_supplier_per_company'
            )
        ]


# ========== PRODUCT MODEL (Productos) ==========
class Product(models.Model):
    """Product model - this is the "productos" table"""
    name = models.CharField(max_length=150, verbose_name="Product name")
    purchase_date = models.DateField(verbose_name="Purchase date")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    supplier = models.ForeignKey(Supplier,on_delete=models.CASCADE,related_name='products',verbose_name="Supplier")
    company = models.ForeignKey(Company,on_delete=models.CASCADE,null=True,blank=True,related_name='products')
    category = models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,blank=True,related_name='products',verbose_name="Category")
    tags = models.ManyToManyField(Tag, blank=True, related_name='products', verbose_name="Tags")
    stock = models.IntegerField(default=0, verbose_name="Stock")
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Sale price")
    sku = models.CharField(max_length=50, blank=True, null=True, verbose_name="SKU")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    min_stock = models.IntegerField(default=0, verbose_name="Minimum stock")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Product image")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    barcode = models.CharField(max_length=100, blank=True, null=True, verbose_name="Barcode", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} - {self.supplier.name}"
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        indexes = [
            models.Index(fields=['company', 'name']),
            models.Index(fields=['company', 'sku']),
            models.Index(fields=['company', 'barcode']),
        ]

# ========== SALE MODEL (Ventas) ==========

class Sale(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sales')
    customer_name = models.CharField(max_length=150, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    invoice_number = models.CharField(max_length=50, blank=True, null=True, unique=True)
    date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    campo_pureba_1 = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.invoice_number or f"Venta #{self.id}"

    def calculate_totals(self):
        items = self.items.all()
        subtotal = sum((item.total_price or 0) for item in items)
        self.subtotal = subtotal
        self.total = subtotal + self.tax - self.discount
        return self.total


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='sale_items')
    description = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.unit_price and self.product is not None:
            self.unit_price = self.product.sale_price or self.product.price
        self.total_price = (self.unit_price * self.quantity) - self.discount
        super().save(*args, **kwargs)

    def __str__(self):
        product_name = self.product.name if self.product else self.description or 'Detalle de venta'
        return f"{product_name} x {self.quantity}"

    class Meta:
        ordering = ['-id']
        