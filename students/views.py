import io, csv, json, pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from .forms import UploadFileForm

def read_into_df(f):
    name = getattr(f, 'name', 'file')
    lower = name.lower()
    try:
        if lower.endswith('.csv'):
            df = pd.read_csv(f)
        elif lower.endswith('.xls') or lower.endswith('.xlsx'):
            df = pd.read_excel(f)
        else:
            raise ValueError('Unsupported file type')
    except Exception as e:
        raise
   
    df.columns = [str(c).strip() for c in df.columns]
    df = df.fillna('')
    return df

def home(request):
    form = UploadFileForm()
    columns = []
    data = None
   
    if request.session.get('student_data'):
        try:
            df = pd.read_json(request.session['student_data'])
            columns = list(df.columns)
            data = df.to_dict(orient='records')
        except Exception:
           
            request.session.pop('student_data', None)

    return render(request, 'students/home.html', {'form': form, 'columns': columns, 'data': data})

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['file']
            try:
                df = read_into_df(f)
            except Exception as e:
                return render(request, 'students/home.html', {'form': form, 'error': f'Failed to parse file: {e}'})

            # Save raw dataframe to session (unfiltered) as json
            request.session['student_data'] = df.to_json()
            request.session.modified = True
            return redirect('home')
    return redirect('home')

def export_csv(request):
    if not request.session.get('student_data'):
        return HttpResponse('No data to export', status=400)
    df = pd.read_json(request.session['student_data'])
    # Optional filters via GET params (exact match)
    branch = request.GET.get('branch','').strip()
    year = request.GET.get('year','').strip()
    interest = request.GET.get('interest','').strip()
    if branch:
        if 'Branch' in df.columns:
            df = df[df['Branch'].astype(str).str.strip() == branch]
    if year:
        if 'Year' in df.columns:
            df = df[df['Year'].astype(str).str.strip() == year]
    if interest:
        if 'Interests' in df.columns:
            df = df[df['Interests'].astype(str).str.strip() == interest]

    buf = io.StringIO()
    df.to_csv(buf, index=False)
    resp = HttpResponse(buf.getvalue(), content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename=filtered_export.csv'
    return resp

@csrf_exempt
def send_email(request):
   
    if request.method != 'POST':
        return JsonResponse({'error':'POST required'}, status=400)
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error':'Invalid JSON'}, status=400)
    subject = payload.get('subject', 'Hello from Dashboard')
    message_template = payload.get('message', 'Hello {name},')
    selected = payload.get('selected', [])
    sent = 0
    for row in selected:
        email = row.get('Email') or row.get('email') or row.get('Email Address') or ''
        name = row.get('Name') or row.get('Full Name') or ''
        if email:
            personalized = message_template.replace('{name}', name)
            try:
                send_mail(subject, personalized, 'no-reply@example.com', [email])
                sent += 1
            except Exception as e:
                print('Email failed for', email, e)
    return JsonResponse({'status':'ok', 'sent': sent})
