# DigitalCampus — Cross-App Audit

Updated 2026-07-13 (supersedes the 2026-07-08 pass — every finding below was re-verified against current code; nothing here is carried over unchecked). Scope: `eduweb`, `management`, `instructor`, `student`, `finance`, `payment`, `library`, plus `support` (new since the last pass, wired into `urls.py` but never previously audited). `parent` remains excluded — still an unwired stub. Still no automated tests anywhere (every `tests.py` is the untouched Django stub) — every fix below needs manual QA.

Five commits landed since the last pass: end-of-session progression/carry-over (new feature), a refund-flow rewrite, and per-module permission gating for the finance and support portals. This pass verifies what those actually changed vs. what they claimed to change — the short version is **two of the three "gating" commits are template-level only**, and the new progression feature has several correctness gaps serious enough to matter before it's relied on.

## Scorecard

| App | Route | Verdict |
|---|---|---|
| eduweb | `/` (shared kernel) | Two guaranteed 500s from last pass are still live; refund/webhook plumbing is solid; settings fail open to `DEBUG=True` if `.env` is missing. |
| management | `/management/` | New progression feature is arithmetically sound but has real double-run, session-timing, and escalation-avoidance holes. Permission matrix still decorative. |
| instructor | `/instructor/` | Still the best-built app; the two previously-flagged bugs (exam-import crash, unvalidated grade score) are both still live. |
| student | `/student/` | Grade fragmentation is no longer just a cosmetic disagreement — it now silently corrupts the new progression feature's CGPA/pass computation. Exam endpoints still under-gated. |
| finance | `/finance/` | "Gated by per-module permission" commit only hid buttons in templates — no view enforces the matrix. |
| payment | `/payment/` | Refund flow is genuinely fixed and Stripe-ordered correctly, but doesn't revert application payment state, and its own permission gate is also template-only despite the commit message. |
| library | `/library/` | Unchanged since the last pass — still the cleanest app, still binary access control. |
| support | `/support/` (new, unaudited before) | Well-built ticket/helpdesk console, real IDOR protections on self-service replies. Same template-only permission gating as finance. |

## Cross-cutting themes

1. **"Gated by permission X" now means three different things, and two of them are false.** Commits 363585b (finance) and e128fed (support) both only touched templates — they hide buttons/links based on `StaffPermissionsMatrix`, but neither `finance/views.py` nor `support/views.py` reads the matrix at all. A finance user with `can_delete=False` can still POST directly to the delete URL and it succeeds. This is the same problem the original audit flagged in `management` (finding #4), now confirmed in two more apps by commits whose own messages claim otherwise. **This is the single most important fix to prioritize** — it's a false sense of security, which is worse than a documented gap.

2. **Grade fragmentation has gone from a UX inconsistency to a data-integrity bug.** `CourseGrade` is still fed only by `QuizAttempt`/`AssignmentSubmission` (`student/views.py:_record_academic_grade`), never by `StudentExamResponse` (the CBT exam engine). The new progression feature computes CGPA and pass/fail entirely from `CourseGrade` (`management/progression.py`). Net effect: **a student who passed a course via the exam engine has no `CourseGrade` row, so they read as failed, and can be stuck in `repeated` status indefinitely with no course of action except an admin manually inserting a grade row.** This must be fixed before progression is trusted for real decisions.

3. **The new progression feature has no double-run protection, no session-timing check, and a real escalation-avoidance loophole.** No idempotency guard means re-submitting the confirm POST (double-click, back-button resubmit) can advance the same student twice. Progression can be run against a session that hasn't closed. A student can indefinitely dodge probation/withdrawal by simply not re-registering for a failed core course (`failed_courses` only counts *current-session* registrations). None of this is exploited maliciously today, but all three are one careless admin click away from a real transcript error.

4. **Two guaranteed 500s from the last audit are still exactly where they were.** `get_student_fee_summary` (`eduweb/views.py:1827-1829,1840`) still calls `.select_related()` on two `@property` methods and still references a settings key that doesn't exist. Zero-line-of-code fix, still not done.

5. **Role-gating is still copy-pasted, not shared**, now in five places instead of three: `management` (`is_admin`/`_is_admin`/`_is_staff`), `finance` (`is_finance_manager`), `payment` (`is_finance_manager` again, separately defined), `support` (`support_required`/`support_admin_required`), none importing `eduweb.decorators`.

6. **Settings fail open, not closed.** `DigitalCampus/settings.py` defaults `SECRET_KEY` to the literal string `"django-insecure-change-this-in-production"` and `DEBUG` to `True` when `.env` is absent or misread. A missing/misconfigured `.env` on a real deploy doesn't crash loudly — it silently serves stack traces with a known secret key. This is new since the last pass wasn't looking at settings.py specifically.

---

## Remediation plan (tracked)

Work is sequenced app-by-app, not by severity alone — **`student` goes first and is fully closed out before moving to the next app**, since it's the surface students touch daily and it's what the new progression feature depends on. Checkboxes are updated in place as work lands; this section is the live source of truth for "what's actually done," the sections below it stay as point-in-time findings.

Three product decisions were made on 2026-07-13 and are now binding on the fixes below:
- **Grade computation**: a course's `CourseGrade` is a weighted blend — **Exam 70% / Quiz 15% / Assignment 15%** by default, overridable per course, with any missing component's weight redistributed proportionally across whatever assessment types the course actually has (e.g., an exam-only course is 100% exam).
- **Fee gating**: course/LMS enrollment itself stays free by design — the payment gate belongs at portal-access/admission, before a student ever reaches the dashboard. This pass verifies that gate is real (the original audit found nothing currently blocks portal access on an unpaid balance) rather than assuming it.
- **Prerequisites**: hard block at registration — a student cannot register for a course whose prerequisite they haven't passed (`CourseGrade.is_passed=True`).

### Phase 1 — `student` (complete, 2026-07-13)

**1. Unify the three grade sources into one real `CourseGrade`**
- [x] Added per-course assessment weight fields (`exam_weight_pct`, `quiz_weight_pct`, `assignment_weight_pct`, default 70/15/15) to `Course` + migration `0040_course_assessment_weights`.
- [x] Added `CourseGrade.recompute_for_student_course(student, course, session, term='')` (`eduweb/models.py`) — weighted blend across `StudentExamResponse` (end-of-semester, graded), `QuizAttempt`, and `AssignmentSubmission`, re-normalizing weights across whichever components exist. `_record_academic_grade` in `student/views.py` is now a thin wrapper around it.
- [x] Wired the recompute into all three trigger points: lesson completion (`_record_academic_grade`), student-side auto-grading (`submit_exam`), and instructor manual grading (`instructor/views.py exam_grade_response`) — each only fires once a response is fully `GRADED`, wrapped in try/except with logging.
- [x] "Grades & Performance" now queries real `CourseGrade` rows instead of the commented-out query.
- [x] "Academic Records" now reads the same `CourseGrade` rows instead of its separate `StudentExamResponse`-only `ExamGradeProxy`.
- [x] Fixed a latent bug surfaced during verification: the assignment-percentage annotation (`F('score') * 100.0 / F('assignment__max_score')`) needs an explicit `ExpressionWrapper(..., output_field=FloatField())` — Django can't infer the output type across Decimal/float otherwise. This bug existed in the original `_record_academic_grade` too (any course with a graded assignment would have crashed it); fixed as part of this rewrite.
- Backfilling pre-existing `CourseGrade` rows created under the old exam-blind logic was not done — they'll self-correct the next time any trigger point fires for that student/course.

**2. Close the exam-endpoint authorization gap**
- [x] `exam_instructions`, `start_exam`, `get_exam_data` now carry `@student_required` and scope the `Exam` queryset to the requester's own active/completed enrollment, matching the pattern already used by `exam_list`. Verified via test client: a non-enrolled user gets 404, an enrolled user proceeds normally.

**3. Registration correctness**
- [x] `my_courses` now excludes courses the student already has a passing `CourseGrade` for from both the semester listing and the carry-over listing.
- [x] `register_semester_course`'s `CourseRegistration.objects.get_or_create(...)` is now wrapped in `try/except ValidationError`, turning the prerequisite-violation crash into a friendly `messages.error` + redirect. `CourseRegistration.clean()`'s existing prerequisite check (unchanged) now actually surfaces to the user.

**4. Payment gate**
- [x] `can_access_student_portal()` now also requires `self.is_paid` (application-fee clearance). No backfill/grandfather clause — applies immediately to all students, including previously-approved ones, per product decision. Verified via test client: flipping `payment_status` to `pending` correctly redirects an otherwise-approved student to `application_status`; reverted after the test.
- [x] `student_required`'s message now distinguishes "please pay your application fee" from the generic "still being processed" case.

**5. Performance**
- [x] `course_detail`'s per-lesson N+1 replaced with a single up-front `LessonProgress` query building a `set` of completed lesson IDs.
- [x] `progress`'s 28-day activity heatmap replaced the 84-query per-day loop with 3 `Counter`-bucketed queries covering the whole window.

**Verification performed**: `python manage.py check` and `makemigrations --check` both clean; `CourseGrade.recompute_for_student_course` exercised directly against real enrollment data and confirmed compatible with `management.progression.compute_cgpa`; `/student/grades/`, `/student/academic-records/`, `/student/courses/`, `/student/progress/` all return 200 via Django test client; exam-endpoint gating and the payment gate both verified to behave correctly for both allowed and blocked cases.

**Phase 1 addendum (2026-07-14 follow-up)** — the user's actual live complaint ("passed 100L, entered a new session, can't register a new-level course") turned out to be a *different, deeper* bug than anything above: `register_semester_course`/`register_all_semester_courses`/the dashboard's `registered_credit_total` scoped the student's credit-cap check across the wrong set of courses once a student had carry-overs spanning levels. Root-caused via reproduction against real dev-DB data (not static reading — an earlier hypothesis about `AcademicSession.is_registration_open`'s window was wrong and the user correctly pushed back on it). Fixed with a new `_registrable_course_ids(profile)` helper used consistently by all three call sites, plus:
- [x] `course_catalog` was excluding a student's own already-enrolled courses once their level/session moved on (`Q(id__in=enrolled_course_ids)` added) — this is what made the catalog look "empty" after progressing.
- [x] `grades.html` never actually rendered the `CourseGrade` data the view had been computing since the original Phase-1 fix — added the real "Official Course Grades" section and fixed a bogus `{% widthratio %}` "Avg. Grade" stat to show real CGPA.
- [x] `academic_records.html` — added the "Progression History" section (`CourseCarryOver`/`ProgressionDecisionLog` were computed but never surfaced).
- [x] `quiz_submit` (`student/views.py`) — found it never called `CourseGrade.recompute_for_student_course` at all (a gap in the original Phase-1 wiring); also rewrote to scope answer lookup to question (security fix), wrap in `transaction.atomic()` + `select_for_update()`, and handle `short_answer`/`essay` text responses with `needs_grading=True` (previously these question types had no rendering or submission path at all — `quiz_take.html`/`quiz_result.html` updated to match).
- [x] `save_answer` now rejects edits after `exam.end_datetime` (previously allowed answer changes after the exam window closed).
- [x] `mark_lesson_complete` crash for preview lessons with no enrollment; `course_detail`'s `Http404`-swallowing bug; `assignment.overdue_status` (was calling a broken `_is_overdue_override`).
- **Verified**: reproduced the original registration-blocked scenario end-to-end via test client against real data (100L → 200L with a first-semester carry-over) and confirmed a new second-level course now registers successfully; `/student/grades/` confirmed to render real CGPA and per-course grades in-browser-equivalent (test client HTML assertion), not just return 200.

### Phase 2 — instructor (complete, 2026-07-14)

**1. Notification/email plumbing**
- [x] Found `instructor_counts` context processor (`eduweb/context.py`) was fully implemented but never registered in `DigitalCampus/settings.py`'s `TEMPLATES[0]['OPTIONS']['context_processors']` — the instructor notification bell had been silently dead. Registered it; added `instructor_pending_exam_count` (submitted-but-ungraded `StudentExamResponse` count) to it.
- [x] `enroll_student`'s "send welcome email" checkbox was a no-op `# TODO` — implemented `send_course_enrollment_email` (`eduweb/emailservices.py`, matches the existing `EmailMultiAlternatives` HTML+text pattern) and wired it in. Verified via `override_settings(EMAIL_BACKEND=locmem)` + `mail.outbox`.

**2. Grading pipeline unification**
- [x] Added `CourseGrade.recompute_for_student_course` calls to `grade_submission` (assignment grading) and `quiz_attempt_detail`'s manual-grading POST branch — neither triggered a recompute before, so instructor-graded work could silently disagree with the dashboard/Grades/Academic Records/progression figures fed by the same model.
- [x] Built the full short-answer/essay quiz grading loop end-to-end: student submission (needs_grading flag, see Phase 1 addendum) → instructor grading UI in `quiz_attempt_detail.html`/`quiz_results.html` (status badges, grading form) → `CourseGrade` recompute → student notification (`_notify_instructor`) on completion. Same student-notification-on-grade-complete pattern added to `exam_grade_response`.

**3. Backend correctness/security**
- [x] `create_assessment`'s inline exam-question-file-import call now shares the same try/except (`_parse_exam_questions_from_file` helper, deduplicated from copy-pasted `ExamQuestion.objects.create()` blocks that referenced already-removed model fields) that the standalone `exam_import_questions` view already had — uploading a bad file while creating a new exam no longer 500s. *(Verified fixed in code this session — no longer matches the AUDIT.md finding below.)*
- [x] `grade_submission`'s score is now validated (`Decimal` parse + `0 <= score <= assignment.max_score` range check with a friendly re-render on failure) instead of writing `request.POST.get('score')` straight to `.save()`. *(Verified fixed in code this session.)*
- [x] Added `@require_POST` to `section_delete`/`lesson_delete` (were GET-triggerable deletes) plus dependent-data guards: `lesson_delete` blocks if `LessonProgress`/`QuizAttempt`/`AssignmentSubmission` exist; `delete_question` blocks if any `QuizResponse` references it; `delete_answer` blocks if any `QuizResponse.selected_answer` references it.
- [x] `CourseForm.clean_academic_course` added — previously any POST could relink an existing LMS course's `academic_course` FK after creation (mass-assignment/IDOR-adjacent).
- [x] Fixed `course_statistics`'s ORM JOIN-multiplication bug — combining `Count('enrollments')` and `Avg('rating')` (over a *different* reverse relation, `Review`) in one `.annotate()` inflates both aggregates via the cross-join. Split into `Count(..., distinct=True)` plus a separate `Review.objects.values_list('course_id').annotate(avg=Avg('rating'))` merged in Python.
- [x] `exam_update` now catches `ValidationError` specifically and surfaces `e.message_dict` (was a generic `except Exception`, swallowing the real validation message).
- [x] Cleanup: moved `from datetime import datetime` out of an inline import inside `enroll_student` to the top-level import.

**Still open (re-verified, unchanged from the 2026-07-13 pass — not touched this session)**
- `course_create`/`course_delete` still redirect to "contact an admin" / raise `PermissionDenied` unconditionally.

### Phase 3 — management (backend punch list closed, 2026-07-14)

**Templates/navigation — complete**, verified via Django test Client against real dev DB (create→edit→delete round trips, full page sweep, no regressions on student/instructor which share the same `base.html`):
- [x] All 9 admin-sidebar bugs fixed in `templates/management/base.html` (Acads Structure toggle missing `progression`/`categories`, "All Users" always-true active-state, Course Intakes/Payment Gateways/System Config links commented out of the nav, Course Categories had zero nav presence, Roles & Permissions never highlighted, Audit Log detail page didn't highlight its parent, Blog post/category edit pages didn't highlight their submenu).
- [x] `intakes_list` crash fixed — `CourseIntake.accepted_count`/`remaining_slots`/`is_full` referenced `self.applications`, but `CourseApplication` had no FK to `CourseIntake`. Added `CourseApplication.intake` FK (migration `0043_courseapplication_intake`).
- [x] Bonus bug found while making Course Categories reachable: its view/template referenced `CourseCategory.lms_courses`, but `LMSCourse.category` is a commented-out FK in `eduweb/models.py` — the page was a guaranteed 500 the moment it became reachable (likely why it had been hidden from the sidebar). Removed the dead `lms_courses` reference; **flagged, not built**: real course-categorization would need a live `LMSCourse.category` FK + UI, currently out of scope pending a product decision.
- [x] Built the entire missing course-category create/edit/delete (views + URLs + new `course_category_form.html` template) since the list page already linked to these unbuilt routes — delete guarded against dependent subcategories per the standing "no deletes with dependent data" rule. Deleted ~125 lines of dead, stale, previously-commented-out duplicate view code that referenced non-existent templates.
- [x] Closes the AUDIT.md finding below re: `role_assign` being cosmetic-only — `QuickRoleChangeForm.role` (the form backing `user_change_role`, the actual mutating endpoint) now excludes `'student'` server-side too, not just the picker dropdown. Verified: raw POST with `role=student` now 400s and the target's role is unchanged.

**Backend — done**, all verified via Django test Client against real dev DB (including the one real non-superuser admin account, `femiadmin`, not just superuser bypass):
- [x] Payment-gateway secrets now matrix-enforced: `payment_gateway_create/edit/delete` gated on `permissions.finance.can_create/edit/delete` (matches the template), delete also blocked if any `Transaction` references the gateway.
- [x] `staff_payroll_create` now checks `finance_payroll.can_create` (its edit/delete siblings already did).
- [x] Payroll template/server module-key mismatch fixed — `payroll.html` now checks `permissions.finance_payroll.can_*` (was `permissions.finance.can_*`).
- [x] **Found a real corollary bug while fixing the above**: the `'admin'` role had no `finance_payroll` row in `StaffPermissionsMatrix` at all (neither in the DB nor in the `ROLE_DEFAULT_PERMISSIONS` dict) — meaning the one non-superuser admin account in the dev DB was *already* silently blocked from payroll edit/delete before this session touched anything, since those checks pre-existed. Backfilled via migration `0044_seed_admin_finance_payroll_defaults`.
- [x] Role/permission changes now write `AuditLog(action='permission_change')` + notify the affected user, in both `user_change_role` and `user_permissions` POST (each wrapped in `transaction.atomic()`). `security_dashboard`'s existing query for these events will now show real data.
- [x] `broadcast_send` double-submit race fixed: added a `'sending'` status (migration `0045_broadcastmessage_sending_status`); the status check-and-flip now happens atomically (`transaction.atomic()` + `select_for_update()`) *before* the background thread starts. Also fixed the all-or-nothing failure — per-batch send exceptions are now caught individually so one bad address no longer discards an otherwise-successful send.
- [x] `announcement_create`: system/course fan-out converted to `Notification.objects.bulk_create(...)` (was one `_notify()` call per recipient). **Also found and fixed a real crash**: category-type announcements 500'd with `FieldError` — `enrollments__course__category` doesn't exist because `LMSCourse.category` is a commented-out FK (same root cause as the course_categories_list bug above). Now degrades to a `messages.warning` instead of a 500.
- [x] Admin inbox/notification views fixed — **not with `is_admin`**. Cross-referencing the sidebar template and role defaults showed `admin_inbox`/`notifications_view` are shared by *all* back-office staff (support/finance/admin), not admin-only — the navbar routes only students/instructors elsewhere. Added a new `is_staff_member()` predicate scoped to `{admin, support, finance}` instead; verified all roles land where they should.
- [x] N+1 in `applications_list` fixed (`'program'` added to `select_related`).
- [x] `enrollment_delete`/`certificate_delete`/`badge_delete`/`review_delete`/`student_badge_delete`/`intake_delete` now all have permission checks; `enrollment_delete`/`badge_delete`/`intake_delete` also got dependent-record guards (confirmed `Badge→StudentBadge` and `Enrollment→LessonProgress` are both `on_delete=CASCADE`, so these guards prevent real silent data loss, not just decorative ones — `Certificate`/`Review` are leaf records with nothing to guard against).
- [x] `transaction.atomic()` added around `admin_exam_approve/reject/publish` and `academic_session_set_current`'s multi-session loop (+ `select_for_update()`, + cleaned up a stray `__import__('datetime')` inline import).
- [x] **Role cleanup (user directive, 2026-07-14): only `student`/`instructor`/`admin`/`support`/`finance` are real roles; `content_manager`/`qa` purged from all live (uncommented) code** — `StaffPayroll.staff`'s `limit_choices_to` (migration `0046_alter_staffpayroll_staff`), `security_middleware.STAFF_ROLES`, `management/views.py`'s new `is_staff_member`/`staff_payroll_list`'s local role lists, and the dev-only `seed.py` management command (was generating `content_manager`/`qa` test users). Confirmed 0 existing users have either phantom role, so no data migration was needed.

**Transcript generation — done, 2026-07-14 (fourth pass)**. `issue_transcript` was a **guaranteed crash on every single call** — it wrote `application.transcript_issued_by = request.user` then `save(update_fields=[..., 'transcript_issued_by'])`, but `CourseApplication` had no such field at all (`ValueError`, caught by the view's own broad `except Exception`, which is why it always failed with a generic "Failed to issue transcript" message and never actually issued anything). Also found: the page's own copy claimed "Once requested, the transcript content is locked. Any pending results added after your request will not appear" — but no locking mechanism existed; the transcript re-rendered live `CourseGrade` data on every page load, so that claim was false. And `issue_transcript` had **zero UI entry point anywhere** — fully orphaned, reachable only by hand-crafting a POST.
- [x] Added `CourseApplication.transcript_issued_by` FK (fixes the crash) and `transcript_snapshot` JSONField (`encoder=DjangoJSONEncoder`) to actually lock content — migration `0047_courseapplication_transcript_fields`.
- [x] Added `CourseGrade.build_transcript_snapshot(student)` classmethod (`eduweb/models.py`) — the canonical, shared computation for both live rendering and the frozen snapshot, so `student` and `management` never hand-roll two copies of the same GPA/grade-grouping logic. Careful to cast Decimal→float before it goes anywhere near the JSON field, since a raw Decimal silently becomes a string after a DB round-trip (JSONField has no Decimal type) — would have made a *locked* score's `{% if g.score %}` truthiness disagree with a *live* score's for the 0.00 edge case.
- [x] `student/views.py academic_records`: requesting a transcript now calls `build_transcript_snapshot` and freezes it onto `CourseApplication.transcript_snapshot`; the view renders the frozen snapshot once `transcript_requested=True`, live data otherwise. Added a "Locked Transcript" badge + "Locked as of ..." timestamp so the UI's own claim is now true instead of aspirational.
- [x] `issue_transcript` now requires `transcript_requested=True` before it can be issued (was previously issuable — and would 500 — on any approved application whether requested or not), added a `permissions.applications.can_edit` matrix check (was `is_admin`-only), and builds the snapshot as a defensive fallback if somehow missing.
- [x] Built the missing UI: a "Transcript" section on `application_detail.html` (not requested / requested-and-pending with an "Issue Transcript" button / issued, mirroring the existing "Admission Acceptance Tracking" section's visual pattern) — this endpoint had never been reachable from anywhere before.
- **Verified end-to-end**: requested a transcript, added a *new* grade afterwards, confirmed the rendered page still showed the pre-request grade count only (proving the lock holds against live DB changes); issued via the new admin UI; confirmed issuing before a request is blocked and re-issuing an already-issued one is a no-op.

**`StaffPermissionsMatrix` create/edit enforcement — done, 2026-07-14 (fourth pass)**, all verified against both superuser and the real non-superuser `femiadmin` account:
- [x] Added `_has_permission` checks to: `faculty_create/edit`, `department_create/edit`, `program_create/edit`, `courses_list`'s inline create/edit actions (the *live* course CRUD — see below), `intake_create/edit`, `blog_post_create/edit/delete`, `blog_category_create/edit/delete` (delete also gained a dependent-post-count guard), `required_payment_create/edit/delete` (delete also guarded — `FeePayment.fee` is `on_delete=CASCADE`, so an unguarded delete would have silently wiped real payment history), `library_item_create/edit/delete`, `admin_exam_timetable_update`, `admin_question_moderation`.
- [x] **Found and deleted a second block of dead orphaned code** while doing this, same pattern as the earlier course-categories cleanup: `courses`/`course_create`/`course_detail`/`course_edit`/`course_delete` (management/views.py) were all fully commented out of `urls.py` and completely unreachable — the *real*, live course CRUD is inline inside `courses_list` (create/edit/delete via `action=` POST params to the same URL). Deleted ~155 dead lines and the matching commented URL block; added the missing permission checks to the actual live `create`/`edit` actions instead (delete already had one).
- [x] `LMSCourse.category` FK is still commented out in the model — flagged again, not built (see the two bugs it already caused, course_categories_list and announcement_create, both worked around this session). No product decision made on it yet; still the one open item from this whole punch list.

---

## eduweb

**Fixed since last pass**
- `get_payment_summary` now correctly uses `settings.STRIPE_PUBLIC_KEY` (was previously also broken here).

**Still broken**
- `get_student_fee_summary` — both guaranteed crashes remain: `.select_related('faculty','department')` on `AllRequiredPayments` (`views.py:1827-1829`), where both are `@property` methods (`models.py:1777-1782`) → `FieldError`; and a reference to `settings.STRIPE_PUBLISHABLE_KEY`, which still doesn't exist (`views.py:1840`; only `STRIPE_PUBLIC_KEY` is defined, `settings.py:220`) → `AttributeError`.
- `SignUpForm.clean_email` still defined twice (`forms.py:55-59` dead, `98-102` wins).
- Email-verification token still never expires — `generate_verification_token()` (`models.py:3460-3463`) stores no timestamp and `verify_email` never checks age, unlike the password-reset token which has a real 1-hour `is_reset_token_valid()` check right next to it.
- Currency still hardcoded in four places with no single source of truth: `'USD'` (`views.py:1791,1806`), `'NGN'` (`1839`), Stripe `currency='usd'`/`'USD'` (`1884,1898`) — none read `AllRequiredPayments.currency`/`SiteConfig`.

**New findings**
- `DigitalCampus/settings.py:24,26` — `SECRET_KEY` and `DEBUG` both fail open to insecure defaults if `.env` is missing/misconfigured, rather than failing to start.
- `BlogPost.increment_views` (`models.py:918-921`) does a plain read-modify-write (`self.views_count += 1; self.save()`) instead of `F('views_count') + 1` — undercounts under concurrent traffic. Notably inconsistent: the `library` view/download counters right next to it in the same file do use `F()` correctly.
- Stripe webhook (`views.py:2130-2145`) remains solid — signature verified via `stripe.Webhook.construct_event`, the only legitimate `@csrf_exempt` in the repo, fails closed before touching DB state.
- No raw SQL, `eval`/`exec`/`pickle.loads`, or additional `csrf_exempt` usage found anywhere in the repo.

---

## management

**New: end-of-session progression/carry-over (`management/progression.py`, wired at `views.py:3339-3439`)**

The feature the last audit's cross-cutting theme #1 asked for now exists, and the CGPA math itself is correct — `compute_cgpa` properly weights grade points by `credit_units`. But four issues need fixing before it should be trusted for real academic decisions:

- **Inherits the `CourseGrade` unreliability** described in cross-cutting theme #2 above — exam-only courses never get a `CourseGrade` row, so `core_passed` is permanently `False` for them.
- **No idempotency guard.** `apply_progression_decision` never checks for an existing `ProgressionDecisionLog` before mutating; the eligibility filter (`progression_status__in=['active','repeated','probation']`) still includes a student immediately after they're promoted, so a resubmitted POST (double-click, back-button, retry) can advance them twice. Client-side `confirm()` dialog only — no server-side dedup.
- **No session-state check.** Every `AcademicSession` is offered for progression, including ones that are `'upcoming'` or still `'active'` — nothing restricts the action to a `'closed'` session.
- **Escalation-avoidance loophole.** `failed_courses` only counts courses the student is registered for *in the current session*. A student who simply doesn't re-register for a previously-failed core course keeps `core_passed=False` (blocked from promotion) but never shows up in `failed_courses`, so `new_status` stays `'repeated'` forever and never escalates to `'probation'`/`'withdrawn'` no matter how many sessions pass.
- **No `transaction.atomic()`** around the per-student batch loop (`views.py:3376-3379`) — a mid-batch exception leaves an inconsistent mix of fully-applied, partially-applied, and untouched students with no rollback.
- Permission gating is inconsistent even within this one feature: GET has no `can_view` check at all (gated only by the coarse hand-rolled `is_admin`); the two POST mutation branches do consult `StaffPermissionsMatrix` (`can_approve`/`can_edit`) — the only two `StaffPermissionsMatrix` reads that exist anywhere in `management/views.py`.
- Student-side gap: course-registration queries (`student/views.py:482-492,703-710`) filter by `year_of_study` only, with no exclusion for courses the student already has a passing grade for — a repeating student can see and re-register for courses at that level they already passed, since only *failed* courses get a `CourseCarryOver` row.

**Still broken (re-verified)**
- `financial_analytics` (`views.py:4598`) — still zero auth decorators, reachable by an unauthenticated visitor.
- `StaffPermissionsMatrix` still functionally decorative — only the two progression POST branches read it; every other view still gates via `is_admin`/`_is_admin`/`_is_staff`, none importing `eduweb.decorators.admin_required`.
- Delete cascades (`faculty_delete:888`, `course_delete:1027`, `department_delete:3155`, `program_delete:3244`) still bare `.delete()` with no dependent-count confirmation.
- `issue_transcript` (`views.py:608-631`) still just flips a boolean and sends an email — no document is generated.
- The role-assign fix (92a2d97) is **cosmetic, not a closed hole**: it only excludes `role='student'` from the dropdown in `role_assign` (`views.py:1600`). The actual mutating endpoints, `user_change_role` (`views.py:1512`) and `user_permissions` (`views.py:1633`), still accept any `pk` with no role exclusion — reachable only by an already-`_is_admin`-gated user, so not a privilege-escalation path, but the fix doesn't prevent an admin from directly POSTing a student into a staff role outside the picker UI.

---

## instructor

**Still broken (re-verified, both are the same as last pass, neither touched)**
- Exam-question file-import still constructs `ExamQuestion.objects.create()` with removed fields (`difficulty`, `order`, `import_row_number`, confirmed removed in `eduweb/models.py:5465-5646`) at `instructor/views.py:3032-3037` (xlsx) and `3052-3057` (docx). The standalone import view still catches this (`views.py:2833-2840`, fails gracefully). The inline call inside `create_assessment` (`views.py:2441`) still has **no try/except** — uploading a question file while creating a new exam still 500s.
- `grade_submission` (`views.py:1074-1082`) still writes `request.POST.get('score')` straight to `.save()` with no `full_clean()` — negative/out-of-range/non-numeric scores still get through.
- `course_create`/`course_delete` still disabled (redirect to "contact an admin" / unconditional `PermissionDenied`); "send welcome email" checkbox still a no-op TODO (`views.py:1198-1200`).

**Confirmed healthy:** ~85 views spot-checked, all still carry `@login_required` + `@instructor_required` with correct `instructor=request.user` ownership scoping. No new gaps found. Stale FAQ/quick-links content from the last audit is gone — that section of the file was refactored away, not fixed in place.

---

## student

**Still broken (re-verified)**
- The three-way grade disagreement is unchanged: dashboard reads real `CourseGrade`; "Grades & Performance" still has its query commented out; "Academic Records" still builds a third proxy from `StudentExamResponse` directly. See cross-cutting theme #2 for why this now matters beyond cosmetics.
- Exam endpoints still under-gated: `exam_instructions` (3818), `start_exam` (3863), `get_exam_data` (3917) carry only `@login_required` — no student-role check, no re-verification that the requester is enrolled in that exam's course. Exam slugs are plain `slugify()`, not random tokens, so a logged-in user who derives/guesses a slug can create a response row and pull exam data for a course they're not enrolled in.
- No fee gate on `enroll_course` (comment "All LMS courses are free" still at `views.py:1323`); prerequisites still display-only, never enforced at registration; N+1 patterns in `course_detail` (per-lesson queries in a loop) and the 28-day activity heatmap (per-day queries) both unchanged.

**Fixed since last pass**
- Support tickets now actually reach staff: `submit_ticket` (student-facing, routed through the new `support` app) creates a real `SupportTicket` row via `StudentSupportTicketForm` — the old plain-`forms.Form`, email-only dead end is gone.

**New finding:** `my_courses.html` correctly flags carry-over courses to the student (orange row, "failed Nx previously") — the display side is good. The gap is upstream, in the registration query noted under `management` above (passed courses at the repeated level aren't excluded from what's offered).

---

## finance

**The "gated by per-module permission" commit (363585b) is template-only.** `finance/views.py` never imports or checks `StaffPermissionsMatrix` — every view is still gated solely by the local `is_finance_manager()` (`views.py:27-33`, unchanged, still not using `eduweb.decorators.finance_required`). The matrix flags (`can_edit`/`can_delete`/`can_export`) only control whether a button renders in the template. A finance user can still POST directly to any finance action (e.g. `payroll_delete`) regardless of their matrix row for that module.

Everything else from the last pass (payroll CRUD, dashboard KPIs, subscription list as display-only, the `except (ImportError, Exception): pass` redundancy) is unchanged — not re-litigated here.

---

## payment

**Fixed since last pass**
- The duplicate `refund_payment` definition and duplicate URL registration are both gone — one function, one route.
- Refund ordering is correct and was already: Stripe `stripe.Refund.create` (`views.py:283-286`) runs and is confirmed successful before any local `payment.save()` (`views.py:306`); a Stripe error aborts cleanly with no local state change.

**Still broken**
- Refund still does **not** revert `CourseApplication` payment state — only `ApplicationPayment.status`/`.failure_reason` are updated (`views.py:298-306`); `CourseApplication.payment_status` (which `is_paid` reads, `models.py:1998-2011`) is never touched. A refunded application still reports as fully paid.
- **The commit's own claim of "gated by `finance_payments.can_edit`" is false at the enforcement layer.** `refund_payment` is gated only by `@user_passes_test(is_finance_manager)` (`views.py:20-26,240-241`) — i.e., `role == 'finance'`, full stop. `StaffPermissionsMatrix`/`finance_payments.can_edit` is referenced only in `templates/finance/payment_detail.html` to hide the refund button. Any finance-role user can POST to the refund endpoint and process a real Stripe refund regardless of their matrix setting.
- `required_payments_list` (`views.py:156-157`) is still a two-line stub with no query.

---

## library

No changes since the last pass (last commit to this app predates 2026-07-08). Access control is still binary `public`/`members`, no program/department/course-level granularity. Still the cleanest app of the eight.

---

## support (new — first audit)

Not mentioned in `CLAUDE.md`'s app map; wired into `DigitalCampus/urls.py` under `/support/`. Worth adding to `CLAUDE.md`'s app-map table.

A genuinely solid helpdesk console: tickets (list/detail/create/reply/assign/escalate/reopen) with SLA policies, departments, agents (with availability/load tracking), a Markdown knowledge base with voting, FAQs, canned responses, an announcements system, and an immutable `SupportAuditLog`. A `ChatSession`/`ChatMessage` model exists but has no view wired up beyond a bare list.

- **Same cosmetic-gating problem as finance.** The e128fed commit only touched templates. `support/views.py` gates purely via `support_required`/`support_admin_required` (`support/permissions.py:36-59`), which check `role in ('admin','support')`/`is_staff` — nothing module-specific. A support user with `can_edit=False` on the knowledge-base module can still POST to `kb_article_edit` and it succeeds.
- **No IDOR found.** The self-service reply path correctly scopes by owner: `get_object_or_404(SupportTicket, ticket_id=..., user=request.user)` (`views.py:83`) — a student can't reply to someone else's ticket. Staff-console visibility (any agent sees any ticket) is by design, not a bug.
- No raw SQL, no `|safe` on user-submitted ticket/reply content (uses `linebreaks`/`linebreaksbr`, which still escape).
- Minor: several staff-side create actions (`sla_save`, `department_save`, `announcement_create`) skip `ModelForm` validation in favor of `.strip()` checks — a data-quality gap, not a security one.

---

## Frontend-wide template sweep (new this pass)

- **CSRF:** every template with `method="post"` (95 top-level, 12 under `support/`) also contains `{% csrf_token %}`. No gaps found.
- **`|safe` usage:** every hit reviewed traces back to admin/staff-authored content (`SiteConfig` embeds, blog post bodies, lesson content, icon/JSON strings) or server-side `json.dumps()` feeding a chart script — none renders arbitrary end-user input. The one point worth a policy decision: `lesson.video_url`/`lesson.content` (`templates/students/lesson.html:44,90`) are instructor-authored, a broader trust boundary than pure-admin content — if instructor accounts are ever considered semi-trusted, this is stored-XSS-capable.
- **One JS-string interpolation inconsistency:** `templates/applications/admission_letter.html:462` interpolates `{{ application.application_id }}` into a JS string literal without `|escapejs`, while the line directly above it does use `|escapejs`. Low risk (the value is a server-generated ID, not free text) but worth fixing for consistency.

---

## Recommended next steps

*Updated 2026-07-14 — items completed in Phases 1–3 above are checked off in place; nothing below was re-numbered so old references still resolve.*

### Quick wins — same file, isolated, still undone from last pass
1. [x] `eduweb`: fix `get_student_fee_summary`'s two guaranteed crashes — done, see Phase 1 (`select_related('program__department__faculty')`, `settings.STRIPE_PUBLIC_KEY`, `fee.currency`).
2. [ ] `eduweb`: delete the dead first `SignUpForm.clean_email` — still duplicated (`eduweb/forms.py:55` dead, `:98` wins). Not touched.
3. [x] `instructor`: wrap the inline exam-import call in `create_assessment` in the same try/except the standalone view already has — done, see Phase 2 (`_parse_exam_questions_from_file` shared helper).
4. [x] `instructor`: route `grade_submission`'s score through validation — done, see Phase 2 (range-checked `Decimal` parse).
5. [x] `management`: add a real decorator to `financial_analytics` — confirmed already in place (`@login_required` + `@user_passes_test(is_admin)`); this finding was stale by the time Phase 3 re-checked it, not actually fixed by this session's work.
6. [ ] `payment`: revert `CourseApplication.payment_status` inside `refund_payment`; make `required_payments_list` query `AllRequiredPayments` — still open, `payment` app not yet in scope.
7. [ ] `eduweb`: fix `SECRET_KEY`/`DEBUG` to fail closed — still open, unchanged (`config("SECRET_KEY", default="django-insecure-change-this-in-production")`, `config("DEBUG", default=True)`).
8. [ ] `eduweb`: switch `BlogPost.increment_views` to `F('views_count') + 1` — still open, unchanged (`LibraryItem.increment_views` right next to it in the same file already does this correctly, for comparison).

### The one thing to fix before trusting any "permission-gated" claim
Wire `StaffPermissionsMatrix` checks into the actual view/decorator layer in `finance`, `payment`, and `support` — not just templates. Right now three separate commits describe themselves as adding permission gating, and none of the three enforce anything server-side. This is worse than having no gating claim at all, because it reads as done. **`management`'s equivalent gap is now closed — see Phase 3.** `finance`/`payment`/`support` remain open; not yet in scope.

### Before the progression feature is used for real decisions
1. [~] Feed `StudentExamResponse` into `CourseGrade` — the three-way grade-source disagreement itself is unified (Phase 1) and the additional `quiz_submit` recompute gap is closed (Phase 1 addendum), but pre-existing `CourseGrade` rows created under the old exam-blind logic were not backfilled — they self-correct next time any trigger point fires for that student/course, not immediately.
2. [ ] Add a `ProgressionDecisionLog` existence check before `apply_progression_decision` mutates (idempotency), restrict the session picker to `status='closed'`, wrap the batch loop in `transaction.atomic()`, and change `failed_courses` to look across all sessions a core course was attempted in. Still open — not part of Phase 3's scope yet (progression correctness vs. the nav/CRUD work done so far).
3. [x] Exclude already-passed courses from the semester registration listing for repeating students — done, see Phase 1 (`my_courses`) and Phase 1 addendum (`_registrable_course_ids` closing the deeper credit-cap scoping bug this same requirement depended on).

### Bigger builds still open from last pass
1. [~] Unify the three grade sources — see item 1 above, mostly done, backfill still open.
2. [ ] Make required payments actually gate registration/enrollment.
3. [~] Consolidate role-gating decorators — still five hand-rolled copies (`management` x3, `finance`, `payment`, `support`); none migrated to `eduweb.decorators` yet, no progress this session (out of scope for student/instructor/management phases so far).
4. [x] Gate `student` exam endpoints by role + enrollment — done, see Phase 1 (`exam_instructions`/`start_exam`/`get_exam_data` now `@student_required` + enrollment-scoped).
5. [ ] Give instructors real course create/delete, or remove the dead UI that implies they can — still open, confirmed unchanged in Phase 2's re-check.
