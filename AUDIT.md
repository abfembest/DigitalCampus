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

### Phase 2 — next apps (order to be finalized once Phase 1 closes)
- `eduweb`: the two guaranteed 500s, duplicate `clean_email`, currency hardcoding, verification-token expiry, `SECRET_KEY`/`DEBUG` fail-open settings.
- `payment` + `finance` + `support`: wire real `StaffPermissionsMatrix` enforcement into the view/decorator layer (currently template-only in all three); `payment` refund → `CourseApplication.payment_status` revert; `required_payments_list` stub.
- `management`: progression feature hardening (idempotency guard, session-closed check, `transaction.atomic()`, cross-session failed-course counting to close the escalation-avoidance loophole), `financial_analytics` access control, delete-cascade safety net, real transcript generation.
- `instructor`: exam-import crash in `create_assessment`, unvalidated `grade_submission` score, instructor course create/delete.
- Cross-app: consolidate five hand-rolled auth-gate copies onto `eduweb.decorators`.

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

### Quick wins — same file, isolated, still undone from last pass
1. `eduweb`: fix `get_student_fee_summary`'s two guaranteed crashes (bad `select_related`, nonexistent settings key).
2. `eduweb`: delete the dead first `SignUpForm.clean_email`.
3. `instructor`: wrap the inline exam-import call in `create_assessment` in the same try/except the standalone view already has; drop the removed `difficulty`/`order`/`import_row_number` kwargs.
4. `instructor`: route `grade_submission`'s score through `full_clean()` or a form.
5. `management`: add a real decorator to `financial_analytics`.
6. `payment`: revert `CourseApplication.payment_status` inside `refund_payment`; make `required_payments_list` query `AllRequiredPayments`.
7. `eduweb`: fix `SECRET_KEY`/`DEBUG` to fail closed (raise) rather than fail open when `.env` is missing.
8. `eduweb`: switch `BlogPost.increment_views` to `F('views_count') + 1`.

### The one thing to fix before trusting any "permission-gated" claim
Wire `StaffPermissionsMatrix` checks into the actual view/decorator layer in `finance`, `payment`, and `support` — not just templates. Right now three separate commits describe themselves as adding permission gating, and none of the three enforce anything server-side. This is worse than having no gating claim at all, because it reads as done.

### Before the progression feature is used for real decisions
1. Feed `StudentExamResponse` into `CourseGrade` (or otherwise unify the three grade sources) — progression math is only as good as its input, and right now exam-only courses can never register a pass.
2. Add a `ProgressionDecisionLog` existence check before `apply_progression_decision` mutates (idempotency), restrict the session picker to `status='closed'`, wrap the batch loop in `transaction.atomic()`, and change `failed_courses` to look across all sessions a core course was attempted in, not just the current one (closes the probation/withdrawal avoidance loophole).
3. Exclude already-passed courses from the semester registration listing for repeating students.

### Bigger builds still open from last pass
1. Unify the three grade sources (now higher priority — see above).
2. Make required payments actually gate registration/enrollment.
3. Consolidate role-gating decorators — five hand-rolled copies now (`management` x3, `finance`, `payment`, `support`) instead of the shared `eduweb.decorators`.
4. Gate `student` exam endpoints by role + enrollment, not just login.
5. Give instructors real course create/delete, or remove the dead UI that implies they can.
