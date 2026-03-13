# 🔄 ROOMAN Workflows

**4 ready-to-use business workflows.** Copy the prompts, paste them into ROOMAN, and watch it work.

---

## Workflow 1: Build Multi-Tenant SaaS from Scratch

**Use this when:** You want to build a subscription software product for multiple clients/customers.

### Step 1 — Architecture (Arch Mind)
```
Design a multi-tenant SaaS architecture for a project management tool.
Requirements:
- Multiple organisations with isolated data
- User roles: admin, manager, member
- Subscription plans: free, pro, enterprise
- Real-time collaboration features
- REST API with webhooks
```

### Step 2 — Backend Infrastructure (InsForge)
```
Build the full-stack backend for a multi-tenant SaaS project manager.
Requirements:
- Postgres database with tenant isolation (row-level security)
- User auth with JWT and refresh tokens
- Subscription management with Stripe webhooks
- REST API: projects, tasks, comments, users
- Storage for file attachments
Include deployment script and cost estimate.
```

### Step 3 — Revenue Forecast (Predict Anything)
```
Forecast first year revenue for a multi-tenant SaaS project management tool.
Assumptions:
- Launch with 0 customers
- Free plan converts 5% to paid ($19/mo)
- Paid plan churns at 3% monthly
- Organic growth of 200 signups/month
- Enterprise plan: $99/mo, targeting 2% of paid users
Forecast month by month for 12 months.
```

### Step 4 — Code the API (Apex Coder)
```
Write complete Python FastAPI code for the multi-tenant SaaS backend.
Use the architecture and infrastructure spec from previous steps.
Include: all CRUD endpoints, JWT auth middleware, Stripe webhook handler,
tenant isolation middleware, error handling, and OpenAPI docs.
```

### Step 5 — Review & Test (Code Reviewer + Test Brain)
```
Review the FastAPI SaaS backend code for security issues, performance
bottlenecks, and missing error handling. Then write a comprehensive
test suite covering auth, multi-tenancy isolation, billing webhooks,
and all API endpoints.
```

**Or run it all at once using the Loop tab:**
```
Goal: Build a multi-tenant SaaS project management tool with full backend,
infrastructure, revenue forecasting for year 1, and complete API code with tests.
```

---

## Workflow 2: E-Commerce Demand Forecasting + Inventory Optimization

**Use this when:** You run an online store and want to stop running out of stock or over-ordering.

### Step 1 — Demand Forecast (Predict Anything)
```
Forecast demand for an e-commerce clothing store for the next 6 months.
Current state:
- 500 SKUs across 3 categories: tops, bottoms, accessories
- Average 800 orders/month
- 30% revenue spike in November-December
- 15% of SKUs cause 60% of revenue
- Current stockout rate: 8%
Predict: units needed per category, peak periods, reorder points, safety stock.
```

### Step 2 — Inventory Backend (InsForge)
```
Build a backend for e-commerce inventory management and demand tracking.
Requirements:
- Postgres: products, inventory_levels, orders, suppliers, forecasts tables
- API endpoints: stock levels, reorder alerts, supplier orders, demand trends
- Automated low-stock alerts (webhook/email trigger when stock < reorder point)
- Dashboard data endpoint: daily sold, current stock, days-of-stock-remaining
- CSV import for product catalogue
Include deployment script for a $10/month VPS.
```

### Step 3 — Pricing Optimization (Predict Anything)
```
Optimize pricing for an e-commerce clothing store to maximize revenue.
Current state:
- Average order value: $65
- Cart abandonment rate: 72%
- Profit margin: 45%
- Top seller sells 200 units/month at $29
- 3 competitors with similar products priced $24-$35
Recommend: optimal price points, bundle strategies, discount timing, upsell opportunities.
```

### Step 4 — Build the Dashboard (Apex Coder)
```
Build a Python Streamlit dashboard for inventory management that shows:
- Real-time stock levels per SKU with color-coded status (green/amber/red)
- Demand forecast chart for next 30/60/90 days
- Low stock alerts list with one-click reorder button
- Sales trend chart (daily/weekly/monthly)
- Supplier order tracker
Use the database schema from the InsForge infrastructure spec.
```

**Loop tab shortcut:**
```
Goal: Build a complete e-commerce inventory optimization system with
6-month demand forecast, pricing optimization, backend database + API,
and a real-time stock management dashboard.
```

---

## Workflow 3: Financial Risk Dashboard & Cash Flow Planning

**Use this when:** You're a business owner, freelancer, or finance professional who needs to understand your money.

### Step 1 — Cash Flow Forecast (Predict Anything)
```
Create a 12-month cash flow forecast for a digital agency.
Current financials:
- Monthly revenue: $45,000 (average, 3 retainer clients + project work)
- Monthly fixed costs: $18,000 (salaries, rent, software)
- Monthly variable costs: 20% of revenue (freelancers, ads)
- Current cash reserve: $60,000
- Accounts receivable: $35,000 (average 45-day payment terms)
- 2 clients at risk (represent 35% of revenue)
Forecast: monthly cash position, risk scenarios (best/base/worst case), break-even.
```

### Step 2 — Risk Assessment (Predict Anything)
```
Assess financial risks for a digital agency and provide mitigation strategies.
Risk factors to analyze:
- Client concentration risk (top 3 clients = 70% of revenue)
- Revenue seasonality (Q4 always drops 25%)
- Accounts receivable risk (2 clients consistently pay late)
- Operational risk (key person dependency on lead developer)
- Market risk (AI tools threatening core service demand)
Score each risk. Recommend specific hedging strategies. Include early warning indicators.
```

### Step 3 — Finance Dashboard Backend (InsForge)
```
Build a financial dashboard backend for an agency.
Requirements:
- Postgres: invoices, payments, expenses, cashflow_projections, risk_flags tables
- API: monthly P&L, cash runway calculator, client revenue concentration, invoice aging
- Automated alerts: overdue invoices, cash below threshold, unusual expense spikes
- Export: monthly financial report as JSON and CSV
- Auth: single user, API key based
Deploy on minimal infrastructure (under $15/month).
```

### Step 4 — Build the Dashboard (Apex Coder)
```
Build a Python Streamlit financial risk dashboard that displays:
- Cash runway gauge (months of runway remaining)
- Monthly cash flow chart with forecast vs actual
- Client revenue concentration pie chart with risk color coding
- Invoice aging report (current/30/60/90+ days)
- Risk score cards for each identified risk factor
- Alert panel for anything needing immediate attention
Make it look professional with charts using plotly.
```

**Loop tab shortcut:**
```
Goal: Build a complete financial risk dashboard for a digital agency including
12-month cash flow forecast, risk assessment with scores, backend database + API,
and a professional Streamlit dashboard with charts.
```

---

## Workflow 4: Multi-Client Agency Scaling System

**Use this when:** You run a freelance business or agency and want to manage multiple clients efficiently.

### Step 1 — Business Growth Forecast (Predict Anything)
```
Forecast growth for a 2-person digital marketing agency looking to scale.
Current state:
- 8 retainer clients at $2,500/month each
- 1 full-time employee + founder
- Monthly revenue: $20,000
- Monthly costs: $12,000
- Client acquisition: 1-2 new clients per month
- Average client lifespan: 18 months
- Churn rate: 5% monthly
Forecast: revenue growth, team size needed, profitability milestones for 24 months.
Model 3 scenarios: conservative, target, aggressive.
```

### Step 2 — Client Management Backend (InsForge)
```
Build a CRM and project management backend for a digital agency.
Requirements:
- Postgres: clients, projects, tasks, invoices, time_entries, contacts, notes tables
- API endpoints: client CRUD, project tracking, invoice generation, time tracking,
  monthly revenue per client, team utilization rate
- Recurring invoice automation (monthly billing trigger)
- Client health score calculation (activity, payment history, engagement)
- Notification webhooks for overdue tasks and invoices
Deploy for under $20/month.
```

### Step 3 — Resource Planning (Predict Anything)
```
Plan resource allocation for a digital agency scaling from 2 to 10 staff.
Current team: founder (strategy), 1 developer
Planned growth: 8 new clients over 12 months
Service mix: web development (40%), SEO (30%), paid ads (20%), content (10%)
Each service requires different skill sets.
Plan: when to hire each role, cost vs revenue crossover points, utilization targets,
how to avoid burnout, outsourcing vs hiring thresholds.
```

### Step 4 — Build the Agency Dashboard (Apex Coder)
```
Build a Python Streamlit agency management dashboard with:
- Client list with health scores (green/amber/red traffic lights)
- Monthly MRR tracker with growth chart
- Project status board (Kanban-style: todo/in progress/review/done)
- Invoice tracker with overdue alerts
- Team utilization gauge per team member
- Revenue per client breakdown
- Quick actions: add client, log time, create invoice
Use tabs for: Dashboard / Clients / Projects / Finance / Team
```

### Step 5 — Document Everything (Doc Writer)
```
Write a complete operations manual for a digital agency using ROOMAN.
Include:
- Client onboarding checklist (12 steps)
- Project delivery process (discovery to launch)
- Monthly billing and reporting procedure
- Team communication protocols
- Quality assurance checklist for deliverables
- How to use each ROOMAN agent in daily operations
Format as a markdown document the team can follow.
```

**Loop tab shortcut:**
```
Goal: Build a complete multi-client agency management system including 24-month
growth and profitability forecast, CRM + billing backend, resource planning for
scaling to 10 staff, and a full Streamlit agency dashboard with client health
scores, project tracking, and financial reporting.
```

---

## Tips for Best Results

1. **Be specific** — the more detail you give, the better the output
2. **Use memory** — check "Use memory" so each agent builds on previous outputs
3. **Use the Loop** — for complex multi-step goals, the Loop tab handles everything automatically
4. **Download as you go** — click download after each step so you don't lose anything
5. **Save to GitHub** — connect GitHub Memory in the sidebar to keep outputs permanently

---

## Combine Workflows

Mix and match! For example:
- Use **Workflow 1** to build the product
- Use **Workflow 2** to forecast demand for it
- Use **Workflow 3** to manage the finances
- Use **Workflow 4** to scale the team selling it

ROOMAN's memory carries context between all steps automatically.
