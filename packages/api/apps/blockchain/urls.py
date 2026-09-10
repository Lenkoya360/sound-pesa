from django.urls import path
from . import views

urlpatterns = [
    path('', views.BlockchainStatusListView.as_view(), name='blockchain_list'),
    path('status/<str:blockchain>/', views.BlockchainStatusView.as_view(), name='blockchain_status'),
    path('<str:blockchain>/balance/<str:address>/', views.BlockchainBalanceView.as_view(), name='blockchain_balance'),
    path('addresses/create/', views.BlockchainAddressCreateView.as_view(), name='blockchain_address_create'),
    path('estimate-fee/', views.BlockchainEstimateFeeView.as_view(), name='blockchain_estimate_fee'),
    path('transaction-status/', views.BlockchainTransactionStatusView.as_view(), name='blockchain_transaction_status'),
]