import random


# These features are realistic and commonly lead to the VulX vulnerability classes naturally.
VULX_FEATURE_GUIDE = """Include realistic features that map to common security categories naturally:
- Access control: workspaces, teams, shared resources, role-based dashboards, invite flows
- Auth: email/password login, signup, password reset, OAuth (Google/GitHub), session management, MFA placeholders
- Data store rules: PostgreSQL database, Prisma ORM, search filters, raw SQL reporting, caching layer
- Data exposure: public profiles, public share links, data exports, activity feeds, API endpoints
- SQLi: search bars, filter queries, admin reporting, dynamic sorting
- XSS: user-generated content (posts, comments, bios), rich text, notification messages, email templates
- Command injection: PDF/image generation, file conversion, calling external CLI tools
- Path traversal: file upload, file download, bulk import/export, attachment serving
- SSRF: webhooks, URL import/fetch, integrations with external services
- XXE: XML import/export, SVG uploads, data migration tools
- SSTI: dynamic email templates, rendered HTML snippets, configurable themes
- Misconfig: debug/error pages, verbose logging, default admin account, open CORS for local dev
- Secrets: API keys, webhook secrets, OAuth credentials, encryption key placeholders
- Dependencies: a rich set of npm packages (auth, ORM, UI, upload, email, payments, real-time)

Do not intentionally introduce vulnerabilities. Just build the app as a real team would."""


def _base_prompt(domain: str, pages: list[str], schema: list[str], features: list[str]) -> str:
    """Build a consistent VulX-aware Next.js prompt for a domain."""
    pages_str = ", ".join(pages)
    schema_str = ", ".join(schema)
    features_str = "\n".join(f"- {f}" for f in features)
    return f"""Create a maximally complex, realistic, production-like Next.js 14 App Router application written in TypeScript that a real {domain} team would build. It should be a single monorepo-style project or a single app with clear module separation.

Requirements:
- Use Next.js 14 with App Router, TypeScript, Tailwind CSS, and shadcn/ui-style components.
- Implement at least 20 pages: {pages_str}.
- Use PostgreSQL + Prisma ORM with the following tables: {schema_str}.
- Implement authentication and authorization: email/password, Google OAuth, GitHub OAuth, session management, password reset, role-based access, and protected routes.
- Implement real features:
{features_str}
- Include both Server Actions and API route handlers (REST or tRPC) for CRUD operations.
- Include a `.env.example` with all necessary placeholders.
- Include `docker-compose.yml` for local PostgreSQL and Redis.
- Include GitHub Actions CI/CD for lint, test, build.
- Include `vercel.json`, comprehensive seed data, and a `README.md`.

{VULX_FEATURE_GUIDE}

Return the complete file tree using the format:

## File: path/to/file
```language
content
```
"""


PROJECT_PROMPTS = [
    {
        "name": "Enterprise SaaS platform",
        "prompt": _base_prompt(
            "enterprise SaaS",
            [
                "landing", "pricing", "docs", "login", "signup", "OAuth callback", "password reset", "MFA setup",
                "onboarding", "dashboard", "team switcher", "workspace settings", "members/invitations", "billing/subscriptions",
                "admin super-dashboard", "user profile", "API keys", "webhooks", "audit logs", "analytics/reports",
                "integrations marketplace", "feature flags", "public status page", "public shareable report page"
            ],
            [
                "workspaces", "users", "roles", "permissions", "audit logs", "subscriptions", "api_keys", "webhooks",
                "integrations", "feature_flags", "invitations"
            ],
            [
                "create workspaces and invite members with role assignments",
                "Stripe subscription billing (mocked)",
                "generate API keys and configure webhooks",
                "view audit logs and analytics dashboards",
                "toggle feature flags and manage integrations",
                "export reports and import data via CSV/XML",
                "public share links and status pages"
            ],
        ),
    },
    {
        "name": "Social media platform",
        "prompt": _base_prompt(
            "social media startup",
            [
                "home feed", "explore", "search", "login", "signup", "onboarding", "create post", "post detail",
                "comments", "nested replies", "likes", "bookmarks", "user profile", "followers/following", "direct messages",
                "group chat", "notifications", "settings", "analytics", "moderation queue", "admin dashboard", "public embed page"
            ],
            [
                "users", "posts", "comments", "likes", "bookmarks", "follows", "conversations", "messages",
                "notifications", "reports", "media"
            ],
            [
                "posts with text, images, and video URLs",
                "comments, likes, bookmarks, and follow/unfollow",
                "direct messages and group conversations via WebSocket/SSE",
                "push notifications and content reporting",
                "admin moderation and data export",
                "embeddable posts and public activity feeds"
            ],
        ),
    },
    {
        "name": "E-commerce marketplace",
        "prompt": _base_prompt(
            "marketplace startup",
            [
                "home", "category catalog", "product search", "product detail", "cart", "checkout", "order confirmation",
                "order history", "login", "signup", "seller onboarding", "seller dashboard", "add/edit product", "seller inventory",
                "seller orders", "seller analytics", "disputes", "messaging", "admin dashboard", "admin users", "admin products", "user profile"
            ],
            [
                "users", "products", "categories", "orders", "order_items", "cart", "reviews", "sellers", "payouts", "disputes"
            ],
            [
                "product listings with variants and search/filter",
                "cart and checkout flow with mocked payment",
                "order tracking and seller inventory management",
                "seller analytics and review system",
                "disputes, refunds, and CSV import/export",
                "admin moderation and messaging between buyers and sellers"
            ],
        ),
    },
    {
        "name": "Project management suite",
        "prompt": _base_prompt(
            "project management SaaS",
            [
                "landing", "login", "signup", "onboarding", "workspace switcher", "project list", "project overview", "Kanban board",
                "Gantt chart", "task detail", "task create/edit", "calendar", "time tracking", "team members", "invitations",
                "automation rules", "templates", "reports", "notifications", "user profile", "workspace settings", "billing", "admin panel"
            ],
            [
                "workspaces", "projects", "tasks", "labels", "statuses", "assignees", "time_entries", "automations", "templates", "audit_logs"
            ],
            [
                "Kanban boards with drag-and-drop and task assignments",
                "due dates, labels, and time tracking",
                "recurring tasks and automation rules",
                "project templates and CSV import/export",
                "reporting dashboards and webhooks",
                "workspace-level roles and billing"
            ],
        ),
    },
    {
        "name": "Learning management system",
        "prompt": _base_prompt(
            "ed-tech",
            [
                "landing", "login", "signup", "student dashboard", "instructor dashboard", "admin dashboard", "course catalog",
                "course detail", "lesson page", "video player", "quiz", "assignment submission", "gradebook", "progress page",
                "grades", "discussion forum", "direct messages", "calendar", "certificates", "notifications", "billing", "user profile"
            ],
            [
                "users", "courses", "lessons", "enrollments", "quizzes", "questions", "submissions", "grades", "assignments", "discussions", "certificates", "payments"
            ],
            [
                "course creation by instructors with video lessons",
                "quizzes with multiple question types",
                "assignments with file uploads and gradebook",
                "progress tracking and certificates",
                "discussion forums and notifications",
                "admin course/user management and CSV import/export"
            ],
        ),
    },
    {
        "name": "Healthcare patient portal",
        "prompt": _base_prompt(
            "healthcare",
            [
                "landing", "login", "signup", "patient dashboard", "provider dashboard", "admin dashboard", "appointments",
                "appointment booking", "medical records", "prescriptions", "lab results", "messages", "billing", "insurance",
                "care plan", "telehealth", "forms", "consents", "audit logs", "profile", "notifications", "reporting", "public provider directory"
            ],
            [
                "patients", "providers", "appointments", "medical_records", "prescriptions", "lab_results", "messages", "billing", "insurance", "consents"
            ],
            [
                "patient and provider dashboards with role-based access",
                "appointment booking and reminders",
                "medical records, prescriptions, and lab results",
                "secure messaging and telehealth placeholders",
                "billing, insurance claims, and consent forms",
                "audit logs and CSV export for admin"
            ],
        ),
    },
    {
        "name": "Financial dashboard",
        "prompt": _base_prompt(
            "fintech",
            [
                "landing", "login", "signup", "dashboard", "accounts", "transactions", "transfers", "budgets", "goals", "investments",
                "reports", "cards", "statements", "taxes", "api keys", "webhooks", "compliance", "audit logs", "admin panel", "user profile", "notifications"
            ],
            [
                "users", "accounts", "transactions", "categories", "budgets", "goals", "investments", "cards", "statements", "api_keys", "webhooks"
            ],
            [
                "multi-account dashboard and transaction history",
                "bank transfer and payment simulation",
                "budgets, goals, and investment tracking",
                "card management and statement generation",
                "webhooks and API keys for integrations",
                "compliance reports and admin audit logs"
            ],
        ),
    },
    {
        "name": "Real estate listing platform",
        "prompt": _base_prompt(
            "real estate",
            [
                "landing", "search", "map view", "listing detail", "login", "signup", "agent dashboard", "add/edit listing",
                "saved searches", "favorites", "mortgage calculator", "contact agent", "tour scheduling", "documents", "leads", "analytics",
                "admin dashboard", "reviews", "blog", "user profile"
            ],
            [
                "users", "listings", "agents", "saved_searches", "favorites", "tours", "leads", "documents", "reviews", "messages"
            ],
            [
                "property search with map view and filters",
                "listing detail pages with images and documents",
                "mortgage calculator and contact agent forms",
                "tour scheduling and lead management",
                "agent dashboard and analytics",
                "admin moderation and CSV import/export"
            ],
        ),
    },
    {
        "name": "Job board and recruitment platform",
        "prompt": _base_prompt(
            "recruitment",
            [
                "landing", "job search", "job detail", "company profile", "login", "signup", "candidate dashboard", "resume builder",
                "applications", "recruiter dashboard", "post job", "manage jobs", "applicant tracking", "interviews", "messages", "referrals",
                "admin dashboard", "billing", "user profile", "analytics"
            ],
            [
                "users", "companies", "jobs", "applications", "resumes", "interviews", "messages", "referrals", "subscriptions", "saved_jobs"
            ],
            [
                "job search with filters and saved jobs",
                "resume builder and applications",
                "recruiter dashboard with applicant tracking",
                "interview scheduling and messaging",
                "referrals and subscription billing",
                "admin reporting and CSV export"
            ],
        ),
    },
    {
        "name": "Content management system",
        "prompt": _base_prompt(
            "CMS startup",
            [
                "landing", "login", "signup", "editor dashboard", "content list", "create page", "edit page", "media library", "categories",
                "tags", "seo settings", "users", "roles", "themes", "menus", "forms", "analytics", "comments", "settings", "public site", "admin panel"
            ],
            [
                "users", "pages", "posts", "categories", "tags", "media", "themes", "menus", "forms", "comments", "roles"
            ],
            [
                "rich text editor and media library",
                "pages, posts, categories, and tags",
                "SEO settings and theme customization",
                "menus and form builder",
                "user roles and public content site",
                "analytics, comments, and CSV import/export"
            ],
        ),
    },
    {
        "name": "Customer support helpdesk",
        "prompt": _base_prompt(
            "customer support SaaS",
            [
                "landing", "login", "signup", "customer dashboard", "create ticket", "ticket detail", "knowledge base", "agent dashboard",
                "queue", "assigned tickets", "team chat", "macros", "automations", "sla", "tags", "customers", "organizations", "reports", "admin panel", "user profile"
            ],
            [
                "users", "tickets", "comments", "tags", "macros", "automations", "organizations", "sla", "knowledge_base", "attachments"
            ],
            [
                "ticket creation and threaded comments",
                "agent queues and assignment",
                "macros and automation rules",
                "knowledge base with article editor",
                "SLA tracking and customer organizations",
                "reporting and CSV export"
            ],
        ),
    },
    {
        "name": "Analytics and BI dashboard",
        "prompt": _base_prompt(
            "analytics",
            [
                "landing", "login", "signup", "dashboard", "data sources", "datasets", "query builder", "charts", "dashboards", "reports",
                "share", "embed", "alerts", "users", "teams", "billing", "api keys", "webhooks", "integrations", "admin panel", "public gallery"
            ],
            [
                "users", "teams", "data_sources", "datasets", "queries", "charts", "dashboards", "reports", "alerts", "api_keys", "webhooks"
            ],
            [
                "connect data sources and upload datasets",
                "query builder and SQL reporting",
                "charts and shareable dashboards",
                "report generation and scheduled alerts",
                "public embeds and API keys",
                "team workspaces and billing"
            ],
        ),
    },
    {
        "name": "HR management system",
        "prompt": _base_prompt(
            "HR tech",
            [
                "landing", "login", "signup", "employee dashboard", "manager dashboard", "HR dashboard", "directory", "profile", "time off",
                "leave requests", "calendar", "payroll", "benefits", "performance reviews", "goals", "recruiting", "onboarding", "documents",
                "reports", "org chart", "settings", "admin panel"
            ],
            [
                "users", "employees", "departments", "roles", "leave_requests", "payroll", "benefits", "reviews", "goals", "documents", "recruiting"
            ],
            [
                "employee directory and org chart",
                "time off requests and approvals",
                "payroll and benefits management",
                "performance reviews and goals",
                "recruiting pipeline and onboarding",
                "document upload and HR reporting"
            ],
        ),
    },
    {
        "name": "Inventory and warehouse management",
        "prompt": _base_prompt(
            "logistics",
            [
                "landing", "login", "signup", "dashboard", "products", "warehouses", "stock", "purchase orders", "receiving", "picking",
                "shipping", "returns", "suppliers", "locations", "barcode scanner", "audit", "reports", "integrations", "admin panel", "user profile"
            ],
            [
                "users", "products", "warehouses", "locations", "stock", "purchase_orders", "receiving", "shipments", "suppliers", "returns"
            ],
            [
                "product catalog and warehouse management",
                "stock levels and purchase orders",
                "receiving, picking, and shipping workflows",
                "returns and supplier management",
                "barcode scanner placeholder and audit logs",
                "CSV import/export and reporting"
            ],
        ),
    },
    {
        "name": "Booking and reservation system",
        "prompt": _base_prompt(
            "booking service",
            [
                "landing", "search", "listing detail", "booking flow", "login", "signup", "host dashboard", "add listing", "calendar",
                "reservations", "guest dashboard", "messages", "reviews", "payments", "availability", "amenities", "admin panel", "reports", "user profile"
            ],
            [
                "users", "listings", "bookings", "reservations", "availability", "reviews", "payments", "messages", "amenities"
            ],
            [
                "search with filters and availability calendar",
                "booking flow and reservation management",
                "host and guest dashboards",
                "messaging and reviews",
                "payment simulation and payout management",
                "admin moderation and CSV export"
            ],
        ),
    },
    {
        "name": "Travel and flight booking platform",
        "prompt": _base_prompt(
            "travel tech",
            [
                "landing", "flight search", "results", "booking", "passengers", "trips", "login", "signup", "profile", "checkout", "orders",
                "check-in", "notifications", "loyalty", "deals", "explore destinations", "reviews", "support", "admin dashboard", "analytics"
            ],
            [
                "users", "flights", "airports", "bookings", "passengers", "trips", "orders", "payments", "loyalty", "reviews"
            ],
            [
                "flight search and results filtering",
                "booking flow with passenger details",
                "trip management and check-in placeholder",
                "loyalty points and deals",
                "notifications and support tickets",
                "admin reporting and CSV export"
            ],
        ),
    },
    {
        "name": "Food delivery marketplace",
        "prompt": _base_prompt(
            "food delivery",
            [
                "landing", "restaurant search", "restaurant page", "menu", "cart", "checkout", "order tracking", "login", "signup",
                "customer orders", "restaurant dashboard", "menu editor", "orders management", "driver dashboard", "driver assignments",
                "reviews", "promotions", "admin dashboard", "user profile", "notifications"
            ],
            [
                "users", "restaurants", "menus", "menu_items", "orders", "order_items", "drivers", "deliveries", "reviews", "promotions"
            ],
            [
                "restaurant search and menu browsing",
                "cart and checkout with mocked payment",
                "real-time order tracking and driver assignment",
                "restaurant and driver dashboards",
                "reviews and promotions",
                "admin moderation and reporting"
            ],
        ),
    },
    {
        "name": "Ride-sharing and logistics platform",
        "prompt": _base_prompt(
            "mobility",
            [
                "landing", "login", "signup", "rider dashboard", "request ride", "trip tracking", "driver dashboard", "driver onboarding",
                "earnings", "fleet management", "dispatch", "payments", "promotions", "support", "trip history", "admin dashboard", "reports", "user profile", "notifications"
            ],
            [
                "users", "drivers", "vehicles", "trips", "requests", "payments", "promotions", "reviews", "documents", "fleets"
            ],
            [
                "ride request and matching",
                "trip tracking and payments",
                "driver onboarding and earnings dashboard",
                "fleet management and dispatch",
                "promotions and support tickets",
                "admin reporting and CSV export"
            ],
        ),
    },
    {
        "name": "Subscription box membership platform",
        "prompt": _base_prompt(
            "subscription commerce",
            [
                "landing", "box catalog", "subscription plans", "quiz", "checkout", "login", "signup", "member dashboard", "subscription management",
                "shipping schedule", "order history", "skip/swap", "referrals", "reviews", "admin dashboard", "inventory", "box builder", "analytics", "user profile"
            ],
            [
                "users", "boxes", "plans", "subscriptions", "orders", "shipments", "items", "inventory", "referrals", "reviews"
            ],
            [
                "box catalog and subscription plans",
                "preference quiz and checkout flow",
                "subscription management and skip/swap",
                "shipping schedule and order history",
                "referrals and reviews",
                "admin box builder and inventory management"
            ],
        ),
    },
    {
        "name": "Crowdfunding platform",
        "prompt": _base_prompt(
            "crowdfunding",
            [
                "landing", "project discovery", "project detail", "rewards", "checkout", "login", "signup", "creator dashboard",
                "create project", "backer dashboard", "pledges", "updates", "comments", "messages", "payments", "fulfillment", "admin dashboard",
                "analytics", "user profile"
            ],
            [
                "users", "projects", "rewards", "pledges", "payments", "updates", "comments", "messages", "fulfillment", "categories"
            ],
            [
                "project discovery and detail pages",
                "reward tiers and pledge flow",
                "creator dashboard and project updates",
                "backer dashboard and pledge management",
                "comments, messages, and fulfillment tracking",
                "admin moderation and reporting"
            ],
        ),
    },
    {
        "name": "Forum and community platform",
        "prompt": _base_prompt(
            "community forum",
            [
                "landing", "category list", "topic list", "topic detail", "create topic", "reply", "login", "signup", "user profile", "reputation",
                "badges", "notifications", "messages", "moderation queue", "reports", "admin dashboard", "settings", "search", "wiki", "events"
            ],
            [
                "users", "categories", "topics", "posts", "replies", "reputations", "badges", "messages", "reports", "wiki_pages"
            ],
            [
                "categories, topics, and threaded replies",
                "reputation, badges, and voting",
                "notifications and direct messages",
                "moderation queue and reporting",
                "wiki pages and events",
                "admin dashboard and CSV export"
            ],
        ),
    },
    {
        "name": "URL shortener and link management",
        "prompt": _base_prompt(
            "link management SaaS",
            [
                "landing", "login", "signup", "dashboard", "create link", "link list", "link detail", "analytics", "qr codes", "bulk import",
                "campaigns", "tags", "domains", "settings", "api keys", "webhooks", "teams", "billing", "admin panel", "public redirect"
            ],
            [
                "users", "teams", "links", "clicks", "campaigns", "tags", "domains", "api_keys", "webhooks", "subscriptions"
            ],
            [
                "short link creation and public redirect",
                "click analytics and QR code generation",
                "bulk import via CSV",
                "campaigns, tags, and custom domains",
                "API keys and webhooks",
                "team workspaces and billing"
            ],
        ),
    },
    {
        "name": "Email marketing platform",
        "prompt": _base_prompt(
            "email marketing",
            [
                "landing", "login", "signup", "dashboard", "campaigns", "create campaign", "template editor", "audiences", "segments", "subscribers",
                "forms", "automation", "analytics", "reports", "deliverability", "api keys", "webhooks", "team", "billing", "admin panel", "user profile"
            ],
            [
                "users", "teams", "campaigns", "templates", "audiences", "segments", "subscribers", "automations", "forms", "api_keys", "webhooks"
            ],
            [
                "campaign creation and template editor",
                "audiences, segments, and subscriber management",
                "signup forms and automation flows",
                "campaign analytics and deliverability",
                "API keys and webhooks",
                "team workspaces and billing"
            ],
        ),
    },
    {
        "name": "AI chatbot assistant platform",
        "prompt": _base_prompt(
            "AI assistant",
            [
                "landing", "login", "signup", "chat", "conversation history", "bots", "knowledge base", "sources", "training", "integrations",
                "widget settings", "analytics", "users", "teams", "billing", "api keys", "webhooks", "admin panel", "public demo", "user profile"
            ],
            [
                "users", "teams", "bots", "conversations", "messages", "knowledge_sources", "documents", "api_keys", "webhooks", "integrations"
            ],
            [
                "chat interface and conversation history",
                "bot creation and knowledge base uploads",
                "website scraping and document ingestion",
                "embeddable widget and integrations",
                "analytics and API keys",
                "team workspaces and billing"
            ],
        ),
    },
    {
        "name": "Document collaboration workspace",
        "prompt": _base_prompt(
            "document collaboration",
            [
                "landing", "login", "signup", "workspace", "documents", "create document", "editor", "comments", "templates", "folders",
                "share", "permissions", "versions", "history", "export", "search", "team", "billing", "api keys", "admin panel", "user profile"
            ],
            [
                "users", "teams", "documents", "folders", "comments", "versions", "permissions", "templates", "shares", "api_keys"
            ],
            [
                "rich text editor and document collaboration",
                "folders, templates, and version history",
                "comments and permissions",
                "share links and exports (PDF, DOCX)",
                "search and API keys",
                "team workspaces and billing"
            ],
        ),
    },
    {
        "name": "Code repository and developer tools platform",
        "prompt": _base_prompt(
            "developer tools",
            [
                "landing", "login", "signup", "repositories", "repo detail", "file browser", "code editor", "commits", "branches", "pull requests",
                "issues", "actions", "secrets", "settings", "members", "wiki", "releases", "packages", "admin panel", "billing", "user profile"
            ],
            [
                "users", "organizations", "repositories", "commits", "branches", "pull_requests", "issues", "actions", "secrets", "releases"
            ],
            [
                "repository listing and file browser",
                "commits, branches, and pull requests",
                "issues and CI/CD actions placeholders",
                "repository secrets and releases",
                "organization members and wiki",
                "admin panel and billing"
            ],
        ),
    },
    {
        "name": "Video streaming platform",
        "prompt": _base_prompt(
            "video streaming",
            [
                "landing", "login", "signup", "home", "video detail", "channel", "subscriptions", "upload", "studio", "analytics",
                "playlists", "watch later", "history", "comments", "live placeholder", "monetization", "admin dashboard", "reports", "user profile", "search"
            ],
            [
                "users", "channels", "videos", "comments", "subscriptions", "playlists", "watch_history", "monetization", "reports"
            ],
            [
                "video upload and playback",
                "channels, subscriptions, and playlists",
                "comments, likes, and watch history",
                "creator studio and analytics",
                "monetization and live placeholder",
                "admin moderation and reporting"
            ],
        ),
    },
    {
        "name": "Music and podcast platform",
        "prompt": _base_prompt(
            "audio streaming",
            [
                "landing", "login", "signup", "discover", "album/episode detail", "player", "library", "playlists", "creator dashboard",
                "upload", "analytics", "subscriptions", "feed", "comments", "categories", "search", "admin panel", "billing", "user profile"
            ],
            [
                "users", "creators", "albums", "tracks", "episodes", "playlists", "subscriptions", "comments", "categories", "payments"
            ],
            [
                "audio upload and player",
                "albums, playlists, and subscriptions",
                "creator dashboard and analytics",
                "comments and categories",
                "subscription billing and feed",
                "admin moderation and reporting"
            ],
        ),
    },
    {
        "name": "Fitness and workout tracking app",
        "prompt": _base_prompt(
            "fitness tech",
            [
                "landing", "login", "signup", "dashboard", "workouts", "create workout", "exercises", "progress", "nutrition", "goals",
                "challenges", "social feed", "friends", "plans", "coach dashboard", "client management", "messages", "admin panel", "billing", "user profile"
            ],
            [
                "users", "workouts", "exercises", "sets", "goals", "nutrition", "challenges", "friends", "messages", "plans", "subscriptions"
            ],
            [
                "workout logging and exercise library",
                "progress tracking and goals",
                "nutrition logging and challenges",
                "social feed and friends",
                "coach dashboard and client management",
                "subscription billing and admin reporting"
            ],
        ),
    },
    {
        "name": "Event management platform",
        "prompt": _base_prompt(
            "event management",
            [
                "landing", "event search", "event detail", "ticket selection", "checkout", "login", "signup", "attendee dashboard", "tickets",
                "organizer dashboard", "create event", "check-in", "agenda", "speakers", "sponsors", "venue map", "messages", "admin dashboard", "analytics", "user profile"
            ],
            [
                "users", "events", "tickets", "ticket_types", "orders", "attendees", "speakers", "sponsors", "venues", "check_ins", "messages"
            ],
            [
                "event search and detail pages",
                "ticket selection and checkout flow",
                "attendee dashboard and ticket management",
                "organizer dashboard and check-in",
                "agenda, speakers, and sponsors",
                "admin moderation and reporting"
            ],
        ),
    },
    {
        "name": "Online voting and survey platform",
        "prompt": _base_prompt(
            "survey and voting",
            [
                "landing", "login", "signup", "surveys", "create survey", "survey builder", "respond", "results", "polls", "votes", "audience",
                "segments", "templates", "logic", "export", "analytics", "api keys", "webhooks", "admin panel", "billing", "user profile"
            ],
            [
                "users", "surveys", "questions", "responses", "polls", "votes", "audiences", "segments", "templates", "api_keys", "webhooks"
            ],
            [
                "survey builder with question types",
                "survey logic and conditional branching",
                "public and private surveys",
                "polls and voting",
                "results, analytics, and CSV export",
                "API keys and webhooks"
            ],
        ),
    },
    {
        "name": "Digital asset management system",
        "prompt": _base_prompt(
            "DAM startup",
            [
                "landing", "login", "signup", "library", "upload", "folders", "collections", "metadata", "search", "preview", "share",
                "download", "versions", "tags", "permissions", "workflows", "annotations", "api keys", "admin panel", "billing", "user profile"
            ],
            [
                "users", "teams", "assets", "folders", "collections", "tags", "metadata", "versions", "annotations", "permissions", "api_keys"
            ],
            [
                "media upload and library grid",
                "folders, collections, and tags",
                "metadata editing and search",
                "preview, share, and download",
                "version control and annotations",
                "permissions, workflows, and API keys"
            ],
        ),
    },
    {
        "name": "Bug bounty and vulnerability disclosure platform",
        "prompt": _base_prompt(
            "security platform",
            [
                "landing", "login", "signup", "programs", "program detail", "submit report", "report detail", "researcher dashboard", "company dashboard",
                "rewards", "leaderboard", "notifications", "messages", "settings", "admin dashboard", "analytics", "billing", "user profile", "api docs"
            ],
            [
                "users", "programs", "reports", "rewards", "messages", "notifications", "companies", "researchers", "leaderboard", "api_keys"
            ],
            [
                "program listing and submission flow",
                "report triage and status tracking",
                "researcher dashboard and rewards",
                "company dashboard and report management",
                "messages and leaderboard",
                "admin moderation and API keys"
            ],
        ),
    },
    {
        "name": "Online course marketplace",
        "prompt": _base_prompt(
            "course marketplace",
            [
                "landing", "course catalog", "course detail", "login", "signup", "student dashboard", "instructor dashboard", "create course",
                "cart", "checkout", "wishlist", "reviews", "discussions", "certificates", "analytics", "affiliates", "admin dashboard", "billing", "user profile"
            ],
            [
                "users", "courses", "lessons", "categories", "orders", "cart", "reviews", "discussions", "certificates", "affiliates", "payments"
            ],
            [
                "course catalog and search/filter",
                "course creation and lesson management",
                "cart and checkout with payment simulation",
                "reviews, discussions, and wishlist",
                "certificates and affiliate tracking",
                "admin moderation and analytics"
            ],
        ),
    },
    {
        "name": "Charity and donation platform",
        "prompt": _base_prompt(
            "nonprofit tech",
            [
                "landing", "campaign search", "campaign detail", "donate", "checkout", "login", "signup", "donor dashboard", "recurring donations",
                "organizer dashboard", "create campaign", "updates", "volunteers", "events", "reports", "admin dashboard", "analytics", "user profile"
            ],
            [
                "users", "campaigns", "donations", "recurring_plans", "updates", "volunteers", "events", "organizations", "payments", "reports"
            ],
            [
                "campaign search and detail pages",
                "one-time and recurring donations",
                "donor and organizer dashboards",
                "campaign updates and volunteer signups",
                "events and payment simulation",
                "admin moderation and reporting"
            ],
        ),
    },
    {
        "name": "Peer-to-peer lending platform",
        "prompt": _base_prompt(
            "fintech lending",
            [
                "landing", "login", "signup", "borrower dashboard", "lender dashboard", "loan listings", "loan detail", "apply", "invest",
                "portfolio", "payments", "kyc", "documents", "risk assessment", "notifications", "admin dashboard", "compliance", "reports", "user profile"
            ],
            [
                "users", "loans", "investments", "payments", "documents", "kyc", "risk_profiles", "portfolios", "transactions", "compliance"
            ],
            [
                "loan listings and borrower application",
                "lender investment and portfolio tracking",
                "payment schedule and transaction history",
                "KYC document upload and risk assessment",
                "notifications and compliance reports",
                "admin dashboard and CSV export"
            ],
        ),
    },
    {
        "name": "Remote desktop and screen sharing service",
        "prompt": _base_prompt(
            "remote access SaaS",
            [
                "landing", "login", "signup", "sessions", "start session", "join session", "devices", "contacts", "chat", "file transfer",
                "recordings", "settings", "teams", "permissions", "audit logs", "api keys", "webhooks", "billing", "admin panel", "user profile"
            ],
            [
                "users", "teams", "sessions", "devices", "contacts", "messages", "recordings", "file_transfers", "api_keys", "webhooks"
            ],
            [
                "session creation and join flow",
                "contact list and team management",
                "chat and file transfer placeholders",
                "recordings and device management",
                "audit logs and API keys",
                "team billing and admin panel"
            ],
        ),
    },
]


def random_prompt() -> dict:
    """Pick a random maximally complex, realistic project spec."""
    return random.choice(PROJECT_PROMPTS)
