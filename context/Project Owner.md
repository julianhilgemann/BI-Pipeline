This document represents the **Project Management Plan**. As the Product Owner (PO), my focus is not on *how* the code is written, but on **Value Delivery, Scope Management, and Stakeholder Satisfaction**.
I bridge the gap between the "Technical Team" (Data Scientist/Engineer) and the "Business Stakeholders" (CFO/Sales Directors who use the dashboard).
---
# Project Charter: Vantage BI Re-Engineering
**Project Owner:** [Your Name]
**Status:** Planning Phase
**Timeline:** 4-Week Sprint Cycle
**Budget:** N/A (Internal Portfolio Initiative)
## 1. Executive Summary & Vision
We are migrating an existing static reporting suite (PDF-based) into a dynamic, automated BI solution. The goal is to move from "Checking what happened" to "Analyzing why it happened."
**Success Definition:** A Controller looking at our new Power BI dashboard cannot distinguish it from the original production data in terms of complexity and logic, even though the data is synthetic.
## 2. The Product Roadmap (Phased Delivery)
I have broken this project down into **4 One-Week Sprints**. This prevents "analysis paralysis" and ensures we ship working software every week.
### **Sprint 1: The Data Foundation (Backend)**
* **Goal:** Generate realistic raw data.
* **Owner:** Data Scientist / Data Engineer.
* **Deliverables:**
* Python generator script finalized.
* DuckDB instance populated with `raw` tables.
* *PM Check:* Do the CSVs look real? Does the "Christmas Spike" exist in the data? Are there returns?
### **Sprint 2: The Logic Core (Middleware)**
* **Goal:** Define the "Single Source of Truth."
* **Owner:** Analytics Engineer (dbt).
* **Deliverables:**
* dbt pipeline running successfully (`stg` -> `int` -> `marts`).
* Currency conversion logic verified.
* **Milestone:** The "Marketing Allocation" test passes (Total Spend in Marketing Table = Total Allocated Spend in Orders Table).
### **Sprint 3: The Visualization (Frontend)**
* **Goal:** Replicate the User Interface.
* **Owner:** BI Developer.
* **Deliverables:**
* Power BI model connected to DuckDB.
* Page 1 (Overview) and Page 4 (Variance) built.
* DAX measures for "Variance %" and "Year-to-Date" implemented.
### **Sprint 4: Polish & Documentation (Release)**
* **Goal:** "Production Readiness."
* **Deliverables:**
* README documentation.
* Data Lineage graph.
* Final design tweaks (colors, fonts matching vantage CI).
* **UAT (User Acceptance Testing):** Self-review against the original PDF.
---
## 3. Key User Stories (The Backlog)
These stories define *what* we are building. The engineering team must satisfy these requirements.
### **Epic 1: Financial Performance**
* **US-1.1:** *As a CFO, I want to see Net Sales and Gross Margin in EUR, so that I can report consistent numbers regardless of where the sale happened (CH/AT/DE).*
* *Acceptance Criteria:* CH orders converted to EUR using daily rate. Returns excluded from Net Sales.
* **US-1.2:** *As a Controller, I want to see the Variance vs. Budget (Absolute and %), so I can identify underperforming regions.*
* *Acceptance Criteria:* Green/Red conditional formatting matching the PDF.
### **Epic 2: Operational Efficiency**
* **US-2.1:** *As a Logistics Manager, I want to see the "Logistics Cost per Order," so I can track if our shipping efficiency is improving.*
* *Acceptance Criteria:* Costs include base fee + weight variable + country surcharges.
* **US-2.2:** *As a Marketing Manager, I want to see the "Contribution Margin 2" (after Marketing Costs) per Product Category.*
* *Acceptance Criteria:* Marketing spend is allocated down to the order line level.
### **Epic 3: Product Analysis**
* **US-3.1:** *As a Category Manager, I want to filter the dashboard by "Schuhe" (Shoes) and see the specific return rate for that category.*
* *Acceptance Criteria:* Selecting "Schuhe" updates all KPI cards.
---
## 4. Risk Register & Mitigation Strategy
As PM, I am monitoring these risks to ensure the project doesn't fail.
| Risk | Impact | Likelihood | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **"Fake" looking data** | High. If the charts look like flat lines, the project fails as a portfolio piece. | Medium | **Direct Data Science to use seasonality:** Ensure Weekends > Weekdays, and November > February. |
| **Logic Mismatch** | High. Margins calculated incorrectly (e.g., forgetting to deduct returns). | Medium | **dbt Tests:** Mandate a test that asserts `Net Sales <= Gross Sales`. |
| **Complexity Overload** | Medium. Trying to model inventory, suppliers, and procurement. | High | **Scope Creep Management:** Strictly out of scope. We assume infinite inventory. We only model *Sales*. |
| **Currency Confusion** | Medium. Summing CHF and EUR directly. | Low | **Code Review:** Check `int_exchange_rates` logic in Sprint 2. |
---
## 5. The "Definition of Done" (DoD)
A task is not complete until:
1. **Code is committed** to the repository.
2. **Pipeline runs** (`dbt build`) without error.
3. **Tests pass** (Data integrity checks).
4. **Visuals match** the reference PDF (pixels, colors, and numbers align).
---
## 6. PM's Final Note to the Team
*"Team (me), the goal here isn't to build the world's most complex database. The goal is to build the **cleanest** one. We want a recruiter to look at the repo and say, 'This person understands how business metrics flow from a raw CSV to a board-level report.' Keep the code simple, keep the variable names readable, and focus on the 'Truth' of the numbers."*