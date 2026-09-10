"""
Transaction URL patterns for Sound Pesa platform.
"""
from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    # Transaction estimation
    path('estimate-fee/', views.estimate_transaction_fee, name='estimate_fee'),
    
    # Transaction creation and management
    path('send/', views.create_transaction, name='create_transaction'),
    path('', views.TransactionListView.as_view(), name='transaction_list'),
    path('<uuid:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('<uuid:transaction_id>/status/', views.get_transaction_status, name='transaction_status'),
    path('<uuid:transaction_id>/cancel/', views.cancel_transaction, name='cancel_transaction'),
    
    # Transaction queries
    path('pending/', views.get_pending_transactions, name='pending_transactions'),
    path('statistics/', views.get_transaction_statistics, name='transaction_statistics'),
    path('health/', views.transaction_system_health, name='system_health'),
    
    # Wallet-specific transaction history
    path('wallets/<uuid:wallet_id>/transactions/', views.get_transaction_history, name='wallet_transactions'),
]