import random
import uuid
from decimal import Decimal
from datetime import timedelta, date
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker

from eduweb.models import (
    SiteConfig, SiteHistoryMilestone, InstitutionMember, Testimonial,
    Announcement, Assignment, AssignmentSubmission, AuditLog, Badge, StudentBadge,
    BlogCategory, BlogPost, Certificate, ContactMessage,
    Faculty, Department, Program, Course, AcademicSession, AllRequiredPayments,
    CourseIntake, CourseApplication, ApplicationDocument, ApplicationPayment,
    CourseCategory, Discussion, DiscussionReply, Enrollment, SupportTicket,
    TicketReply, Invoice, LessonProgress, LMSCourse, Lesson, LessonSection,
    Message, Notification, PaymentGateway, Transaction, Quiz, QuizQuestion,
    QuizAnswer, QuizAttempt, QuizResponse, Review, SubscriptionPlan,
    Subscription, SystemConfiguration, UserProfile, Vendor, StudyGroup,
    StudyGroupMember, StudyGroupMessage, BroadcastMessage, StaffPayroll,
    ListOfCountry, FeePayment, LibraryItem
)

fake = Faker()

# ── MELBAC YouTube teaching embed codes ──────────────────────────────────────
EMBED_CODES = [
    '<iframe width="560" height="315" src="https://www.youtube.com/embed/-mJFZp84TIY?si=GaHX9emFQiFb9uqa" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>',
    '<iframe width="560" height="315" src="https://www.youtube.com/embed/hnVOvvbQrwA?si=dGpgO4TTbiodxWwl" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>',
    '<iframe width="560" height="315" src="https://www.youtube.com/embed/kFe-RRaOy48?si=8ckGG-v-_Ne3G_rX" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>',
    '<iframe width="560" height="315" src="https://www.youtube.com/embed/JvC7aA24m4Q?si=CHCpJvjlj7NR1hcp" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>',
    '<iframe width="560" height="315" src="https://www.youtube.com/embed/wa0IVAIqbo0?si=7IPmWFuHJm3_r-KX" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>',
]

CAMPUS_MAP_EMBED = (
    '<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3964.5!2d3.279!3d6.468!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x103b8b0f2d3a0001%3A0xabc123def456!2sFestac+Town%2C+Lagos!5e0!3m2!1sen!2sng!4v1234567890" '
    'width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>'
)

PROMO_VIDEO_EMBED = (
    '<iframe width="560" height="315" src="https://www.youtube.com/embed/-mJFZp84TIY?si=GaHX9emFQiFb9uqa" '
    'title="MELBAC — Melchisedec Graduate Bible Academy Promo" frameborder="0" allow="accelerometer; autoplay; clipboard-write; '
    'encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" '
    'allowfullscreen></iframe>'
)

# ── Actual blog posts from MELBAC teaching series ────────────────────────────
MELBAC_BLOG_POSTS = [
    {
        'title': '61: Part 1 — Due Process in Christendom',
        'subtitle': 'There is a "Due Process" in the Kingdom of God that cannot be skipped, hacked, or hurried.',
        'excerpt': 'We live in a microwave generation, but we serve a Crock-Pot God. In this opening message of a new teaching series, Apostle John Daniel reveals the divine protocol that every believer must understand.',
        'content': '<p>There is a "Due Process" in the Kingdom of God that cannot be skipped, hacked, or hurried. We live in a microwave generation, but we serve a Crock-Pot God.</p><p>This teaching unveils the spiritual mechanics behind divine timing, kingdom protocol, and what it means to walk in alignment with God\'s process — not man\'s shortcuts.</p><p>Key scriptures explored: Habakkuk 2:3, Isaiah 40:31, Galatians 6:9.</p>',
        'author_name': 'Apostle John Daniel',
        'author_title': 'Founder & President, MELBAC',
        'read_time': 12,
        'publish_days_ago': 21,
        'slug': 'due-process-in-christendom-part-1',
        'tags': ['due process', 'kingdom of God', 'divine timing', 'patience'],
    },
    {
        'title': '60: Part 5 — Forgiveness: Conclusion',
        'subtitle': 'The spiritual necessity of the sacrifice of Jesus Christ and steps to genuine repentance.',
        'excerpt': 'In this conclusion of the series on God\'s Forgiveness, we touch on the spiritual necessity of the sacrifice of Jesus Christ and the specific steps required for genuine repentance.',
        'content': '<p>In this powerful conclusion to the Forgiveness series, Apostle John Daniel brings together all five parts into a compelling summary of God\'s redemptive plan.</p><p>The teaching covers the absolute necessity of Christ\'s atoning sacrifice, and outlines the practical, biblical steps that every believer must take to receive and walk in God\'s forgiveness.</p><p>Key scriptures: 1 John 1:9, Romans 10:9-10, Hebrews 9:22.</p>',
        'author_name': 'Apostle John Daniel',
        'author_title': 'Founder & President, MELBAC',
        'read_time': 15,
        'publish_days_ago': 28,
        'slug': 'forgiveness-conclusion-part-5',
        'tags': ['forgiveness', 'repentance', 'Jesus Christ', 'salvation'],
    },
    {
        'title': '58: Part 4 — Understanding Blasphemy and the Sin Unto Death',
        'subtitle': 'Specific boundaries to divine pardon that every believer must understand.',
        'excerpt': 'We address the serious and often misunderstood topic of blasphemy against the Holy Ghost, revealing specific boundaries to divine pardon that every believer must understand.',
        'content': '<p>This teaching tackles one of the most difficult doctrines in the New Testament — the sin unto death and blasphemy against the Holy Spirit.</p><p>Apostle John Daniel carefully expounds the scriptural evidence, distinguishing between sins that God will forgive and the one unpardonable transgression, giving believers clarity and confidence in their walk with God.</p><p>Key scriptures: Matthew 12:31-32, 1 John 5:16-17, Hebrews 6:4-6.</p>',
        'author_name': 'Apostle John Daniel',
        'author_title': 'Founder & President, MELBAC',
        'read_time': 18,
        'publish_days_ago': 35,
        'slug': 'blasphemy-sin-unto-death-part-4',
        'tags': ['blasphemy', 'Holy Spirit', 'forgiveness', 'sin'],
    },
    {
        'title': '57: Part 3 — Conditions for God\'s Forgiveness Towards Men',
        'subtitle': 'Exploring the biblical principles and requirements for receiving God\'s mercy.',
        'excerpt': 'We explore the biblical principles and requirements for receiving God\'s mercy, diving deep into the "if" found in God\'s promises of forgiveness.',
        'content': '<p>Forgiveness is not unconditional in the way many preachers teach. This message carefully lays out the divine conditions that Scripture itself attaches to God\'s offer of mercy.</p><p>Apostle John Daniel walks through key passages revealing what God requires of man — not as works for salvation, but as the posture of the heart that opens the door to heaven\'s grace.</p><p>Key scriptures: 2 Chronicles 7:14, Mark 11:25-26, Luke 17:3-4.</p>',
        'author_name': 'Apostle John Daniel',
        'author_title': 'Founder & President, MELBAC',
        'read_time': 14,
        'publish_days_ago': 42,
        'slug': 'conditions-gods-forgiveness-part-3',
        'tags': ['forgiveness', 'mercy', 'repentance', 'conditions'],
    },
    {
        'title': '56: Part 2 — Steps to a Spirit of Genuine Repentance and of Faith Towards God',
        'subtitle': 'The profound spiritual mechanics of God\'s Forgiveness.',
        'excerpt': 'Part 2 explores the profound spiritual mechanics of God\'s Forgiveness and why humanity required a redeemer after the sin of Adam.',
        'content': '<p>This teaching traces the root of humanity\'s need for a redeemer all the way back to the Garden of Eden, and shows why genuine repentance — not mere sorrow — is the gateway to divine forgiveness.</p><p>The message outlines practical, scriptural steps believers can take to cultivate a spirit of true repentance and living faith toward God.</p><p>Key scriptures: Genesis 3, Romans 5:12, Acts 2:38, Hebrews 6:1.</p>',
        'author_name': 'Apostle John Daniel',
        'author_title': 'Founder & President, MELBAC',
        'read_time': 16,
        'publish_days_ago': 49,
        'slug': 'genuine-repentance-faith-towards-god-part-2',
        'tags': ['repentance', 'faith', 'forgiveness', 'Adam', 'redemption'],
    },
    {
        'title': '55: Part 1 — The Mystery of Forgiveness',
        'subtitle': 'Forgiveness is an 11-letter word that signifies judgment.',
        'excerpt': 'A teaching on the spiritual mechanics of forgiveness — why forgiveness is an 11-letter word that signifies judgment, and what this means for every believer.',
        'content': '<p>In this opening of the Forgiveness series, Apostle John Daniel drops a profound insight: the very word "forgiveness" carries within it the concept of judgment — both divine and human.</p><p>This message sets the theological foundation for the entire series, exploring what forgiveness truly means in the Kingdom of God, and why so many believers misunderstand and misapply it in their lives and ministries.</p><p>Key scriptures: Luke 7:47-48, Ephesians 1:7, Colossians 1:14.</p>',
        'author_name': 'Apostle John Daniel',
        'author_title': 'Founder & President, MELBAC',
        'read_time': 13,
        'publish_days_ago': 56,
        'slug': 'mystery-of-forgiveness-part-1',
        'tags': ['forgiveness', 'judgment', 'grace', 'doctrine'],
    },
    {
        'title': '54: Part 5 — The Authority of a Believer | Mystery of Divine Blessings and Prosperity',
        'subtitle': 'Divine principles that unlock true wealth through Wisdom, Knowledge, and Understanding.',
        'excerpt': 'We dive deep into the Mystery of Divine Blessings and Prosperity, learning the divine principles that unlock true wealth through Wisdom, Knowledge, and Understanding.',
        'content': '<p>This climactic teaching in the Authority of a Believer series turns to the mystery of true prosperity — not the prosperity gospel\'s distortion, but the genuine biblical pattern of divine blessings that flow through wisdom, knowledge, and understanding.</p><p>Apostle John Daniel unpacks Proverbs 24:3-4 and connects it to the believer\'s authority, showing that real wealth in the Kingdom flows from spiritual alignment, not human striving.</p><p>Key scriptures: Proverbs 24:3-4, Deuteronomy 8:18, 3 John 1:2.</p>',
        'author_name': 'Apostle John Daniel',
        'author_title': 'Founder & President, MELBAC',
        'read_time': 20,
        'publish_days_ago': 63,
        'slug': 'authority-believer-divine-blessings-prosperity-part-5',
        'tags': ['authority', 'prosperity', 'wisdom', 'blessings', 'kingdom'],
    },
    {
        'title': '53: Part 4 — The Authority of a Believer: How to be a God Pleaser',
        'subtitle': 'The vital difference between being a "God Pleaser" versus a "Man Pleaser."',
        'excerpt': 'We continue our series on the "Authority of a Believer," focusing on the vital difference between being a "God Pleaser" versus a "Man Pleaser."',
        'content': '<p>One of the greatest hindrances to walking in true kingdom authority is the fear of man. In this powerful message, Apostle John Daniel draws a sharp biblical contrast between those who live to please God and those who live to please people.</p><p>The teaching reveals why man-pleasing is a spiritual trap that neutralises a believer\'s authority, and offers a practical, scriptural pathway to becoming a genuine God-pleaser.</p><p>Key scriptures: Galatians 1:10, John 12:42-43, Acts 5:29, Hebrews 11:6.</p>',
        'author_name': 'Apostle John Daniel',
        'author_title': 'Founder & President, MELBAC',
        'read_time': 17,
        'publish_days_ago': 70,
        'slug': 'authority-believer-god-pleaser-part-4',
        'tags': ['authority', 'God-pleaser', 'man-pleaser', 'faith'],
    },
    {
        'title': '52: Part 3 — The Authority of a Believer: Exercising Kingdom Authority',
        'subtitle': 'The spiritual mechanics of faith, confession, and the "last command" principle.',
        'excerpt': 'We explore the spiritual mechanics of faith, confession, and the "last command" principle in exercising Kingdom Authority as a believer.',
        'content': '<p>In Part 3 of the Authority of a Believer series, Apostle John Daniel introduces the "last command" principle — a key spiritual law that governs how believers operate in Kingdom authority.</p><p>The teaching carefully expounds on the role of faith, the power of confessing the Word, and the order in which authority is exercised in the realm of the Spirit, giving believers a clear, practical framework for spiritual dominion.</p><p>Key scriptures: Mark 11:22-24, Romans 10:8-10, Matthew 28:18-20.</p>',
        'author_name': 'Apostle John Daniel',
        'author_title': 'Founder & President, MELBAC',
        'read_time': 15,
        'publish_days_ago': 77,
        'slug': 'authority-believer-kingdom-authority-part-3',
        'tags': ['authority', 'faith', 'confession', 'kingdom authority'],
    },
    {
        'title': '51: Part 2 — The Authority of a Believer: Exercising Kingdom Authority',
        'subtitle': 'How believers can exercise the dominion restored to us by Christ.',
        'excerpt': 'We dive deep into how we can exercise the dominion restored to us by Christ, tackling difficult challenges facing ministers of the Gospel today.',
        'content': '<p>In Part 2 of the Authority of a Believer series, Apostle John Daniel builds on the foundational principles of the previous teaching and goes deeper into the practical exercise of kingdom dominion.</p><p>This message addresses some of the most pressing challenges facing ministers of the Gospel today — spiritual opposition, discouragement, and the tactics of the enemy — and equips believers to walk victoriously in the authority Christ restored to them.</p><p>Key scriptures: Luke 10:19, Ephesians 1:19-23, Colossians 2:15.</p>',
        'author_name': 'Apostle John Daniel',
        'author_title': 'Founder & President, MELBAC',
        'read_time': 14,
        'publish_days_ago': 84,
        'slug': 'authority-believer-exercising-dominion-part-2',
        'tags': ['authority', 'dominion', 'kingdom', 'ministry'],
    },
]


# ── HELPER: generate a guaranteed-unique slug with a uuid suffix ──────────────
def unique_slug(base_title, model_class, extra_filter=None):
    """
    Generates a slug from base_title. If a record with that slug already exists
    (optionally filtered by extra_filter dict), appends a uuid hex suffix to guarantee
    uniqueness. Used for models with unique_together on (course, slug) etc.
    """
    base = slugify(base_title)
    slug = base
    qs = model_class.objects.filter(slug=slug)
    if extra_filter:
        qs = qs.filter(**extra_filter)
    if qs.exists():
        slug = f"{base}-{uuid.uuid4().hex[:6]}"
    return slug


class Command(BaseCommand):
    help = 'Seeds ALL tables with MELBAC-specific realistic data covering every single field'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING(
            "🚀 Starting FULL MELBAC database seeding — every table, every field..."
        ))

        # ── CLEANUP ──────────────────────────────────────────────────────────
        self.stdout.write("🧹 Clearing existing data...")
        models_to_clear = [
            AuditLog, Notification, Message, TicketReply, SupportTicket,
            StudentBadge, Badge, QuizResponse, QuizAttempt, QuizAnswer,
            QuizQuestion, Quiz, AssignmentSubmission, Assignment,
            LessonProgress, Certificate, Review, Enrollment, DiscussionReply,
            Discussion, Lesson, LessonSection, LMSCourse, CourseCategory,
            ApplicationPayment, ApplicationDocument, CourseApplication,
            CourseIntake, AllRequiredPayments, StaffPayroll,
            Course, AcademicSession, Program, Department, Faculty,
            Invoice, Transaction, Subscription, SubscriptionPlan,
            PaymentGateway, BlogPost, BlogCategory, ContactMessage,
            Vendor, SystemConfiguration, Announcement,
            StudyGroupMessage, StudyGroupMember, StudyGroup, BroadcastMessage,
            InstitutionMember, SiteHistoryMilestone, SiteConfig, Testimonial, ListOfCountry, LibraryItem, FeePayment
        ]
        for model in models_to_clear:
            model.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("   ✅ All data cleared"))

        # ── 0. LIST OF COUNTRIES ─────────────────────────────────────────────
        self.stdout.write("🌍 Seeding countries...")
        country_data = [
            ('Nigeria', 'NG', '+234', 'Nigerian'),
            ('United States', 'US', '+1', 'American'),
            ('United Kingdom', 'GB', '+44', 'British'),
            ('Canada', 'CA', '+1', 'Canadian'),
            ('Germany', 'DE', '+49', 'German'),
            ('France', 'FR', '+33', 'French'),
            ('Australia', 'AU', '+61', 'Australian'),
            ('India', 'IN', '+91', 'Indian'),
            ('Ghana', 'GH', '+233', 'Ghanaian'),
            ('South Africa', 'ZA', '+27', 'South African'),
            ('Kenya', 'KE', '+254', 'Kenyan'),
            ('Cameroon', 'CM', '+237', 'Cameroonian'),
            ('Sierra Leone', 'SL', '+232', 'Sierra Leonean'),
            ('Liberia', 'LR', '+231', 'Liberian'),
            ('Tanzania', 'TZ', '+255', 'Tanzanian'),
            ('Uganda', 'UG', '+256', 'Ugandan'),
            ('Zimbabwe', 'ZW', '+263', 'Zimbabwean'),
            ('Jamaica', 'JM', '+1-876', 'Jamaican'),
            ('Trinidad and Tobago', 'TT', '+1-868', 'Trinidadian'),
            ('Brazil', 'BR', '+55', 'Brazilian'),
        ]
        for country, code, phonecode, nationality in country_data:
            ListOfCountry.objects.get_or_create(
                country_code=code,
                defaults={
                    'country': country,
                    'country_phonecode': phonecode,
                    'nationality': nationality,
                }
            )
        self.stdout.write(self.style.SUCCESS(f"   ✅ {ListOfCountry.objects.count()} countries seeded"))

        # ── 1. SITE CONFIG ───────────────────────────────────────────────────
        self.stdout.write("🌐 Creating site configuration...")
        SiteConfig.objects.create(
            school_name='Melchisedec Graduate Bible Academy',
            school_short_name='MELBAC',
            tagline='Training End-Time Ministers of God — Free of Charge',
            theme_color='#7c3aed',
            email='inquiry@melbac.org',
            phone_primary='+1 862 405 7143',
            phone_secondary='+1 908 205 2535',
            phone_ng_primary='+234 903 8133 047',
            phone_ng_secondary='+234 815 3465 278',
            whatsapp='18624057143',
            address_usa='50 4th Avenue, Newark NJ 07104, USA',
            address_nigeria='401 Road B Close, Plot 1649b (Harmabitrac International Education Network), Festac Town, Lagos, Nigeria',
            facebook='https://www.facebook.com/melchisedecacademy',
            instagram='https://www.instagram.com/melchisedec_academy/',
            youtube='https://www.youtube.com/channel/UCmIBajrcfeWnuqHoYCl-raw',
            twitter='https://twitter.com/melbacedu',
            tiktok='http://tiktok.com/@melchisedec1989',
            linkedin='https://linkedin.com/school/melchisedec-graduate-bible-academy',
            email_admissions='inquiry@melbac.org',
            email_info='inquiry@melbac.org',
            email_international='inquiry@melbac.org',
            phone_admissions='+1 862 405 7143',
            phone_general='+234 903 8133 047',
            phone_international='+1 908 205 2535',
            office_hours_weekday='Monday – Friday: 9:00 AM – 5:00 PM',
            office_hours_saturday='Saturday: 10:00 AM – 2:00 PM',
            office_hours_sunday='Sunday: Closed',
            promo_video_url=PROMO_VIDEO_EMBED,
            campus_map_embed_url=CAMPUS_MAP_EMBED,
            campus_map_address='401 Road B Close, Plot 1649b, Festac Town, Lagos, Nigeria',
            footer_tagline=(
                'Training end-time ministers of God on a free-of-charge basis since 2000 — '
                'grounded in the pure Word of God, approved by the Federal Government of Nigeria.'
            ),
            copyright_year='2026',
            meta_description=(
                'Melchisedec Graduate Bible Academy (MELBAC) — a non-denominational, non-profit '
                'Christian seminary offering free Bachelors, Masters and Doctoral degrees in '
                'Theology, Christian Education, Church Management and the Arts. Lagos, Nigeria & Newark NJ USA.'
            ),
            meta_keywords=(
                'MELBAC, Melchisedec Graduate Bible Academy, free Bible degree, theology Nigeria, '
                'Christian seminary, Apostle John Daniel, church management, divinity degree, Lagos'
            ),
        )
        self.stdout.write(self.style.SUCCESS("   ✅ SiteConfig created"))

        # ── 1a. HISTORY MILESTONES ────────────────────────────────────────────
        self.stdout.write("📜 Creating history milestones...")
        site_cfg = SiteConfig.objects.first()
        milestones = [
            (1995, 'Foundation of the Ministry',
             'Melchisedec Graduate Bible Academy is a subsidiary of Help and Reconciliation Ministry '
             'AKA Harmabitrac World Outreach, which was physically founded in Lagos, Nigeria on '
             'October 15, 1995 by Apostle John Daniel.', 1),
            (2000, 'Birth of the Bible Training College',
             'The Bible study portion of the Ministry was upgraded to an Institution and founded by '
             'Dr. John A. Daniel on 15th January 2000, registered and approved by the Federal '
             'Government of Nigeria as Help and Reconciliation Ministry and Bible Training College '
             'with vested authority to award basic, advanced and diploma certificates to its students.', 2),
            (2004, 'USA Campus Founded',
             'In January 2004, Apostle John Daniel physically founded Help and Reconciliation Ministry '
             'and Bible Training College Newark NJ USA as a non-profit organisation, providing the same '
             'services as the Lagos office with particular attention to social and charitable services.', 3),
            (2007, 'Registered as a Degree-Awarding University',
             'After applying to the Federal Ministry of Education Nigeria and two years of inspecting '
             'core requirements, MELBAC was finally approved and registered by the Federal Government '
             'of Nigeria in November 2007 as Melchisedec Graduate Bible Academy Lagos Nigeria.', 4),
            (2024, 'Full University Status',
             'Due to further demand from both students and graduates who could not afford tuition fees '
             'for degree programs at other theological institutions, the Lord granted the request to '
             'further upgrade the institution to a degree-awarding university, offering Bachelors, '
             'Masters and Doctorate programs completely free of charge.', 5),
        ]
        for year, title, desc, order in milestones:
            SiteHistoryMilestone.objects.create(
                site=site_cfg, year=year, title=title,
                description=desc, display_order=order, is_active=True,
            )
        self.stdout.write(self.style.SUCCESS(f"   ✅ {SiteHistoryMilestone.objects.count()} history milestones created"))

        # ── 1b. TESTIMONIALS ─────────────────────────────────────────────────
        self.stdout.write("💬 Creating testimonials...")
        testimonial_data = [
            ('MELBAC transformed my understanding of the Word of God. The teachings of Apostle John '
             'Daniel are deep, uncompromising, and grounded in pure Scripture. My ministry has never '
             'been the same since I enrolled.',
             'Pastor Emmanuel Adeyemi', 'Bachelor of Christian Religious Studies, MELBAC Graduate', 1),
            ('The fact that MELBAC charges nothing for tuition is a miracle in itself. I was able to '
             'obtain my Master\'s degree in Theology while serving full-time in ministry. This '
             'institution truly operates by faith.',
             'Rev. Grace Okonkwo', 'Masters in Theology and Pastoral Counseling, MELBAC Graduate', 2),
            ('I enrolled from the United Kingdom with doubts, but within the first semester my faith '
             'was completely rebuilt on the solid rock of God\'s Word. The Faculty of Arts curriculum '
             'is exceptional — practical and deeply biblical.',
             'Minister Chukwuemeka Eze', 'Bachelor of Theology, MELBAC Graduate', 3),
            ('MELBAC\'s teaching on the Authority of a Believer and the Mystery of Forgiveness '
             'radically changed my approach to prayer and deliverance ministry. I now lead a thriving '
             'prayer group of 200 members. All glory to God.',
             'Evangelist Ruth Mensah', 'Bachelor of Intercessory Prayer & Deliverance Studies, MELBAC Graduate', 4),
            ('As a pastor in Lagos for 15 years, I thought I knew the Bible well. But enrolling in '
             'MELBAC\'s doctoral program showed me how much deeper the Word of God goes. The academic '
             'rigour combined with the anointing on this institution is unmatched.',
             'Dr. Samuel Obiora', 'Doctor of Divinity, MELBAC Graduate', 5),
        ]
        for quote, author_name, author_role, order in testimonial_data:
            Testimonial.objects.create(
                quote=quote, author_name=author_name,
                author_role=author_role, order=order, is_active=True,
            )
        self.stdout.write(self.style.SUCCESS(f"   ✅ {Testimonial.objects.count()} testimonials created"))

        # ── 2. INSTITUTION MEMBERS ───────────────────────────────────────────
        self.stdout.write("👔 Creating institution members...")
        institution_members_data = [
            ('admin_board', 'Dr. John Amarachukwu Daniel', 'Founder / President', 0,
             'Founder and President of MELBAC and Harmabitrac World Outreach. Anointed servant of God, '
             'teacher of the pure Word, and visionary behind free theological education in Nigeria and the USA.'),
            ('admin_board', 'Mrs. Blessings J. Daniel', 'Vice President Administration', 1,
             'Co-founder and Vice President of Administration, overseeing operational and administrative '
             'affairs across the Lagos and Newark campuses of MELBAC.'),
            ('admin_board', 'Sunday Ehichioya', 'Registrar', 2,
             'Registrar of MELBAC, responsible for student admissions, records, and academic administration '
             'across all programs and campuses.'),
            ('admin_board', 'Ruth Phillips', 'Coordinator, MELBAC Satellite Campuses / Special Assistant to the President on Foreign Affairs', 3,
             'Oversees the coordination of MELBAC satellite campuses internationally and manages foreign '
             'affairs correspondence on behalf of the President.'),
            ('admin_board', 'Julian C. Obiora', 'Admin Officer / Board Secretary', 4,
             'Board Secretary and Administrative Officer responsible for correspondence, board minutes, '
             'and the day-to-day administration of MELBAC.'),
            ('academic_board', 'Sunday Ehichioya', 'Registrar', 0,
             'Serves on the Academic Board as Registrar, ensuring alignment between academic policy '
             'and student administration.'),
            ('academic_board', 'Titus Ehizode', 'Dean, Faculty of Arts', 1,
             'Dean of the Faculty of Arts, overseeing programs in Theology, Missiology, Christian '
             'Leadership, Divinity, and Intercessory Prayer & Deliverance Studies.'),
            ('academic_board', 'Chidi Akoma', 'Dean of Student Affairs', 2,
             'Dean of Student Affairs, responsible for student welfare, disciplinary matters, and '
             'pastoral care across all MELBAC student populations.'),
            ('academic_board', 'Boniface Uzoigwe', 'Dean, Faculty of Christian Education', 3,
             'Dean of the Faculty of Christian Education, overseeing programs in Religious Studies, '
             'Christian Counseling, Educational Administration, and Ethics.'),
            ('academic_board', 'Goodluck Olatunji', 'Dean of Post Graduate Studies', 4,
             'Dean of Post Graduate Studies, coordinating all Masters and Doctoral programs across '
             'the three faculties of MELBAC.'),
            ('academic_board', 'George Odjeni', 'Vice President, Academic Matters', 5,
             'Vice President for Academic Matters and Dean of the Faculty of Church Management & '
             'Administration, overseeing programs in Missiology, Church Finance, and Intercultural Relations.'),
            ('academic_board', 'Dr. John Amarachukwu Daniel', 'Founder / President', 6,
             'Founder and President of MELBAC, providing apostolic and academic oversight across '
             'all faculties, programs, and campuses.'),
            ('advisorate_board', 'Theophilus O. Ihekoronye', 'Pro-Chancellor / Chairman Board of Advisorate', 0,
             'Pro-Chancellor of MELBAC and Chairman of the Board of Advisorate, providing '
             'governance and strategic oversight for the institution\'s growth and mission.'),
            ('advisorate_board', 'Dr. John Amarachukwu Daniel', 'Founder / President', 1,
             'Serves on the Advisorate Board in his capacity as Founder and President, '
             'providing spiritual and visionary direction to the institution.'),
            ('advisorate_board', 'Cyril Azobu', 'Adviser on Financial Matters', 2,
             'Financial adviser to the institution, providing guidance on budgeting, resource '
             'allocation, and the sustainability of MELBAC\'s free-of-charge model.'),
            ('advisorate_board', 'Ezenwa Anumnu', 'Adviser on Legal Affairs', 3,
             'Legal adviser to MELBAC, ensuring the institution\'s compliance with Nigerian law '
             'and international regulatory requirements for theological institutions.'),
            ('advisorate_board', 'Sunny Faith Ugbah', 'Vice Chairman / Adviser Administrative Matters', 4,
             'Vice Chairman of the Advisorate Board and administrative adviser, supporting the '
             'board\'s oversight of MELBAC\'s operational and institutional affairs.'),
        ]
        for mtype, name, role, order, bio in institution_members_data:
            InstitutionMember.objects.create(
                member_type=mtype, name=name, role=role,
                bio=bio, display_order=order, is_active=True,
            )
        self.stdout.write(self.style.SUCCESS(f"   ✅ {InstitutionMember.objects.count()} institution members created"))

        # ── 3. USERS ─────────────────────────────────────────────────────────
        self.stdout.write("👥 Creating users...")
        users = {
            'students': [], 'instructors': [], 'admins': [],
            'support': [], 'content_managers': [], 'finance': [], 'qa': [],
        }

        FIRST_NAMES = [
            'Emmanuel', 'Grace', 'Samuel', 'Ruth', 'Chukwuemeka', 'Blessing',
            'Joshua', 'Esther', 'Daniel', 'Patience', 'Ebenezer', 'Faith',
            'Solomon', 'Peace', 'Goodluck', 'Mercy', 'Elijah', 'Gloria',
            'Moses', 'Deborah', 'Aaron', 'Miriam', 'Isaiah', 'Lydia',
        ]
        LAST_NAMES = [
            'Adeyemi', 'Okonkwo', 'Mensah', 'Obiora', 'Ehichioya', 'Uzoigwe',
            'Azobu', 'Anumnu', 'Ugbah', 'Olatunji', 'Ehizode', 'Akoma',
            'Phillips', 'Williams', 'Johnson', 'Thompson', 'Odjeni', 'Ihekoronye',
            'Daniel', 'Adeleke', 'Nwosu', 'Okeke', 'Eze', 'Nduka',
        ]

        def make_users(username_prefix, role_key, count=6, is_staff=False):
            created = []
            for i in range(count):
                uname = f"{username_prefix}{i + 1}" if i > 0 else username_prefix
                u = User.objects.create_user(
                    username=uname,
                    email=f"{uname}@melbac.org",
                    password="12345",
                    first_name=random.choice(FIRST_NAMES),
                    last_name=random.choice(LAST_NAMES),
                    is_staff=is_staff,
                )
                p = u.profile
                p.role = role_key
                p.bio = (
                    f"A dedicated minister of the Gospel pursuing biblical education at MELBAC. "
                    f"Committed to knowing and teaching the pure Word of God."
                )
                p.phone = random.choice(['+234', '+1']) + str(random.randint(8000000000, 9099999999))
                p.date_of_birth = fake.date_of_birth(minimum_age=22, maximum_age=65)
                p.address = fake.street_address()
                p.city = random.choice(['Lagos', 'Abuja', 'Newark', 'London', 'Houston', 'Port Harcourt', 'Enugu', 'Ibadan'])
                p.country = random.choice(['Nigeria', 'United States', 'United Kingdom', 'Ghana', 'Canada'])
                p.website = ''
                p.linkedin = ''
                p.twitter = ''
                p.email_notifications = True
                p.marketing_emails = random.choice([True, False])
                p.email_verified = i < 4
                p.save()
                created.append(u)
            return created

        users['students'] = make_users('student', 'student', 8)
        users['instructors'] = make_users('instructor', 'instructor', 6)
        users['admins'] = make_users('admin', 'admin', 4, is_staff=True)
        users['content_managers'] = make_users('content_mgr', 'content_manager', 4)
        users['support'] = make_users('support', 'support', 4)
        users['finance'] = make_users('finance', 'finance', 4)
        users['qa'] = make_users('qa', 'qa', 4)

        all_users = sum(users.values(), [])
        verified_students = [u for u in users['students'] if u.profile.email_verified]
        verified_instructors = [u for u in users['instructors'] if u.profile.email_verified]
        verified_admins = [u for u in users['admins'] if u.profile.email_verified]
        verified_support = [u for u in users['support'] if u.profile.email_verified]
        verified_finance = [u for u in users['finance'] if u.profile.email_verified]
        verified_content = [u for u in users['content_managers'] if u.profile.email_verified]
        verified_all = [u for u in all_users if u.profile.email_verified]
        staff_users = (
            users['instructors'] + users['admins'] +
            users['support'] + users['finance'] + users['content_managers']
        )
        self.stdout.write(self.style.SUCCESS(f"   ✅ {len(all_users)} users created"))

        # ── 4. VENDORS ───────────────────────────────────────────────────────
        self.stdout.write("🏢 Creating vendors...")
        vendors = []
        for vd in [
            ('Harmabitrac World Outreach', 'Nigeria'),
            ('Nigerian Bible Society', 'Nigeria'),
            ('IPMA Educational Partners', 'United Kingdom'),
            ('African Christian Education Alliance', 'South Africa'),
            ('Global Missions Network', 'United States'),
        ]:
            vendors.append(Vendor.objects.create(
                name=vd[0],
                email=fake.company_email(),
                country=vd[1],
                stripe_account_id=f"acct_{uuid.uuid4().hex[:16]}",
                is_active=True,
            ))

        # ── 5. SYSTEM CONFIGURATIONS ─────────────────────────────────────────
        self.stdout.write("⚙️  Creating system configurations...")
        cfg_data = [
            ('site_name', 'MELBAC Learning Platform', 'text', True),
            ('max_upload_size', '10485760', 'number', False),
            ('email_notifications_enabled', 'true', 'boolean', True),
            ('maintenance_mode', 'false', 'boolean', False),
            ('default_currency', 'USD', 'text', True),
            ('max_enrollments_per_user', '50', 'number', False),
            ('certificate_enabled', 'true', 'boolean', True),
            ('forum_enabled', 'true', 'boolean', True),
            ('registration_open', 'true', 'boolean', True),
            ('smtp_host', 'smtp.gmail.com', 'text', False),
        ]
        cfg_editors = users['admins'] + users['content_managers']
        for key, val, stype, is_pub in cfg_data:
            SystemConfiguration.objects.create(
                key=key, value=val, setting_type=stype,
                description=f"Controls {key.replace('_', ' ')}",
                is_public=is_pub,
                updated_by=random.choice(cfg_editors),
            )

        # ── 6. PAYMENT GATEWAYS ──────────────────────────────────────────────
        self.stdout.write("💳 Creating payment gateways...")
        gateways = []
        for name, slug, gtype, active in [
            ('Stripe', 'stripe', 'stripe', True),
            ('PayPal', 'paypal', 'paypal', True),
            ('Flutterwave', 'flutterwave', 'flutterwave', True),
        ]:
            gateways.append(PaymentGateway.objects.create(
                name=name, slug=slug, gateway_type=gtype,
                api_key=f"pk_test_{uuid.uuid4().hex}",
                api_secret=f"sk_test_{uuid.uuid4().hex}",
                webhook_secret=f"whsec_{uuid.uuid4().hex}",
                is_active=active, is_test_mode=True,
            ))

        # ── 7. SUBSCRIPTION PLANS ────────────────────────────────────────────
        self.stdout.write("📋 Creating subscription plans...")
        plans = []
        plan_data = [
            ('Free Access', 'Full access to all MELBAC teachings and resources — free of charge', Decimal('0.00'), 'yearly',
             ['All teaching content', 'Community forums', 'Academic resources', 'Prayer group access'], None, True),
            ('Ministry Partner', 'Support MELBAC\'s mission while accessing premium resources', Decimal('10.00'), 'monthly',
             ['All free features', 'Priority support', 'Downloadable study materials', 'Monthly ministry update'], None, False),
            ('Campus Sponsor', 'Help fund satellite campus operations and student support', Decimal('50.00'), 'monthly',
             ['All Ministry Partner features', 'Sponsor certificate', 'Direct admin access', 'Quarterly impact report'], None, False),
            ('Institutional Partner', 'For churches and ministries partnering with MELBAC', Decimal('200.00'), 'monthly',
             ['All Campus Sponsor features', 'Institutional listing', 'Custom branding', 'API access', 'Dedicated liaison'], None, False),
        ]
        for idx, (name, desc, price, cycle, features, max_c, popular) in enumerate(plan_data):
            plans.append(SubscriptionPlan.objects.create(
                name=name, description=desc, price=price, currency='USD',
                billing_cycle=cycle, features=features,
                max_courses=max_c, is_active=True,
                is_popular=popular, display_order=idx,
            ))

        # ── 8. SUBSCRIPTIONS ─────────────────────────────────────────────────
        self.stdout.write("🎫 Creating subscriptions...")
        for student in verified_students:
            plan = random.choice(plans)
            days = 30 if plan.billing_cycle == 'monthly' else 365
            start = timezone.now().date() - timedelta(days=random.randint(0, 60))
            status = random.choice(['active', 'active', 'active', 'cancelled', 'expired'])
            Subscription.objects.create(
                user=student, plan=plan, status=status,
                end_date=start + timedelta(days=days),
                auto_renew=random.choice([True, False]),
                gateway_subscription_id=f"sub_{uuid.uuid4().hex[:24]}",
                cancelled_at=timezone.now() - timedelta(days=random.randint(1, 20))
                if status == 'cancelled' else None,
            )

        # ── 9. FACULTIES ─────────────────────────────────────────────────────
        self.stdout.write("🎓 Creating faculties...")
        faculty_raw = [
            {
                'name': 'Faculty of Christian Education', 'code': 'FCE',
                'icon': 'book-open', 'color_primary': 'purple', 'color_secondary': 'violet',
                'tagline': 'Building Faith on a Solid Biblical Foundation',
                'description': (
                    'The Faculty of Christian Education offers undergraduate and graduate degree programs '
                    'including Departments of Educational Administration, Religious Studies, '
                    'Christian Counseling, and Christian Education and Ethics.'
                ),
                'mission': (
                    'To equip ministers of God with a thorough knowledge of Christian Education principles, '
                    'sound doctrine, and ethical living grounded in the pure Word of God.'
                ),
                'vision': (
                    'A faculty that produces biblically literate, ethically sound, and spiritually '
                    'grounded Christian educators and counselors for the global body of Christ.'
                ),
                'accreditation': 'Approved by the Federal Government of Nigeria — International Professional Managers Association (IPMA) UK',
                'student_count': 420, 'placement_rate': 98,
                'partner_count': 12, 'international_faculty': 6,
                'special_features': [
                    'Free tuition for all enrolled students',
                    'Intensive fasting and prayer orientation for new students',
                    'Practical counseling training integrated into every program',
                    'International satellite campus delivery (Nigeria & USA)',
                ],
                'dean_name': 'Dr. Boniface Uzoigwe',
                'dean_role': 'Dean',
                'dean_faculty_label': 'Faculty of Christian Education',
            },
            {
                'name': 'Faculty of Church Management & Administration', 'code': 'FCMA',
                'icon': 'briefcase', 'color_primary': 'gold', 'color_secondary': 'yellow',
                'tagline': 'Equipping Leaders to Steward God\'s House',
                'description': (
                    'The Faculty of Church Management & Administration offers undergraduate and graduate '
                    'degree programs across Departments of Church and Intercultural Relations, Christian Ministry, '
                    'Church Business Management, Financial Management, and Church Administration.'
                ),
                'mission': (
                    'To develop principled, Spirit-led church administrators and managers who operate '
                    'with integrity, competence, and a deep knowledge of God\'s Word in every area of church life.'
                ),
                'vision': (
                    'A globally recognised faculty producing church leaders who blend sound biblical '
                    'principles with effective organisational and financial stewardship.'
                ),
                'accreditation': 'Approved by the Federal Government of Nigeria — International Professional Managers Association (IPMA) UK',
                'student_count': 310, 'placement_rate': 97,
                'partner_count': 10, 'international_faculty': 5,
                'special_features': [
                    'Programs in Missiology and Intercultural Church Relations',
                    'Church Financial Management & Administration specialisation',
                    'Free registration and tuition for all students',
                    'Practical ministerial attachment upon graduation',
                ],
                'dean_name': 'Dr. George Odjeni',
                'dean_role': 'Dean',
                'dean_faculty_label': 'Faculty of Church Management & Administration',
            },
            {
                'name': 'Faculty of Arts', 'code': 'FA',
                'icon': 'cross', 'color_primary': 'blue', 'color_secondary': 'indigo',
                'tagline': 'Deep Doctrine — Pure Word — Apostolic Fire',
                'description': (
                    'The Faculty of Arts offers undergraduate and graduate degree programs across '
                    'Departments of Prayer and Deliverance Studies, Christian Leadership/Discipleship, '
                    'Divinity, Missiology, Christian Communication, and Theology.'
                ),
                'mission': (
                    'To teach the pure, uncompromised Word of God and raise end-time ministers '
                    'grounded in deep doctrine, intercessory prayer, apostolic power, and '
                    'unwavering faith in Jesus Christ.'
                ),
                'vision': (
                    'A faculty synonymous with doctrinal depth, apostolic authority, and the '
                    'raising of ministers who walk in the fullness of the Kingdom of God.'
                ),
                'accreditation': 'Approved by the Federal Government of Nigeria — International Professional Managers Association (IPMA) UK',
                'student_count': 580, 'placement_rate': 99,
                'partner_count': 15, 'international_faculty': 8,
                'special_features': [
                    'Department of Prayer and Deliverance Studies — unique in Nigeria',
                    'Doctoral programs in Theology, Divinity, Missiology, and Christian Leadership',
                    'All programs completely free of charge',
                    'Students must be born again and baptised in water and the Holy Ghost',
                ],
                'dean_name': 'Dr. Titus Ehizode',
                'dean_role': 'Dean',
                'dean_faculty_label': 'Faculty of Arts',
            },
        ]
        faculties = []
        for idx, fd in enumerate(faculty_raw):
            f = Faculty.objects.create(
                name=fd['name'], code=fd['code'],
                icon=fd['icon'],
                color_primary=fd['color_primary'],
                color_secondary=fd['color_secondary'],
                tagline=fd['tagline'],
                description=fd['description'],
                mission=fd['mission'],
                vision=fd['vision'],
                dean_name=fd['dean_name'],
                dean_role=fd['dean_role'],
                dean_faculty_label=fd['dean_faculty_label'],
                accreditation=fd['accreditation'],
                student_count=fd['student_count'],
                placement_rate=fd['placement_rate'],
                partner_count=fd['partner_count'],
                international_faculty=fd['international_faculty'],
                special_features=fd['special_features'],
                meta_description=fd['description'][:160],
                meta_keywords=f"{fd['name']}, MELBAC, Bible degree, {fd['code']}, Nigeria",
                is_active=True, display_order=idx,
            )
            faculties.append(f)

        # ── 10. DEPARTMENTS ──────────────────────────────────────────────────
        self.stdout.write("🏛️  Creating departments...")
        dept_raw = [
            # Faculty of Christian Education
            (faculties[0], 'Department of Educational Administration', 'DEA',
             'Equipping Christian educators with the administrative and leadership skills to manage '
             'educational institutions in line with biblical principles.', 0),
            (faculties[0], 'Department of Religious Studies', 'DRS',
             'A comprehensive study of the Christian faith, Scripture, and the history of the Church '
             'from a biblically grounded and non-denominational perspective.', 1),
            (faculties[0], 'Department of Christian Counseling', 'DCC',
             'Preparing ministers to provide sound, biblically-rooted counseling to individuals, '
             'families, and churches facing life\'s challenges.', 2),
            (faculties[0], 'Department of Christian Education and Ethics', 'DCEE',
             'Exploring the moral and ethical demands of Scripture and equipping ministers to apply '
             'Christian ethics in all areas of life and ministry.', 3),
            # Faculty of Church Management & Administration
            (faculties[1], 'Department of Church and Intercultural Relations', 'DCIR',
             'Training ministers to navigate intercultural church dynamics and build bridges across '
             'cultural divides within the body of Christ.', 0),
            (faculties[1], 'Department of Christian Ministry', 'DCM',
             'Focused on the practical dimensions of pastoral and ministerial calling, equipping '
             'students with tools for effective Gospel ministry.', 1),
            (faculties[1], 'Department of Church Business Management', 'DCBM',
             'Equipping church leaders with business management principles applied through a '
             'biblical and ethical lens for the sustainable operation of Christian organisations.', 2),
            (faculties[1], 'Department of Financial Management/Administration', 'DFMA',
             'Training ministers in godly financial stewardship, church accounting, and the '
             'administration of resources within Christian institutions.', 3),
            (faculties[1], 'Department of Church Management/Administration', 'DCMA',
             'A broad study of the structures, policies, and practices that govern effective '
             'and Spirit-led church administration.', 4),
            # Faculty of Arts
            (faculties[2], 'Department of Prayer and Deliverance Studies', 'DPDS',
             'Arguably unique in Nigeria — this department trains ministers in the theology and '
             'practice of intercessory prayer, spiritual warfare, and deliverance ministry.', 0),
            (faculties[2], 'Department of Christian Leadership/Discipleship', 'DCLD',
             'Equipping the next generation of Kingdom leaders with the character, competence, '
             'and conviction needed to make disciples and lead God\'s people effectively.', 1),
            (faculties[2], 'Department of Divinity', 'DD',
             'The highest level of theological study offered at MELBAC, exploring the nature '
             'of God, the mystery of the Trinity, and the depths of divine revelation in Scripture.', 2),
            (faculties[2], 'Department of Missiology', 'DM',
             'Training cross-cultural missionaries and evangelists to fulfil the Great Commission '
             'through contextualised, biblically faithful missionary practice.', 3),
            (faculties[2], 'Department of Christian Communication', 'DCC2',
             'Developing effective communicators of the Gospel through preaching, teaching, '
             'writing, and modern media within a solid theological framework.', 4),
            (faculties[2], 'Department of Theology', 'DT',
             'A rigorous systematic and biblical theology program covering doctrines of God, '
             'man, sin, salvation, the Church, eschatology, and the Holy Spirit.', 5),
        ]
        departments = []
        for fac, name, code, desc, order in dept_raw:
            d = Department.objects.create(
                faculty=fac, name=name, code=code,
                description=desc, is_active=True, display_order=order,
            )
            departments.append(d)

        # Assign faculty/department to staff and student profiles
        for u in users['students'] + users['instructors'] + users['support']:
            fac = random.choice(faculties)
            fac_depts = [d for d in departments if d.faculty == fac]
            p = u.profile
            p.faculty = fac
            p.department = random.choice(fac_depts) if fac_depts else departments[0]
            p.save()

        # ── 11. PROGRAMS ─────────────────────────────────────────────────────
        self.stdout.write("📖 Creating programs...")
        prog_raw = [
            # Faculty of Christian Education — Bachelors
            (departments[0], 'Bachelor of Christian Educational Administration', 'BCR-CEA', 'undergraduate',
             Decimal('4.0'), 480, Decimal('0.00'), Decimal('0.00'), 100, True, 0),
            (departments[1], 'Bachelor of Christian Religious Studies/Ministry', 'BCR-CRS', 'undergraduate',
             Decimal('4.0'), 480, Decimal('0.00'), Decimal('0.00'), 120, True, 1),
            (departments[2], 'Bachelor of Christian Counseling', 'BCR-CC', 'undergraduate',
             Decimal('4.0'), 480, Decimal('0.00'), Decimal('0.00'), 80, False, 2),
            (departments[3], 'Bachelor of Christian Education and Ethics', 'BCR-CEE', 'undergraduate',
             Decimal('4.0'), 480, Decimal('0.00'), Decimal('0.00'), 80, False, 3),
            # Faculty of Christian Education — Masters
            (departments[0], 'Master of Christian Educational Administration', 'MCR-CEA', 'masters',
             Decimal('2.0'), 240, Decimal('0.00'), Decimal('0.00'), 50, False, 4),
            (departments[3], 'Master of Christian Education and Ethics', 'MCR-CEE', 'masters',
             Decimal('2.0'), 240, Decimal('0.00'), Decimal('0.00'), 40, False, 5),
            (departments[1], 'Master of Christian Religious Studies/Ministry', 'MCR-CRS', 'masters',
             Decimal('2.0'), 240, Decimal('0.00'), Decimal('0.00'), 40, False, 6),
            # Faculty of Christian Education — Doctoral
            (departments[3], 'Doctor of Christian Education and Ethics', 'DCR-CEE', 'phd',
             Decimal('3.0'), 360, Decimal('0.00'), Decimal('0.00'), 20, False, 7),
            (departments[0], 'Doctor of Christian Educational Administration', 'DCR-CEA', 'phd',
             Decimal('3.0'), 360, Decimal('0.00'), Decimal('0.00'), 20, False, 8),
            # Faculty of Church Management — Bachelors
            (departments[7], 'Bachelor of Church Financial Management & Administration', 'BCMA-CFM', 'undergraduate',
             Decimal('4.0'), 480, Decimal('0.00'), Decimal('0.00'), 90, True, 0),
            (departments[4], 'Bachelor of Church & Intercultural Relations', 'BCMA-CIR', 'undergraduate',
             Decimal('4.0'), 480, Decimal('0.00'), Decimal('0.00'), 70, False, 1),
            (departments[6], 'Bachelor of Church Business Management', 'BCMA-CBM', 'undergraduate',
             Decimal('4.0'), 480, Decimal('0.00'), Decimal('0.00'), 70, False, 2),
            # Faculty of Church Management — Masters
            (departments[3], 'Master of Missiology', 'MCMA-MISS', 'masters',
             Decimal('2.0'), 240, Decimal('0.00'), Decimal('0.00'), 40, False, 3),
            (departments[7], 'Master of Church Financial Management & Administration', 'MCMA-CFM', 'masters',
             Decimal('2.0'), 240, Decimal('0.00'), Decimal('0.00'), 30, False, 4),
            (departments[4], 'Master of Church & Intercultural Communications', 'MCMA-CIC', 'masters',
             Decimal('2.0'), 240, Decimal('0.00'), Decimal('0.00'), 30, False, 5),
            # Faculty of Church Management — Doctoral
            (departments[8], 'Doctor of Church Management & Administration', 'DCMA-CMA', 'phd',
             Decimal('3.0'), 360, Decimal('0.00'), Decimal('0.00'), 15, False, 6),
            # Faculty of Arts — Bachelors
            (departments[12], 'Bachelor of Christian Communication (Evangelism)', 'FA-BCE', 'undergraduate',
             Decimal('4.0'), 480, Decimal('0.00'), Decimal('0.00'), 100, True, 0),
            (departments[9], 'Bachelor of Intercessory Prayer & Deliverance Studies', 'FA-BPD', 'undergraduate',
             Decimal('4.0'), 480, Decimal('0.00'), Decimal('0.00'), 90, True, 1),
            (departments[11], 'Bachelor of Missiology', 'FA-BM', 'undergraduate',
             Decimal('4.0'), 480, Decimal('0.00'), Decimal('0.00'), 80, False, 2),
            (departments[14], 'Bachelor of Theology', 'FA-BT', 'undergraduate',
             Decimal('4.0'), 480, Decimal('0.00'), Decimal('0.00'), 120, True, 3),
            # Faculty of Arts — Masters
            (departments[10], 'Master of Christian Leadership and Discipleship', 'FA-MCLD', 'masters',
             Decimal('2.0'), 240, Decimal('0.00'), Decimal('0.00'), 50, False, 4),
            (departments[14], 'Master of Theology and Pastoral Counseling', 'FA-MTPC', 'masters',
             Decimal('2.0'), 240, Decimal('0.00'), Decimal('0.00'), 50, True, 5),
            # Faculty of Arts — Doctoral
            (departments[14], 'Doctor of Theology', 'FA-DT', 'phd',
             Decimal('3.0'), 360, Decimal('0.00'), Decimal('0.00'), 20, False, 6),
            (departments[10], 'Doctor of Christian Leadership / Discipleship', 'FA-DCLD', 'phd',
             Decimal('3.0'), 360, Decimal('0.00'), Decimal('0.00'), 15, False, 7),
            (departments[11], 'Doctor of Missiology and Christian Communication', 'FA-DMCC', 'phd',
             Decimal('3.0'), 360, Decimal('0.00'), Decimal('0.00'), 15, False, 8),
            (departments[11], 'Doctor of Divinity', 'FA-DD', 'phd',
             Decimal('3.0'), 360, Decimal('0.00'), Decimal('0.00'), 10, True, 9),
        ]
        programs = []
        for (dept, name, code, degree, dur, cred, app_fee, tuit, max_stu, feat, order) in prog_raw:
            base_name = name.split('of ')[-1] if ' of ' in name else name.split()[-1]
            p = Program.objects.create(
                department=dept, name=name, code=code,
                degree_level=degree, duration_years=dur,
                credits_required=cred, application_fee=app_fee,
                tuition_fee=tuit, max_students=max_stu,
                is_featured=feat, is_active=True, display_order=order,
                tagline=f"Train as a minister of God — {name}",
                overview=(
                    f"The {name} program at MELBAC is offered completely free of charge to all "
                    f"qualified students. It provides a rigorous biblical foundation for ministry "
                    f"and Christian service in {base_name}."
                ),
                description=(
                    f"This program equips students with deep knowledge of {base_name} through "
                    f"biblical instruction, practical training, and mentoring from experienced "
                    f"ministers of the Gospel. All study is grounded in the pure Word of God."
                ),
                available_study_modes=['full_time', 'online', 'blended'],
                entry_requirements=[
                    "Must be born again and have a personal relationship with Jesus Christ",
                    "Must be baptised in water",
                    "Must be baptised in the Holy Ghost (or willing to pursue this)",
                    "Must be resolved to be trained as a minister of the Gospel",
                    "Irrespective of nationality, gender, race, age, disability, ethnicity, or colour",
                    "Must accept MELBAC's statement of faith and code of conduct",
                ],
                core_courses=[
                    f"{code}-101 Foundations of {base_name}",
                    f"{code}-201 Intermediate {base_name}",
                    f"{code}-301 Advanced {base_name}",
                    f"{code}-401 Research Methods in {base_name}",
                ],
                specialization_tracks=[
                    f"Applied {base_name}",
                    f"Ministry and Mission — {base_name}",
                    f"Teaching and Discipleship in {base_name}",
                ],
                learning_outcomes=[
                    f"Demonstrate comprehensive biblical knowledge of {base_name}",
                    "Apply doctrinal knowledge in practical ministry settings",
                    "Preach, teach, and communicate the Gospel with clarity and power",
                    "Lead and disciple others within the body of Christ",
                ],
                career_paths=[
                    "Pastor / Senior Minister",
                    "Evangelist / Missionary",
                    f"{base_name} Lecturer or Academic",
                    "Church Administrator or Ministry Leader",
                ],
                avg_starting_salary="Ministry-based (not salary-driven)",
                job_placement_rate=98,
                meta_description=f"Study {name} at MELBAC — free of charge, accredited, biblically grounded.",
                meta_keywords=f"{name}, {code}, MELBAC, Bible degree Nigeria, theology, free seminary",
            )
            programs.append(p)

        # Assign program to student profiles
        for u in users['students']:
            p = u.profile
            if p.department:
                dept_progs = [pr for pr in programs if pr.department == p.department]
                if dept_progs:
                    p.program = random.choice(dept_progs)
                    p.save()

        # ── 12. ACADEMIC SESSIONS ────────────────────────────────────────────
        self.stdout.write("📅 Creating academic sessions...")
        sessions = []
        session_data = [
            ('2023/2024',
             date(2023, 11, 1), date(2024, 4, 5),
             date(2024, 4, 22), date(2024, 8, 23),
             date(2023, 8, 28), date(2023, 10, 25), 'closed', False),
            ('2024/2025',
             date(2024, 11, 4), date(2025, 4, 4),
             date(2025, 4, 28), date(2025, 8, 22),
             date(2024, 8, 26), date(2024, 10, 28), 'active', True),
            ('2025/2026',
             date(2025, 11, 3), date(2026, 4, 3),
             date(2026, 4, 27), date(2026, 8, 21),
             date(2025, 8, 25), date(2025, 10, 27), 'upcoming', False),
        ]
        for (name, fs, fe, ss, se, rs, re, status, is_curr) in session_data:
            s = AcademicSession.objects.create(
                name=name,
                first_semester_start=fs, first_semester_end=fe,
                second_semester_start=ss, second_semester_end=se,
                registration_start=rs, registration_end=re,
                status=status, is_current=is_curr,
            )
            sessions.append(s)

        # ── 13. COURSES (Academic) ────────────────────────────────────────────
        self.stdout.write("📚 Creating academic courses...")
        course_templates = [
            (programs[1],  'Introduction to Christian Religious Studies',        'CRS101', 'core',     3, 1),
            (programs[1],  'Old Testament Survey',                                'CRS102', 'core',     3, 1),
            (programs[14], 'Foundations of Systematic Theology',                  'THL101', 'core',     3, 1),
            (programs[14], 'New Testament Survey',                                'THL102', 'core',     3, 1),
            (programs[17], 'Principles of Intercessory Prayer',                   'PDS101', 'core',     3, 1),
            (programs[17], 'Spiritual Warfare and Deliverance Ministry',          'PDS201', 'core',     3, 2),
            (programs[2],  'Introduction to Christian Counseling',                'CC101',  'core',     3, 1),
            (programs[2],  'Biblical Foundations of Counseling',                  'CC102',  'core',     3, 1),
            (programs[9],  'Church Financial Management Principles',              'CFM101', 'core',     3, 1),
            (programs[9],  'Biblical Stewardship and Accountability',             'CFM102', 'core',     3, 1),
            (programs[10], 'Church and Intercultural Relations',                  'CIR101', 'core',     3, 1),
            (programs[12], 'Introduction to Missiology',                          'MISS101', 'core',    3, 1),
            (programs[18], 'Cross-Cultural Mission Strategies',                   'MISS201', 'core',    3, 2),
            (programs[20], 'Christian Leadership Principles',                     'CLD201', 'core',     3, 2),
            (programs[20], 'Discipleship: Making and Training Disciples',         'CLD202', 'elective', 3, 2),
            (programs[3],  'Ethics in Christian Ministry',                        'CEE201', 'core',     3, 2),
            (programs[21], 'Pastoral Counseling in the Local Church',             'PCT301', 'core',     3, 3),
            (programs[22], 'Advanced Theology: Soteriology and Eschatology',      'THL401', 'core',     3, 4),
            (programs[25], 'Doctoral Research Methods in Divinity',               'DIV901', 'core',     6, 1),
            (programs[22], 'The Authority of the Believer',                       'THL310', 'elective', 3, 3),
        ]
        courses = []
        current_session = sessions[1]
        for prog, title, code, ctype, credits, yr in course_templates:
            c = Course.objects.create(
                program=prog,
                academic_session=current_session,
                name=title,
                code=code,
                course_type=ctype,
                credit_units=credits,
                year_of_study=yr,
                description=(
                    f"This course provides a comprehensive study of {title.lower()}, "
                    f"equipping students with sound biblical knowledge and practical ministry application."
                ),
                is_active=True,
            )
            courses.append(c)

        # ── 14. COURSE INTAKES ───────────────────────────────────────────────
        self.stdout.write("📋 Creating course intakes...")
        intakes = []
        # ✅ FIX: unique_together = [['program', 'intake_period', 'year']]
        # Use get_or_create to safely skip duplicates; vary intake_period per session
        intake_period_cycle = ['january', 'may', 'september']
        for prog_idx, prog in enumerate(random.sample(programs, k=min(12, len(programs)))):
            for sess_idx, session in enumerate(sessions[:2]):
                # Vary period by program index + session index to avoid collisions
                period = intake_period_cycle[(prog_idx + sess_idx) % 3]
                year_val = session.first_semester_start.year
                intake, _ = CourseIntake.objects.get_or_create(
                    program=prog,
                    intake_period=period,
                    year=year_val,
                    defaults=dict(
                        start_date=session.first_semester_start,
                        application_deadline=session.registration_end,
                        available_slots=prog.max_students,
                        is_active=True,
                    )
                )
                intakes.append(intake)

        # ── 15. REQUIRED PAYMENTS ────────────────────────────────────────────
        self.stdout.write("💰 Creating required payments...")
        for prog in programs:
            # ✅ FIX: correct fields — no name/description/currency/is_required/payment_stage
            AllRequiredPayments.objects.create(
                program=prog,
                purpose='Application Processing Fee',
                amount=Decimal('0.00'),
                due_date=date.today(),
                who_to_pay='applicant',
                is_active=True,
            )

        # ── 16. COURSE APPLICATIONS ──────────────────────────────────────────
        self.stdout.write("📝 Creating course applications...")
        applications = []
        statuses = ['approved', 'approved', 'under_review', 'draft', 'approved', 'payment_complete']
        # ✅ FIX: move verified_admins_list outside loop (no per-iteration change)
        verified_admins_list = [u for u in users['admins'] if u.profile.email_verified]
        for idx, student in enumerate(users['students']):
            prog = random.choice(programs)
            intake = random.choice(intakes) if intakes else None
            status = statuses[idx % len(statuses)]
            admitted = status == 'approved'
            dept_approved = admitted
            # ✅ FIX: uuid hex guarantees no UNIQUE collision; None (not '') for non-admitted
            adm_number = (
                f"MELBAC/{date.today().year}/{uuid.uuid4().hex[:8].upper()}"
                if admitted else None
            )

            app = CourseApplication.objects.create(
                user=student,                       # ✅ FIX: was student=
                program=prog,
                intake=intake,
                study_mode=random.choice(['full_time', 'part_time', 'online']),  # ✅ required field
                first_name=student.first_name,
                last_name=student.last_name,
                email=student.email,                # ✅ required field
                phone='+234' + str(random.randint(8000000000, 9099999999)),  # ✅ required field
                date_of_birth=fake.date_of_birth(minimum_age=22, maximum_age=65),
                gender=random.choice(['male', 'female']),
                nationality=random.choice(['Nigerian', 'Ghanaian', 'American', 'British', 'Cameroonian']),
                address_line1=fake.street_address(),
                address_line2='',
                city=random.choice(['Lagos', 'Abuja', 'Newark', 'London', 'Accra', 'Houston']),
                state=random.choice(['Lagos State', 'FCT', 'New Jersey', 'Texas', 'Greater Accra']),
                postal_code=fake.postcode(),
                country=random.choice(['Nigeria', 'United States', 'United Kingdom', 'Ghana']),
                highest_qualification=random.choice(
                    ['Secondary School', 'OND', 'HND', 'Bachelor Degree', 'Masters Degree']
                ),
                institution_name=random.choice([
                    'Lagos State University', 'University of Nigeria Nsukka',
                    'Covenant University', 'University of Lagos',
                    'Redeemer\'s University', 'Babcock University',
                ]),
                graduation_year=str(random.randint(2005, 2023)),
                gpa_or_grade=random.choice(['First Class', 'Second Class Upper', 'Second Class Lower', 'Pass']),
                language_skill='none',
                language_score=None,
                work_experience_years=random.randint(0, 20),
                personal_statement=(
                    "I am a born-again, Spirit-filled believer called by God to minister His Word. "
                    "I believe MELBAC's training will equip me to fulfil my God-given calling. "
                    "I am committed to the study of the pure Word of God and to a life of prayer, "
                    "holiness, and faithful ministry."
                ),
                how_did_you_hear=random.choice(
                    ['Social Media', 'Friend/Colleague in Ministry', 'Church Announcement',
                     'YouTube', 'Website', 'WhatsApp Group']
                ),
                how_did_you_hear_other='',
                scholarship=False,
                accept_privacy_policy=True,
                accept_terms_conditions=True,
                marketing_consent=random.choice([True, False]),
                emergency_contact_name=fake.name(),
                emergency_contact_phone='+234' + str(random.randint(8000000000, 9099999999)),
                emergency_contact_relationship=random.choice(
                    ['Spouse', 'Parent', 'Pastor', 'Sibling', 'Guardian']
                ),
                emergency_contact_email=fake.email(),
                emergency_contact_address=fake.address()[:255],
                status=status,
                reviewer=random.choice(verified_admins_list) if random.random() > 0.5 else None,
                review_notes=(
                    'Applicant meets all spiritual and academic requirements for admission to MELBAC.'
                ) if random.random() > 0.5 else '',
                submitted_at=timezone.now() - timedelta(days=random.randint(1, 90))
                if status != 'draft' else None,
                payment_status='completed',
                in_processing=status in ['under_review', 'payment_complete'],
                admission_accepted=admitted,
                admission_accepted_at=timezone.now() - timedelta(days=random.randint(1, 30))
                if admitted else None,
                admission_number=adm_number,
                department_approved=dept_approved,
                department_approved_at=timezone.now() - timedelta(days=random.randint(1, 15))
                if dept_approved else None,
                department_approved_by=random.choice(verified_admins_list) if dept_approved else None,
            )
            applications.append(app)

        # ── 17. APPLICATION DOCUMENTS ────────────────────────────────────────
        self.stdout.write("📎 Creating application documents (metadata only)...")
        for app in applications:
            for doc_type in random.sample(
                ['transcript', 'certificate', 'cv', 'passport', 'id_document', 'recommendation'],
                k=random.randint(2, 5)
            ):
                ApplicationDocument.objects.create(
                    application=app, file_type=doc_type,
                    file='documents/placeholder.pdf',
                    original_filename=f"{doc_type}_{uuid.uuid4().hex[:6]}.pdf",
                    file_size=random.randint(100_000, 5_000_000),
                )

        # ── 18. APPLICATION PAYMENTS ─────────────────────────────────────────
        for app in [a for a in applications if a.status in ['payment_complete', 'under_review', 'approved']]:
            method = random.choice(['card', 'bank_transfer'])   # ← pull method out first
            ApplicationPayment.objects.create(
                application=app,
                amount=Decimal('0.00'),
                currency='USD',
                status='success',
                payment_method=method,
                payment_reference=f"MELBAC-{uuid.uuid4().hex[:12].upper()}",
                gateway_payment_id=f"pi_{uuid.uuid4().hex[:24]}",
                card_last4=str(random.randint(1000, 9999)) if method == 'card' else '',   # ← guarded
                card_brand=random.choice(['Visa', 'Mastercard', 'Verve']) if method == 'card' else '',  # ← guarded
                paid_at=timezone.now() - timedelta(days=random.randint(1, 60)),
                payment_metadata={
                    'note': 'MELBAC is free — no tuition charged.',
                    'ip_address': fake.ipv4(),
                    'device': random.choice(['desktop', 'mobile', 'tablet']),
                },
                failure_reason='',
            )

        # ── 19. COURSE CATEGORIES (LMS) ──────────────────────────────────────
        self.stdout.write("🗂️  Creating LMS course categories...")
        cat_raw = [
            ('Biblical Doctrine & Theology', 'book-open', 'purple'),
            ('Prayer & Spiritual Warfare', 'zap', 'blue'),
            ('Christian Leadership & Discipleship', 'users', 'gold'),
            ('Missiology & Evangelism', 'globe', 'green'),
            ('Church Management & Administration', 'briefcase', 'orange'),
            ('Christian Counseling', 'heart', 'pink'),
            ('Intercessory Prayer & Deliverance', 'shield', 'indigo'),
            ('Christian Ethics & Education', 'award', 'teal'),
            ('Old & New Testament Studies', 'scroll', 'amber'),
            ('Apostolic & Prophetic Ministry', 'flame', 'red'),
        ]
        categories = []
        for idx, (name, icon, color) in enumerate(cat_raw):
            categories.append(CourseCategory.objects.create(
                name=name,
                description=(
                    f"A curated collection of MELBAC teachings and courses in {name.lower()}, "
                    f"grounded in the pure Word of God and practical ministry application."
                ),
                icon=icon, color=color, display_order=idx, is_active=True,
            ))
        # Sub-categories
        sub_cat_data = [
            (categories[0], 'Systematic Theology', 'book', 'violet'),
            (categories[0], 'Biblical Hermeneutics', 'search', 'indigo'),
            (categories[1], 'Advanced Intercession', 'zap', 'sky'),
        ]
        for parent, name, icon, color in sub_cat_data:
            CourseCategory.objects.create(
                name=name, parent=parent,
                description=f"Advanced study in {name.lower()} for experienced ministers.",
                icon=icon, color=color, display_order=99, is_active=True,
            )

        # ── 20. LMS COURSES ──────────────────────────────────────────────────
        self.stdout.write("🎥 Creating LMS courses...")
        lms_templates = [
            ('The Authority of a Believer — Complete Series', categories[0], 'intermediate', 12.5,
             'A 5-part teaching series by Apostle John Daniel unpacking the God-given authority '
             'of every believer in Christ — from kingdom dominion to divine blessings and prosperity.'),
            ('The Mystery of Forgiveness — Complete Series', categories[0], 'beginner', 10.0,
             'A 5-part series exploring the spiritual mechanics of divine forgiveness, repentance, '
             'blasphemy, and the conditions for receiving God\'s mercy, taught by Apostle John Daniel.'),
            ('Due Process in Christendom', categories[0], 'beginner', 3.5,
             'A new teaching series revealing the divine protocol and timing of God\'s Kingdom — '
             'why there are no shortcuts in the spiritual life and how believers must align themselves '
             'with God\'s process.'),
            ('Principles of Intercessory Prayer', categories[1], 'beginner', 8.0,
             'A foundational course in the ministry of intercession — what it is, how it works, '
             'and how believers can develop a powerful, consistent prayer life that moves the hand of God.'),
            ('Spiritual Warfare & Deliverance Ministry', categories[6], 'intermediate', 14.0,
             'A comprehensive course covering the theology and practice of spiritual warfare, '
             'deliverance, binding and loosing, and ministering freedom to the captives in Jesus\'s name.'),
            ('Foundations of Systematic Theology', categories[0], 'beginner', 16.0,
             'A rigorous introduction to systematic theology covering Bibliology, Theology Proper, '
             'Christology, Pneumatology, Anthropology, Soteriology, Ecclesiology, and Eschatology.'),
            ('Christian Leadership & Discipleship', categories[2], 'intermediate', 11.0,
             'Equipping ministers to lead with character, call, and competence — developing disciples '
             'who make disciples, in line with the Great Commission of Jesus Christ.'),
            ('Introduction to Missiology & Cross-Cultural Ministry', categories[3], 'beginner', 9.5,
             'A biblical and practical introduction to world missions, covering the theology of the '
             'Great Commission, cultural intelligence, and strategies for effective cross-cultural ministry.'),
            ('Church Financial Management & Biblical Stewardship', categories[4], 'intermediate', 10.5,
             'Equipping church leaders with the principles of godly financial stewardship, biblical '
             'accountability, budgeting, and the practical management of church resources.'),
            ('Old Testament Survey: From Genesis to Malachi', categories[8], 'beginner', 18.0,
             'A sweeping survey of the entire Old Testament, exploring the narrative arc of Scripture '
             'from creation and the fall to the prophets — and how it all points to Jesus Christ.'),
        ]
        lms_courses = []
        instructor_course_map = {}
        for idx, (title, cat, diff, dur, desc) in enumerate(lms_templates):
            instructor = users['instructors'][idx % len(users['instructors'])]
            lc = LMSCourse.objects.create(
                title=title,
                code=f"MELBAC{idx + 1:03d}",
                category=cat,
                short_description=desc[:500],
                description='\n\n'.join([
                    desc,
                    'This course is offered completely free of charge to all MELBAC students. '
                    'Content is grounded in the pure Word of God and the apostolic teaching of Apostle John Daniel.',
                    'Students are expected to be born again and committed to the study of Scripture and prayer.',
                    'Assignments and assessments are designed to develop both doctrinal knowledge '
                    'and practical ministry application.',
                ]),
                learning_objectives=[
                    f"Understand the core biblical principles of {title.split(':')[0].split('—')[0].strip()}",
                    "Apply the teaching to personal spiritual growth and ministry practice",
                    "Engage with Scripture through prayer, study, and meditation",
                    "Develop ministry skills grounded in the pure Word of God",
                ],
                prerequisites=(
                    ['None — open to all born-again believers'] if diff == 'beginner'
                    else ['Completion of at least one foundational MELBAC course', 'Active prayer life and regular Bible study']
                ),
                difficulty_level=diff,
                duration_hours=Decimal(str(dur)),
                language='English',
                instructor=instructor,
                instructor_name=instructor.get_full_name(),
                instructor_bio=(
                    'A dedicated minister of God and MELBAC faculty member committed to teaching '
                    'the pure, uncompromised Word of God to end-time ministers worldwide.'
                ),
                promo_video_url='https://www.youtube.com/watch?v=-mJFZp84TIY',
                max_students=None,
                enrollment_start_date=date(2025, 1, 1),
                enrollment_end_date=date(2026, 12, 31),
                is_published=True,
                is_featured=random.random() > 0.6,
                has_certificate=True,
                certificate_template='melbac_standard',
                meta_description=desc[:160],
                meta_keywords=f"{title}, MELBAC, Bible teaching, Apostle John Daniel, free course",
            )
            lms_courses.append(lc)
            instructor_course_map.setdefault(instructor, []).append(lc)

        # ── 21. LESSON SECTIONS & LESSONS ────────────────────────────────────
        self.stdout.write("📹 Creating lesson sections and lessons...")
        bible_section_titles = [
            'Introduction & Biblical Foundation',
            'Core Doctrine',
            'Deep Study',
            'Practical Ministry Application',
            'Prayer & Activation',
            'Assessment & Review',
        ]
        lesson_type_pool = ['video', 'video', 'video', 'text', 'quiz', 'assignment']
        all_lessons = []
        for lc in lms_courses:
            for s_idx, s_title in enumerate(
                random.sample(bible_section_titles, k=random.randint(3, 5))
            ):
                section = LessonSection.objects.create(
                    course=lc, title=s_title,
                    description=(
                        f"In this section of {lc.title}, students will go deeper into "
                        f"{s_title.lower()} through focused teaching, Scripture study, and prayer."
                    ),
                    display_order=s_idx, is_active=True,
                )
                bible_lesson_titles = [
                    'Opening Prayer and Scripture Reading',
                    'Foundational Biblical Principles',
                    'Exegesis of Key Passages',
                    'Doctrinal Depth — Going Deeper',
                    'Ministry Application and Practical Examples',
                    'Question & Answer with Apostle John Daniel',
                    'Prayer Activation and Confession of the Word',
                ]
                for l_idx in range(random.randint(3, 7)):
                    ltype = random.choice(lesson_type_pool)
                    video_embed = random.choice(EMBED_CODES) if ltype == 'video' else ''
                    lesson_title = bible_lesson_titles[l_idx % len(bible_lesson_titles)]
                    lesson = Lesson.objects.create(
                        course=lc, section=section,
                        title=f"{s_title} – Part {l_idx + 1}: {lesson_title}",
                        lesson_type=ltype,
                        description=(
                            f"In this lesson, students will study {lesson_title.lower()} "
                            f"as part of the {s_title} section of {lc.title}."
                        ),
                        content=(
                            f"Lesson content: {lesson_title}. "
                            f"Students are encouraged to read along with their Bibles open, pray before "
                            f"and after each session, and take notes for personal reflection and ministry."
                        ),
                        video_url=video_embed,
                        video_duration_minutes=random.randint(20, 75) if ltype == 'video' else 0,
                        is_preview=(l_idx == 0),
                        is_active=True,
                        display_order=l_idx,
                    )
                    all_lessons.append(lesson)

        # ── 22. ENROLLMENTS ──────────────────────────────────────────────────
        self.stdout.write("🎓 Creating enrollments...")
        enrollments = []
        for student in verified_students:
            for lc in random.sample(lms_courses, k=random.randint(2, 7)):
                status = random.choice(['active', 'active', 'completed', 'dropped'])
                progress = Decimal(str(round(random.uniform(0, 100), 2)))
                enr = Enrollment.objects.create(
                    student=student, course=lc,
                    enrolled_by=random.choice(users['admins']),
                    progress_percentage=progress,
                    completed_lessons=random.randint(0, 20),
                    current_grade=Decimal(str(round(random.uniform(60, 100), 2)))
                    if progress > 30 else None,
                    status=status,
                    completed_at=timezone.now() - timedelta(days=random.randint(1, 60))
                    if status == 'completed' else None,
                    last_accessed=timezone.now() - timedelta(hours=random.randint(1, 720)),
                )
                enrollments.append(enr)

        # ── 23. LESSON PROGRESS ──────────────────────────────────────────────
        self.stdout.write("📈 Creating lesson progress records...")
        for enr in enrollments[:40]:
            course_lessons = list(enr.course.lessons.filter(is_active=True))
            for lesson in random.sample(course_lessons, k=min(5, len(course_lessons))):
                is_done = random.random() > 0.4
                LessonProgress.objects.get_or_create(
                    enrollment=enr, lesson=lesson,
                    defaults=dict(
                        is_completed=is_done,
                        completion_percentage=Decimal('100.00') if is_done
                        else Decimal(str(round(random.uniform(10, 90), 2))),
                        time_spent_minutes=random.randint(15, 90),
                        video_progress_seconds=random.randint(0, 4500),
                        started_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                        completed_at=timezone.now() - timedelta(days=random.randint(0, 10))
                        if is_done else None,
                    )
                )

        # ── 24. ASSIGNMENTS ──────────────────────────────────────────────────
        self.stdout.write("📝 Creating assignments...")
        assignments = []
        ministry_assignments = [
            'Write a 3-page reflection on the teaching and its implications for your ministry.',
            'Find 10 scriptures that support the main doctrine taught in this lesson and explain each.',
            'Share how you have applied this teaching in your personal prayer life this week.',
            'Write a sermon outline based on one of the key passages covered in this lesson.',
            'Identify and address one doctrinal error in your local church or community using this teaching.',
            'Write a testimony of how this teaching has impacted your relationship with the Lord.',
            'Summarise the key points of this lesson in 500 words in your own words.',
        ]
        for lesson in random.sample(all_lessons, k=min(40, len(all_lessons))):
            if lesson.lesson_type in ['video', 'text']:
                a = Assignment.objects.create(
                    lesson=lesson,
                    title=f"Reflection Assignment: {lesson.section.title}",
                    description=random.choice(ministry_assignments),
                    instructions=(
                        'Submit your assignment in written form. All work must be your own reflection '
                        'on the Word of God. Cite scripture references where applicable. '
                        'Pray before you begin writing.'
                    ),
                    max_score=Decimal('100.00'),
                    passing_score=Decimal('60.00'),
                    due_date=timezone.now() + timedelta(days=random.randint(14, 60)),
                    allow_late_submission=True,
                    late_penalty_percent=0,
                    is_active=True,
                )
                assignments.append(a)

        # ── 25. ASSIGNMENT SUBMISSIONS ───────────────────────────────────────
        self.stdout.write("📤 Creating assignment submissions...")
        for assignment in random.sample(assignments, k=min(30, len(assignments))):
            enrolled = list(
                Enrollment.objects.filter(course=assignment.lesson.course, status='active')
            )
            for enr in random.sample(enrolled, k=min(4, len(enrolled))):
                graded = random.random() > 0.4
                AssignmentSubmission.objects.create(
                    assignment=assignment,
                    student=enr.student,
                    submission_text=(
                        f"This teaching on {assignment.lesson.section.title} has deeply impacted "
                        f"my understanding of the Word of God. I have found that when I apply these "
                        f"principles in prayer and ministry, there is a noticeable difference in "
                        f"the spiritual results I see. Scripture references: Romans 8:1, Ephesians 6:10-18."
                    ),
                    score=Decimal(str(round(random.uniform(60, 100), 2))) if graded else None,
                    status='graded' if graded else 'submitted',  # ✅ FIX: is_graded → status
                    graded_by=random.choice(users['instructors']) if graded else None,
                    graded_at=timezone.now() - timedelta(days=random.randint(1, 14)) if graded else None,
                    feedback=(
                        'Excellent reflection. Your engagement with the Scripture references shows '
                        'genuine study and prayer. Keep pressing deeper into the Word.'
                    ) if graded else '',
                    submitted_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                )

        # ── 26 & 27. QUIZZES & QUESTIONS ─────────────────────────────────────
        self.stdout.write("❓ Creating quizzes and questions...")
        quiz_questions_pool = [
            (
                'According to Matthew 28:18, what did Jesus declare before commissioning His disciples?',
                ['All authority in heaven and on earth has been given to me',
                 'Go into all the world and preach the Gospel',
                 'I will be with you always, to the end of the age',
                 'Baptising them in the name of the Father and the Son and the Holy Spirit'],
                0
            ),
            (
                'What does Habakkuk 2:3 teach about God\'s timing?',
                ['God is never in a hurry and His promises have an appointed time',
                 'God changes His plans based on human actions',
                 'All prophecy must be fulfilled within one generation',
                 'God requires human effort to speed up His plan'],
                0
            ),
            (
                'In 1 John 1:9, what is the condition for receiving God\'s forgiveness?',
                ['Confessing and forsaking sin',
                 'Offering a sacrifice at the altar',
                 'Performing acts of penance',
                 'Repeating the sinner\'s prayer daily'],
                0
            ),
            (
                'Which of the following best describes "blasphemy against the Holy Spirit" as taught by Jesus in Matthew 12:31-32?',
                ['Persistently attributing the works of the Holy Spirit to Satan',
                 'Using the Lord\'s name in vain',
                 'Denying the existence of God',
                 'Refusing water baptism'],
                0
            ),
            (
                'What is the biblical basis for the "authority of a believer" as taught at MELBAC?',
                ['Luke 10:19 — believers are given authority over all the power of the enemy',
                 'James 4:7 — resist the devil and he will flee',
                 'Psalm 91:1 — dwelling in the secret place of the Most High',
                 'Romans 8:1 — no condemnation for those in Christ'],
                0
            ),
            (
                'According to Galatians 1:10, what distinguishes a God-pleaser from a man-pleaser?',
                ['A God-pleaser seeks the approval of God, not men',
                 'A God-pleaser always avoids conflict with other believers',
                 'A God-pleaser never holds a leadership position',
                 'A God-pleaser speaks only in tongues during prayer'],
                0
            ),
            (
                'What does Proverbs 24:3-4 teach about prosperity?',
                ['A house is built through wisdom, and through knowledge its rooms are filled with treasure',
                 'The righteous shall flourish like a green tree',
                 'God blesses those who give ten percent of their income',
                 'Prosperity comes to those who avoid all financial debt'],
                0
            ),
            (
                'Which year was MELBAC physically founded by Dr. John A. Daniel?',
                ['2000', '1995', '2007', '2004'],
                0
            ),
            (
                'What is MELBAC\'s primary requirement for student admission?',
                ['Students must be born again and resolved to be trained ministers of the Gospel',
                 'Students must have a degree from a recognised university',
                 'Students must be ordained by a recognised denomination',
                 'Students must pay a registration and tuition fee'],
                0
            ),
            (
                'What does Mark 11:23 teach about the operation of faith?',
                ['Whoever says to the mountain with belief and no doubt in their heart, it shall be done',
                 'Faith without works is dead',
                 'The effectual fervent prayer of a righteous man avails much',
                 'Faith is the substance of things hoped for, the evidence of things not seen'],
                0
            ),
        ]

        quizzes = []
        for lesson in random.sample(all_lessons, k=min(30, len(all_lessons))):
            if lesson.lesson_type in ['video', 'text']:
                quiz = Quiz.objects.create(
                    lesson=lesson,
                    title=f"Quiz: {lesson.section.title}",
                    description=(
                        'Test your understanding of the teaching in this lesson. '
                        'Pray for the Holy Spirit\'s guidance as you answer.'
                    ),
                    time_limit_minutes=random.choice([15, 20, 30]),
                    passing_score=Decimal('60.00'),
                    max_attempts=3,
                    is_active=True,
                )
                quizzes.append(quiz)
                for i, (qtext, options, correct_idx) in enumerate(
                    random.sample(quiz_questions_pool, k=min(5, len(quiz_questions_pool)))
                ):
                    q = QuizQuestion.objects.create(
                        quiz=quiz, question_type='multiple_choice',
                        question_text=qtext,
                        explanation=(
                            'This is a key doctrine taught by Apostle John Daniel at MELBAC. '
                            'Review the lesson content and your Bible for the full context.'
                        ),
                        points=Decimal('1.00'),
                        display_order=i, is_active=True,
                    )
                    for j, opt_text in enumerate(options):
                        QuizAnswer.objects.create(
                            question=q,
                            answer_text=opt_text,
                            is_correct=(j == correct_idx),
                            display_order=j,
                        )

        # ── 28. QUIZ ATTEMPTS & RESPONSES ────────────────────────────────────
        self.stdout.write("🎯 Creating quiz attempts and responses...")
        for quiz in random.sample(quizzes, k=min(len(quizzes), 40)):
            enrolled = list(
                Enrollment.objects.filter(course=quiz.lesson.course, status='active')
            )
            for enr in random.sample(enrolled, k=min(4, len(enrolled))):
                for _ in range(random.randint(1, 2)):
                    pct = Decimal(str(round(random.uniform(60, 100), 2)))
                    attempt = QuizAttempt.objects.create(
                        quiz=quiz, student=enr.student,
                        score=pct, max_score=Decimal('100.00'), percentage=pct,
                        is_completed=True,
                        passed=pct >= quiz.passing_score,
                        completed_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                        time_taken_minutes=random.randint(5, quiz.time_limit_minutes or 30),
                    )
                    for q in quiz.questions.all():
                        answers = list(q.answers.all())
                        if answers:
                            sel = random.choice(answers)
                            QuizResponse.objects.get_or_create(
                                attempt=attempt, question=q,
                                defaults=dict(
                                    selected_answer=sel,
                                    text_response='',
                                    is_correct=sel.is_correct,
                                    points_earned=q.points if sel.is_correct else Decimal('0.00'),
                                )
                            )

        # ── 29. REVIEWS ──────────────────────────────────────────────────────
        self.stdout.write("⭐ Creating reviews...")
        review_texts = [
            'This teaching has completely transformed my prayer life and ministry. Apostle John Daniel teaches with deep anointing and clarity. Highly recommended.',
            'I have been in ministry for 10 years, but this course opened my eyes to dimensions of the Word I had never seen. MELBAC is a true gift to the body of Christ.',
            'The depth of doctrine in this series is unmatched. I\'ve taken courses at several Bible schools and nothing compares to the purity and depth of MELBAC\'s teaching.',
            'I started this course as a young believer and it has given me a solid foundation. I now lead a Bible study group in my church using what I learned here.',
            'Every minister of God must take this course. The teaching on spiritual authority alone is worth more than any seminary education I have encountered.',
        ]
        for lc in lms_courses:
            enrolled = list(Enrollment.objects.filter(course=lc))
            for enr in random.sample(enrolled, k=min(random.randint(3, 8), len(enrolled))):
                Review.objects.get_or_create(
                    course=lc, student=enr.student,
                    defaults=dict(
                        rating=random.randint(4, 5),
                        review_text=random.choice(review_texts),
                        is_approved=random.random() > 0.1,
                    )
                )

        # ── 30. CERTIFICATES ─────────────────────────────────────────────────
        self.stdout.write("🏆 Creating certificates...")
        completed = [
            e for e in enrollments if e.status == 'completed' and e.course.has_certificate
        ]
        for enr in completed:
            Certificate.objects.get_or_create(
                student=enr.student, course=enr.course,
                defaults=dict(
                    completion_date=(enr.completed_at or timezone.now()).date(),
                    grade=random.choice(['A', 'A+', 'B', 'Distinction', 'Pass with Merit']),
                    verification_code=uuid.uuid4(),
                    is_verified=True,
                )
            )

        # ── 31. TRANSACTIONS ─────────────────────────────────────────────────
        self.stdout.write("💳 Creating transactions...")
        for student in verified_students:
            for _ in range(random.randint(1, 3)):
                gw = random.choice(gateways)
                Transaction.objects.create(
                    user=student, transaction_type='enrollment',
                    amount=Decimal('0.00'), currency='USD',
                    gateway=gw,
                    gateway_transaction_id=f"{gw.slug}_{uuid.uuid4().hex[:20]}",
                    status='completed',
                    course=random.choice(lms_courses),
                    metadata={
                        'note': 'MELBAC is free of charge — no payment required.',
                        'device': random.choice(['desktop', 'mobile', 'tablet']),
                    },
                    completed_at=timezone.now() - timedelta(days=random.randint(1, 90)),
                )

        # ── 32. INVOICES ─────────────────────────────────────────────────────
        self.stdout.write("🧾 Creating invoices...")
        completed_txns = list(Transaction.objects.filter(status='completed'))
        for txn in random.sample(completed_txns, k=min(30, len(completed_txns))):
            # ✅ FIX: safe date conversion — completed_at may be None
            completed_dt = txn.completed_at or timezone.now()
            Invoice.objects.create(
                student=txn.user,
                course=txn.course if txn.course else None,
                subtotal=Decimal('0.00'),
                tax_rate=Decimal('0.00'),
                discount_amount=Decimal('0.00'),
                currency='USD',
                status='paid',
                due_date=(completed_dt + timedelta(days=30)).date(),
                paid_date=completed_dt.date(),
                notes=(
                    f"MELBAC enrollment invoice for transaction {txn.transaction_id}. "
                    f"No charge — MELBAC provides all programs free of charge by the grace of God."
                ),
            )

        # ── 33. BADGES ───────────────────────────────────────────────────────
        self.stdout.write("🏅 Creating badges...")
        badge_raw = [
            ('First Teaching Completed', 'book-open', 'bronze', 10,
             'Complete your first MELBAC teaching course'),
            ('Faithful Student', 'star', 'gold', 25,
             'Complete 5 or more MELBAC courses'),
            ('Prayer Warrior', 'zap', 'purple', 20,
             'Complete the Intercessory Prayer & Deliverance series'),
            ('Doctrine Champion', 'award', 'gold', 30,
             'Score 90%+ on 5 consecutive quizzes'),
            ('Ministry Ready', 'flag', 'green', 35,
             'Complete all core programs in your faculty'),
            ('Faithful Scribe', 'file-text', 'blue', 15,
             'Submit 10 written reflection assignments'),
            ('Community Builder', 'users', 'cyan', 20,
             'Contribute helpful replies to 10 forum discussions'),
            ('Word Ambassador', 'globe', 'orange', 25,
             'Share MELBAC teaching content on social media 5 times'),
        ]
        badges = []
        for name, icon, color, points, criteria in badge_raw:
            badges.append(Badge.objects.create(
                name=name, icon=icon, color=color, points=points,
                criteria=criteria,
                description=f"Awarded to MELBAC students for: {criteria.lower()}",
                is_active=True,
            ))

        # ── 34. STUDENT BADGES ────────────────────────────────────────────────
        self.stdout.write("🎖️  Awarding badges...")
        for student in verified_students:
            for badge in random.sample(badges, k=random.randint(1, 4)):
                StudentBadge.objects.get_or_create(
                    student=student, badge=badge,
                    defaults=dict(
                        awarded_by=random.choice(users['admins'] + users['instructors']),
                        reason=(
                            "Awarded for faithful engagement with MELBAC teaching content "
                            "and consistent pursuit of God's Word."
                        ),
                    )
                )

        # ── 35. BLOG CATEGORIES ───────────────────────────────────────────────
        self.stdout.write("📰 Creating blog categories...")
        blog_cat_raw = [
            ('Biblical Doctrine & Teaching', 'book-open', 'purple'),
            ('Prayer & Intercession', 'zap', 'blue'),
            ('Christian Living', 'heart', 'green'),
            ('Ministry & Leadership', 'award', 'gold'),
            ('MELBAC News & Updates', 'newspaper', 'red'),
            ('Forgiveness & Repentance', 'refresh-cw', 'teal'),
        ]
        blog_categories = []
        for idx, (name, icon, color) in enumerate(blog_cat_raw):
            blog_categories.append(BlogCategory.objects.create(
                name=name, icon=icon, color=color,
                description=(
                    f"Teaching posts and articles from MELBAC in the area of {name.lower()}, "
                    f"grounded in the pure Word of God."
                ),
                display_order=idx, is_active=True,
            ))

        # ── 36. BLOG POSTS ────────────────────────────────────────────────────
        self.stdout.write("✍️  Creating blog posts (actual MELBAC teachings)...")
        post_category_assignments = [
            blog_categories[0],  # 61 Due Process
            blog_categories[5],  # 60 Forgiveness Conclusion
            blog_categories[5],  # 58 Blasphemy
            blog_categories[5],  # 57 Conditions for Forgiveness
            blog_categories[5],  # 56 Repentance Steps
            blog_categories[5],  # 55 Mystery of Forgiveness
            blog_categories[3],  # 54 Authority - Blessings
            blog_categories[3],  # 53 Authority - God Pleaser
            blog_categories[3],  # 52 Authority - Kingdom Part 3
            blog_categories[3],  # 51 Authority - Kingdom Part 2
        ]
        admin_author = users['admins'][0]
        for idx, post_data in enumerate(MELBAC_BLOG_POSTS):
            BlogPost.objects.create(
                title=post_data['title'],
                slug=post_data['slug'],           # ✅ explicit slug avoids auto-slug collisions
                subtitle=post_data['subtitle'],
                excerpt=post_data['excerpt'],
                content=post_data['content'],
                category=post_category_assignments[idx],
                tags=post_data['tags'],
                author=admin_author,
                author_name=post_data['author_name'],
                author_title=post_data['author_title'],
                author_bio=(
                    'Apostle John Daniel is the Founder and President of Melchisedec Graduate Bible Academy '
                    '(MELBAC) and Harmabitrac World Outreach. He is an anointed teacher of God\'s pure Word '
                    'and a visionary behind free theological education globally.'
                ),
                featured_image_alt=post_data['title'],
                read_time=post_data['read_time'],
                views_count=random.randint(100, 8000),
                status='published',
                is_featured=(idx < 3),
                publish_date=timezone.now() - timedelta(days=post_data['publish_days_ago']),
                meta_description=post_data['excerpt'][:155],
                meta_keywords=', '.join(post_data['tags'] + ['MELBAC', 'Apostle John Daniel', 'Bible teaching']),
            )
        self.stdout.write(self.style.SUCCESS(f"   ✅ {BlogPost.objects.count()} blog posts created"))

        # ── 37. DISCUSSIONS & REPLIES ─────────────────────────────────────────
        self.stdout.write("💬 Creating discussions...")
        discussion_topics = [
            'How has this teaching on the Authority of a Believer changed your prayer life?',
            'What scriptures have helped you the most in understanding forgiveness?',
            'How do you apply the concept of "Due Process" in your daily walk with God?',
            'What is the difference between genuine repentance and mere sorrow?',
            'How do you exercise spiritual authority in your local church context?',
            'What practical steps have you taken in developing your intercessory prayer life?',
            'How do you balance being a God-pleaser and relating graciously with other believers?',
            'Share a testimony of how God\'s Word has delivered you or someone you know.',
        ]
        discussions = []
        for lc in lms_courses:
            enrolled_users = list(User.objects.filter(enrollments__course=lc))
            for disc_idx in range(random.randint(2, 5)):
                if not enrolled_users:
                    break
                author = random.choice(enrolled_users)
                topic = discussion_topics[disc_idx % len(discussion_topics)]
                # ✅ FIX: unique_together is (course, slug). Build a unique slug per course.
                disc_slug = unique_slug(topic, Discussion, extra_filter={'course': lc})
                disc = Discussion.objects.create(
                    course=lc,
                    title=topic,
                    slug=disc_slug,
                    content=(
                        'Sharing my reflection on this week\'s teaching. I\'d love to hear how others '
                        'are applying this in their ministries. The Word of God is truly alive and '
                        'powerful — let\'s encourage one another. Scripture: Hebrews 10:24-25.'
                    ),
                    author=author,
                    is_pinned=random.random() > 0.85,
                    is_locked=False,
                    views_count=random.randint(10, 500),
                )
                discussions.append(disc)
                repliers = [u for u in enrolled_users if u != author]
                ministry_replies = [
                    'Thank you for sharing this. This teaching also impacted me deeply. '
                    'The scripture you referenced really opened my eyes.',
                    'I have been applying this in my church and I\'m seeing real results. '
                    'God\'s Word never returns void. Glory to God!',
                    'I struggled with this concept initially, but after praying about it '
                    'the Holy Spirit gave me clarity. Apostle John Daniel\'s teaching is a blessing.',
                    'This is exactly what I needed to hear today. I will be sharing this '
                    'with my prayer group. Thank you for the encouragement.',
                ]
                for _ in range(random.randint(1, 6)):
                    if repliers:
                        DiscussionReply.objects.create(
                            discussion=disc,
                            author=random.choice(repliers),
                            content=random.choice(ministry_replies),
                            is_solution=random.random() > 0.9,
                        )

        # ── 38. STUDY GROUPS & MESSAGES ──────────────────────────────────────
        self.stdout.write("👥 Creating study groups and messages...")
        study_groups = []
        study_group_names = [
            'Prayer Warriors — West Africa',
            'Theology Deep Dive Group',
            'Women in Ministry — MELBAC',
            'Forgiveness Series Study Circle',
            'Authority of the Believer Study Group',
            'UK & Europe Ministers Network',
            'Nigeria Pastors Fellowship — MELBAC',
            'New Believers Discipleship Circle',
        ]
        for idx, lc in enumerate(random.sample(lms_courses, k=min(6, len(lms_courses)))):
            creator = random.choice(verified_students + verified_instructors)
            sg = StudyGroup.objects.create(
                name=study_group_names[idx % len(study_group_names)],
                description=(
                    f"A study group for MELBAC students going through {lc.title}. "
                    f"We meet to pray together, discuss the teaching, and encourage one another in the Word."
                ),
                course=lc,
                max_members=random.randint(10, 30),
                is_active=True,
                is_public=random.choice([True, False]),
                created_by=creator,
            )
            study_groups.append(sg)
            StudyGroupMember.objects.create(
                study_group=sg, user=creator, role='admin', is_active=True,
            )
            enrolled_ids = list(
                Enrollment.objects.filter(course=lc).values_list('student', flat=True)
            )
            member_users = [creator]
            for sid in random.sample(enrolled_ids, k=min(sg.max_members - 1, len(enrolled_ids))):
                if sid != creator.id:
                    try:
                        member_user = User.objects.get(id=sid)
                        StudyGroupMember.objects.get_or_create(
                            study_group=sg, user=member_user,
                            defaults=dict(
                                role=random.choice(['member', 'member', 'moderator']),
                                is_active=True,
                            )
                        )
                        member_users.append(member_user)
                    except User.DoesNotExist:
                        pass
            group_messages = [
                'Praise God! I just finished today\'s lesson and I am on fire for the Lord.',
                'Has everyone finished the reflection assignment? Let\'s share our insights.',
                'I found a parallel passage in Acts 10 that perfectly supports today\'s teaching.',
                'Let us pray together at 6am tomorrow morning before the next lesson.',
                'Apostle John Daniel\'s teaching on this topic is so deep. I\'ve watched it three times already.',
                'Can someone explain the point about the "last command" principle? I need clarity.',
                'I shared this teaching with my pastor and he wants us to do a church-wide study on it.',
            ]
            for _ in range(random.randint(3, 10)):
                StudyGroupMessage.objects.create(
                    study_group=sg,
                    author=random.choice(member_users),
                    content=random.choice(group_messages),
                )

        # ── 39. MESSAGES ──────────────────────────────────────────────────────
        self.stdout.write("✉️  Creating messages...")
        message_subjects = [
            'Question about the Forgiveness series',
            'Request for prayer — family situation',
            'Application follow-up — MELBAC 2025 intake',
            'Clarification needed on the quiz question about authority',
            'Testimony — God healed my marriage through this teaching',
            'Can I get more information about the Doctoral program?',
            'Request for confirmation of enrollment',
            'Struggling with understanding blasphemy against the Holy Spirit',
        ]
        for user in verified_all:
            others = [u for u in all_users if u != user]
            for _ in range(random.randint(1, 4)):
                recipient = random.choice(others)
                is_read = random.choice([True, False])
                msg = Message.objects.create(
                    sender=user, recipient=recipient,
                    subject=random.choice(message_subjects),
                    body=(
                        'Greetings in the name of our Lord Jesus Christ. I hope this message finds you '
                        'well in the Lord. I am writing to enquire about the MELBAC program and teaching '
                        'content. Please let me know how I can be of assistance or how we can pray together.'
                    ),
                    is_read=is_read,
                    read_at=timezone.now() - timedelta(hours=random.randint(1, 72))
                    if is_read else None,
                )
                if random.random() > 0.6:
                    Message.objects.create(
                        sender=recipient, recipient=user,
                        subject=f"Re: {msg.subject}",
                        body=(
                            'Thank you for reaching out. I am glad you are engaged with the Word of God '
                            'through MELBAC. I will respond fully shortly. Continue to pray and study. '
                            'God bless you richly.'
                        ),
                        parent=msg,
                        is_read=random.choice([True, False]),
                    )

        # ── 40. SUPPORT TICKETS ───────────────────────────────────────────────
        self.stdout.write("🎫 Creating support tickets...")
        tickets = []
        ticket_subjects = [
            'Unable to access lesson video',
            'Request to change program from Bachelor\'s to Master\'s',
            'Login issue — cannot access my account',
            'Request for official enrollment confirmation letter',
            'Missing assignment submission — technical error',
            'Question about the ministerial attachment requirement',
            'Request for transcript from 2024/2025 session',
            'Unable to download course materials',
        ]
        ticket_creators = (
            verified_students +
            random.sample(verified_instructors, k=min(3, len(verified_instructors)))
        )
        for creator in ticket_creators:
            for _ in range(random.randint(1, 3)):
                status = random.choice(
                    ['open', 'in_progress', 'waiting_response', 'resolved', 'closed']
                )
                # ✅ FIX: 'resolution' field does NOT exist on SupportTicket model — removed
                ticket = SupportTicket.objects.create(
                    user=creator,
                    category=random.choice(['technical', 'account', 'course', 'payment', 'other']),
                    subject=random.choice(ticket_subjects),
                    description=(
                        'I am a MELBAC student and I am experiencing the following issue. '
                        'Please assist me at your earliest convenience so I can continue '
                        'my studies without interruption. Thank you and God bless you.'
                    ),
                    priority=random.choice(['low', 'normal', 'high', 'urgent']),
                    status=status,
                    assigned_to=random.choice(users['support']),
                    resolved_at=timezone.now() - timedelta(days=random.randint(1, 7))
                    if status in ['resolved', 'closed'] else None,
                )
                tickets.append(ticket)
                if random.random() > 0.5:
                    # ✅ FIX: content → message, is_staff_reply → is_internal_note
                    TicketReply.objects.create(
                        ticket=ticket,
                        author=random.choice(users['support']),
                        message=(
                            'Thank you for contacting MELBAC support. We have received your ticket '
                            'and are looking into the issue. We will respond within 24 hours. '
                            'May God continue to bless your study of His Word.'
                        ),
                        is_internal_note=False,
                    )

        # ── 41. NOTIFICATIONS ─────────────────────────────────────────────────
        self.stdout.write("🔔 Creating notifications...")
        notification_messages = [
            ('New Teaching Available', 'A new teaching post by Apostle John Daniel has been published on the blog.'),
            ('Assignment Due Reminder', 'Your reflection assignment is due in 3 days. Submit your response before the deadline.'),
            ('Quiz Graded', 'Your quiz has been graded. Log in to view your score and feedback.'),
            ('New Semester Starting', 'The 2025/2026 academic session begins soon. Check the academic calendar for key dates.'),
            ('Application Status Update', 'Your MELBAC application status has been updated. Log in to view the details.'),
            ('Study Group Message', 'A new message has been posted in your study group. Join the discussion.'),
            ('Certificate Issued', 'Congratulations! Your MELBAC certificate of completion has been issued.'),
            ('Upcoming Seminar', 'MELBAC Annual University Seminar is coming up. Details will be sent by email.'),
        ]
        for user in verified_all:
            for _ in range(random.randint(2, 8)):
                title, message = random.choice(notification_messages)
                Notification.objects.create(
                    user=user,
                    title=title,
                    message=message,
                    notification_type=random.choice(['info', 'success', 'warning', 'system']),
                    is_read=random.choice([True, False]),
                    read_at=timezone.now() - timedelta(hours=random.randint(1, 48))
                    if random.random() > 0.5 else None,
                )

        # ── 42. ANNOUNCEMENTS ─────────────────────────────────────────────────
        self.stdout.write("📢 Creating announcements...")
        announcement_data = [
            ('2025/2026 Academic Session — Registration Now Open',
             'Regular admission for the 2025/2026 academic session is now open. '
             'Applications are being accepted from August 25 to October 27, 2025. '
             'All programs are completely free of charge. Apply now through the admissions portal '
             'or contact us at inquiry@melbac.org.',
             'all', True),
            ('New Teaching Series — Due Process in Christendom',
             'Apostle John Daniel has begun a new teaching series titled "Due Process in Christendom." '
             'Part 1 is now available on the blog and MELBAC YouTube channel. This teaching reveals '
             'the divine protocol of God\'s Kingdom and why there are no shortcuts in the spiritual life.',
             'all', True),
            ('Convocation & Annual University Seminar — November 2025',
             'MELBAC\'s Annual University Seminar and Convocation will hold in November 2025 '
             'at the Lagos campus (Festac Town). All students, graduates, and ministry partners '
             'are invited. Details will be communicated via email and the MELBAC social media channels.',
             'all', True),
            ('Ministerial Attachment — August to November 2025',
             'All Diploma and Bachelor\'s Degree graduates from the 2024/2025 session are reminded '
             'that ministerial attachment runs from the 3rd week of August to the 2nd week of November. '
             'This is a mandatory component of your graduation requirement. Contact the registrar\'s '
             'office for placement details.',
             'student', True),
            ('Faculty Meeting — Academic Board',
             'The MELBAC Academic Board meeting will hold on the 2nd Saturday of October. '
             'All faculty members and academic board members are required to attend. '
             'Minutes from the previous meeting will be circulated prior to the meeting.',
             'staff', False),
        ]
        announcement_creators = users['admins'] + users['content_managers']
        for title, content, audience, is_pub in announcement_data:
            # ✅ FIX: target_audience/is_published/is_pinned don't exist
            # Model has: announcement_type, priority, is_active
            Announcement.objects.create(
                title=title,
                content=content,
                announcement_type='system',
                priority='high' if is_pub else 'normal',
                is_active=is_pub,
                created_by=random.choice(announcement_creators),
                publish_date=timezone.now() - timedelta(days=random.randint(1, 60)),
                expiry_date=timezone.now() + timedelta(days=random.randint(30, 180)),
            )

        # ── 43. CONTACT MESSAGES ──────────────────────────────────────────────
        self.stdout.write("📬 Creating contact messages...")
        # ✅ subject must match ContactMessage.SUBJECT_CHOICES keys exactly
        contact_subjects = ['admissions', 'programs', 'campus', 'financial', 'support', 'other']
        contact_names = [
            'Emmanuel Adeyemi', 'Grace Okonkwo', 'Samuel Ehichioya', 'Faith Williams',
            'Joshua Mensah', 'Patience Daniel', 'Blessing Nwosu', 'Elijah Okeke',
            'Ruth Uzoigwe', 'Deborah Azobu', 'Moses Phillips', 'Miriam Obiora',
        ]
        contact_messages_list = [
            'I am interested in enrolling in MELBAC and would like more information about the admission process.',
            'Good day. I am a pastor in Lagos and I want to know if MELBAC can accept mature believers without a secondary school certificate.',
            'I live in the United Kingdom and would like to know if I can study MELBAC programs online.',
            'My name is Pastor Emmanuel. I am interested in the Doctoral program in Theology. Please advise.',
            'I watched the teaching on YouTube and I am convinced God is calling me to study at MELBAC. How do I begin?',
            'Can you please send me information about the MELBAC annual seminar and how I can attend?',
            'I would like to visit the Lagos campus. What are your office hours and address?',
            'My church would like to partner with MELBAC as a satellite campus location. Please advise.',
        ]
        for i in range(12):
            responded = random.random() > 0.5
            ContactMessage.objects.create(
                name=contact_names[i % len(contact_names)],
                email=f"contact{i + 1}@example.com",
                # ✅ FIX: 'phone' field does not exist on ContactMessage — removed
                subject=random.choice(contact_subjects),
                message=random.choice(contact_messages_list),
                is_read=random.choice([True, False]),
                responded=responded,
                responded_at=timezone.now() - timedelta(days=random.randint(1, 14)) if responded else None,
                responded_by=random.choice(users['admins']) if responded else None,
            )

        # ── 44. AUDIT LOGS ────────────────────────────────────────────────────
        self.stdout.write("📋 Creating audit logs...")
        audit_actions = [
            ('login', 'User logged into the MELBAC platform.'),
            ('blog_post_published', 'New teaching post published on the blog.'),
            ('application_approved', 'Student application approved by admin.'),
            ('enrollment_created', 'Student enrolled in a MELBAC course.'),
            ('certificate_issued', 'Certificate of completion issued to student.'),
            ('announcement_published', 'New announcement published to all students.'),
        ]
        for user in random.sample(all_users, k=min(20, len(all_users))):
            for _ in range(random.randint(2, 6)):
                action, description = random.choice(audit_actions)
                AuditLog.objects.create(
                    user=user,
                    action=action,
                    description=description,
                    ip_address=fake.ipv4(),
                    user_agent=random.choice([
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                        'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0)',
                        'Mozilla/5.0 (Linux; Android 11)',
                    ]),
                    extra_data={'platform': 'MELBAC', 'session_id': uuid.uuid4().hex},
                )

        # ── 45. BROADCAST MESSAGES ────────────────────────────────────────────
        self.stdout.write("📡 Creating broadcast messages...")
        broadcast_data = [
            ('New Teaching Available — Due Process in Christendom',
             'Dear MELBAC family, Apostle John Daniel has released a powerful new teaching series. '
             'Part 1 — "Due Process in Christendom" is now available on the blog and YouTube. '
             'Do not miss this life-changing message. Shalom.',
             'email', 'all', 'sent'),
            ('2025/2026 Admission — Last Call',
             'Supplementary/Late Admission for 2025/2026 is now open until mid-January. '
             'Lectures for students admitted in this period begin in late January. '
             'Apply now at melbac.org or contact inquiry@melbac.org. All programs are FREE.',
             'email', 'all', 'sent'),
            ('MELBAC Annual Seminar — Save the Date',
             'The MELBAC Annual University Seminar and Convocation is scheduled for November. '
             'All students, graduates, and partners are encouraged to attend. '
             'Watch your email for full details and the programme of events.',
             'email', 'all', 'scheduled'),
            ('Reminder: Ministerial Attachment — Diploma & Bachelor Graduates',
             'This is a reminder to all 2024/2025 Diploma and Bachelor Degree graduates that '
             'ministerial attachment (3rd week August – 2nd week November) is mandatory. '
             'Please contact the registrar\'s office for your placement assignment.',
             'email', 'graduates', 'sent'),
        ]
        broadcast_creators = users['admins'] + users['content_managers']
        for title, content, btype, ftype, status in broadcast_data:
            fvals = ['all students', 'active'] if ftype == 'all' else [ftype]
            emails = [fake.email() for _ in range(random.randint(50, 500))]
            # ✅ FIX: title → subject, content → message, message_type doesn't exist
            BroadcastMessage.objects.create(
                subject=title,
                message=content,
                filter_type=ftype,
                filter_values=fvals,
                recipient_emails=emails,
                recipient_count=len(emails),
                status=status,
                created_by=random.choice(broadcast_creators),
                sent_at=timezone.now() - timedelta(days=random.randint(1, 30))
                if status == 'sent' else None,
                error_message='' if status != 'failed' else 'SMTP connection timeout',
            )

        # ── 46. STAFF PAYROLL ─────────────────────────────────────────────────
        self.stdout.write("💰 Creating staff payroll records (full 12-month history)...")
        finance_admin = users['finance'][0]
        approver = users['admins'][0]
        for staff in staff_users:
            for month in range(1, 13):
                base = Decimal(str(round(random.uniform(800, 3500), 2)))
                allowances = Decimal(str(round(random.uniform(50, 500), 2)))
                bonuses = Decimal(str(round(random.uniform(0, 300), 2)))
                tax = Decimal(str(round(float(base + allowances + bonuses) * 0.07, 2)))
                other_ded = Decimal(str(round(random.uniform(10, 100), 2)))
                pstatus = random.choice(['paid', 'paid', 'paid', 'pending', 'processing'])
                StaffPayroll.objects.get_or_create(
                    staff=staff,
                    month=month,
                    year=2025,
                    defaults=dict(
                        base_salary=base,
                        allowances=allowances,
                        bonuses=bonuses,
                        tax_deduction=tax,
                        other_deductions=other_ded,
                        payment_status=pstatus,
                        payment_method=random.choice(['bank_transfer', 'mobile_money', 'check']),
                        payment_date=date(2025, month, random.randint(25, 28))
                        if pstatus == 'paid' else None,
                        bank_name=random.choice([
                            'Zenith Bank', 'GTBank', 'First Bank', 'UBA', 'Access Bank',
                            'Fidelity Bank', 'Sterling Bank'
                        ]),
                        account_number=str(random.randint(1_000_000_000, 9_999_999_999)),
                        notes=(
                            f"Monthly payroll for "
                            f"{date(2025, month, 1).strftime('%B %Y')}. "
                            f"Processed by MELBAC finance team. All staff are valued servants of God."
                        ),
                        created_by=finance_admin,
                        approved_by=approver if pstatus == 'paid' else None,
                        approved_at=timezone.now() - timedelta(days=random.randint(1, 28))
                        if pstatus == 'paid' else None,
                    )
                )

        # ── 47. FEE PAYMENTS ─────────────────────────────────────────────────
        self.stdout.write("💵 Creating fee payments...")
        all_required_payments = list(AllRequiredPayments.objects.all())
        if all_required_payments and verified_students:
            for student in verified_students:
                # Give each student 1–3 fee payments
                sampled_fees = random.sample(
                    all_required_payments,
                    k=min(random.randint(1, 3), len(all_required_payments))
                )
                for fee in sampled_fees:
                    status = random.choice(['success', 'success', 'success', 'pending', 'failed'])
                    method = random.choice(['card', 'bank_transfer', 'paypal'])
                    FeePayment.objects.create(
                        fee=fee,
                        user=student,
                        amount=fee.amount,
                        currency='USD',
                        status=status,
                        payment_method=method,
                        gateway_payment_id=f"gw_{uuid.uuid4().hex[:24]}" if status == 'success' else '',
                        card_last4=str(random.randint(1000, 9999)) if method == 'card' else '',
                        card_brand=random.choice(['Visa', 'Mastercard', 'Verve']) if method == 'card' else '',
                        failure_reason='' if status != 'failed' else 'Insufficient funds',
                        paid_at=timezone.now() - timedelta(days=random.randint(1, 90))
                        if status == 'success' else None,
                    )
        self.stdout.write(self.style.SUCCESS(f"   ✅ {FeePayment.objects.count()} fee payments created"))

        # ── 48. LIBRARY ITEMS ─────────────────────────────────────────────────
        self.stdout.write("📚 Seeding digital library...")
 
        LIBRARY_SEED_DATA = [
            # ── BOOKS ─────────────────────────────────────────────────────────
            {
                'category': 'Books', 'subcategory': 'Melbac Books',
                'title': 'Christian Race To The End (Qualification For The Throne)',
                'author': 'Apostle Dr. John Daniel',
                'description': 'A compelling examination of what it means to run the Christian race faithfully to the end and qualify for the heavenly throne.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://melbac.org',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': True,
            },
            {
                'category': 'Books', 'subcategory': 'Melbac Books',
                'title': 'Covenant',
                'author': 'Apostle Dr. John Daniel',
                'description': 'An in-depth study of the covenants of God — from Eden to the New Covenant in Christ — and their implications for the believer today.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://melbac.org',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'Books', 'subcategory': 'Melbac Books',
                'title': 'Jesus Christ The Special Grace Of God To Humanity',
                'author': 'Apostle Dr. John Daniel',
                'description': 'Explores the unique grace that Jesus Christ represents to all humanity — a theological and devotional study.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://melbac.org',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'Books', 'subcategory': 'Melbac Books',
                'title': 'Endtime Spiritual Ways of Praying Prayers',
                'author': 'Apostle Dr. John Daniel',
                'description': 'A practical and prophetic guide to end-time prayer, equipping believers with spiritual strategies for intercession.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://melbac.org',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': True,
            },
            {
                'category': 'Books', 'subcategory': 'Melbac Books',
                'title': 'Submission: The Authority Channel of God',
                'author': 'Apostle Dr. John Daniel',
                'description': 'Unpacks the biblical doctrine of submission as the God-ordained channel through which divine authority flows in the home, church, and nation.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://melbac.org',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'Books', 'subcategory': 'Melbac Books',
                'title': 'Tabernacle As A Shadow of Christ',
                'author': 'Apostle Dr. John Daniel',
                'description': 'A detailed typological study of the Old Testament Tabernacle and how every element foreshadows the person and work of Jesus Christ.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://melbac.org',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'Books', 'subcategory': 'Apologetics Books',
                'title': 'Apologetics Study Collection',
                'author': '',
                'description': 'A curated collection of texts defending the Christian faith against philosophical and theological objections.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://melbac.org/library',
                'external_url_label': 'Browse Collection',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'Books', 'subcategory': 'Bible Studies Books',
                'title': 'Bible Studies Resource Library',
                'author': '',
                'description': 'Comprehensive Bible study materials covering both Old and New Testaments, suitable for individual and group use.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://melbac.org/library',
                'external_url_label': 'Browse Collection',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'Books', 'subcategory': 'Christian Counseling Books',
                'title': 'Counseling Recipes',
                'author': 'Timothy Tow',
                'description': 'Practical biblical counseling guidance drawn from Scripture, offering applicable principles for Christian counselors.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://melbac.org/library',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'Books', 'subcategory': 'Christian Counseling Books',
                'title': 'Biblical Counseling Manual',
                'author': 'Adam Pulanski',
                'description': 'A structured manual providing biblical frameworks and practical tools for Christian counselors in ministry settings.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://melbac.org/library',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'Books', 'subcategory': 'Christian Counseling Books',
                'title': 'Biblical Counseling Seminar',
                'author': 'Dr. Edward Watke Jr.',
                'description': 'Seminar notes and teaching material on the foundations and practice of biblical counseling.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://melbac.org/library',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'Books', 'subcategory': 'Theology Books',
                'title': 'Theology Reference Collection',
                'author': '',
                'description': 'A wide-ranging selection of theological texts covering systematic, biblical, and historical theology.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://melbac.org/library',
                'external_url_label': 'Browse Collection',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'Books', 'subcategory': 'Evangelism Books',
                'title': 'Evangelism Resource Library',
                'author': '',
                'description': 'Books and manuals equipping believers and ministers with practical evangelism strategies rooted in Scripture.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://melbac.org/library',
                'external_url_label': 'Browse Collection',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'Books', 'subcategory': 'Leadership Books',
                'title': 'Christian Leadership Library',
                'author': '',
                'description': 'Books on servant leadership, pastoral ministry, and kingdom leadership principles for Christian leaders.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://melbac.org/library',
                'external_url_label': 'Browse Collection',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
 
            # ── PERIODICALS ───────────────────────────────────────────────────
            {
                'category': 'Periodicals', 'subcategory': 'Acta Theologica',
                'title': 'Acta Theologica — Full Journal Archive',
                'author': '',
                'description': 'South African journal of theology covering biblical studies, church history, and systematic theology.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://journals.ufs.ac.za/index.php/at',
                'external_url_label': 'Visit Journal',
                'allow_download': False, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'Periodicals', 'subcategory': 'Tyndale Bulletin',
                'title': 'Tyndale Bulletin — Complete Archive',
                'author': '',
                'description': 'Peer-reviewed journal of biblical and theological research published by Tyndale House, Cambridge.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.tyndalehouse.com/tynbul/',
                'external_url_label': 'Visit Journal',
                'allow_download': False, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'Periodicals', 'subcategory': 'Westminster Theological Journal',
                'title': 'Westminster Theological Journal — Archive',
                'author': '',
                'description': 'Reformed theological journal published by Westminster Theological Seminary covering exegesis, theology, and church history.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.wts.edu/resources/westminster-theological-journal/',
                'external_url_label': 'Visit Journal',
                'allow_download': False, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'Periodicals', 'subcategory': 'Theology Today',
                'title': 'Theology Today — Journal Archive',
                'author': '',
                'description': 'Interdenominational journal of theology and culture published by Princeton Theological Seminary.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://journals.sagepub.com/home/ttj',
                'external_url_label': 'Visit Journal',
                'allow_download': False, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'Periodicals', 'subcategory': 'Old Testament Essays',
                'title': 'Old Testament Essays — Full Archive',
                'author': '',
                'description': 'Journal of the Old Testament Society of South Africa covering all aspects of OT scholarship.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://ojs.unisa.ac.za/index.php/OTE',
                'external_url_label': 'Visit Journal',
                'allow_download': False, 'allow_read_online': True, 'featured': False,
            },
 
            # ── REFERENCES: Commentaries ──────────────────────────────────────
            {
                'category': 'References', 'subcategory': 'Commentaries',
                'title': 'Commentary on the Whole Bible',
                'author': 'Matthew Henry',
                'description': 'The classic, complete verse-by-verse commentary on the entire Bible by the Puritan minister Matthew Henry.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.ccel.org/ccel/henry/mhc',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': True,
            },
            {
                'category': 'References', 'subcategory': 'Commentaries',
                'title': 'Commentary Critical and Explanatory on the Whole Bible',
                'author': 'Jamieson, Fausset & Brown',
                'description': 'A thorough critical and explanatory commentary on every book of the Bible, widely used in evangelical scholarship.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.ccel.org/ccel/jamieson/jfb',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': True,
            },
            {
                'category': 'References', 'subcategory': 'Commentaries',
                'title': 'Commentary on the New Testament from the Talmud and Hebraica',
                'author': 'John Lightfoot',
                'description': 'Lightfoot\'s pioneering work situating the New Testament in its Jewish context using Talmudic and Hebraic sources.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.ccel.org/ccel/lightfoot/talmud',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'References', 'subcategory': 'Commentaries',
                'title': "Coffman's Commentaries on the Bible",
                'author': 'James Burton Coffman',
                'description': 'A comprehensive set of evangelical commentaries on every book of the Bible, known for clarity and faithfulness to the text.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.studylight.org/commentaries/bcc/',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'References', 'subcategory': 'Commentaries',
                'title': 'Bible Commentary by David Guzik',
                'author': 'David Guzik',
                'description': 'Accessible, verse-by-verse commentary on the entire Bible combining solid exposition with pastoral application.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://enduringword.com/bible-commentary/',
                'external_url_label': 'Read Online',
                'allow_download': False, 'allow_read_online': True, 'featured': False,
            },
 
            # ── REFERENCES: Dictionaries ──────────────────────────────────────
            {
                'category': 'References', 'subcategory': 'Dictionaries',
                'title': "Smith's Bible Dictionary",
                'author': 'William Smith',
                'description': "One of the most widely used Bible dictionaries, covering persons, places, and subjects of the Bible with scholarly depth.",
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.ccel.org/ccel/smith_w/bibledict',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'References', 'subcategory': 'Dictionaries',
                'title': "Easton's Bible Dictionary",
                'author': 'George Easton',
                'description': 'A concise and reliable Bible dictionary covering the key terms, names, and concepts of both testaments.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.ccel.org/ccel/easton/ebd',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'References', 'subcategory': 'Dictionaries',
                'title': "Holman Bible Dictionary",
                'author': 'Trent C. Butler',
                'description': 'A comprehensive evangelical Bible dictionary with detailed articles on persons, places, theology, and archaeology.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.studylight.org/dictionaries/hbd/',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'References', 'subcategory': 'Dictionaries',
                'title': "Baker's Evangelical Dictionary of Biblical Theology",
                'author': 'Walter Elwell',
                'description': 'An authoritative reference covering the major theological themes and concepts of the Bible from an evangelical perspective.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.biblestudytools.com/dictionaries/bakers-evangelical-dictionary/',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
 
            # ── REFERENCES: Encyclopedias ─────────────────────────────────────
            {
                'category': 'References', 'subcategory': 'Encyclopedias',
                'title': 'International Standard Bible Encyclopedia',
                'author': 'James Orr',
                'description': 'A comprehensive multi-volume Bible encyclopedia covering biblical history, geography, theology, and archaeology.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.ccel.org/ccel/orr/isbe',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': True,
            },
            {
                'category': 'References', 'subcategory': 'Encyclopedias',
                'title': 'New Schaff-Herzog Encyclopedia of Religious Knowledge',
                'author': 'Samuel Macauley Jackson',
                'description': 'The definitive multi-volume encyclopedia of Christian and world religious knowledge, covering history, doctrine, and biography.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.ccel.org/ccel/schaff/encyc',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
 
            # ── REFERENCES: Concordances ──────────────────────────────────────
            {
                'category': 'References', 'subcategory': 'Concordances',
                'title': "Strong's Exhaustive Concordance",
                'author': 'James Strong',
                'description': 'The most widely used biblical concordance, providing every word in the KJV Bible with Hebrew and Greek lexicon numbers.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.blueletterbible.org/lexicon/h1/kjv/wlc/0-1/',
                'external_url_label': 'Read Online',
                'allow_download': False, 'allow_read_online': True, 'featured': True,
            },
 
            # ── REFERENCES: Creeds ────────────────────────────────────────────
            {
                'category': 'References', 'subcategory': 'Creeds',
                'title': 'Creeds of Christendom, with History and Critical Notes — Vol. 1',
                'author': 'Philip Schaff',
                'description': 'A scholarly collection and critical study of the historic creeds of the Christian church, tracing their development and theological significance.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.ccel.org/ccel/schaff/creeds1',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
 
            # ── REFERENCES: History ───────────────────────────────────────────
            {
                'category': 'References', 'subcategory': 'History',
                'title': 'History of the Christian Church (8 Volumes)',
                'author': 'Philip Schaff',
                'description': "Schaff's monumental eight-volume history of the Christian Church from the apostolic era through the Reformation.",
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.ccel.org/ccel/schaff/hcc1',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'References', 'subcategory': 'History',
                'title': 'The History of Protestantism',
                'author': 'J.A. Wylie',
                'description': "A sweeping narrative history of the Protestant Reformation and its spread across Europe, tracing God's hand in church history.",
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.ccel.org/ccel/wylie/protestantism',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
 
            # ── REFERENCES: Theology References ───────────────────────────────
            {
                'category': 'References', 'subcategory': 'Theology References',
                'title': 'Institutes of the Christian Religion',
                'author': 'John Calvin',
                'description': "Calvin's foundational systematic theology — the definitive statement of Reformed doctrine, covering God, man, Christ, and the church.",
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.ccel.org/ccel/calvin/institutes',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': True,
            },
            {
                'category': 'References', 'subcategory': 'Theology References',
                'title': 'Manual of Theology',
                'author': 'J.L. Dagg',
                'description': 'A systematic theology written from a Baptist perspective, covering doctrine in a clear and devotional manner.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.ccel.org/ccel/dagg/theology',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
 
            # ── REFERENCES: Notes on the Bible ────────────────────────────────
            {
                'category': 'References', 'subcategory': 'Notes on the Bible',
                'title': "Wesley's Notes on the New Testament",
                'author': 'John Wesley',
                'description': "John Wesley's devotional and expository notes on the New Testament, widely used in Methodist and evangelical traditions.",
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.ccel.org/ccel/wesley/notes',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'References', 'subcategory': 'Notes on the Bible',
                'title': 'Barnes Notes on the New Testament',
                'author': 'Albert Barnes',
                'description': "Albert Barnes's thorough and practical notes on the New Testament, combining scholarly insight with pastoral application.",
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.ccel.org/ccel/barnes/notes',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
            {
                'category': 'References', 'subcategory': 'Notes on the Bible',
                'title': 'Scofield Reference Notes',
                'author': 'C.I. Scofield',
                'description': 'The influential Scofield Reference Bible notes, providing dispensational commentary and cross-references throughout Scripture.',
                'language': 'en', 'access': 'public',
                'external_url': 'https://www.ccel.org/ccel/scofield/notes',
                'external_url_label': 'Read Online',
                'allow_download': True, 'allow_read_online': True, 'featured': False,
            },
        ]
 
        library_admin = users['admins'][0]
        for order_idx, item_data in enumerate(LIBRARY_SEED_DATA):
            LibraryItem.objects.get_or_create(
                title=item_data['title'],
                category=item_data['category'],
                subcategory=item_data['subcategory'],
                defaults={
                    'author':               item_data.get('author', ''),
                    'description':          item_data.get('description', ''),
                    'language':             item_data.get('language', 'en'),
                    'access':               item_data.get('access', 'public'),
                    'external_url':         item_data.get('external_url', ''),
                    'external_url_label':   item_data.get('external_url_label', 'Read / Download'),
                    'allow_download':       item_data.get('allow_download', True),
                    'allow_read_online':    item_data.get('allow_read_online', True),
                    'featured':             item_data.get('featured', False),
                    'is_active':            True,
                    'order':                order_idx,
                    'created_by':           library_admin,
                },
            )
        self.stdout.write(self.style.SUCCESS(f"   ✅ {LibraryItem.objects.count()} library items seeded"))

        # ── FINAL: UPDATE COURSE STATISTICS ──────────────────────────────────
        self.stdout.write("📊 Updating course statistics...")
        for lc in lms_courses:
            lc.update_statistics()

        # ── SUMMARY ───────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write(self.style.SUCCESS(
            "✅  MELBAC SEEDING COMPLETE — every table, every field populated"
        ))
        self.stdout.write(self.style.SUCCESS("=" * 70))
        rows = [
            ("SiteConfig",              SiteConfig.objects.count()),
            ("History Milestones",      SiteHistoryMilestone.objects.count()),
            ("Testimonials",            Testimonial.objects.count()),
            ("Institution Members",     InstitutionMember.objects.count()),
            ("Countries",               ListOfCountry.objects.count()),
            ("Users",                   User.objects.count()),
            ("Vendors",                 Vendor.objects.count()),
            ("System Configurations",   SystemConfiguration.objects.count()),
            ("Payment Gateways",        PaymentGateway.objects.count()),
            ("Subscription Plans",      SubscriptionPlan.objects.count()),
            ("Subscriptions",           Subscription.objects.count()),
            ("Faculties",               Faculty.objects.count()),
            ("Departments",             Department.objects.count()),
            ("Programs",                Program.objects.count()),
            ("Academic Sessions",       AcademicSession.objects.count()),
            ("Academic Courses",        Course.objects.count()),
            ("Course Intakes",          CourseIntake.objects.count()),
            ("Required Payments",       AllRequiredPayments.objects.count()),
            ("Applications",            CourseApplication.objects.count()),
            ("Application Documents",   ApplicationDocument.objects.count()),
            ("Application Payments",    ApplicationPayment.objects.count()),
            ("LMS Course Categories",   CourseCategory.objects.count()),
            ("LMS Courses",             LMSCourse.objects.count()),
            ("Lesson Sections",         LessonSection.objects.count()),
            ("Lessons",                 Lesson.objects.count()),
            ("Enrollments",             Enrollment.objects.count()),
            ("Lesson Progress",         LessonProgress.objects.count()),
            ("Assignments",             Assignment.objects.count()),
            ("Submissions",             AssignmentSubmission.objects.count()),
            ("Quizzes",                 Quiz.objects.count()),
            ("Quiz Questions",          QuizQuestion.objects.count()),
            ("Quiz Attempts",           QuizAttempt.objects.count()),
            ("Reviews",                 Review.objects.count()),
            ("Certificates",            Certificate.objects.count()),
            ("Transactions",            Transaction.objects.count()),
            ("Invoices",                Invoice.objects.count()),
            ("Badges",                  Badge.objects.count()),
            ("Student Badges",          StudentBadge.objects.count()),
            ("Blog Categories",         BlogCategory.objects.count()),
            ("Blog Posts",              BlogPost.objects.count()),
            ("Discussions",             Discussion.objects.count()),
            ("Discussion Replies",      DiscussionReply.objects.count()),
            ("Study Groups",            StudyGroup.objects.count()),
            ("Study Group Members",     StudyGroupMember.objects.count()),
            ("Study Group Messages",    StudyGroupMessage.objects.count()),
            ("Messages",                Message.objects.count()),
            ("Support Tickets",         SupportTicket.objects.count()),
            ("Ticket Replies",          TicketReply.objects.count()),
            ("Notifications",           Notification.objects.count()),
            ("Announcements",           Announcement.objects.count()),
            ("Contact Messages",        ContactMessage.objects.count()),
            ("Audit Logs",              AuditLog.objects.count()),
            ("Broadcast Messages",      BroadcastMessage.objects.count()),
            ("Staff Payrolls",          StaffPayroll.objects.count()),
            ("Fee Payments",            FeePayment.objects.count()),
            ("Library Items",           LibraryItem.objects.count()),
        ]
        for label, count in rows:
            self.stdout.write(f"   {label:<36} {count}")
        self.stdout.write(self.style.SUCCESS("=" * 70 + "\n"))