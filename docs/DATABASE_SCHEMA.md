# Carbonly Database Schema

PostgreSQL schema for carbon accounting and emissions reporting. All monetary and emissions values are stored in base units (kg CO₂e); display as tCO₂e where needed.

---

## Entity Relationship Overview

```
User ──┬──< Report (created_by)
       └── Company (many users per company via company_id)

Company ──┬── DataSourceConnection
          ├── ActivityRecord
          ├── EmissionEstimate (via ActivityRecord)
          ├── EmissionsSummary
          └── Report

ActivityRecord ──> EmissionFactor (logical; linked via activity_type/scope)
ActivityRecord ──> EmissionEstimate (one estimate per record × factor)
EmissionFactor (reference/lookup table, not FK from activity)
```

---

## Tables

### 1. `users`

| Column        | Type         | Constraints     | Description                |
| ------------- | ------------ | --------------- | -------------------------- |
| id            | UUID         | PK              |                            |
| email         | VARCHAR(255) | UNIQUE NOT NULL | Login identifier           |
| password_hash | VARCHAR(255) |                 | Nullable if only OAuth     |
| full_name     | VARCHAR(255) |                 |                            |
| company_id    | UUID         | FK → companies  | One company per user       |
| google_id     | VARCHAR(255) | UNIQUE          | For "Continue with Google" |
| is_active     | BOOLEAN      | DEFAULT true    |                            |
| created_at    | TIMESTAMPTZ  | NOT NULL        |                            |
| updated_at    | TIMESTAMPTZ  | NOT NULL        |                            |

---

### 2. `companies`

| Column                  | Type         | Constraints            | Description          |
| ----------------------- | ------------ | ---------------------- | -------------------- |
| id                      | UUID         | PK                     |                      |
| name                    | VARCHAR(255) | NOT NULL               | Company name         |
| industry                | VARCHAR(64)  |                        | e.g. SaaS, Software  |
| employee_count          | INTEGER      |                        | 10–200 SMB range     |
| hq_location             | VARCHAR(255) |                        | HQ location          |
| reporting_year          | INTEGER      | NOT NULL               | Default current year |
| email_notifications     | BOOLEAN      | DEFAULT true           | Settings             |
| monthly_summary_reports | BOOLEAN      | DEFAULT true           | Settings             |
| unit_system             | VARCHAR(32)  | DEFAULT 'metric_tco2e' | Unit preference      |
| created_at              | TIMESTAMPTZ  | NOT NULL               |                      |
| updated_at              | TIMESTAMPTZ  | NOT NULL               |                      |

---

### 3. `data_source_connections`

Tracks connection status for cloud providers (AWS, GCP, Azure) and other sources.

| Column                | Type         | Constraints             | Description                                    |
| --------------------- | ------------ | ----------------------- | ---------------------------------------------- |
| id                    | UUID         | PK                      |                                                |
| company_id            | UUID         | FK → companies NOT NULL |                                                |
| source_type           | VARCHAR(64)  | NOT NULL                | e.g. aws, gcp, azure                           |
| display_name          | VARCHAR(128) | NOT NULL                | e.g. AWS, GCP, Azure                           |
| status                | VARCHAR(32)  | NOT NULL                | connected, ai_estimated, not_connected, manual |
| credentials_encrypted | TEXT         |                         | For connected; nullable                        |
| last_synced_at        | TIMESTAMPTZ  |                         | Last successful sync                           |
| created_at            | TIMESTAMPTZ  | NOT NULL                |                                                |
| updated_at            | TIMESTAMPTZ  | NOT NULL                |                                                |

**Unique:** `(company_id, source_type)`.

---

### 4. `activity_records`

Raw activity data: consumption or usage that will be multiplied by emission factors.

| Column                    | Type          | Constraints                  | Description                                                              |
| ------------------------- | ------------- | ---------------------------- | ------------------------------------------------------------------------ |
| id                        | UUID          | PK                           |                                                                          |
| company_id                | UUID          | FK → companies NOT NULL      |                                                                          |
| data_source_connection_id | UUID          | FK → data_source_connections | Null = manual entry                                                      |
| scope                     | SMALLINT      | NOT NULL                     | 1, 2, or 3                                                               |
| scope_3_category          | VARCHAR(64)   |                              | cloud, travel, remote_work, commuting, purchased_services (Scope 3 only) |
| activity_type             | VARCHAR(64)   | NOT NULL                     | e.g. electricity_kwh, cloud_usage, km_travel                             |
| quantity                  | NUMERIC(18,6) | NOT NULL                     | Amount of activity                                                       |
| unit                      | VARCHAR(32)   | NOT NULL                     | e.g. kWh, km, USD                                                        |
| period_start              | DATE          | NOT NULL                     | Start of reporting period                                                |
| period_end                | DATE          | NOT NULL                     | End of reporting period                                                  |
| data_quality              | VARCHAR(32)   | NOT NULL                     | measured, estimated, manual                                              |
| assumptions               | TEXT          |                              | Free-text assumptions                                                    |
| confidence_score          | NUMERIC(5,2)  |                              | 0–100                                                                    |
| metadata                  | JSONB         |                              | Source-specific payload                                                  |
| created_at                | TIMESTAMPTZ   | NOT NULL                     |                                                                          |
| updated_at                | TIMESTAMPTZ   | NOT NULL                     |                                                                          |

---

### 5. `emission_factors`

Reference table: emission factor per unit of activity (e.g. kg CO₂e per kWh).

| Column           | Type          | Constraints | Description              |
| ---------------- | ------------- | ----------- | ------------------------ |
| id               | UUID          | PK          |                          |
| name             | VARCHAR(255)  | NOT NULL    | e.g. UK Grid Electricity |
| activity_type    | VARCHAR(64)   | NOT NULL    | Matches activity_records |
| factor_value     | NUMERIC(18,6) | NOT NULL    | kg CO₂e per unit         |
| unit             | VARCHAR(32)   | NOT NULL    | e.g. kWh                 |
| scope            | SMALLINT      | NOT NULL    | 1, 2, or 3               |
| scope_3_category | VARCHAR(64)   |             | For Scope 3              |
| source_citation  | TEXT          |             | For defensible reports   |
| region           | VARCHAR(64)   |             | Optional region          |
| valid_from       | DATE          |             | Factor validity          |
| valid_to         | DATE          |             | Factor validity          |
| created_at       | TIMESTAMPTZ   | NOT NULL    |                          |
| updated_at       | TIMESTAMPTZ   | NOT NULL    |                          |

---

### 6. `emission_estimates`

Computed: **Emissions = Activity × Emission factor**. One row per activity record × factor used; stores denormalized values for auditability.

| Column             | Type          | Constraints                    | Description                      |
| ------------------ | ------------- | ------------------------------ | -------------------------------- |
| id                 | UUID          | PK                             |                                  |
| company_id         | UUID          | FK → companies NOT NULL        |                                  |
| activity_record_id | UUID          | FK → activity_records NOT NULL |                                  |
| emission_factor_id | UUID          | FK → emission_factors NOT NULL |                                  |
| scope              | SMALLINT      | NOT NULL                       | 1, 2, or 3                       |
| scope_3_category   | VARCHAR(64)   |                                | For Scope 3                      |
| activity_quantity  | NUMERIC(18,6) | NOT NULL                       | Snapshot of quantity             |
| factor_value       | NUMERIC(18,6) | NOT NULL                       | Snapshot of factor               |
| emissions_kg_co2e  | NUMERIC(18,6) | NOT NULL                       | activity_quantity × factor_value |
| data_quality       | VARCHAR(32)   | NOT NULL                       | measured, estimated, manual      |
| assumptions        | TEXT          |                                |                                  |
| confidence_score   | NUMERIC(5,2)  |                                | 0–100                            |
| period_start       | DATE          | NOT NULL                       |                                  |
| period_end         | DATE          | NOT NULL                       |                                  |
| created_at         | TIMESTAMPTZ   | NOT NULL                       |                                  |
| updated_at         | TIMESTAMPTZ   | NOT NULL                       |                                  |

---

### 7. `emissions_summaries`

Pre-aggregated totals for dashboard and reports: by company, year, period (annual/monthly), scope, and optionally Scope 3 category.

| Column               | Type          | Constraints             | Description            |
| -------------------- | ------------- | ----------------------- | ---------------------- |
| id                   | UUID          | PK                      |                        |
| company_id           | UUID          | FK → companies NOT NULL |                        |
| reporting_year       | INTEGER       | NOT NULL                |                        |
| period_type          | VARCHAR(16)   | NOT NULL                | annual, monthly        |
| period_value         | VARCHAR(16)   | NOT NULL                | e.g. 2024, 2024-01     |
| scope                | SMALLINT      | NOT NULL                | 1, 2, or 3             |
| scope_3_category     | VARCHAR(64)   |                         | For Scope 3            |
| total_kg_co2e        | NUMERIC(18,6) | NOT NULL                |                        |
| measured_kg_co2e     | NUMERIC(18,6) | NOT NULL                | Default 0              |
| estimated_kg_co2e    | NUMERIC(18,6) | NOT NULL                | Default 0              |
| manual_kg_co2e       | NUMERIC(18,6) | NOT NULL                | Default 0              |
| confidence_score_avg | NUMERIC(5,2)  |                         | Weighted or simple avg |
| created_at           | TIMESTAMPTZ   | NOT NULL                |                        |
| updated_at           | TIMESTAMPTZ   | NOT NULL                |                        |

**Unique:** `(company_id, reporting_year, period_type, period_value, scope, scope_3_category)` (use COALESCE(scope_3_category, '') for uniqueness).

---

### 8. `reports`

Generated carbon disclosure reports (draft or published).

| Column                | Type          | Constraints             | Description                                           |
| --------------------- | ------------- | ----------------------- | ----------------------------------------------------- |
| id                    | UUID          | PK                      |                                                       |
| company_id            | UUID          | FK → companies NOT NULL |                                                       |
| created_by_user_id    | UUID          | FK → users NOT NULL     |                                                       |
| title                 | VARCHAR(255)  | NOT NULL                | Report title                                          |
| company_name_snapshot | VARCHAR(255)  |                         | Company name at generation                            |
| reporting_year        | INTEGER       | NOT NULL                |                                                       |
| total_kg_co2e         | NUMERIC(18,6) | NOT NULL                | Annual total                                          |
| status                | VARCHAR(32)   | NOT NULL                | draft, published                                      |
| shareable_token       | VARCHAR(64)   | UNIQUE                  | For public link; nullable                             |
| pdf_path              | VARCHAR(512)  |                         | Stored path or object key                             |
| content_snapshot      | JSONB         |                         | Executive summary, methodology, breakdowns, citations |
| generated_at          | TIMESTAMPTZ   |                         |                                                       |
| published_at          | TIMESTAMPTZ   |                         |                                                       |
| created_at            | TIMESTAMPTZ   | NOT NULL                |                                                       |
| updated_at            | TIMESTAMPTZ   | NOT NULL                |                                                       |

**content_snapshot** structure (JSON):

- `executive_summary`: string
- `scope_1_kg_co2e`, `scope_2_kg_co2e`, `scope_3_kg_co2e`: numbers
- `scope_3_breakdown`: `{ "cloud": number, "travel": number, "remote_work": number, "commuting": number, "purchased_services": number }`
- `methodology_notes`: string
- `assumptions_limitations`: string
- `emission_factor_citations`: array of { source, url_or_ref }
- `monthly_breakdown`: array of { month, scope_1, scope_2, scope_3, total }

---

## Enums (application-level)

- **DataSourceStatus:** `connected`, `ai_estimated`, `not_connected`, `manual`
- **DataQuality:** `measured`, `estimated`, `manual`
- **ReportStatus:** `draft`, `published`
- **Scope:** 1, 2, 3
- **Scope3Category:** `cloud`, `travel`, `remote_work`, `commuting`, `purchased_services`

---

## Indexes

- `users`: `company_id`, `email`, `google_id`
- `companies`: (none beyond PK)
- `data_source_connections`: `company_id`, `(company_id, source_type)` UNIQUE
- `activity_records`: `company_id`, `(company_id, period_start, period_end)`, `data_source_connection_id`, `scope`, `scope_3_category`
- `emission_factors`: `activity_type`, `scope`, `scope_3_category`, `valid_from`, `valid_to`
- `emission_estimates`: `company_id`, `activity_record_id`, `(company_id, period_start, period_end)`, `scope`
- `emissions_summaries`: `company_id`, `(company_id, reporting_year, period_type, period_value)`, `scope`
- `reports`: `company_id`, `created_by_user_id`, `status`, `shareable_token`

---

## Auditability

- Every emissions value is traceable: **emission_estimates** → **activity_records** + **emission_factors**.
- **activity_records** and **emission_estimates** store **data_quality**, **assumptions**, and **confidence_score**.
- **emission_factors** store **source_citation** for methodology and citations in reports.
- **reports.content_snapshot** stores a point-in-time snapshot so published reports remain defensible and unchanged.
