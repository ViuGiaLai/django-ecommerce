from django import forms
from django.contrib.auth.models import User
from .models import Profile
from .models import Address
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, label='Tên')
    last_name = forms.CharField(max_length=30, required=True, label='Họ')
    email = forms.EmailField(required=True, label='Email')
    dob = forms.DateField(required=False, label='Ngày sinh', widget=forms.DateInput(attrs={'type': 'date'}))
    phone = forms.CharField(max_length=15, required=False, label='Điện thoại')
    gender = forms.ChoiceField(choices=[('M', 'Nam'), ('F', 'Nữ')], required=False, label='Giới tính')
    image = forms.ImageField(required=False, label='Ảnh', widget=forms.ClearableFileInput(attrs={'clear_checkbox_label': 'Xóa'}))

    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].initial = self.instance.user.first_name
        self.fields['last_name'].initial = self.instance.user.last_name
        self.fields['email'].initial = self.instance.user.email
        self.fields['gender'].choices = [('M', 'Nam'), ('F', 'Nữ')]  # Ensure choices are set

    def save(self, commit=True):
        user = self.instance.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            super(ProfileUpdateForm, self).save(commit=commit)
        return self.instance
    
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'email', 'dob', 'phone', 'gender', 'image']

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'phone', 'street_address', 'province', 'district', 'ward']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Họ và tên'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Số điện thoại'}),
            'street_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Địa chỉ cụ thể'}),
            'province': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tỉnh/Thành phố'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Quận/Huyện'}),
            'ward': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phường/Xã'})
        }

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập email của bạn'
        })
    )
    
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize form field widgets and attributes
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nhập tên đăng nhập'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Xác nhận mật khẩu'
        })
        
        # Custom error messages in Vietnamese
        self.fields['username'].error_messages.update({
            'required': 'Vui lòng nhập tên đăng nhập',
            'unique': 'Tên đăng nhập đã tồn tại'
        })
        self.fields['email'].error_messages.update({
            'required': 'Vui lòng nhập email',
            'invalid': 'Email không hợp lệ'
        })
        self.fields['password1'].error_messages.update({
            'required': 'Vui lòng nhập mật khẩu'
        })
        self.fields['password2'].error_messages.update({
            'required': 'Vui lòng xác nhận mật khẩu',
            'password_mismatch': 'Hai mật khẩu không khớp'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Email đã được sử dụng')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập tên đăng nhập',
            'autocomplete': 'username',
        }),
        error_messages={
            'required': 'Vui lòng nhập tên đăng nhập',
        }
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu',
            'autocomplete': 'current-password',
        }),
        error_messages={
            'required': 'Vui lòng nhập mật khẩu',
        }
    )

    error_messages = {
        'invalid_login': 'Tên đăng nhập hoặc mật khẩu không chính xác',
        'inactive': 'Tài khoản này đã bị vô hiệu hóa',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].error_messages.update({
            'required': 'Vui lòng nhập tên đăng nhập',
        })
        self.fields['password'].error_messages.update({
            'required': 'Vui lòng nhập mật khẩu',
        })
