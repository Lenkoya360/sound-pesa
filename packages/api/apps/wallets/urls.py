from django.urls import path
from . import views

urlpatterns = [
    path('', views.WalletListView.as_view(), name='wallet_list'),
    path('create/', views.WalletCreateView.as_view(), name='wallet_create'),
    path('create-all/', views.WalletCreateAllView.as_view(), name='wallet_create_all'),
    path('summary/', views.WalletSummaryView.as_view(), name='wallet_summary'),
    path('<str:pk>/', views.WalletDetailView.as_view(), name='wallet_detail'),
    path('<str:blockchain>/balance/', views.WalletBalanceView.as_view(), name='wallet_balance'),
    path('<str:blockchain>/history/', views.WalletTransactionHistoryView.as_view(), name='wallet_history'),
    path('<str:blockchain>/refresh/', views.refresh_wallet_balance, name='wallet_refresh'),
]