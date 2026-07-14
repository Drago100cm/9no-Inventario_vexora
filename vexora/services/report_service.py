from django.db.models import Sum, Count, Avg, F, Q, Min, Max
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from ..models import Product, Sale, SaleItem, Category, Supplier

class ReportService:
    
    def __init__(self, company):
        self.company = company
    
    # ============================================
    # REPORTES DE PRODUCTOS
    # ============================================
    
    def get_total_products(self):
        """Total de productos registrados"""
        return Product.objects.filter(company=self.company).count()
    
    def get_products_by_status(self):
        """Productos activos e inactivos"""
        active = Product.objects.filter(company=self.company, is_active=True).count()
        inactive = Product.objects.filter(company=self.company, is_active=False).count()
        return {
            'active': active,
            'inactive': inactive,
            'total': active + inactive
        }
    
    def get_products_by_category(self):
        """Productos por categoría"""
        categories = Category.objects.filter(company=self.company)
        result = []
        total = self.get_total_products()
        
        for category in categories:
            count = Product.objects.filter(company=self.company, category=category).count()
            result.append({
                'category': category.name,
                'category_id': category.id,
                'count': count,
                'percentage': (count / total * 100) if total > 0 else 0
            })
        return result
    
    def get_low_stock_products(self, threshold=10):
        """Productos con bajo stock"""
        return Product.objects.filter(
            company=self.company,
            stock__lte=threshold,
            stock__gt=0,
            is_active=True
        ).values('id', 'name', 'stock', 'category__name', 'sku').order_by('stock')
    
    def get_out_of_stock_products(self):
        """Productos sin existencias"""
        return Product.objects.filter(
            company=self.company,
            stock=0,
            is_active=True
        ).values('id', 'name', 'category__name', 'sku')
    
    def get_best_selling_products(self, days=30, limit=10):
        """Productos más vendidos"""
        since = timezone.now() - timedelta(days=days)
        return SaleItem.objects.filter(
            sale__company=self.company,
            sale__created_at__gte=since,
            sale__status='completed'
        ).values(
            'product__id', 
            'product__name', 
            'product__sku',
            'product__category__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('unit_price')),
            total_discount=Sum('discount'),
            net_revenue=Sum(F('quantity') * F('unit_price')) - Sum('discount')
        ).order_by('-total_quantity')[:limit]
    
    def get_worst_selling_products(self, days=30, limit=10):
        """Productos menos vendidos"""
        since = timezone.now() - timedelta(days=days)
        sold_products = SaleItem.objects.filter(
            sale__company=self.company,
            sale__created_at__gte=since,
            sale__status='completed'
        ).values('product_id').distinct()
        
        return Product.objects.filter(
            company=self.company,
            is_active=True
        ).exclude(
            id__in=[p['product_id'] for p in sold_products]
        ).values('id', 'name', 'stock', 'sku', 'category__name')[:limit]
    
    def get_inventory_value(self):
        """Inventario valorizado (valor total del stock)"""
        result = Product.objects.filter(company=self.company).aggregate(
            total_value=Sum(F('stock') * F('sale_price')),
            total_cost=Sum(F('stock') * F('price'))
        )
        return {
            'total_value': result['total_value'] or Decimal('0.00'),
            'total_cost': result['total_cost'] or Decimal('0.00'),
            'potential_profit': (result['total_value'] or Decimal('0.00')) - (result['total_cost'] or Decimal('0.00'))
        }
    
    def get_suppliers_summary(self):
        """Resumen de proveedores"""
        suppliers = Supplier.objects.filter(company=self.company)
        result = []
        for supplier in suppliers:
            products_count = Product.objects.filter(company=self.company, supplier=supplier).count()
            result.append({
                'id': supplier.id,
                'name': supplier.name,
                'address': supplier.address,
                'products_count': products_count
            })
        return result
    
    def get_products_by_supplier(self):
        """Productos por proveedor"""
        return Product.objects.filter(company=self.company).values(
            'supplier__id', 
            'supplier__name'
        ).annotate(
            count=Count('id'),
            total_value=Sum(F('stock') * F('sale_price'))
        ).order_by('-count')
    
    # ============================================
    # REPORTES DE VENTAS
    # ============================================
    
    def get_sales_by_period(self, period='day'):
        """Ventas por período (día, semana, mes, año)"""
        today = timezone.now()
        
        if period == 'day':
            start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            trunc = TruncDate('created_at')
        elif period == 'week':
            start = today - timedelta(days=7)
            trunc = TruncDate('created_at')
        elif period == 'month':
            start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            trunc = TruncDate('created_at')
        elif period == 'year':
            start = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            trunc = TruncMonth('created_at')
        else:
            start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            trunc = TruncDate('created_at')
        
        return Sale.objects.filter(
            company=self.company,
            created_at__gte=start,
            status='completed'
        ).annotate(period=trunc).values('period').annotate(
            total_sales=Sum('total'),
            count=Count('id'),
            avg_sale=Avg('total')
        ).order_by('period')
    
    def get_sales_by_date_range(self, start_date, end_date):
        """Ventas por rango de fechas"""
        return Sale.objects.filter(
            company=self.company,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            status='completed'
        ).aggregate(
            total=Sum('total'),
            count=Count('id'),
            average=Avg('total'),
            min_sale=Min('total'),
            max_sale=Max('total')
        )
    
    def get_total_revenue(self, days=None):
        """Total de ingresos"""
        queryset = Sale.objects.filter(company=self.company, status='completed')
        if days:
            since = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(created_at__gte=since)
        return queryset.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    
    def get_daily_average_sales(self, days=30):
        """Promedio de ventas por día"""
        since = timezone.now() - timedelta(days=days)
        sales = Sale.objects.filter(
            company=self.company,
            created_at__gte=since,
            status='completed'
        )
        total_days = days
        if sales.count() == 0:
            return Decimal('0.00')
        total_amount = sales.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        return total_amount / Decimal(str(total_days))
    
    def get_sales_by_seller(self, days=30):
        """Ventas por vendedor"""
        since = timezone.now() - timedelta(days=days)
        return Sale.objects.filter(
            company=self.company,
            created_at__gte=since,
            status='completed',
            user__isnull=False
        ).values(
            'user__id',
            'user__username', 
            'user__first_name', 
            'user__last_name',
            'user__email'
        ).annotate(
            total_sales=Sum('total'),
            count=Count('id'),
            average=Avg('total')
        ).order_by('-total_sales')
    
    def get_sales_by_client(self, days=30, limit=10):
        """Ventas por cliente"""
        since = timezone.now() - timedelta(days=days)
        return Sale.objects.filter(
            company=self.company,
            created_at__gte=since,
            status='completed'
        ).exclude(
            customer_name__isnull=True,
            customer_email__isnull=True
        ).values(
            'customer_name', 
            'customer_email',
            'customer_phone'
        ).annotate(
            total_purchases=Sum('total'),
            count=Count('id'),
            average=Avg('total'),
            last_purchase=Max('created_at')
        ).order_by('-total_purchases')[:limit]
    
    def get_sales_by_status(self):
        """Ventas por estado"""
        return Sale.objects.filter(company=self.company).values('status').annotate(
            count=Count('id'),
            total=Sum('total')
        ).order_by('status')
    
    def get_cancelled_sales(self, days=30):
        """Ventas canceladas"""
        since = timezone.now() - timedelta(days=days)
        return Sale.objects.filter(
            company=self.company,
            created_at__gte=since,
            status='cancelled'
        ).values(
            'id', 
            'total', 
            'status', 
            'user__username',
            'customer_name',
            'created_at',
            'notes'
        ).order_by('-created_at')
    
    def get_products_sold_per_period(self, start_date, end_date):
        """Productos vendidos por período"""
        return SaleItem.objects.filter(
            sale__company=self.company,
            sale__created_at__date__gte=start_date,
            sale__created_at__date__lte=end_date,
            sale__status='completed'
        ).values(
            'product__id', 
            'product__name', 
            'product__sku',
            'product__category__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('unit_price')),
            total_discount=Sum('discount'),
            net_revenue=Sum(F('quantity') * F('unit_price')) - Sum('discount')
        ).order_by('-total_quantity')
    
    # ============================================
    # REPORTES FINANCIEROS
    # ============================================
    
    def get_financial_by_period(self, period='month'):
        """Ingresos por período"""
        today = timezone.now()
        
        if period == 'day':
            start = today - timedelta(days=1)
        elif period == 'week':
            start = today - timedelta(days=7)
        elif period == 'month':
            start = today - timedelta(days=30)
        elif period == 'year':
            start = today - timedelta(days=365)
        else:
            start = today - timedelta(days=30)
        
        sales = Sale.objects.filter(
            company=self.company,
            created_at__gte=start,
            status='completed'
        )
        
        sale_items = SaleItem.objects.filter(sale__in=sales)
        
        revenue = sales.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        cost = sale_items.aggregate(
            total=Sum(F('quantity') * F('product__price'))
        )['total'] or Decimal('0.00')
        
        return {
            'period': period,
            'start_date': start,
            'end_date': today,
            'revenue': revenue,
            'cost': cost,
            'profit': revenue - cost,
            'profit_margin': ((revenue - cost) / revenue * 100) if revenue > 0 else 0,
            'sales_count': sales.count(),
            'items_sold': sale_items.aggregate(total=Sum('quantity'))['total'] or 0
        }
    
    def get_product_profitability(self, limit=20):
        """Utilidad por producto y productos con mayor margen"""
        products = Product.objects.filter(company=self.company, is_active=True)
        result = []
        
        for product in products:
            if product.price > 0:
                margin_percentage = ((product.sale_price - product.price) / product.price * 100) if product.sale_price else 0
            else:
                margin_percentage = 0
            
            sales_data = SaleItem.objects.filter(
                product=product,
                sale__company=self.company,
                sale__status='completed'
            ).aggregate(
                total_quantity=Sum('quantity'),
                total_revenue=Sum(F('quantity') * F('unit_price')),
                total_discount=Sum('discount')
            )
            
            total_revenue = sales_data['total_revenue'] or Decimal('0.00')
            total_quantity = sales_data['total_quantity'] or 0
            
            result.append({
                'product_id': product.id,
                'product_name': product.name,
                'sku': product.sku,
                'price': product.price,
                'sale_price': product.sale_price,
                'margin_per_unit': (product.sale_price - product.price) if product.sale_price else 0,
                'margin_percentage': margin_percentage,
                'total_sold': total_quantity,
                'total_revenue': total_revenue,
                'stock': product.stock,
                'category': product.category.name if product.category else 'Sin categoría'
            })
        
        result.sort(key=lambda x: x['margin_percentage'], reverse=True)
        return result[:limit]
    
    def get_profit_summary(self, days=30):
        """Resumen de ganancias"""
        since = timezone.now() - timedelta(days=days)
        
        sales = Sale.objects.filter(
            company=self.company,
            created_at__gte=since,
            status='completed'
        )
        
        sale_items = SaleItem.objects.filter(sale__in=sales)
        
        total_revenue = sales.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        total_discount = sale_items.aggregate(total=Sum('discount'))['total'] or Decimal('0.00')
        total_cost = sale_items.aggregate(
            total=Sum(F('quantity') * F('product__price'))
        )['total'] or Decimal('0.00')
        
        return {
            'period_days': days,
            'total_revenue': total_revenue,
            'total_discount': total_discount,
            'total_cost': total_cost,
            'gross_profit': total_revenue - total_cost,
            'profit_margin': ((total_revenue - total_cost) / total_revenue * 100) if total_revenue > 0 else 0,
            'sales_count': sales.count(),
            'average_sale': total_revenue / sales.count() if sales.count() > 0 else 0
        }