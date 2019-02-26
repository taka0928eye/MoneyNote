import bootstrap_datepicker_plus as datetimepicker
from django import forms
from cms.models import Trade, User
import datetime
from django.contrib.auth.forms import (AuthenticationForm, UserCreationForm, 
PasswordChangeForm, PasswordResetForm, SetPasswordForm)


CHOICES = (
    ("", "選択肢から選んでください"),
    ("JPY", "円"),
    ("USD", "ドル"),
    ("EUR", "ユーロ"),
    ("GBP", "ポンド")
)


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label  # placeholderにフィールドのラベルを入れる

class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        if User.USERNAME_FIELD == 'email':
            fields = ('email',)
        else:
            fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        if User.USERNAME_FIELD == 'email':
            fields = ('email', 'first_name', 'last_name')
        else:
            fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class MyPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class MyPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class MySetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class TradeForm(forms.ModelForm):
    class Meta:
        model = Trade
        fields = ("date", "name", "supplier", "price", "currency",)
        widgets = {
            "date": datetimepicker.DatePickerInput(format='%Y-%m-%d',
            options={
                "locale": "ja",
                "dayViewHeaderFormat": "YYYY年 MMMM",
            }),
            "currency": forms.Select(choices=CHOICES),
        }

class SearchForm(forms.Form):
    start = forms.DateField(label = "開始日", required = False, widget = datetimepicker.DatePickerInput(format='%Y-%m-%d',
    options={
        "locale": "ja",
        "dayViewHeaderFormat": "YYYY年 MMMM",
        }))
    end = forms.DateField(label = "終了日", required = False, widget = datetimepicker.DatePickerInput(format='%Y-%m-%d',
    options={
        "locale": "ja",
        "dayViewHeaderFormat": "YYYY年 MMMM",
        }))
    name = forms.CharField(label = "品目名", max_length=255, required = False)
    supplier = forms.CharField(label = "取引先", max_length=255, required = False)
    min_price = forms.FloatField(label = "最低金額", required = False)
    max_price = forms.FloatField(label = "最高金額", required = False)
    currency = forms.CharField(label = "通貨", max_length=3, required = False, widget=forms.Select(choices=CHOICES))

    def clean_end(self):
        end = self.cleaned_data["end"]
        start = self.cleaned_data["start"]
        if end < start:
            raise forms.ValidationError("開始日よりも遅い日付を設定してください")
        return end

    def clean_max_price(self):
        max_price = float(self.cleaned_data["max_price"])
        min_price = float(self.cleaned_data["min_price"])
        if max_price < min_price:
            raise forms.ValidationError("最低金額よりも高い金額を設定してください")
        return max_price
