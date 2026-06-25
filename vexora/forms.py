from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import *
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, Permission
from django import forms
from .models import SiteConfiguration
from django.contrib.auth.models import Group, Permission

#--------------------Formulario de grupos y permisos-------------------
class GroupForm(forms.ModelForm):

    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:

        model = Group

        fields = ['name', 'permissions']
#--------------------Configuración del sitio-------------------
class SiteConfigurationForm(forms.ModelForm):

    class Meta:

        model = SiteConfiguration

        fields = [
            'primary_color',
            'secondary_color',
            'accent_color',
            'background_color',
            'card_background',
            'text_color',
            'logo',
            'favicon',
        ]

        widgets = {


            'primary_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),

            'secondary_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),

            'accent_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),

            'background_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),

            'card_background': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),

            'text_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),

        }

class SMTPConfigurationForm(forms.ModelForm):

    class Meta:
        model = SMTPConfiguration
        fields = [
            'email_host',
            'email_port',
            'email_host_user',
            'email_host_password',
            'use_tls',
            'use_ssl',
            'active',
        ]
        widgets = {
            'email_host': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'email_port': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'email_host_user': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'email_host_password': forms.PasswordInput(attrs={
                'class': 'form-control'
            }),
            'use_tls': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'use_ssl': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

class AIChatForm(forms.Form):
    prompt = forms.CharField(
        label='Pregunta al asistente',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Escribe tu consulta aquí...'
        }),
        max_length=2000,
    )

#----------------Login-------------------
class CustomAuthenticationForm(forms.Form):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            user = authenticate(self.request, username=email, password=password)
            if user is None:
                raise forms.ValidationError("Correo o contraseña incorrectos.")
            if not user.is_active:
                raise forms.ValidationError("Esta cuenta está inactiva.")
            self.user = user
        return self.cleaned_data

    def get_user(self):
        return self.user
#--------------------Crear usuario -------------------
class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['avatar'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['groups'].widget.attrs.update({
            'class': 'form-control selectpicker',
            'data-live-search': 'true',
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['username'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['first_name'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['last_name'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['phone'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['password1'].widget.attrs.update({   
            'class': 'form-control'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control'
        })
    class Meta:
        model = CustomUser
        fields = ["avatar","email", "username", "first_name", "last_name", "phone", "password1", "password2", "is_staff", "is_active","groups"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email
    
#--------------------Actualizar Usuario -------------------
class CustomUserUpdateForm(forms.ModelForm):   # 👈 Cambié a ModelForm
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("current_user", None)
        super().__init__(*args, **kwargs)

        self.fields['email'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['groups'].widget.attrs.update({
            'class': 'form-control selectpicker',
            'data-live-search': 'true',
        })
        self.fields['username'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['first_name'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['last_name'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['phone'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['cover'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['avatar'].widget.attrs.update({
            'class': 'form-control'
        })
        if "is_staff" in self.fields:
            self.fields["is_staff"].widget.attrs.update({"class": "form-check-input"})

        # Si no es superusuario, quítale is_staff e is_active del form
        if user is not None and not user.is_superuser:
            self.fields.pop("is_staff", None)
            self.fields.pop("is_active", None)
        # Ojo: normalmente en un update no editas password aquí
        # si quieres mantener password1 y password2 deberías heredar de UserCreationForm
        # y definir fields = (...)
        
    class Meta:
        model = CustomUser
        fields = ("email", "username", "first_name", "last_name", "phone", "is_staff", "is_active","cover","avatar", "groups")
        
#--------------------Formulario de empresas-------------------
class CompanyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['address'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['phone'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['slug'].widget.attrs.update({
            'class': 'form-control'
        })
        
    
    class Meta:
        model = Company
        fields = ["name", "address", "phone", "email", "slug"]



# ============================================
# CATEGORY, SUPPLIER AND PRODUCT FORMS
# ============================================

#==============================================
# CATEGORY FORM
#==============================================
class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
        })

        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3,
        })

    class Meta:
        model = Category
        fields = ["name", "description"]
        

# ============================================
# SUPPLIER FORM
# ============================================
class SupplierForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nombre del proveedor',
            'autofocus': 'autofocus'
        })

        self.fields['address'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Dirección del proveedor',
            'rows': 3
        })

        # 👇 ASIGNAR COMPANY AUTOMÁTICAMENTE
        if self.user and hasattr(self.user, 'company') and self.user.company:
            self.fields['company'].widget = forms.HiddenInput()
            self.fields['company'].initial = self.user.company
        else:
            self.fields['company'].widget.attrs.update({
                'class': 'form-control'
            })
            self.fields['company'].queryset = Company.objects.all()

    class Meta:
        model = Supplier
        fields = ["name", "address", "company"]


# ============================================
# PRODUCT FORM
# ============================================
class ProductForm(forms.ModelForm):
    stock_addition = forms.IntegerField(
        label='Cantidad a agregar al stock',
        required=False,
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'min': '0'
        }),
        help_text='Ingresa la cantidad de unidades que deseas agregar al stock actual'
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Determinar si es edición (tiene instancia) o creación
        is_edit = self.instance and self.instance.pk is not None

        # Nombre
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nombre del producto'
        })

        # SKU
        self.fields['sku'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'SKU (código único)'
        })

        # Código de barras
        self.fields['barcode'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Código de barras'
        })

        # Descripción
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descripción del producto'
        })

        # Fecha de compra
        self.fields['purchase_date'].widget.attrs.update({
            'class': 'form-control',
            'type': 'date'
        })

        # Precio
        self.fields['price'].widget.attrs.update({
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        })

        # Precio de venta
        self.fields['sale_price'].widget.attrs.update({
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        })

        # Stock - Solo lectura si es edición
        if is_edit:
            self.fields['stock'].widget.attrs.update({
                'class': 'form-control',
                'min': 0,
                'placeholder': '0',
                'readonly': 'readonly'  # Solo lectura en edición
            })
        else:
            self.fields['stock'].widget.attrs.update({
                'class': 'form-control',
                'min': 0,
                'placeholder': '0'
            })

        # Stock mínimo
        self.fields['min_stock'].widget.attrs.update({
            'class': 'form-control',
            'min': 0,
            'placeholder': '0'
        })

        # Activo
        self.fields['is_active'].widget.attrs.update({
            'class': 'form-check-input'
        })

        # Imagen
        self.fields['image'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'image/*'
        })

        # Proveedor
        self.fields['supplier'].widget.attrs.update({
            'class': 'form-control'
        })
        if self.user and hasattr(self.user, 'company') and self.user.company:
            self.fields['supplier'].queryset = Supplier.objects.filter(
                models.Q(company=self.user.company) | models.Q(company__isnull=True)
            )
        else:
            self.fields['supplier'].queryset = Supplier.objects.all()

        # Categoría
        self.fields['category'].widget.attrs.update({
            'class': 'form-control'
        })
        if self.user and hasattr(self.user, 'company') and self.user.company:
            self.fields['category'].queryset = Category.objects.filter(company=self.user.company)
        else:
            self.fields['category'].queryset = Category.objects.all()

        # Tags
        self.fields['tags'].widget.attrs.update({
            'class': 'form-control'
        })
        if self.user and hasattr(self.user, 'company') and self.user.company:
            self.fields['tags'].queryset = Tag.objects.filter(company=self.user.company)
        else:
            self.fields['tags'].queryset = Tag.objects.all()

        # Company
        if self.user and hasattr(self.user, 'company') and self.user.company:
            self.fields['company'].widget = forms.HiddenInput()
            self.fields['company'].initial = self.user.company
        else:
            self.fields['company'].widget.attrs.update({
                'class': 'form-control'
            })
            self.fields['company'].queryset = Company.objects.all()

        # Si es creación, eliminar el campo stock_addition
        if not is_edit:
            self.fields.pop('stock_addition', None)

    class Meta:
        model = Product
        fields = [
            "name", "sku", "barcode", "description", "purchase_date",
            "price", "sale_price", "stock", "min_stock", "is_active",
            "supplier", "category", "tags", "company", "image",
            "stock_addition"  
        ]   
                 
#---------------ventas
class SalesForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].widget.attrs.update({
            'class': 'form-control selectpicker',
            'data-live-search': 'true',
        })
        self.fields['customer_name'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['customer_email'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['customer_phone'].widget.attrs.update({
            'class': 'form-control'
        })
        
    
    class Meta:
        model = Sale
        fields = ["company", "customer_name", "customer_email", "customer_phone"]

