from django.urls import path
from cms import views

app_name = "cms"
urlpatterns = [
    path("login/", views.Login.as_view(), name="login"),
    path("logout/", views.Logout.as_view(), name="logout"),
    path('user_create/', views.UserCreate.as_view(), name='user_create'),
    path('user_create/done', views.UserCreateDone.as_view(), name='user_create_done'),
    path('user_create/complete/<token>/', views.UserCreateComplete.as_view(), name='user_create_complete'),
    path('user_detail/<int:pk>/', views.UserDetail.as_view(), name='user_detail'),
    path('user_update/<int:pk>/', views.UserUpdate.as_view(), name='user_update'),
    path('password_change/', views.PasswordChange.as_view(), name='password_change'),
    path('password_change/done/', views.PasswordChangeDone.as_view(), name='password_change_done'),
    path("trade/", views.trade_list, name="trade_list"),   #一覧
    path("trade/add/", views.trade_edit, name="trade_add"),  # 登録
    path("trade/mod/<int:id>/", views.trade_edit, name="trade_mod"),  # 修正
    path("trade/del/<int:id>/", views.trade_del, name="trade_del"),   # 削除
    path("trade/export/", views.export, name='export'),
    path("trade/search/", views.trade_search, name="trade_search"),   # 検索
]
