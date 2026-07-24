from django.urls import path
from .views import *
from . import views
from .api import *
from .views import SubscriptionPlanListView, SubscriptionChooseView, SubscriptionDetailView
app_name = 'vexora'
urlpatterns = [


    #----------------------Home----------------------
    path('', HomeView.as_view(), name='home'),
    path('Dashboard/',DashboardView.as_view(),name='dashboard'),

    #----------------------Autenticación----------------------
    path("login/", CustomLoginView.as_view(), name="login"),
    path('logout/', LogoutRedirectView.as_view(), name='logout'),
    path("Registro/", RegisterView.as_view(), name="registro"),
    #----------------------Configuración del sitio----------------------
    path('configuration/',SiteConfigurationUpdateView.as_view(),name='site_configuration'),
    path('smtp_configuration/', SMTPConfigurationUpdateView.as_view(), name='smtp_configuration'),
    path('smtp_test/',SMTPTestView.as_view(),name='smtp_test'),
    #----------------------Grupos y permisos----------------------
    path('groups/',GroupListView.as_view(),name='group_list'),
    path('group_create/',GroupCreateView.as_view(),name='group_create'),
    path('group_edit/<int:pk>/',GroupUpdateView.as_view(),name='group_edit'),
    path('group_delete/<int:pk>/', views.delete_group, name='group_delete'),
    
    #----------------------Planes de suscripción----------------------
    path('plans/', PlanListView.as_view(), name='plan_list'),
    path('plans/create/', PlanCreateView.as_view(), name='plan_create'),
    path('plans/edit/<int:pk>/', PlanUpdateView.as_view(), name='plan_edit'),
    path('plans/delete/<int:pk>/', views.delete_plan, name='plan_delete'),
    
    #----------------------Suscripciones----------------------
    path('subscription_list/', SubscriptionPlanListView.as_view(), name='subscription_list'),
    path('subscriptions/choose/<int:plan_id>/', SubscriptionChooseView.as_view(), name='subscription_choose'),
    path('subscriptions/detail/', SubscriptionDetailView.as_view(), name='subscription_detail'),
    path('assistant/', AIChatView.as_view(), name='ai_assistant'),
    
    #----------------------Uuarios----------------------
    path("users/", UserListView.as_view(), name="user_list"),
    path("user_create", UserCreateView.as_view(), name="user_create"),
    path("user_edit/<int:pk>", UserUpdateView.as_view(), name="user_edit"),
    path("user_delete/<int:pk>", views.delete_user, name="user_delete"),
    path('profil/<int:pk>/', ProfileView.as_view(), name='profil'),
    path('members/', MembersView.as_view(), name='member_list'),
    #----------------------Empresas----------------------
    path("companies/", CompanyListView.as_view(), name="company_list"),
    path("company/<slug:slug>/", CompanyDetailView.as_view(), name="company_detail"),
    path("company_create/", CompanyCreateView.as_view(), name="company_create"),
    path("company_edit/<int:pk>", CompanyUpdateView.as_view(), name="company_edit"),
    path("company_delete/<int:pk>", views.delete_company, name="company_delete"),
    #----------------------RegistroClientes----------------------
    path("customer_register/<slug:slug>/", CustomerRegisterView.as_view(), name="customer_register"),
    path("client_List/", ClientsListView.as_view(), name="client_list"),


    # ============================================
    # CATEGORY URLs (Categorías)
    # ============================================
    path('categories/', views.CategoryListView.as_view(), name='list_categories'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='create_category'),
    path('categories/update/<int:id>/', views.CategoryUpdateView.as_view(), name='edit_category'),
    path('categories/delete/<int:pk>/', views.delete_category, name='delete_category'),
    
    # ============================================
    # SUPPLIER URLs (Proveedores)
    # ============================================
    path('suppliers/', views.SupplierListView.as_view(), name='list_suppliers'),
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='create_supplier'),
    path('suppliers/update/<int:id>/', views.SupplierUpdateView.as_view(), name='edit_supplier'),
    path('suppliers/delete/<int:pk>/', views.delete_supplier, name='delete_supplier'),
    # ============================================
    # PRODUCT URLs (Productos)
    # ============================================
    path('list_products/', views.ProductListView.as_view(), name='list_products'),
    path('products/create/', views.ProductCreateView.as_view(), name='create_product'),
    path('products/update/<int:id>/', views.ProductUpdateView.as_view(), name='edit_product'),
    path('products/view/<int:pk>/', views.view_product, name='view_product'),    
    path('products/delete/<int:id>/', views.delete_product, name='delete_product'), 
    path('products/quick-create/', views.ProductQuickCreateView.as_view(), name='product_quick_create'),
    
    

    # =================================
    # Members URLs (Miembros)
    # =================================
    
    path('members/', views.MembersView.as_view(), name='list_members'),
    path('members/create/', views.MembersCreateView.as_view(), name='create_member'),
    path('members/update/<int:id>/', views.MemberUpdateView.as_view(), name='edit_member'),
    path('members/delete/<int:id>/', views.delete_member, name='delete_member'),
    
    # ============================================
    # REPORTES URLs
    # ============================================
    path('reports/', views.ReportsDashboardView.as_view(), name='reports_dashboard'),
    path('reports/products/', views.ProductReportsView.as_view(), name='product_reports'),
    path('reports/sales/', views.SalesReportsView.as_view(), name='sales_reports'),
    path('reports/financial/', views.FinancialReportsView.as_view(), name='financial_reports'),
    
    # ============================================
    # EXPORTAR REPORTES A PDF
    # ============================================
    path('reports/export/dashboard/', views.ExportDashboardPDFView.as_view(), name='export_dashboard_pdf'),
    path('reports/export/products/', views.ExportProductsPDFView.as_view(), name='export_products_pdf'),
    path('reports/export/sales/', views.ExportSalesPDFView.as_view(), name='export_sales_pdf'),
    path('reports/export/financial/', views.ExportFinancialPDFView.as_view(), name='export_financial_pdf'),
    # ============================================
    # EXPORTAR REPORTES A PDF POR SECCIÓN
    # ============================================

    # Reportes de Productos - Secciones
    path('reports/export/products/category/', views.ExportProductsCategoryPDFView.as_view(), name='export_products_category_pdf'),
    path('reports/export/products/supplier/', views.ExportProductsSupplierPDFView.as_view(), name='export_products_supplier_pdf'),
    path('reports/export/products/best-sellers/', views.ExportProductsBestSellersPDFView.as_view(), name='export_products_best_sellers_pdf'),
    path('reports/export/products/worst-sellers/', views.ExportProductsWorstSellersPDFView.as_view(), name='export_products_worst_sellers_pdf'),
    path('reports/export/products/out-of-stock/', views.ExportProductsOutOfStockPDFView.as_view(), name='export_products_out_of_stock_pdf'),

    # Reportes de Ventas - Secciones
    path('reports/export/sales/daily/', views.ExportSalesDailyPDFView.as_view(), name='export_sales_daily_pdf'),
    path('reports/export/sales/weekly/', views.ExportSalesWeeklyPDFView.as_view(), name='export_sales_weekly_pdf'),
    path('reports/export/sales/monthly/', views.ExportSalesMonthlyPDFView.as_view(), name='export_sales_monthly_pdf'),
    path('reports/export/sales/yearly/', views.ExportSalesYearlyPDFView.as_view(), name='export_sales_yearly_pdf'),
    path('reports/export/sales/by-seller/', views.ExportSalesBySellerPDFView.as_view(), name='export_sales_by_seller_pdf'),
    path('reports/export/sales/by-client/', views.ExportSalesByClientPDFView.as_view(), name='export_sales_by_client_pdf'),

    # Reportes Financieros - Secciones
    path('reports/export/financial/weekly/', views.ExportFinancialWeeklyPDFView.as_view(), name='export_financial_weekly_pdf'),
    path('reports/export/financial/monthly/', views.ExportFinancialMonthlyPDFView.as_view(), name='export_financial_monthly_pdf'),
    path('reports/export/financial/yearly/', views.ExportFinancialYearlyPDFView.as_view(), name='export_financial_yearly_pdf'),
    path('reports/export/financial/profitability/', views.ExportFinancialProfitabilityPDFView.as_view(), name='export_financial_profitability_pdf'),
    path('reports/export/financial/cancelled/', views.ExportFinancialCancelledPDFView.as_view(), name='export_financial_cancelled_pdf'),

    # ============================================
    # SALES URLs (Ventas )
    # ============================================
    path('sales/', views.SalesListView.as_view(), name='list_sales'),
    path('sales/create/', views.SalesCreateView.as_view(), name='create_sale'),
    path('sales/update/<int:id>/', views.SalesUpdateView.as_view(), name='edit_sale'),
    path('sales/delete/<int:pk>/', views.delete_sale, name='delete_sale'),

    # ============================================
    # SALES MAIN URLs (Ventas Frontend)
    # ============================================
    path('sales-main/', views.SalesMainListView.as_view(), name='sales_main_list'),
    path('sales-main/create/', views.SalesMainCreateView.as_view(), name='sales_main_create'),
    path('sales-main/update/', views.SalesMainUpdateView.as_view(), name='sales_main_update'),
    path('sales-main/delete/<int:pk>/', views.delete_sale, name='sales_main_delete'),
    
    # ============================================
    # STORE URLs (Tienda pública)

    
# ============================================
# STORE URLs
# ============================================

    # ============================================
    path('store/cart/update/<int:item_id>/', views.CartUpdateView.as_view(), name='cart_update'),
    path('store/cart/remove/<int:item_id>/', views.CartRemoveView.as_view(), name='cart_remove'),
    path('store/', views.StoreHomeView.as_view(), name='store_home'),
    path('store/product/<int:pk>/', views.StoreProductoView.as_view(), name='store_product'),
    path('store/cart/', views.StoreCarritoView.as_view(), name='store_cart'),
    path('store/checkout/', views.StoreCheckoutView.as_view(), name='store_checkout'),
    path('store/confirmation/<int:pk>/', views.StoreConfirmacionView.as_view(), name='store_confirmation'),
    path('store/cart/count/', views.CartCountView.as_view(), name='cart_count'),


path("store/",views.StoreHomeView.as_view(),name="store_home",),

path(
    "store/product/<int:pk>/",
    views.StoreProductoView.as_view(),
    name="store_product",
),

path(
    "store/cart/",
    views.StoreCarritoView.as_view(),
    name="store_cart",
),

path(
    "store/cart/add/",
    views.cart_add,
    name="cart_add",
),

path(
    "store/cart/update/<int:item_id>/",
    views.CartUpdateView.as_view(),
    name="cart_update",
),

path(
    "store/cart/remove/<int:item_id>/",
    views.CartRemoveView.as_view(),
    name="cart_remove",
),

path(
    "store/cart/count/",
    views.CartCountView.as_view(),
    name="cart_count",
),

path(
    "store/checkout/",
    views.StoreCheckoutView.as_view(),
    name="store_checkout",
),

path(
    "store/confirmation/<int:pk>/",
    views.StoreConfirmacionView.as_view(),
    name="store_confirmation",
),

path(
    "store/order/<int:pk>/pdf/",
    views.store_order_pdf,
    name="store_order_pdf",
),
    # API endpoints
    path('api/register/', api_register, name='api_register'),
    path('api/login/', api_login, name='api_login'),
    path('api/list_productos/', api_productos, name='api_productos'),
    path('api/list_proveedores/', api_proveedores, name='api_proveedores'),
    path('api/crear_producto/', api_crear_producto, name='api_crear_producto'),
    path('api/editar_producto/<int:id>/', api_product_update, name='api_product_update'),
    path('api/crear_proveedor/', api_crear_proveedor, name='api_crear_proveedor'),
    path('api/editar_proveedor/<int:id>/', api_supplier_update, name='api_supplier_update'),

    # ============================================home empresas=============
    
    path('<slug:slug>/',views.company_home,name='company_home'),
    path('<slug:slug>/register/',views.RegisterView.as_view(),name='company_register'),
    path('<slug:slug>/login/',views.CustomLoginView.as_view(),name='company_login'),
]