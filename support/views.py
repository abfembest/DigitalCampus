"""
support/views.py — uses eduweb.SupportTicket as the ticket model.

Field mapping from old support.Ticket → eduweb.SupportTicket:
  title        → subject
  created_by   → user
  status values: open, in_progress, waiting_response, resolved, closed
  priority values: low, normal, high, urgent  (no 'medium' / 'critical')
  category values: technical, account, course, payment, other
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta

from eduweb.models import SupportTicket, TicketReply
from .models import (
    SupportTicketExtra, SupportDepartment, SLAPolicy,
    TicketAttachment, TicketHistory, TicketEscalation, TicketFeedback,
    KBCategory, KBArticle, FAQCategory, FAQ, CannedResponse,
    ChatSession, AgentProfile, SupportAnnouncement, SupportAuditLog,
)
from .permissions import support_required, support_admin_required, get_client_ip


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _log(request, action, target_type='', target_id='', description=''):
    SupportAuditLog.objects.create(
        actor=request.user,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        description=description,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
    )


def _get_or_create_extra(ticket):
    extra, _ = SupportTicketExtra.objects.get_or_create(ticket=ticket)
    return extra


OPEN_STATUSES = ['open', 'in_progress', 'waiting_response']
CLOSED_STATUSES = ['resolved', 'closed']


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@support_required
def dashboard(request):
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    all_tickets = SupportTicket.objects.all()
    open_qs = all_tickets.filter(status__in=OPEN_STATUSES)

    total_open = open_qs.count()
    urgent_count = open_qs.filter(priority='urgent').count()
    resolved_today = all_tickets.filter(status='resolved', resolved_at__gte=today_start).count()

    # SLA — tickets with due_at in the past and still open
    sla_breached = SupportTicketExtra.objects.filter(
        due_at__lt=now, ticket__status__in=OPEN_STATUSES
    ).count()
    sla_at_risk = SupportTicketExtra.objects.filter(
        due_at__gt=now,
        due_at__lt=now + timedelta(hours=2),
        ticket__status__in=OPEN_STATUSES
    ).select_related('ticket').order_by('due_at')[:5]

    waiting_user = all_tickets.filter(status='waiting_response').count()
    unassigned = open_qs.filter(assigned_to__isnull=True).count()
    escalated = SupportTicketExtra.objects.filter(
        is_escalated=True, ticket__status__in=OPEN_STATUSES
    ).count()

    # 14-day volume
    fourteen_days = [now - timedelta(days=i) for i in range(13, -1, -1)]
    chart_labels = [d.strftime('%b %d') for d in fourteen_days]
    chart_created = []
    chart_resolved = []
    for day in fourteen_days:
        day_end = day.replace(hour=23, minute=59, second=59)
        day_start = day.replace(hour=0, minute=0, second=0)
        chart_created.append(all_tickets.filter(created_at__range=(day_start, day_end)).count())
        chart_resolved.append(all_tickets.filter(status='resolved', resolved_at__range=(day_start, day_end)).count())

    # Priority breakdown
    priority_counts = {p: open_qs.filter(priority=p).count() for p in ['low', 'normal', 'high', 'urgent']}

    # Recent tickets
    recent_tickets = all_tickets.select_related('user', 'assigned_to').order_by('-created_at')[:10]
    my_tickets = all_tickets.filter(
        assigned_to=request.user, status__in=OPEN_STATUSES
    ).select_related('user').order_by('-created_at')[:8]

    # CSAT
    avg_csat = TicketFeedback.objects.aggregate(avg=Avg('rating'))['avg']

    # Agent leaderboard
    leaderboard = (
        User.objects.filter(
            assigned_tickets__status='resolved',
            assigned_tickets__resolved_at__gte=now - timedelta(days=30)
        )
        .annotate(resolved=Count('assigned_tickets'))
        .order_by('-resolved')[:5]
    )

    recent_feedback = TicketFeedback.objects.select_related('ticket', 'submitted_by').order_by('-created_at')[:5]

    return render(request, 'support/dashboard.html', {
        'total_open': total_open,
        'urgent_count': urgent_count,
        'resolved_today': resolved_today,
        'sla_breached': sla_breached,
        'sla_at_risk': sla_at_risk,
        'waiting_user': waiting_user,
        'unassigned': unassigned,
        'escalated': escalated,
        'avg_csat': round(avg_csat, 1) if avg_csat else None,
        'chart_labels': chart_labels,
        'chart_created': chart_created,
        'chart_resolved': chart_resolved,
        'priority_counts': priority_counts,
        'recent_tickets': recent_tickets,
        'my_tickets': my_tickets,
        'leaderboard': leaderboard,
        'recent_feedback': recent_feedback,
        'kb_count': KBArticle.objects.filter(status='published').count(),
        'resolved_week': all_tickets.filter(
            status='resolved',
            resolved_at__gte=now - timedelta(days=7)
        ).count(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Ticket List
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@support_required
def ticket_list(request):
    qs = SupportTicket.objects.select_related('user', 'assigned_to').order_by('-created_at')

    # Filters
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    category_filter = request.GET.get('category', '')
    quick = request.GET.get('quick', '')

    if search:
        qs = qs.filter(
            Q(ticket_id__icontains=search) |
            Q(subject__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search)
        )
    if status_filter:
        qs = qs.filter(status=status_filter)
    if priority_filter:
        qs = qs.filter(priority=priority_filter)
    if category_filter:
        qs = qs.filter(category=category_filter)

    if quick == 'mine':
        qs = qs.filter(assigned_to=request.user)
    elif quick == 'open':
        qs = qs.filter(status__in=OPEN_STATUSES)
    elif quick == 'escalated':
        qs = qs.filter(extra__is_escalated=True)
    elif quick == 'sla':
        qs = qs.filter(extra__due_at__lt=timezone.now(), status__in=OPEN_STATUSES)
    elif quick == 'urgent':
        qs = qs.filter(priority='urgent')
    elif quick == 'waiting':
        qs = qs.filter(status='waiting_response')
    elif quick == 'unassigned':
        qs = qs.filter(assigned_to__isnull=True, status__in=OPEN_STATUSES)

    paginator = Paginator(qs, 25)
    tickets = paginator.get_page(request.GET.get('page'))

    return render(request, 'support/ticket_list.html', {
        'tickets': tickets,
        'search': search,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'quick': quick,
        'status_choices': SupportTicket.STATUS_CHOICES,
        'priority_choices': SupportTicket.PRIORITY_CHOICES,
        'category_choices': SupportTicket.CATEGORY_CHOICES,
        'total_count': qs.count(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Ticket Detail
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@support_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(SupportTicket.objects.select_related('user', 'assigned_to'), ticket_id=ticket_id)
    extra = _get_or_create_extra(ticket)

    # Increment view count
    SupportTicketExtra.objects.filter(pk=extra.pk).update(view_count=extra.view_count + 1)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'reply':
            body = request.POST.get('body', '').strip()
            is_internal = request.POST.get('is_internal') == '1'
            if body:
                reply = TicketReply.objects.create(
                    ticket=ticket,
                    author=request.user,
                    message=body,
                    is_internal_note=is_internal,
                )
                # Mark first response
                if not extra.first_response_at and not is_internal:
                    extra.first_response_at = timezone.now()
                    extra.save(update_fields=['first_response_at'])

                # Handle attachments
                for f in request.FILES.getlist('attachments'):
                    if f.size <= 10 * 1024 * 1024:
                        TicketAttachment.objects.create(
                            ticket=ticket,
                            reply=reply,
                            uploaded_by=request.user,
                            file=f,
                            original_name=f.name,
                            file_size=f.size,
                        )
                # Auto-move to in_progress if open
                if ticket.status == 'open':
                    ticket.status = 'in_progress'
                    ticket.save(update_fields=['status'])
                TicketHistory.objects.create(
                    ticket=ticket, changed_by=request.user,
                    field_name='reply', new_value='Reply added',
                    note='Internal' if is_internal else ''
                )
                _log(request, 'ticket_reply', 'SupportTicket', ticket.ticket_id, f'{"Internal note" if is_internal else "Reply"} added')
                messages.success(request, 'Reply posted successfully.')
            return redirect('support:ticket_detail', ticket_id=ticket_id)

        elif action == 'update_status':
            old_status = ticket.status
            new_status = request.POST.get('status')
            valid = [s[0] for s in SupportTicket.STATUS_CHOICES]
            if new_status in valid:
                ticket.status = new_status
                if new_status == 'resolved':
                    ticket.resolved_at = timezone.now()
                ticket.save()
                TicketHistory.objects.create(
                    ticket=ticket, changed_by=request.user,
                    field_name='status', old_value=old_status, new_value=new_status
                )
                _log(request, 'status_change', 'SupportTicket', ticket.ticket_id, f'{old_status} → {new_status}')
                messages.success(request, f'Status updated to {new_status}.')
            return redirect('support:ticket_detail', ticket_id=ticket_id)

        elif action == 'assign':
            agent_id = request.POST.get('agent_id')
            old_agent = ticket.assigned_to
            if agent_id:
                agent = get_object_or_404(User, pk=agent_id)
                ticket.assigned_to = agent
                if ticket.status == 'open':
                    ticket.status = 'in_progress'
            else:
                ticket.assigned_to = None
            ticket.save()
            TicketHistory.objects.create(
                ticket=ticket, changed_by=request.user,
                field_name='assigned_to',
                old_value=str(old_agent) if old_agent else '',
                new_value=str(ticket.assigned_to) if ticket.assigned_to else 'Unassigned',
            )
            _log(request, 'assign', 'SupportTicket', ticket.ticket_id)
            messages.success(request, 'Ticket assignment updated.')
            return redirect('support:ticket_detail', ticket_id=ticket_id)

        elif action == 'escalate':
            reason = request.POST.get('reason', 'other')
            notes = request.POST.get('notes', '')
            escalated_to_id = request.POST.get('escalated_to_id')
            escalated_to = User.objects.filter(pk=escalated_to_id).first() if escalated_to_id else None
            TicketEscalation.objects.create(
                ticket=ticket, escalated_by=request.user,
                escalated_to=escalated_to,
                reason=reason, notes=notes,
                level=extra.escalation_level + 1,
            )
            extra.is_escalated = True
            extra.escalation_level += 1
            extra.save(update_fields=['is_escalated', 'escalation_level'])
            ticket.status = 'in_progress'
            ticket.save(update_fields=['status'])
            TicketHistory.objects.create(
                ticket=ticket, changed_by=request.user,
                field_name='escalated', new_value='true', note=notes
            )
            _log(request, 'escalate', 'SupportTicket', ticket.ticket_id, notes)
            messages.warning(request, 'Ticket escalated.')
            return redirect('support:ticket_detail', ticket_id=ticket_id)

        elif action == 'update_priority':
            old_priority = ticket.priority
            new_priority = request.POST.get('priority')
            valid_priorities = [p[0] for p in SupportTicket.PRIORITY_CHOICES]
            if new_priority in valid_priorities:
                ticket.priority = new_priority
                ticket.save(update_fields=['priority'])
                TicketHistory.objects.create(
                    ticket=ticket, changed_by=request.user,
                    field_name='priority', old_value=old_priority, new_value=new_priority
                )
                messages.success(request, f'Priority updated to {new_priority}.')
            return redirect('support:ticket_detail', ticket_id=ticket_id)

        elif action == 'reopen':
            ticket.status = 'open'
            ticket.save(update_fields=['status'])
            extra.reopen_count += 1
            extra.save(update_fields=['reopen_count'])
            TicketHistory.objects.create(
                ticket=ticket, changed_by=request.user,
                field_name='status', old_value='closed', new_value='open', note='Reopened'
            )
            messages.info(request, 'Ticket reopened.')
            return redirect('support:ticket_detail', ticket_id=ticket_id)

    replies = ticket.replies.select_related('author').all()
    attachments = ticket.attachments.select_related('uploaded_by').all()
    history = ticket.history.select_related('changed_by').all()
    escalations = ticket.escalations.select_related('escalated_by', 'escalated_to').all()
    feedback = TicketFeedback.objects.filter(ticket=ticket).first()
    agents = User.objects.filter(
        Q(is_staff=True) | Q(profile__role__in=['admin', 'support'])
    ).select_related('profile').order_by('first_name')
    canned_responses = CannedResponse.objects.filter(is_active=True).order_by('title')

    return render(request, 'support/ticket_detail.html', {
        'ticket': ticket,
        'extra': extra,
        'replies': replies,
        'attachments': attachments,
        'history': history,
        'escalations': escalations,
        'feedback': feedback,
        'agents': agents,
        'canned_responses': canned_responses,
        'status_choices': SupportTicket.STATUS_CHOICES,
        'priority_choices': SupportTicket.PRIORITY_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Ticket Create
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@support_required
def ticket_create(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', 'other')
        priority = request.POST.get('priority', 'normal')
        source = request.POST.get('source', 'portal')
        assigned_to_id = request.POST.get('assigned_to_id')
        department_id = request.POST.get('department_id')

        if not subject or not description:
            messages.error(request, 'Subject and description are required.')
        else:
            created_user = request.user
            if user_id:
                created_user = get_object_or_404(User, pk=user_id)

            assigned_to = None
            if assigned_to_id:
                assigned_to = User.objects.filter(pk=assigned_to_id).first()

            ticket = SupportTicket.objects.create(
                user=created_user,
                subject=subject,
                description=description,
                category=category,
                priority=priority,
                status='open' if not assigned_to else 'in_progress',
                assigned_to=assigned_to,
            )
            extra = SupportTicketExtra.objects.create(
                ticket=ticket,
                source=source,
                tags=request.POST.get('tags', ''),
            )
            if department_id:
                dept = SupportDepartment.objects.filter(pk=department_id).first()
                if dept:
                    extra.department = dept
                    extra.save(update_fields=['department'])

            for f in request.FILES.getlist('attachments'):
                if f.size <= 10 * 1024 * 1024:
                    TicketAttachment.objects.create(
                        ticket=ticket, uploaded_by=request.user,
                        file=f, original_name=f.name, file_size=f.size,
                    )

            _log(request, 'ticket_create', 'SupportTicket', ticket.ticket_id, subject)
            messages.success(request, f'Ticket {ticket.ticket_id} created.')
            return redirect('support:ticket_detail', ticket_id=ticket.ticket_id)

    students = User.objects.all().order_by('first_name', 'last_name')
    agents = User.objects.filter(
        Q(is_staff=True) | Q(profile__role__in=['admin', 'support'])
    ).order_by('first_name')
    departments = SupportDepartment.objects.filter(is_active=True)

    return render(request, 'support/ticket_create.html', {
        'students': students,
        'agents': agents,
        'departments': departments,
        'category_choices': SupportTicket.CATEGORY_CHOICES,
        'priority_choices': SupportTicket.PRIORITY_CHOICES,
        'source_choices': SupportTicketExtra.SOURCE_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Base
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@support_required
def kb_list(request):
    qs = KBArticle.objects.select_related('category', 'author').all()
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    cat_filter = request.GET.get('category', '')
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(tags__icontains=search))
    if status_filter:
        qs = qs.filter(status=status_filter)
    if cat_filter:
        qs = qs.filter(category_id=cat_filter)
    paginator = Paginator(qs, 18)
    articles = paginator.get_page(request.GET.get('page'))
    return render(request, 'support/kb_list.html', {
        'articles': articles,
        'categories': KBCategory.objects.filter(is_active=True),
        'search': search,
        'status_filter': status_filter,
        'cat_filter': cat_filter,
        'total_published': KBArticle.objects.filter(status='published').count(),
        'total_draft': KBArticle.objects.filter(status='draft').count(),
    })


@login_required
@support_required
def kb_article_detail(request, slug):
    article = get_object_or_404(KBArticle, slug=slug)
    KBArticle.objects.filter(pk=article.pk).update(view_count=article.view_count + 1)
    related = article.related_articles.filter(status='published')[:4]
    return render(request, 'support/kb_article_detail.html', {'article': article, 'related': related})


@login_required
@support_required
def kb_article_create(request):
    if request.method == 'POST':
        cat = get_object_or_404(KBCategory, pk=request.POST.get('category_id'))
        article = KBArticle.objects.create(
            category=cat,
            title=request.POST.get('title', '').strip(),
            summary=request.POST.get('summary', '').strip(),
            body=request.POST.get('body', '').strip(),
            status=request.POST.get('status', 'draft'),
            tags=request.POST.get('tags', '').strip(),
            is_featured='is_featured' in request.POST,
            is_pinned='is_pinned' in request.POST,
            author=request.user,
        )
        messages.success(request, 'Article created.')
        return redirect('support:kb_article_detail', slug=article.slug)
    return render(request, 'support/kb_article_form.html', {
        'categories': KBCategory.objects.filter(is_active=True),
        'page_title': 'New Article',
    })


@login_required
@support_required
def kb_article_edit(request, slug):
    article = get_object_or_404(KBArticle, slug=slug)
    if request.method == 'POST':
        cat = get_object_or_404(KBCategory, pk=request.POST.get('category_id'))
        article.category = cat
        article.title = request.POST.get('title', '').strip()
        article.summary = request.POST.get('summary', '').strip()
        article.body = request.POST.get('body', '').strip()
        article.status = request.POST.get('status', 'draft')
        article.tags = request.POST.get('tags', '').strip()
        article.is_featured = 'is_featured' in request.POST
        article.is_pinned = 'is_pinned' in request.POST
        article.save()
        messages.success(request, 'Article updated.')
        return redirect('support:kb_article_detail', slug=article.slug)
    return render(request, 'support/kb_article_form.html', {
        'article': article,
        'categories': KBCategory.objects.filter(is_active=True),
        'page_title': f'Edit: {article.title}',
    })


# ─────────────────────────────────────────────────────────────────────────────
# FAQs
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@support_required
def faq_list(request):
    search = request.GET.get('search', '')
    categories = FAQCategory.objects.filter(is_active=True).prefetch_related('faqs')
    if search:
        categories = categories.filter(
            Q(faqs__question__icontains=search) | Q(faqs__answer__icontains=search)
        ).distinct()
    return render(request, 'support/faq_list.html', {'categories': categories, 'search': search})


@login_required
@support_required
def faq_create(request):
    if request.method == 'POST':
        cat = get_object_or_404(FAQCategory, pk=request.POST.get('category_id'))
        FAQ.objects.create(
            category=cat,
            question=request.POST.get('question', '').strip(),
            answer=request.POST.get('answer', '').strip(),
            order=int(request.POST.get('order', 0)),
            created_by=request.user,
        )
        messages.success(request, 'FAQ added.')
    return redirect('support:faq_list')


@login_required
@support_admin_required
def faq_delete(request, pk):
    if request.method == 'POST':
        FAQ.objects.filter(pk=pk).delete()
        messages.success(request, 'FAQ deleted.')
    return redirect('support:faq_list')


# ─────────────────────────────────────────────────────────────────────────────
# Canned Responses
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@support_required
def canned_list(request):
    search = request.GET.get('search', '')
    qs = CannedResponse.objects.filter(is_active=True)
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(body__icontains=search))
    return render(request, 'support/canned_list.html', {
        'canned': qs,
        'search': search,
        'category_choices': SupportTicket.CATEGORY_CHOICES,
    })


@login_required
@support_required
def canned_create(request):
    if request.method == 'POST':
        CannedResponse.objects.create(
            title=request.POST.get('title', '').strip(),
            body=request.POST.get('body', '').strip(),
            category=request.POST.get('category', ''),
            created_by=request.user,
        )
        messages.success(request, 'Canned response created.')
    return redirect('support:canned_list')


@login_required
@support_admin_required
def canned_delete(request, pk):
    if request.method == 'POST':
        CannedResponse.objects.filter(pk=pk).delete()
        messages.success(request, 'Canned response deleted.')
    return redirect('support:canned_list')


# ─────────────────────────────────────────────────────────────────────────────
# SLA Policies (admin)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@support_admin_required
def sla_list(request):
    return render(request, 'support/sla_list.html', {
        'slas': SLAPolicy.objects.all(),
        'priority_choices': SupportTicket.PRIORITY_CHOICES,
    })


@login_required
@support_admin_required
def sla_save(request):
    if request.method == 'POST':
        SLAPolicy.objects.update_or_create(
            priority=request.POST.get('priority'),
            defaults={
                'name': request.POST.get('name', '').strip(),
                'first_response_hours': int(request.POST.get('first_response_hours', 4)),
                'resolution_hours': int(request.POST.get('resolution_hours', 24)),
                'escalation_hours': int(request.POST.get('escalation_hours', 8)),
                'is_active': True,
            }
        )
        messages.success(request, 'SLA policy saved.')
    return redirect('support:sla_list')


# ─────────────────────────────────────────────────────────────────────────────
# Departments (admin)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@support_admin_required
def department_list(request):
    departments = SupportDepartment.objects.prefetch_related('members').annotate(
        ticket_count=Count('dept_tickets', filter=Q(dept_tickets__ticket__status__in=OPEN_STATUSES))
    )
    all_agents = User.objects.filter(
        Q(is_staff=True) | Q(profile__role__in=['admin', 'support'])
    ).order_by('first_name')
    return render(request, 'support/department_list.html', {
        'departments': departments,
        'all_agents': all_agents,
    })


@login_required
@support_admin_required
def department_save(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        head_id = request.POST.get('head_id')
        dept = SupportDepartment.objects.create(
            name=name,
            email=request.POST.get('email', '').strip(),
            description=request.POST.get('description', '').strip(),
            head=User.objects.filter(pk=head_id).first() if head_id else None,
        )
        _log(request, 'dept_create', 'SupportDepartment', dept.pk, name)
        messages.success(request, f'Department "{name}" created.')
    return redirect('support:department_list')


# ─────────────────────────────────────────────────────────────────────────────
# Agents (admin)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@support_admin_required
def agent_list(request):
    agents = User.objects.filter(
        Q(is_staff=True) | Q(profile__role__in=['admin', 'support'])
    ).order_by('first_name').annotate(
        open_count=Count('assigned_tickets', filter=Q(assigned_tickets__status__in=OPEN_STATUSES)),
        resolved_count=Count('assigned_tickets', filter=Q(assigned_tickets__status='resolved')),
        avg_csat=Avg('assigned_tickets__feedback__rating'),
    )
    return render(request, 'support/agent_list.html', {'agents': agents})


# ─────────────────────────────────────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@support_required
def analytics(request):
    days = int(request.GET.get('days', 30))
    since = timezone.now() - timedelta(days=days)
    qs = SupportTicket.objects.filter(created_at__gte=since)

    total = qs.count()
    resolved = qs.filter(status='resolved').count()
    resolution_rate = round((resolved / total) * 100, 1) if total else 0
    avg_csat = TicketFeedback.objects.filter(created_at__gte=since).aggregate(avg=Avg('rating'))['avg']
    avg_per_day = round(total / days, 1) if days else 0

    sla_total = SupportTicketExtra.objects.filter(ticket__created_at__gte=since, due_at__isnull=False).count()
    sla_ok = SupportTicketExtra.objects.filter(
        ticket__created_at__gte=since, due_at__isnull=False,
        ticket__resolved_at__lte=models_F('due_at') if False else timezone.now()
    ).count()

    # Daily trend
    daily = []
    for i in range(days - 1, -1, -1):
        day = timezone.now() - timedelta(days=i)
        ds = day.replace(hour=0, minute=0, second=0)
        de = day.replace(hour=23, minute=59, second=59)
        daily.append({
            'label': day.strftime('%b %d'),
            'created': qs.filter(created_at__range=(ds, de)).count(),
            'resolved': qs.filter(status='resolved', resolved_at__range=(ds, de)).count(),
        })

    category_stats = qs.values('category').annotate(n=Count('id')).order_by('-n')
    status_stats = qs.values('status').annotate(n=Count('id'))
    priority_stats = qs.values('priority').annotate(n=Count('id'))

    agents = User.objects.filter(
        Q(is_staff=True) | Q(profile__role__in=['admin', 'support'])
    ).annotate(
        total=Count('assigned_tickets', filter=Q(assigned_tickets__created_at__gte=since)),
        resolved=Count('assigned_tickets', filter=Q(
            assigned_tickets__created_at__gte=since,
            assigned_tickets__status='resolved'
        )),
        avg_rating=Avg('assigned_tickets__feedback__rating'),
    ).filter(total__gt=0).order_by('-resolved')

    return render(request, 'support/analytics.html', {
        'days': days,
        'total': total,
        'resolved': resolved,
        'resolution_rate': resolution_rate,
        'avg_csat': round(avg_csat, 1) if avg_csat else None,
        'avg_per_day': avg_per_day,
        'daily': daily,
        'category_stats': list(category_stats),
        'status_stats': list(status_stats),
        'priority_stats': list(priority_stats),
        'agents': agents,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Chat Sessions
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@support_required
def chat_list(request):
    status_filter = request.GET.get('status', '')
    qs = ChatSession.objects.select_related('student', 'agent').order_by('-started_at')
    if status_filter:
        qs = qs.filter(status=status_filter)
    paginator = Paginator(qs, 25)
    sessions = paginator.get_page(request.GET.get('page'))
    return render(request, 'support/chat_list.html', {
        'sessions': sessions,
        'status_filter': status_filter,
        'status_choices': CHAT_STATUS_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Announcements
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@support_required
def announcement_list(request):
    return render(request, 'support/announcement_list.html', {
        'announcements': SupportAnnouncement.objects.select_related('created_by').all(),
    })


@login_required
@support_required
def announcement_create(request):
    if request.method == 'POST':
        SupportAnnouncement.objects.create(
            title=request.POST.get('title', '').strip(),
            body=request.POST.get('body', '').strip(),
            target_role=request.POST.get('target_role', ''),
            is_pinned='is_pinned' in request.POST,
            expires_at=request.POST.get('expires_at') or None,
            created_by=request.user,
        )
        messages.success(request, 'Announcement published.')
    return redirect('support:announcement_list')


@login_required
@support_admin_required
def announcement_delete(request, pk):
    if request.method == 'POST':
        SupportAnnouncement.objects.filter(pk=pk).delete()
        messages.success(request, 'Announcement deleted.')
    return redirect('support:announcement_list')


# ─────────────────────────────────────────────────────────────────────────────
# Audit Log
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@support_admin_required
def audit_log(request):
    qs = SupportAuditLog.objects.select_related('actor').all()
    search = request.GET.get('search', '')
    action_filter = request.GET.get('action', '')
    if search:
        qs = qs.filter(Q(description__icontains=search) | Q(target_id__icontains=search))
    if action_filter:
        qs = qs.filter(action__icontains=action_filter)
    paginator = Paginator(qs, 50)
    logs = paginator.get_page(request.GET.get('page'))
    return render(request, 'support/audit_log.html', {
        'logs': logs,
        'search': search,
        'action_filter': action_filter,
    })


# ─────────────────────────────────────────────────────────────────────────────
# AJAX APIs
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@support_required
def api_ticket_stats(request):
    now = timezone.now()
    open_qs = SupportTicket.objects.filter(status__in=OPEN_STATUSES)
    return JsonResponse({
        'total_open': open_qs.count(),
        'urgent': open_qs.filter(priority='urgent').count(),
        'sla_breached': SupportTicketExtra.objects.filter(
            due_at__lt=now, ticket__status__in=OPEN_STATUSES
        ).count(),
        'unassigned': open_qs.filter(assigned_to__isnull=True).count(),
        'escalated': SupportTicketExtra.objects.filter(
            is_escalated=True, ticket__status__in=OPEN_STATUSES
        ).count(),
        'open_chats': ChatSession.objects.filter(status='active').count(),
    })


@login_required
@support_required
def api_canned_response(request, pk):
    cr = get_object_or_404(CannedResponse, pk=pk, is_active=True)
    CannedResponse.objects.filter(pk=pk).update(use_count=cr.use_count + 1)
    return JsonResponse({'body': cr.body, 'title': cr.title})


@login_required
@support_required
def api_kb_article_vote(request, pk):
    article = get_object_or_404(KBArticle, pk=pk)
    vote = request.POST.get('vote')
    if vote == 'yes':
        KBArticle.objects.filter(pk=pk).update(helpful_count=article.helpful_count + 1)
    elif vote == 'no':
        KBArticle.objects.filter(pk=pk).update(not_helpful_count=article.not_helpful_count + 1)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect('support:kb_article_detail', slug=article.slug)
