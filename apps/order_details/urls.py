from django.urls import path
from apps.order_details.views import *

urlpatterns = [
    path('', Orders.as_view(), name='order_request'),
    path('order/', OrderDetails.as_view(), name='order'),
    path('tracking_details/', OrderTrackingDetails.as_view(), name="tracking_details")
]