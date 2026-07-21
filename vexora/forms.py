from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import *
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, Permission
from django import forms
from .models import SiteConfiguration
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError

#--------------------Formulario de grupos y permisos-------------------
class GroupForm(forms.ModelForm):



    class Meta:

        model = Role

        fields = ['name']
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
# -------------------- Registro público --------------------

class PublicUserRegistrationForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        campos = [
            "avatar",
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
            "password1",
            "password2",
        ]

        for field_name in campos:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    "class": "form-control"
                })

    class Meta:
        model = CustomUser
        fields = [
            "avatar",
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
            "password1",
            "password2",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if email:
            email = email.strip().lower()

        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Este correo ya está registrado."
            )

        return email
    
#--------------------Crear usuario -------------------
class CustomUserRegisterForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        self.fields['avatar'].widget.attrs.update({
            'class': 'form-control'
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
        fields = ["avatar","email", "username", "first_name", "last_name", "phone", "password1", "password2", "is_staff", "is_active"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email
    
#--------------------Actualizar Usuario -------------------
# -------------------- Crear usuario dentro de una empresa --------------------

class CustomUserCreationForm(UserCreationForm):
    role = forms.ModelChoiceField(
        queryset=Role.objects.none(),
        required=True,
        label="Rol"
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields["role"].queryset = Role.objects.filter(
                company=company,
                active=True
            )

        self.fields["role"].widget.attrs.update({
            "class": "form-select",
            "data-live-search": "true",
        })

        campos_form_control = [
            "avatar",
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
            "password1",
            "password2",
        ]

        for field_name in campos_form_control:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    "class": "form-control"
                })

    class Meta:
        model = CustomUser
        fields = [
            "avatar",
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
            "password1",
            "password2",
            "role",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if email:
            email = email.strip().lower()

        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Este correo ya está registrado."
            )

        return email
    
# -------------------- Actualizar usuario --------------------

class CustomUserUpdateForm(forms.ModelForm):
    role = forms.ModelChoiceField(
        queryset=Role.objects.none(),
        required=True,
        label="Rol"
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        company = kwargs.pop("company", None)

        super().__init__(*args, **kwargs)

        if company:
            self.fields["role"].queryset = Role.objects.filter(
                company=company,
                active=True
            )

            # Mostrar el rol actual del usuario
            if self.instance and self.instance.pk:
                membership = CompanyMember.objects.filter(
                    user=self.instance,
                    company=company
                ).select_related("role").first()

                if membership:
                    self.fields["role"].initial = membership.role

        campos_form_control = [
            "avatar",
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
        ]

        for field_name in campos_form_control:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    "class": "form-control"
                })

        self.fields["role"].widget.attrs.update({
            "class": "form-select",
            "data-live-search": "true",
        })

        if "is_active" in self.fields:
            self.fields["is_active"].widget.attrs.update({
                "class": "form-check-input"
            })

        if "is_staff" in self.fields:
            self.fields["is_staff"].widget.attrs.update({
                "class": "form-check-input"
            })

    class Meta:
        model = CustomUser
        fields = [
            "avatar",
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
            "is_active",
            "is_staff",
            "role",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if email:
            email = email.strip().lower()

        correo_existente = CustomUser.objects.filter(
            email__iexact=email
        ).exclude(
            pk=self.instance.pk
        ).exists()

        if correo_existente:
            raise forms.ValidationError(
                "Este correo ya está registrado."
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=commit)

        company = getattr(self, "company", None)
        role = self.cleaned_data.get("role")

        return user  
#--------------------Formulario de empresas-------------------
# -------------------- Formulario de empresas --------------------

class CompanyForm(forms.ModelForm):

    class Meta:
        model = Company
        fields = [
            "name",
            "address",
            "phone",
            "email",
            "slug",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "required": True,
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "required": True,
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "required": True,
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "required": True,
                }
            ),
            "slug": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }
        
    class Meta:
        model = Company
        fields = ["name", "address", "phone", "email", "slug"]


#==============================================
# CATEGORY FORM
#==============================================
class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ej: Bebidas, Electrónicos, etc.'
        })

        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descripción de la categoría'
        })

        # Si el usuario tiene compañía, la establecemos automáticamente
        if user and hasattr(user, 'company') and user.company:
            # Ocultar el campo y asignar el valor
            self.fields['company'].widget = forms.HiddenInput()
            self.fields['company'].initial = user.company.id  # ← IMPORTANTE: usar .id
            self.fields['company'].required = False  # ← No requerido porque ya tiene valor
        else:
            # Si no tiene compañía, mostramos el selector
            self.fields['company'].widget.attrs.update({
                'class': 'form-control select2'
            })
            self.fields['company'].queryset = Company.objects.all()
            self.fields['company'].empty_label = 'Seleccione una compañía'

    class Meta:
        model = Category
        fields = ["name", "description", "company"]

#==============================================
# SUPPLIER FORM 
#==============================================
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

        # Asignar company automáticamente
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

#==============================================
# PRODUCT FORM
#==============================================
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

        is_edit = self.instance and self.instance.pk is not None

        # Campo item_number - solo lectura (se muestra pero no se edita)
        self.fields['item_number'] = forms.IntegerField(
            label='N° Producto',
            required=False,
            widget=forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'disabled': 'disabled'
            }),
            help_text='Número secuencial asignado automáticamente'
        )

        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nombre del producto'
        })

        self.fields['sku'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'SKU (código único)'
        })
        #DEBE DE SER UN CAMPO BOOLEANO
        self.fields['is_store'].widget.attrs.update({
                'class': 'form-check-input',
                'placeholder': '¿DESEA QUE ESTE PRODUCTO SE VEA EN LA TIENDA?'
        })

        self.fields['barcode'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Código de barras'
        })

        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descripción del producto'
        })

        self.fields['purchase_date'].widget.attrs.update({
            'class': 'form-control',
            'type': 'date'
        })

        self.fields['price'].widget.attrs.update({
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        })

        self.fields['sale_price'].widget.attrs.update({
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        })

        if is_edit:
            self.fields['stock'].widget.attrs.update({
                'class': 'form-control',
                'min': 0,
                'placeholder': '0',
                'readonly': 'readonly'
            })
        else:
            self.fields['stock'].widget.attrs.update({
                'class': 'form-control',
                'min': 0,
                'placeholder': '0'
            })

        self.fields['min_stock'].widget.attrs.update({
            'class': 'form-control',
            'min': 0,
            'placeholder': '0'
        })

        self.fields['is_active'].widget.attrs.update({
            'class': 'form-check-input'
        })

        self.fields['image'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'image/*'
        })

        # Filtrar proveedores SOLO de la compañía del usuario
        self.fields['supplier'].widget.attrs.update({
            'class': 'form-control'
        })
        if self.user and hasattr(self.user, 'company') and self.user.company:
            self.fields['supplier'].queryset = Supplier.objects.filter(company=self.user.company)
        else:
            self.fields['supplier'].queryset = Supplier.objects.none()

        # Filtrar categorías SOLO de la compañía del usuario
        self.fields['category'].widget.attrs.update({
            'class': 'form-control'
        })
        if self.user and hasattr(self.user, 'company') and self.user.company:
            self.fields['category'].queryset = Category.objects.filter(company=self.user.company)
        else:
            self.fields['category'].queryset = Category.objects.none()

        # Filtrar tags SOLO de la compañía del usuario
        self.fields['tags'].widget.attrs.update({
            'class': 'form-control selectpicker'
        })
        if self.user and hasattr(self.user, 'company') and self.user.company:
            self.fields['tags'].queryset = Tag.objects.filter(company=self.user.company)
        else:
            self.fields['tags'].queryset = Tag.objects.none()

        # Company - ocultar y asignar automáticamente
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
            "item_number", "name", "sku", "barcode", "description", "purchase_date",
            "price", "sale_price", "stock", "min_stock", "is_active",
            "supplier", "category", "tags", "company", "image",
            "stock_addition","is_store"
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

#----------------------------planes----------------------

class PlanesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'required': 'required   '
        })
        self.fields['price'].widget.attrs.update({
            'class': 'form-control',
        })
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
        })

        self.fields['max_users'].widget.attrs.update({
            'class': 'form-control',
            'required': 'required'
        })
        self.fields['max_products'].widget.attrs.update({
            'class': 'form-control',
            'required': 'required'
        })
        self.fields['max_groups'].widget.attrs.update({
            'class': 'form-control',
            'required': 'required'
        })
        self.fields['max_providers'].widget.attrs.update({
            'class': 'form-control',
            'required': 'required'
        })
        self.fields['custom_domain'].widget.attrs.update({
            'class': 'form-control-input',
        })
        self.fields['active'].widget.attrs.update({
            'class': 'form-control-input',
        })
        self.fields['priority_support'].widget.attrs.update({
            'class': 'form-control-input',
        })


    
    class Meta:
        model = Plan
        fields = ["name", "price", "max_users","description", "max_products", "max_groups", "max_providers", "custom_domain", "priority_support", "active"]

# ============================================
# MEMBERS FORMS
# ============================================
class MemberCreateForm(forms.ModelForm):

    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario'
        }),
        label='Nombre de usuario'
    )
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        }),
        label='Nombre'
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellidos'
        }),
        label='Apellidos'
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        label='Correo electrónico'
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+52 123 456 7890'
        }),
        label='Teléfono'
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        }),
        label='Contraseña'
    )
    password_confirm = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        }),
        label='Confirmar contraseña'
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Configurar clases CSS para el campo role
        self.fields['role'].widget.attrs.update({
            'class': 'form-select'
        })
            
        if user and user.company:
            self.fields['role'].queryset = Role.objects.filter(
                company=user.company,
                active=True
            )
        else:
            self.fields['role'].queryset = Role.objects.none()

    class Meta:
        model = CompanyMember
        fields = ["role"]

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError(f"El nombre de usuario '{username}' ya está en uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(f"El correo '{email}' ya está registrado.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Las contraseñas no coinciden.")
        
        if password and len(password) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
        
        return cleaned_data

    def save(self, commit=True):
        # Crear el usuario
        user = CustomUser.objects.create_user(
            username=self.cleaned_data.get('username'),
            email=self.cleaned_data.get('email'),
            first_name=self.cleaned_data.get('first_name'),
            last_name=self.cleaned_data.get('last_name'),
            password=self.cleaned_data.get('password')
        )
        
        # Agregar teléfono si existe
        phone = self.cleaned_data.get('phone')
        if phone:
            user.phone = phone
            user.save()
        
        # Asignar el usuario al miembro
        self.instance.user = user
        
        return super().save(commit=commit)


class MemberForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Obtener el usuario de los kwargs
        user = kwargs.pop('user', None)
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        self.fields['company'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['user'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['role'].widget.attrs.update({
            'class': 'form-select'
        })
        if user and user.company:
            self.fields['role'].queryset = Role.objects.filter(
                company=user.company,
                active=True
            )
        else:
            self.fields['role'].queryset = Role.objects.none()
        # Si hay un usuario, filtrar los usuarios disponibles
        if user:
            company = user.company
            
            # Obtener todos los usuarios que pertenecen a la empresa del usuario actual
            # a través de CompanyMember
            company_user_ids = CompanyMember.objects.filter(
                company=company
            ).values_list('user_id', flat=True)
            
            # Si es una edición (el formulario tiene una instancia), excluir el usuario actual
            if self.instance and self.instance.pk:
                company_user_ids = list(company_user_ids)
                if self.instance.user_id in company_user_ids:
                    company_user_ids.remove(self.instance.user_id)
            else:
                company_user_ids = list(company_user_ids)
            
            # Obtener usuarios que están en la empresa (a través de memberships)
            # y que NO son miembros de la empresa actual
            # Primero, obtener todos los usuarios que tienen membresía en esta empresa
            existing_member_ids = CompanyMember.objects.filter(
                company=company
            ).values_list('user_id', flat=True)
            
            # Si es una edición, incluir al usuario actual
            if self.instance and self.instance.pk:
                existing_member_ids = existing_member_ids.exclude(id=self.instance.user_id)
            
            # Filtrar usuarios que son de la empresa y no son miembros aún
            # Un usuario es de la empresa si tiene al menos una membresía en ella
            users_in_company = CustomUser.objects.filter(
                memberships__company=company
            ).distinct()
            
            # Excluir los que ya son miembros de esta empresa
            self.fields['user'].queryset = users_in_company.exclude(
                id__in=existing_member_ids
            ).order_by('username')
            
            # Si es una edición, incluir el usuario actual
            if self.instance and self.instance.pk:
                current_user = self.instance.user
                # Asegurarse de que el usuario actual esté en el queryset
                if current_user not in self.fields['user'].queryset:
                    if self.instance and self.instance.pk:
                        current_user = self.instance.user
                        # Usar union() en lugar de |
                        self.fields['user'].queryset = self.fields['user'].queryset.union(
                            CustomUser.objects.filter(id=current_user.id)
                        )
        
        # Marcar el campo 'company' como hidden
        self.fields['company'].widget = forms.HiddenInput()
        
        # Hacer el campo 'user' de solo lectura en edición
        if self.instance and self.instance.pk:
            self.fields['user'].widget.attrs['disabled'] = 'disabled'
            self.fields['user'].help_text = "El usuario no puede ser modificado"
            


    class Meta:
        model = CompanyMember
        fields = ["company", "user", "role"]
        
    def clean(self):
        cleaned_data = super().clean()
        company = cleaned_data.get('company')
        user = cleaned_data.get('user')
        role = cleaned_data.get('role')
        
        # Validar que no exista duplicado (excepto en edición)
        if company and user and role:
            existing = CompanyMember.objects.filter(
                company=company,
                user=user
            )
            
            # Si es edición, excluir la instancia actual
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    f"El usuario '{user.username}' ya es miembro de esta empresa."
                )
        
        return cleaned_data