from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ---------- existing paths ---------- #
    path('signup', views.signup, name='accounts.signup'),
    path('login/', views.login, name='accounts.login'),
    path('logout/', views.logout, name='accounts.logout'),

    # ---------- SECURITY-QUESTION reset flow ---------- #
    # step 1: ask username + birth city
    path(
        'password_reset/',
        views.SecurityQuestionView.as_view(),
        name='password_reset',
    ),
    # step 2: set new password (re-uses your old confirm template)
    path(
        'password_reset/confirm/',
        views.SetNewPasswordView.as_view(),
        name='password_reset_confirm',
    ),
    # final "done" page – keep Django's stock view & your template
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/registration/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),

    # ---------- any other existing paths ---------- #
    #path('orders/', views.orders, name='accounts.orders'),
]
