from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, CustomErrorList, SecurityQuestionForm, NewPasswordForm
from .models import BirthCitySecret
from django.contrib.auth.models import User
from django.views.generic import FormView
@login_required
def logout(request):
    auth_logout(request)
    return redirect('home.index')


def login(request):
    template_data = {'title': 'Login'}
    if request.method == 'GET':
        return render(request, 'accounts/login.html',
                      {'template_data': template_data})
    # POST
    user = authenticate(
        request,
        username=request.POST['username'],
        password=request.POST['password'],
    )
    if user is None:
        template_data['error'] = 'The username or password is incorrect.'
        return render(request, 'accounts/login.html',
                      {'template_data': template_data})
    auth_login(request, user)
    return redirect('home.index')


def signup(request):
    template_data = {'title': 'Sign Up'}
    if request.method == 'GET':
        template_data['form'] = CustomUserCreationForm()
        return render(request, 'accounts/signup.html',
                      {'template_data': template_data})

    # POST
    form = CustomUserCreationForm(
        request.POST,
        error_class=CustomErrorList,
    )
    if not form.is_valid():
        template_data['form'] = form
        return render(request, 'accounts/signup.html',
                      {'template_data': template_data})

    # save user & secret answer
    user = form.save()
    secret = BirthCitySecret(user=user)
    secret.set_answer(form.cleaned_data['birth_city'])
    secret.save()
    return redirect('accounts.login')


# ----------  password-reset (new) ---------- #
class SecurityQuestionView(FormView):
    """
    Step 1 – verify username + security answer.
    On success, store user id in session and redirect to set-new-pw page.
    """
    template_name = 'accounts/registration/password_reset_form.html'
    form_class = SecurityQuestionForm

    def form_valid(self, form):
        username = form.cleaned_data['username'].strip()
        answer = form.cleaned_data['birth_city'].strip()

        try:
            user = User.objects.get(username=username)
            secret = user.birthcitysecret  # OneToOne accessor
        except (User.DoesNotExist, BirthCitySecret.DoesNotExist):
            messages.error(self.request, 'Invalid username or answer.')
            return redirect('password_reset')

        if not secret.check_answer(answer):
            messages.error(self.request, 'Invalid username or answer.')
            return redirect('password_reset')

        # success – keep the user pk for step 2
        self.request.session['pwd_reset_uid'] = user.pk
        return redirect('password_reset_confirm')


class SetNewPasswordView(FormView):
    """
    Step 2 – let the verified user pick a new password.
    Uses existing confirm template.
    """
    template_name = 'accounts/registration/password_reset_confirm.html'

    def get_user(self):
        uid = self.request.session.get('pwd_reset_uid')
        if uid is None:
            return None
        try:
            return User.objects.get(pk=uid)
        except User.DoesNotExist:
            return None

    def get_form_class(self):
        user = self.get_user()
        return lambda *a, **kw: NewPasswordForm(user, *a, **kw)

    def form_valid(self, form):
        user = self.get_user()
        if user is None:
            messages.error(self.request, 'Session expired. Try again.')
            return redirect('password_reset')

        form.save()                      # sets new password
        update_session_auth_hash(self.request, user)
        # clean up
        self.request.session.pop('pwd_reset_uid', None)
        return redirect('password_reset_complete')