from django.shortcuts import render

# Create your views here.

# Create your views here.
def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def apply(request):
    return render(request, 'form.html')

def detail(request):
    return render(request, 'detail.html')

def admission_course(request):
    return render(request, 'course.html')
