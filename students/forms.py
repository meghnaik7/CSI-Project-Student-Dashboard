from django import forms
class UploadFileForm(forms.Form):
    file = forms.FileField(label='Upload Excel or CSV', help_text='(.xlsx, .xls or .csv)')
