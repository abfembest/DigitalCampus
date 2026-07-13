"""
Seeds academic-progression test data on top of whatever's already in the DB.

Does NOT touch/clear existing data (unlike the full `seed` command) — safe to
run against a live dev DB, and safe to re-run (everything is get_or_create /
update_or_create keyed on natural fields).

Builds four scenarios inside the BSc Artificial Intelligence program (the
program the existing 'talia' test account already belongs to), against a
newly-closed '2025/2026' session, so `management:academic_progression` has
real cases to click through:

  - talia             (existing account) passes every year-1 core course -> should PROMOTE
  - marcus_repeat      fails one core course, first attempt              -> should REPEAT
  - priya_escalate     has an open carry-over (attempts=2) from an even earlier
                        session and does NOT re-register for it this session
                        -> exercises the escalation-avoidance fix, should
                        still show up as failed and escalate to WITHDRAWN
  - jordan_processed   already has a ProgressionDecisionLog for this session
                        -> should show as "Already processed" and be skipped
                        by a bulk confirm (idempotency guard)
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from eduweb.models import (
    Program, Course, AcademicSession, CourseGrade,
    CourseRegistration, CourseCarryOver, ProgressionDecisionLog,
)


class Command(BaseCommand):
    help = 'Seeds academic-progression demo data (sessions + student scenarios) without clearing existing data.'

    def handle(self, *args, **options):
        try:
            program = Program.objects.get(code='BSC-AI')
        except Program.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                "Program 'BSC-AI' not found — run `python manage.py seed` first."
            ))
            return

        core_courses = list(
            Course.objects.filter(program=program, year_of_study=1, course_type='core', is_active=True)
            .order_by('semester', 'code')
        )
        if len(core_courses) < 2:
            self.stderr.write(self.style.ERROR('Not enough year-1 core courses on BSC-AI to build scenarios.'))
            return

        try:
            talia = User.objects.get(username='talia')
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR("User 'talia' not found — expected an existing test account."))
            return

        admin_user = User.objects.filter(is_superuser=True).first() or User.objects.filter(profile__role='admin').first()

        # ── Sessions ─────────────────────────────────────────────────────────
        session_old, _ = AcademicSession.objects.get_or_create(
            name='2024/2025',
            defaults={
                'term_dates': [
                    {'term': 'first', 'start': '2024-09-02', 'end': '2025-01-17'},
                    {'term': 'second', 'start': '2025-01-27', 'end': '2025-05-30'},
                ],
                'status': 'closed',
            },
        )
        session_closed, _ = AcademicSession.objects.get_or_create(
            name='2025/2026',
            defaults={
                'term_dates': [
                    {'term': 'first', 'start': '2025-09-01', 'end': '2026-01-16'},
                    {'term': 'second', 'start': '2026-01-26', 'end': '2026-05-29'},
                ],
                'status': 'closed',
            },
        )
        # Force closed even if the session pre-existed with a different status —
        # bulk progression now requires status='closed' to run against a session.
        for s in (session_old, session_closed):
            if s.status != 'closed':
                s.status = 'closed'
                s.save(update_fields=['status'])

        def grade_row(student, course, session, grade, score):
            CourseGrade.objects.update_or_create(
                student=student, course=course, session=session, term=course.semester,
                defaults={
                    'score': Decimal(str(score)),
                    'grade': grade,
                    'credit_units': course.credit_units,
                    'is_passed': grade != 'F',
                    'result_status': 'released',
                },
            )

        def register_row(student, course, session, status='approved'):
            # Bypass CourseRegistration.clean()'s registration-window check —
            # this is historical seed data for a session whose window is long
            # closed, not a live registration.
            reg = CourseRegistration.objects.filter(
                student=student, course=course, session=session, term=course.semester,
            ).first()
            if reg:
                if reg.status != status:
                    reg.status = status
                    reg.save(skip_clean=True)
                return reg
            reg = CourseRegistration(
                student=student, course=course, session=session, term=course.semester, status=status,
            )
            reg.save(skip_clean=True)
            return reg

        def make_student(username, first_name, last_name, year_of_study, progression_status):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@miu-demo.test', 'first_name': first_name, 'last_name': last_name},
            )
            if created:
                user.set_password('demo12345')
                user.save()
            profile = user.profile
            profile.role = 'student'
            profile.program = program
            profile.year_of_study = year_of_study
            profile.progression_status = progression_status
            profile.email_verified = True
            profile.save()
            return user

        self.stdout.write(self.style.WARNING('Seeding academic-progression demo data...'))

        # ── Talia (existing account) — clean pass, should promote ──────────────
        for course in core_courses:
            grade_row(talia, course, session_closed, 'A', 78)
            register_row(talia, course, session_closed)
        self.stdout.write(self.style.SUCCESS(
            f'  talia: {len(core_courses)} core courses passed in {session_closed.name} — should PROMOTE'
        ))

        # ── Marcus — fails one core course this session, first attempt ────────
        marcus = make_student('marcus_repeat', 'Marcus', 'Ade', 1, 'active')
        for i, course in enumerate(core_courses):
            if i == 0:
                grade_row(marcus, course, session_closed, 'F', 32)
            else:
                grade_row(marcus, course, session_closed, 'B', 65)
            register_row(marcus, course, session_closed)
        self.stdout.write(self.style.SUCCESS(
            f'  marcus_repeat: failed {core_courses[0].code}, first attempt — should REPEAT'
        ))

        # ── Priya — open carry-over from an earlier session, doesn't re-register
        #    this time; exercises the escalation-avoidance fix (attempts 2 -> 3) ──
        priya = make_student('priya_escalate', 'Priya', 'Nair', 1, 'repeated')
        carry_course = core_courses[1]
        for course in core_courses:
            if course.pk == carry_course.pk:
                continue
            grade_row(priya, course, session_closed, 'B', 62)
            register_row(priya, course, session_closed)
        CourseCarryOver.objects.update_or_create(
            student=priya, course=carry_course,
            defaults={
                'first_failed_session': session_old,
                'first_failed_term': carry_course.semester,
                'attempts': 2,
                'is_cleared': False,
            },
        )
        self.stdout.write(self.style.SUCCESS(
            f'  priya_escalate: open carry-over on {carry_course.code} (attempts=2), not '
            f're-registered this session — should still be flagged and escalate to WITHDRAWN'
        ))

        # ── Jordan — already processed for this session; idempotency demo ─────
        jordan = make_student('jordan_processed', 'Jordan', 'Lee', 2, 'active')
        for course in core_courses:
            grade_row(jordan, course, session_closed, 'A', 80)
            register_row(jordan, course, session_closed)
        ProgressionDecisionLog.objects.get_or_create(
            student=jordan, session=session_closed,
            defaults={
                'slug': slugify(f'jordan-processed-{session_closed.name}'),
                'previous_year_of_study': 1,
                'new_year_of_study': 2,
                'previous_status': 'active',
                'new_status': 'active',
                'cgpa': Decimal('5.00'),
                'core_courses_passed': True,
                'changed_by': admin_user,
                'note': 'Seed data — pre-existing decision, for testing the idempotency guard.',
            },
        )
        self.stdout.write(self.style.SUCCESS(
            "  jordan_processed: already has a ProgressionDecisionLog for this session "
            "— should show 'Already processed' and be skipped on bulk confirm"
        ))

        self.stdout.write(self.style.WARNING(
            f"\nDone. In the admin: Progression & Carry-Over -> Program '{program.name}', Session '{session_closed.name}'."
        ))
        self.stdout.write('New accounts (password: demo12345): marcus_repeat, priya_escalate, jordan_processed')
        self.stdout.write("(talia's existing login/password are unchanged.)")
