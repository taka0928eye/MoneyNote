from django.shortcuts import render, resolve_url
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView,
PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView)
from django.contrib.sites.shortcuts import get_current_site
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.views import generic
from cms.models import Trade, User
from cms.forms import (TradeForm, SearchForm, UserCreateForm, LoginForm, UserUpdateForm, 
MyPasswordChangeForm, MyPasswordResetForm, MySetPasswordForm)

import math
import numpy as np
import pandas as pd
import pandas_datareader.data as web
from datetime import timedelta
import datetime
import csv
import urllib

trades = Trade.objects.all().order_by('id')
User = get_user_model()

class Top(generic.TemplateView):
    template_name = "trade_list.html"


class Login(LoginView):
    form_class = LoginForm
    template_name = 'login.html'


class Logout(LoginRequiredMixin, LogoutView):
    template_name = 'trade_list.html'

class UserCreate(generic.CreateView):
    template_name = 'user_create.html'
    form_class = UserCreateForm

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # アクティベーションURLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': self.request.scheme,
            'domain': domain,
            'token': dumps(user.pk),
            'user': user,
        }

        subject_template = get_template('create/subject.txt')
        subject = subject_template.render(context)

        message_template = get_template('create/message.txt')
        message = message_template.render(context)

        user.email_user(subject, message)
        return redirect('cms:user_create_done')


class UserCreateDone(generic.TemplateView):
    template_name = 'user_create_done.html'


class UserCreateComplete(generic.TemplateView):
    template_name = 'user_create_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)  # デフォルトでは1日以内

    def get(self, request, **kwargs):
        token = kwargs.get('token')
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                return HttpResponseBadRequest()
            else:
                if not user.is_active:
                    # 問題なければ本登録とする
                    user.is_active = True
                    user.save()
                    return super().get(request, **kwargs)

        return HttpResponseBadRequest()

class OnlyYouMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return user.pk == self.kwargs['pk'] or user.is_superuser


class UserDetail(OnlyYouMixin, generic.DetailView):
    model = User
    template_name = 'user_detail.html'


class UserUpdate(OnlyYouMixin, generic.UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'user_form.html'

    def get_success_url(self):
        return resolve_url('cms:user_detail', pk=self.kwargs['pk'])

class PasswordChange(PasswordChangeView):
    form_class = MyPasswordChangeForm
    success_url = reverse_lazy('cms:password_change_done')
    template_name = 'password_change.html'


class PasswordChangeDone(PasswordChangeDoneView):
    template_name = 'password_change_done.html'


class PasswordReset(PasswordResetView):
    subject_template_name = 'password_reset/subject.txt'
    email_template_name = 'password_reset/message.txt'
    template_name = 'password_reset_form.html'
    form_class = MyPasswordResetForm
    success_url = reverse_lazy('cms:password_reset_done')


class PasswordResetDone(PasswordResetDoneView):
    template_name = 'password_reset_done.html'


class PasswordResetConfirm(PasswordResetConfirmView):
    form_class = MySetPasswordForm
    success_url = reverse_lazy('cms:password_reset_complete')
    template_name = 'password_reset_confirm.html'


class PasswordResetComplete(PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'

def trade_list(request):
    trades = Trade.objects.all().order_by('id')
    return render(request,
                  "trade_list.html",     # 使用するテンプレート
                  {"trades": trades, "op": 0})         # テンプレートに渡すデータ


def trade_edit(request, id=None):
    if id: # 修正時
        trade = get_object_or_404(Trade, pk=id)
    else:  # 追加時
        trade = Trade()

    if request.method == 'POST':
        form = TradeForm(request.POST, instance=trade)
        if form.is_valid():
            trade = form.save(commit=False)
            trade.save()
            return redirect("cms:trade_list")
    else:
        form = TradeForm(instance=trade)

    return render(request, "trade_edit.html", dict(form=form, id=id))    


def trade_del(request, id):
    trade = get_object_or_404(Trade, pk=id)
    trade.delete()
    return redirect("cms:trade_list")

def export(request):
    global trades
    currency = {0: "DEXJPUS", 1: "DEXUSEU", 2: "DEXUSUK",}
    for trade in trades:
        t = trade.date - timedelta(7)
        t1str = t.strftime('%Y-%m-%d')
        t2str = trade.date.strftime('%Y-%m-%d')
        df = web.DataReader(currency.values(), "fred", t1str, t2str)
        rate = df.values
        try:
            if trade.currency == "USD":
                trade.price = math.ceil(trade.price * rate[0][0])
            elif trade.currency == "EUR":
                trade.price = math.ceil(trade.price * rate[0][0] * rate[0][1])
                trade.currency = "JPY"
            elif trade.currency == "GBP":
                trade.price = math.ceil(trade.price * rate[0][0] * rate[0][2])
                trade.currency = "JPY"
            else:
                pass
        except:
            pass
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=MoneyNote.csv'    
    writer = csv.writer(response)
    writer.writerow(["ID", "日付", "品目名", "取引先", "金額 (円)"])
    for trade in trades:
        writer.writerow([trade.id, trade.date, trade.name, trade.supplier, trade.price])
    return response

def trade_search(request):
    global trades
    if request.method == 'POST':
        form = SearchForm(request.POST)
        start = request.POST["start"]
        end = request.POST["end"]
        name = request.POST["name"]
        supplier = request.POST["supplier"]
        min_price = request.POST["min_price"]
        max_price = request.POST["max_price"]
        currency = request.POST["currency"]

        if start != "":
            trades = trades.filter(date__gte=start)
        else:
            pass
        if end != "":
            trades = trades.filter(date__lte=end)
        else:
            pass
        if name != "":
            trades = trades.filter(name__contains=name)
        else:
            pass
        if supplier != "":
            trades = trades.filter(supplier__contains=supplier)
        else:
            pass
        if min_price != "":
            trades = trades.filter(price__gte=min_price)
        else:
            pass
        if max_price != "":
            trades = trades.filter(price__lte=max_price)
        else:
            pass
        if currency != "":
            trades = trades.filter(currency__contains=currency)
        else:
            pass
        return render(request,
                  "trade_list.html",     # 使用するテンプレート
                  {"trades": trades, "op": 1})         # テンプレートに渡すデータ    
    else:
        form = SearchForm(None)

    return render(request, "trade_search.html", {"form": form})    
