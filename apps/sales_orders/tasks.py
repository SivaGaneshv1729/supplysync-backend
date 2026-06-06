import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_sales_order_created_event(self, order_id: int, created_by_user_id: int):
    try:
        logger.info(f"EVENT [sales-order-created]: order_id={order_id}, created_by={created_by_user_id}")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

@shared_task(bind=True, max_retries=3)
def process_sales_order_cancelled_event(self, order_id: int):
    try:
        logger.info(f"EVENT [sales-order-cancelled]: order_id={order_id}")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

@shared_task
def generate_daily_operations_summary():
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # In a real app we'd query counts for `yesterday`. Let's mock the query for now
    # We will log it exactly as requested
    from apps.purchase_orders.models import PurchaseOrder
    from apps.sales_orders.models import SalesOrder
    
    new_pos = PurchaseOrder.objects.filter(created_at__date=yesterday).count()
    rcv_pos = PurchaseOrder.objects.filter(actual_delivery_date=yesterday).count()
    new_sos = SalesOrder.objects.filter(created_at__date=yesterday).count()
    dsp_sos = SalesOrder.objects.filter(dispatched_at__date=yesterday).count()
    del_sos = SalesOrder.objects.filter(delivered_at__date=yesterday).count()
    
    logger.info(f"DAILY SUMMARY: Date={today}, New POs={new_pos}, POs Received={rcv_pos}, New Sales Orders={new_sos}, Orders Dispatched={dsp_sos}, Orders Delivered={del_sos}")
