from django.shortcuts import render, redirect
from django.contrib import messages
from eduweb.models import Faculty, Department, Program, BlogPost


# ──────────────────────────────────────────────
# Helper: MELBAC faculty slugs (subset of all faculties)
# Adjust these slugs to match what is actually seeded in your Faculty table.
MELBAC_FACULTY_SLUGS = [
    'faculty-of-christian-education',
    'faculty-of-church-management-administration',
    'faculty-of-arts',
]
# ──────────────────────────────────────────────


def index(request):
    """
    MELBAC public homepage.
    Pulls the three MELBAC faculties with their programs for the
    academic overview section, and the 6 most recent blog posts.
    """
    faculties = (
        Faculty.objects
        .filter(slug__in=MELBAC_FACULTY_SLUGS, is_active=True)
        .prefetch_related('departments__programs')
        .order_by('display_order')
    )

    recent_posts = (
        BlogPost.objects
        .filter(status='published')
        .select_related('author')
        .order_by('-publish_date')[:6]
    )

    context = {
        'faculties': faculties,
        'recent_posts': recent_posts,
    }
    return render(request, 'melbac/index.html', context)


def about(request):
    """MELBAC About page — history, mission, boards."""
    context = {}
    return render(request, 'melbac/about.html', context)


def academics(request):
    """
    Academics overview: all MELBAC faculties → departments → programs.
    Also renders the Academic Calendar.
    """
    faculties = (
        Faculty.objects
        .filter(slug__in=MELBAC_FACULTY_SLUGS, is_active=True)
        .prefetch_related(
            'departments',
            'departments__programs',
        )
        .order_by('display_order')
    )

    context = {
        'faculties': faculties,
    }
    return render(request, 'melbac/academics.html', context)


def activities(request):
    """Student Activities page."""
    context = {}
    return render(request, 'melbac/activities.html', context)


def contact(request):
    """Contact page — renders form and handles POST submission."""
    from eduweb.models import ContactMessage

    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', 'other')
        message = request.POST.get('message', '').strip()

        if name and email and message:
            ContactMessage.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=name,
                email=email,
                subject=subject,
                message=message,
            )
            messages.success(request, 'Your message has been received. We will respond shortly.')
            return redirect('melbac:contact')
        else:
            messages.error(request, 'Please fill in all required fields.')

    context = {}
    return render(request, 'melbac/contact.html', context)


def blog_list(request):
    """MELBAC blog listing."""
    posts = (
        BlogPost.objects
        .filter(status='published')
        .select_related('author')
        .order_by('-publish_date')
    )
    context = {'posts': posts}
    return render(request, 'melbac/blog.html', context)