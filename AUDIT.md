# DigitalCampus — Cross-App Audit

Prepared 2026-07-08. Scope: `eduweb`, `management`, `instructor`, `student`, `finance`, `payment`, `library`. The `parent` app is excluded pending a decision on whether to scrap it. None of the seven apps audited have automated tests (every `tests.py` is the untouched Django stub) — worth weighing how much manual QA each fix below will need.

Shareable version with nicer formatting: https://claude.ai/code/artifact/5c7bdd46-3a97-4bf4-8215-22db10206515

## Scorecard

| App | Route | Verdict |
|---|---|---|
| eduweb | `/` (shared kernel) | Core is solid; two guaranteed 500s and a currency mess sit right at the payment edge. |
| management | `/management/` | Back office works day-to-day; one public analytics leak and zero end-of-session logic. |
| instructor | `/instructor/` | Best-built app in the codebase; the exam lifecycle is genuinely production-grade. |
| student | `/student/` | Largest surface area; grading has three sources of truth that disagree with each other. |
| finance | `/finance/` | Good dashboarding, but payroll and subscriptions are record-keeping, not real processing. |
| payment | `/payment/` | Real Stripe refunds, but a dead duplicate function and a state-integrity bug on refund. |
| library | `/library/` | The cleanest app of the seven — does one job, does it correctly, no surprises. |

## Cross-cutting themes

These span two or more apps and matter more than any single bug below.

1. **Student progression is not built, anywhere.** `UserProfile.year_of_study` is written exactly once, at admission (`management.make_decision`). `progression_status` defaults to `'active'` at seed time and is never touched again by any view, command, or job in any of the seven apps. There is no carry-over/repeat tracking at all — `'repeated'` exists as an enum value with nothing behind it. `management` is the natural home (it already owns `AcademicSession`, `CourseRegistration`, `CourseGrade`) but has zero code toward this today.

2. **Grades have three sources of truth that disagree.** The student dashboard reads real `CourseGrade` rows. The "Grades & Performance" page has its `CourseGrade` query commented out and shows quiz/assignment stats instead. "Academic Records" fabricates a third, separate proxy from `StudentExamResponse`. Worse: the function that actually writes `CourseGrade` (`_record_academic_grade`) only reads `QuizAttempt` and `AssignmentSubmission` — it never reads `StudentExamResponse`, so scores from the CBT exam engine (the most polished grading system in the app) never reach a student's official record.

3. **Money doesn't gate anything.** `AllRequiredPayments`, `Invoice`, and outstanding-balance totals are surfaced for display in `student`, `finance`, and `payment` — but nothing blocks course registration, LMS enrollment, or portal access on an unpaid balance. Combined with the refund bug in `payment` (below), a refunded application still reads as fully paid.

4. **The permission matrix is decorative.** `StaffPermissionsMatrix` — the granular per-role `can_view`/`can_edit`/`can_export` model — is fully editable through `management`'s UI, but no view in `management` ever reads it. Every destructive action there is gated by one of three near-duplicate coarse booleans instead.

5. **Role gating is copy-pasted, not shared.** `eduweb/decorators.py` defines the canonical `instructor_required` / `admin_required` / `finance_required`. `management`, `finance`, and `payment` each define their own local gate instead — with subtly different behavior (no superuser-bypass, no `is_active`/`email_verified` check). A policy fix to the shared decorators today would not reach three of the seven apps.

6. **Currency handling has no single source of truth.** `USD`, `NGN`, and literal `'usd'`/`'gbp'` Stripe amounts all appear hardcoded across `eduweb`'s payment views, independently of each other, despite `AllRequiredPayments.currency` and `SiteConfig` already existing for exactly this.

7. **Zero automated tests, anywhere.** Every app's `tests.py` is the untouched Django stub. Nearly every runtime bug below (several are guaranteed 500s on first hit) would have been caught by one view-level test.

---

## eduweb

Route `/` · views.py ~2168 lines · models.py ~6096 lines · shared by every other app. The shared kernel — public site, auth/OTP, the admissions pipeline, and the model layer everything else imports.

**Working**
- Public site (index/about/programs/faculty/blog) — proper `select_related`/`prefetch_related` and pagination, uniformly gated by `@check_for_auth`. `views.py:733–1047`
- Auth/OTP — signup with math captcha + password-strength validation, 6-digit OTP login with 10-minute expiry, 5-attempt lockout, single-device session enforcement. `views.py:449–621`
- Admissions pipeline end-to-end — apply → draft → submit → review → approve → accept → admission number all connect; `accept_admission` correctly syncs `UserProfile.program/department/faculty/year_of_study/admission_session`. `views.py:1441–1461`
- Email service — 24 distinct notification functions, HTML+text, exception-safe, dynamic branding. `emailservices.py:13–45`
- Stripe webhook — really exists and really verifies the signature (`stripe.Webhook.construct_event`), so async payment confirmation is real. It lives here rather than in `payment`. `views.py:2086–2101`

**Broken now**
- `get_student_fee_summary` will 500 on every hit — calls `.select_related('faculty','department')` on `AllRequiredPayments`, but those are Python `@property` methods, not FK fields → `FieldError`. `views.py:1779–1797`
- Same view references `settings.STRIPE_PUBLISHABLE_KEY`, which doesn't exist (only `STRIPE_PUBLIC_KEY` is defined). Second guaranteed crash on the same endpoint. `views.py:1795`

**Missing / gaps**
- No expiry check on the email-verification token, despite the email claiming "expires in 24 hours". `emailservices.py:150`
- `accept_admission`'s `UserProfile` sync is wrapped in a bare `try/except: logger.exception(...)` with no user-facing failure signal.
- No `Enrollment` is ever created on admission — a student who clears `can_access_student_portal()` still has zero course enrollments.
- Four hardcoded currencies on one payment surface — `'USD'`, `'NGN'`, literal Stripe `'usd'`/`'gbp'` intents, none read from `AllRequiredPayments.currency` or `SiteConfig`. `views.py:1746,1762,1794,1839,1888,1899`
- Dead code worth deleting: `SignUpForm.clean_email` defined twice (`forms.py:55,98`); commented-out duplicate Stripe routes in `urls.py:91–97`.

**Cross-app note:** every other app imports these models directly rather than redefining them — confirmed via grep, no drift. Fragile only at the two broken views above and the exam-lock middleware's hardcoded `/student/exam/` path assumption.

---

## management

Route `/management/` · views.py ~5686 lines · urls.py ~244 lines. The admin/back-office portal.

**Working**
- Application review & decisions — filters, pagination, correct auto-transition to `under_review`, `make_decision` syncs the approved student's `UserProfile`. `views.py:413,463,493`
- Faculty / Department / Program / Course CRUD — functional (see cascade risk below). `views.py:846–3383`
- Academic session management — create/edit plus a "set current" action that recomputes other sessions' status from term dates. `views.py:3245,3283`
- Staff & user management — list/create/edit/toggle-active/change-role/bulk actions all complete. `views.py:1269–1704`
- Exam approval workflow — the best-built feature in this app: enforces `SUBMITTED → APPROVED → PUBLISHED`, rejects wrong-state transitions, writes an immutable audit log, notifies the instructor. `views.py:5397,5432,5473`
- Permission-matrix editor — reads/writes `StaffPermissionsMatrix` correctly as a data-entry screen. `views.py:1620`

**Broken / risky now**
- `financial_analytics` has no access control at all — no login check, no admin check. Reachable by anyone, including an unauthenticated visitor. `views.py:4606`
- Delete cascades have no safety net — Faculty → Department → Program → Course, and Course → CourseRegistration/CourseGrade/CourseIntake/CourseApplication are all `on_delete=CASCADE`. Delete views call `.delete()` directly with no dependent-count check and no server-side confirmation.

**Missing / gaps**
- The permission matrix is never actually enforced — `StaffPermissionsMatrix`/`request.permissions` has zero read-references anywhere in `management/views.py`. Real gating relies on three near-duplicate coarse gates (`is_admin`, `_is_admin`, `_is_staff`), none importing the shared `eduweb.decorators.admin_required`.
- Exam approval is gated more loosely than it looks — commented "SUPERADMIN VIEWS" but actually gated by plain Django `is_staff`. `views.py:5322,5325`
- Confirmed dead code — a full second `course_create/detail/edit/delete` implementation exists but is unreachable (routes commented out); same for course-category CRUD. `views.py:916–1033`, `urls.py:55–65`
- `issue_transcript` issues nothing — flips a boolean, sends an email, no document is ever generated. `views.py:601`
- **Confirmed directly: end-of-session processing does not exist.** Grepped for `bulk`, `process_result`, `end_of_session`, `cohort`, `promote`, `graduate`, `probation`, `repeat`, `carry-over`, `next_level` — only "bulk" hits are user activate/deactivate. No management command package exists in this app. The one and only `year_of_study` write is the one-time set in `make_decision`.

**Cross-app note:** approval → `UserProfile` sync is real and correct. But Course/Program deletion cascades silently break what `student` shows as registered courses and what `instructor` shows as a teaching list, with no warning to the admin performing the delete.

---

## instructor

Route `/instructor/` · views.py ~3413 lines · urls.py ~288 lines. Course/section/lesson/quiz/assignment CRUD and grading — the closest of the seven apps to "done."

**Working**
- Course/section/lesson CRUD — clean ownership chain (`instructor=request.user`) enforced at every level; every route maps to a real view. `views.py:325–620`
- Quiz engine — complete CRUD plus correctly read-only instructor review of auto-graded attempts. `views.py:668–2058`
- Assignment grading — verifies the submission belongs to the instructor's own course before allowing a grade. `views.py:1055,1071–1072`
- Exam lifecycle (DRAFT → SUBMITTED → APPROVED → PUBLISHED) — the strongest feature in the whole codebase. Correct state-transition guards, immutable status log, published exams frozen against edits, genuinely connects end-to-end to management's approval views. `views.py:2770–3105`
- Permission gating — all ~85 views checked carry both `@login_required` and `@instructor_required`, scoped correctly; no cross-instructor authorization gap found.

**Broken now**
- Exam question file-import uses removed model fields — constructs `ExamQuestion.objects.create()` with `difficulty`/`order`/`import_row_number`, all deliberately removed from the model. The standalone import view catches this (feature just doesn't work); the same call inline inside `create_assessment` has **no** try/except — uploading a question file while creating a new exam will 500 the request. `views.py:3239,2693–2696,3287–3312`
- Assignment scores bypass validation — `grade_submission` writes `submission.score = request.POST.get('score')` straight to `.save()` without `full_clean()`. Negative scores, scores above `max_score`, and non-numeric input all get through (the last raises an uncaught error), and this pollutes the auto-computed grade average downstream. `views.py:1078–1083`

**Missing / gaps**
- Instructors cannot create or delete their own courses — `course_create` always redirects to "contact an admin" (route commented out); `course_delete` unconditionally raises `PermissionDenied`. `views.py:317,414`
- "Send welcome email" checkbox is a silent no-op (TODO, never implemented). `views.py:1200–1202`
- Stale help content — FAQ tells instructors how to create a course, contradicting the fact it's disabled; four "quick links" point to `#`. `views.py:1811,1920–1945`

**Cross-app note:** instructor quiz/assignment grading feeds `CourseGrade` automatically through `student`'s `_record_academic_grade` — but that function never reads `StudentExamResponse`, so the careful exam work here currently never reaches a student's official grade record.

---

## student

Route `/student/` · views.py ~4412 lines · urls.py ~107 lines. Largest app by view count — dashboard, registration, enrollment, lessons, assignments, quizzes, and a second, newer CBT exam engine running in parallel.

**Working**
- Course registration — checks the registration window and session status, pulls the credit-unit cap dynamically from `Program.max_credits_per_semester`, enforces all-core-courses-selected, does real LMS auto-enrollment matching. `views.py:631,722,782`
- Enrollment / lesson progress — access verified before granting content, progress tracked correctly, completion triggers grading, certificates, notifications. `views.py:1359,1576`
- Assignments — complete: prefetch-optimized, late-penalty handling, overdue checks. `views.py:1677,1835`
- Notifications / inbox / study groups — implemented and functional, correct ownership checks. `views.py:2510–3609`
- CBT exam engine — question shuffling, auto-grading by question type, manual-grade queue for essay/short-answer, tab-switch flagging. The more polished of the two grading systems in this app. `views.py:4008–4284`

**Broken now**
- Three "what's my grade" pages disagree — dashboard reads real `CourseGrade`; "Grades & Performance" has its `CourseGrade` query commented out and shows quiz/assignment stats only; "Academic Records" builds a third, disconnected proxy from `StudentExamResponse`. `views.py:354,2814–2834,3840`
- Exam start/data endpoints are under-gated — `exam_instructions`, `start_exam`, `get_exam_data` carry only `@login_required` (siblings also check student role), and none re-verify the requester is enrolled in that exam's course. `views.py:4074,4120,4174`
- Student support tickets vanish — the "help & support" form is a plain `forms.Form`, not a `ModelForm`; it only sends an email and never creates a `SupportTicket` row, so tickets never reach the staff queue in `management`. `views.py:3154`

**Missing / gaps**
- No prerequisite enforcement at registration — `Course.prerequisites` is fetched for display only.
- No fee gate on enrollment — `enroll_course`'s own comment states "All LMS courses are free — enrollment is immediate." `views.py:1277,1280`
- Duplicated, drifting query logic — `UserProfile.get_current_courses()` exists for exactly this, but three views hand-roll the same filter independently.
- Real N+1 performance issues — `course_detail` queries per lesson in a loop; the progress page issues ~84 queries per request for a 28-day activity heatmap regardless of course count. `views.py:1188–1199,2911–2954`

**Cross-app note:** registration/enrollment correctly respect `AcademicSession`/`Program` config owned by `eduweb`/`management`. But grade fragmentation means `instructor`'s exam work doesn't reach the official record, and payment status from `finance`/`payment` gates nothing here.

---

## finance

Route `/finance/` · views.py ~521 lines · urls.py ~39 lines. Finance-staff dashboard: payroll and subscription oversight — honest about being a reporting layer, not a payments engine.

**Working**
- Finance dashboard — real KPI aggregation (revenue, refunds, success rate, payment-method mix, daily revenue, top programs), date-range picker, graceful degradation on import failure. `views.py:38–287`
- Payroll CRUD — complete: create/list, status workflow with audit-stamped `approved_by`/`approved_at`, delete gated by `payroll.can_delete()`, per-attachment delete. `views.py:344–522`
- Subscription list — filterable, with a live MRR calculation. `views.py:294–338`

**Missing / gaps**
- Payroll is record-keeping, not payment processing — no payout API anywhere; marking payroll "paid" is a manual status flip.
- Subscription management is display-only — no create/upgrade/cancel view exists; the only `Subscription` rows anywhere were fabricated by the seed command, and `student` never reads the model.
- Local, divergent auth gate — every view uses its own `is_finance_manager()` rather than the shared `finance_required` decorator; skips the superuser/admin bypass and `is_active`/`email_verified` checks. `views.py:27–33`

Minor: `except (ImportError, Exception): pass` appears three times — `Exception` already covers `ImportError`, silently swallowing any error as "model unavailable." `views.py:196,219,239`

---

## payment

Route `/payment/` · views.py ~400 lines · urls.py ~49 lines. Payment records, refunds, invoices, transaction reports, Stripe SDK calls. Smallest app by line count, but carries the most state-integrity risk.

**Working**
- List/detail/reports/invoice-PDF views — functional, degrade cleanly if the PDF library is missing. `views.py:33–309`
- The surviving refund path is correctly ordered — calls real `stripe.Refund.create` before writing local state, aborts cleanly on a Stripe error. `views.py:356–376`
- Async confirmation is real — the Stripe webhook exists and verifies `STRIPE_WEBHOOK_SECRET`, but it lives in `eduweb`, not here.

**Broken now**
- `refund_payment` is defined twice in the same file — the dead first copy never calls Stripe at all; would have shipped a fake refund had it been the surviving definition. `views.py:124–187,315–401`
- The route name `refund_payment` is registered twice, at two different URL paths, both resolving to the same view. `urls.py:24–27,49`
- Refunding doesn't undo the application's paid state — only updates `ApplicationPayment.status`, never reverts `CourseApplication.payment_status`. Since `CourseApplication.is_paid` reads that field, **a refunded application still reports as fully paid** and keeps document upload/submission unlocked. `views.py:378–385`, `eduweb/models.py:1991–2015`

**Missing / gaps**
- `required_payments_list` is a two-line stub — renders a template with zero context, no query against `AllRequiredPayments` at all. `views.py:229–230`
- Two disconnected ledgers for the same money — this app builds all reporting/invoicing on `ApplicationPayment`; `Invoice` and `Transaction` are only created by the seed command and only read by `management`. No reconciliation between what Stripe/the webhook recorded and what these models say.
- Hardcoded institution details on generated invoices — company name/address/email/phone hardcoded rather than pulled from `SystemConfig`. `views.py:284–292`

**Cross-app note:** sharpest evidence for cross-cutting theme 3 — `AllRequiredPayments` is confirmed unenforced anywhere in `student`, and the refund bug means payment state and application state can now openly disagree.

---

## library

Route `/library/` · views.py ~339 lines · urls.py ~20 lines. Digital library browsing — smallest app audited, fewest surprises.

**Working**
- Fully DB-driven taxonomy and browsing — dynamic categories, featured/recent items, detail view with view-count tracking, download endpoint with counter, genuine multi-field search (title, author, subcategory, description, tags, publisher) with sorting and pagination. `views.py:80–340`
- CRUD correctly lives elsewhere — this app has no create/update/delete views by design; full item CRUD is in `management`, properly gated there.

**Missing / gaps**
- Access control is binary only — items are `public` or `members`, nothing finer; no program/department/course-level restriction. `eduweb/models.py:4414–4417`

---

## Recommended next steps

### Quick wins — do first (isolated, one-file fixes)
1. `eduweb`: fix `get_student_fee_summary`'s `select_related` on non-FK properties, and its reference to a Stripe setting that doesn't exist — two guaranteed 500s on one endpoint.
2. `payment`: delete the dead first `refund_payment` definition and its duplicate URL registration; make refund also revert `CourseApplication.payment_status`.
3. `instructor`: wrap the inline exam-question-import call in `create_assessment` in the same try/except the standalone import view already has, and drop the removed `difficulty`/`order`/`import_row_number` kwargs from the `ExamQuestion.objects.create()` call.
4. `instructor`: route `grade_submission`'s incoming score through `full_clean()` or a form.
5. `management`: add an admin-only decorator to `financial_analytics` — currently open to the public internet.
6. `eduweb`: delete the duplicate `SignUpForm.clean_email`.

### Bigger builds — roughly in priority order
1. **End-of-session progression in `management`** — compute pass/fail from `CourseGrade`, advance `year_of_study`, set `progression_status`, track carry-over/repeat courses. The feature that started this audit, and the one with the least existing code to build on.
2. **Unify the grade sources** — decide whether `StudentExamResponse`, `QuizAttempt`/`AssignmentSubmission`, or both feed `CourseGrade`, and make the dashboard, grades page, and academic records agree with each other and with progression above.
3. **Make required payments actually gate something** — registration and enrollment in `student`, and fix the refund/application-state disagreement in `payment`.
4. **Decide the fate of `StaffPermissionsMatrix`** — wire it into `management`'s real view checks, or remove the editor if it isn't going to be the permission model.
5. **Consolidate role-gating decorators** — point `finance`, `payment`, and `management` at `eduweb.decorators` instead of their local copies.
