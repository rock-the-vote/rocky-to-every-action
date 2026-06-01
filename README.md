# Rocky → Every Action Sync

This project connects Rock the Vote's Rocky civic engagement platform with EveryAction, a CRM used by many partner organizations.

When someone uses a Rock the Vote tool, this integration extends how partners can use that data — making it easier to connect with existing systems.

---

- [Why this matters](#why-this-matters)
- [How it works](#how-it-works)
- [Security and data privacy](#security-and-data-privacy)
- [Before you start](#before-you-start)
- [Setup guide](#setup-guide)
- [Changing the sync frequency](#changing-the-sync-frequency)
- [Enabling additional tools](#enabling-additional-tools)
- [Optional: Tag synced contacts with an Activist Code](#optional-tag-synced-contacts-with-an-activist-code)
- [Optional: Sync partner opt-in preferences](#optional-sync-partner-opt-in-preferences)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [For developers — running locally](#for-developers--running-locally)

---

## Why this matters

Rocky is a powerful platform for voter registration, absentee ballot requests, pledge to vote campaigns, voter status lookups, and more.

Many partners also rely on EveryAction to manage outreach, communications, and campaigns.

This integration connects those systems, making it easy to move data from Rocky into EveryAction so partners can continue engaging users within their existing tools.

---

## How it works

```
User fills out a Rocky form
        ↓
Rocky processes and stores the data
        ↓
This integration formats the data
        ↓
Data is sent to EveryAction automatically
        ↓
Partner can use it in their CRM
```

Once set up, this runs on GitHub's free infrastructure — no server to manage, no monthly cost. It pulls new records from your Rocky account on a daily schedule and sends them to EveryAction. If a person already exists in EA they are updated, not duplicated.

---

## What this does NOT do

- It does **not** collect voter data itself
- It does **not** replace Rocky or EveryAction
- It does **not** provide a user interface
- It is purely a data bridge between systems

---

## Who this is for

- Partner organizations using both Rocky and EveryAction
- Developers building or maintaining the integration
- Product and operations teams who need data flowing between systems

---

## Security and data privacy

This integration follows standard security practices to protect voter data:

- HTTPS only for all data transmission
- Authenticated API access via secure, server-side credentials
- No voter data stored — records are pulled from Rocky and pushed directly to EveryAction with nothing retained in between
- No data is stored by this integration beyond what is required for processing
- No sensitive logic or credentials exposed client-side
- Minimal data handling — only the fields required for EveryAction matching are transmitted
- Run logs contain no PII by default — names and emails are only visible at debug level
- Workflow fails immediately if the repository is set to public, preventing accidental log exposure
- Credentials are stored as GitHub Secrets — injected as environment variables at runtime, never written to disk
- Integration activity is logged for monitoring and debugging; logs are retained by GitHub Actions and visible only to users with repository access
- Failed records are automatically retried on the next scheduled run via the lookback window

**Credentials are never in the code.**
Rocky and EveryAction API keys are stored as GitHub Secrets — encrypted by GitHub and never visible in logs or source code.

**Keep your fork private.**
When you fork this repo, set it to **Private**. The workflow enforces this and will refuse to run on a public repository.

**Treat your API keys like passwords.**
If you suspect a key has been compromised, rotate it immediately in Rocky or EveryAction and update the corresponding GitHub Secret.

**Limit who has access.**
Only give GitHub repo access to people who need it. Anyone with access can view run logs and trigger syncs manually.

---

**Supported Rocky tools:**

| Tool | Config key | Notes |
|---|---|---|
| Online Voter Registration | `registration` | Enabled by default |
| OVR Extended | `registration_extended` | Includes UTM params, state API status, previous names |
| Pledge to Vote | `pledge` | |
| Absentee Ballot Request | `absentee` | |
| Voter Status Lookup | `lookup` | |

Each tool syncs the following fields into Every Action:

| Rocky field | Every Action field |
|---|---|
| First name | First name |
| Last name | Last name |
| Email | Email |
| Phone | Phone (type preserved from Rocky; omitted if unknown) |
| Date of birth | Date of birth |
| Street address | Address |
| Zip code | Zip code |

---

## Before you start

Gather these four credentials before you begin. You will paste them into GitHub in Step 3.

**From Rock the Vote:**
- **Partner ID**
- **API Key** — reach out to support for this key

**From EveryAction:**
- **API Key** — Log into EveryAction and navigate to Administrative Menu → Integrations → API Integrations.

  Request or create an API key for use with the Rock the Vote integration. EveryAction API keys are tied to specific security profiles and permissions. Depending on your organization's setup, an EveryAction administrator, account representative, or NGP VAN support staff may need to configure the key with the appropriate access before it can be used.

  If you are unsure which permissions are required, contact your EveryAction representative for assistance.
- **Database name** — Usually `EveryAction`. Use `MyCampaign` only if instructed to do so by your EveryAction representative.

---

## Setup guide

### Step 1 — Create a free GitHub account

If you already have a GitHub account, skip to Step 2.

1. Go to https://github.com and click **Sign up**
2. Enter your email, create a password, and choose a username
3. Verify your email address

> GitHub's free plan includes everything you need. You do not need to pay for anything.

---

### Step 2 — Fork the template repo

"Forking" creates your own copy of this template under your GitHub account.

1. Go to the Rock the Vote sync repo: **`https://github.com/rock-the-vote/rocky-to-every-action`**
2. Click the **Fork** button in the top-right corner
3. On the next screen:
   - Change **Owner** to your GitHub account (or your organization if you have one)
   - Change **Repository name** to something like `rocky-ea-sync`
   - Check **Copy the `main` branch only**
   - > **Important:** Set visibility to **Private**. Run logs may contain voter names and should not be publicly visible.
4. Click **Create fork**

You now have your own copy of the sync code at `https://github.com/YOUR-USERNAME/rocky-ea-sync`.

---

### Step 3 — Add your credentials

Your credentials are stored as **Secrets** — GitHub encrypts them and never displays them again after you save. They are never visible in your code.

1. In your forked repo, click the **Settings** tab (top of the page)
2. In the left sidebar, click **Secrets and variables** → **Actions**
3. Click **New repository secret** and add each of the following, one at a time:

| Secret name | Value |
|---|---|
| `ROCKY_PARTNER_ID` | Your Rocky Partner ID |
| `ROCKY_API_KEY` | Your Rocky API Key |
| `EA_API_KEY` | Your Every Action API Key |
| `EA_LOGIN_NAME` | The login name provided with your EA API key |
| `EA_DATABASE` | `EveryAction` (or `MyCampaign` if told otherwise) |

> **Important:** Secret names must match exactly, including capitalization. Copy them from the table above.

---

### Step 4 — Enable the workflow

GitHub disables scheduled workflows on forked repos by default. You need to turn it on once.

1. Click the **Actions** tab at the top of your repo
2. You will see a yellow banner: *"Workflows aren't being run on this forked repository"*
3. Click **I understand my workflows, go ahead and enable them**

---

### Step 5 — Do a test run (dry run)

Dry run mode is on by default — nothing will be written to Every Action until you turn it off in Step 6. Your first run is always safe.

1. Click the **Actions** tab
2. In the left sidebar, click **Rocky → Every Action Sync**
3. Click the **Run workflow** dropdown on the right
4. Click the green **Run workflow** button
5. Refresh the page — a new run will appear. Click it to watch the logs.

A successful dry run looks like this in the logs:

```
2025-01-01T10:00:01Z INFO Fetching Rocky registrants since 2024-12-31
2025-01-01T10:00:08Z INFO Found 12 registrants to sync.
2025-01-01T10:00:08Z INFO [DRY RUN] Would upsert: Jane Smith <jane@example.com>
2025-01-01T10:00:08Z INFO [DRY RUN] Would upsert: John Doe <john@example.com>
...
2025-01-01T10:00:08Z INFO Sync complete — 12 synced, 0 errors.
```

If you see errors, check the **Troubleshooting** section below before continuing.

---

### Step 6 — Go live

Once the dry run looks correct:

1. In your repo, open the file **`config.yml`**
2. Click the **pencil icon** (Edit this file) in the top-right
3. Change `dry_run: true` to `dry_run: false`
4. Scroll down and click **Commit changes**

The sync will now run automatically once a day and write real records to Every Action.

---

## Changing the sync frequency

The schedule is set in `.github/workflows/sync.yml`. To change it:

1. Open `.github/workflows/sync.yml` in your repo
2. Click the pencil icon to edit
3. Find this line:
   ```
   - cron: '0 9 * * *'
   ```
4. Replace it with one of these (or use [crontab.guru](https://crontab.guru) to build your own):

| Schedule | Cron expression |
|---|---|
| Once a day at 9am UTC | `0 9 * * *` |
| Twice a day (9am + 5pm UTC) | `0 9,17 * * *` |
| Every 4 hours | `0 */4 * * *` |
| Every hour | `0 * * * *` |

5. Click **Commit changes**

> **Note:** Running more frequently than once a day provides no real benefit. Rocky's API filters by date (not time), so every run pulls at least the current day's records regardless of how often you run. Once a day is the recommended cadence — Every Action handles updates gracefully if the same person is sent more than once.

---

## Enabling additional tools

By default only the voter registration tool syncs. To enable others, open `config.yml`, click the pencil icon, and set `enabled: true` for any tool you want:

```yaml
tools:
  registration:
    enabled: true
  pledge:
    enabled: true    # turn on Pledge to Vote
  absentee:
    enabled: true    # turn on Absentee Ballot Request
  lookup:
    enabled: false
```

Click **Commit changes** when done.

---

## Optional: Tag synced contacts with an Activist Code

Each tool can apply its own Every Action Activist Code to every person synced — useful for segmenting "Rocky Registrant" vs "Rocky Absentee Requester" in EA.

1. In Every Action, find the ID for your activist code:
   - Go to **Contacts → Activist Codes**
   - Click on your code
   - The ID is in the URL: `.../activistcodes/**12345**/...`

2. Open `config.yml`, click the pencil icon, and set `activist_code_id` under the relevant tool:
   ```yaml
   tools:
     registration:
       enabled: true
       activist_code_id: 12345
     pledge:
       enabled: true
       activist_code_id: 67890
   ```

3. Click **Commit changes**

---

## Optional: Sync partner opt-in preferences

Rocky collects three partner opt-in fields that you can sync into Every Action:

| Rocky field | What it captures |
|---|---|
| Opt-in to Partner email | User agreed to receive email from your organization |
| Opt-in to Partner SMS/robocall | User agreed to receive texts or robocalls from your organization |
| Volunteer for partner | User expressed interest in volunteering for your organization |

### Partner email opt-in

This is handled automatically — no setup required. When someone opts in to partner email, their record is synced to Every Action with their email marked as subscribed. If they do not opt in, their existing subscription status in Every Action is left untouched — this integration will never unsubscribe someone based on a Rocky form alone.

### Partner SMS opt-in and Volunteer

SMS consent and volunteer interest can be tracked using Activist Codes — the same mechanism described in the previous section. If your Every Action instance has native fields for either, contact your EA rep about a custom integration instead.

To enable either (or both):

1. In Every Action, create an Activist Code for each one you want to track — for example, "Rocky SMS Opt-in" and "Rocky Volunteer Interest". Find the ID for each code in the URL when you open it: `.../activistcodes/**12345**/...`

2. Open `sync.py` in your repo and click the pencil icon to edit it.

3. Find the section that begins:
   ```
   # Tag volunteers:
   # if van_id and parse_bool(norm.get("volunteer_for_partner")):
   ```

4. To enable volunteer tagging, uncomment those two lines and replace `YOUR_VOLUNTEER_CODE_ID` with your activist code ID:
   ```python
   if van_id and parse_bool(norm.get("volunteer_for_partner")):
       van.toggle_activist_code(van_id, 12345, "Apply")
   ```

5. To enable SMS opt-in tagging, do the same for the SMS block just below it, replacing `YOUR_SMS_OPTIN_CODE_ID` with your activist code ID:
   ```python
   if van_id and parse_bool(norm.get("optin_to_partner_sms")):
       van.toggle_activist_code(van_id, 67890, "Apply")
   ```

6. Click **Commit changes**.

> **Note:** These activist codes are applied when the sync runs. They are only applied to contacts who opted in — contacts who did not opt in are synced normally without the code.

---

## Troubleshooting

### "No registrants found" but I know there are new registrations

Check that your `ROCKY_PARTNER_ID` is correct. This ID controls which registrations are visible to the API. You can confirm it by logging into the Rocky partner portal.

### Every Action is rejecting records (401 Unauthorized)

Your `EA_API_KEY` is wrong or expired. In Every Action, go to Administrative Menu → Integrations → API Integrations → API Keys to find your key. Update the `EA_API_KEY` secret in GitHub (Settings → Secrets and variables → Actions).

### "Only works on MyMembers, EveryAction, MyCampaign databases"

Your `EA_DATABASE` secret is set to `MyVoters`, which is a read-only voter file database. Change it to `EveryAction` or ask your Every Action account rep which database you should be writing to.

### The run failed and I got an email from GitHub

GitHub automatically emails you when a workflow fails. Click **View workflow run** in the email to see the logs. Look for lines beginning with `ERROR` — they will tell you which records failed and why.

### I want to see exactly what's happening

1. Open `.github/workflows/sync.yml` and click the pencil icon
2. Find the `Run sync` step and add `LOG_LEVEL: DEBUG` under `env:`
   ```yaml
   env:
     LOG_LEVEL: DEBUG
     ROCKY_PARTNER_ID: ...
   ```
3. Commit and run the workflow. The logs will show every record being processed and all Rocky column names.
4. Remove `LOG_LEVEL: DEBUG` when you're done — it produces a lot of output.

---

## FAQ

**How far back does it look on each run?**<br>
By default, 1 day. This creates a small overlap between runs so no registrations are missed. You can change `lookback_days` in `config.yml`.

**What if the same person is synced twice?**<br>
Every Action's upsert logic matches on name + email. If the person already exists they are updated, not duplicated.

**Does this sync registration status (submitted, under 18, etc.)?**<br>
Not by default — it syncs contact information only. If you need to filter by status, contact Rock the Vote for guidance on which status values to include or exclude.

**Is there a cost?**<br>
GitHub's free plan includes 2,000 Actions minutes per month. An hourly sync uses roughly 120 minutes per month, well within the free limit.

**What if I want to stop the sync?**<br>
Go to Actions → Rocky → Every Action Sync → the three-dot menu (⋯) → **Disable workflow**.

**Does this sync people who only completed step 1 of a voter registration (partial registrations)?**<br>
Yes — Rocky's reports include partial completions alongside fully submitted registrations. If you need to separate them, the `status` field is available in the report data. For voter registrations, common status values include `step_1`, `step_2`, `step_3`, `step_4`, `under_18`, `complete`, and `rejected`. These may vary depending on your Rocky version — if you're unsure, enable `LOG_LEVEL: DEBUG` to inspect the raw values coming through.

**Can I get real-time or near-real-time syncs?**<br>
Not quite. Rocky's API is date-based polling rather than event-driven, so there is no way to trigger an instant push when someone completes a form. Hourly is the practical minimum (set `cron: '0 * * * *'` in the workflow file), but once a day is recommended — Rocky filters by date only, so every run pulls the full current day regardless of how often you run.

---

## For developers — running locally

Use this to test changes without triggering a GitHub Actions run.

### 1 — Clone the repo

```
git clone https://github.com/YOUR-USERNAME/rocky-ea-sync
cd rocky-ea-sync
```

### 2 — Create a `.env` file

Create a file named `.env` in the root of the repo and add your credentials:

```
ROCKY_PARTNER_ID=your_partner_id
ROCKY_API_KEY=your_rocky_api_key
EA_API_KEY=your_ea_api_key
EA_LOGIN_NAME=your_ea_login_name
EA_DATABASE=EveryAction
```

This file is listed in `.gitignore` and will never be committed. Do not rename it.

### 3 — Create and activate a virtual environment

Modern Python on macOS and Linux blocks installing packages outside a virtual environment. You need to create one first:

```
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:
```
python -m venv .venv
.venv\Scripts\activate
```

You should see `(.venv)` in your terminal prompt. If you skip this step and see an `externally-managed-environment` error, come back here.

### 4 — Install dependencies

```
pip install -r requirements.txt
```

Note: inside an activated virtual environment, `pip` works — no need for `pip3`.

### 5 — Run the sync

Make sure `dry_run: true` is set in `config.yml`, then:

```
python sync.py
```

A successful dry run prints a line for each record it would sync, followed by a summary. No data is written to Every Action.

When you're ready to test a live write, set `dry_run: false` in `config.yml` and run again. Change it back when you're done.

---

## Need help?

Contact your Rock the Vote partner representative.

---

## Built with

[Parsons](https://github.com/move-coop/parsons) — an open source data connector library maintained by the [Movement Cooperative](https://movementcooperative.org) and the progressive tech community. This project uses Parsons' [RockTheVote connector](https://move-coop.github.io/parsons/stable/rockthevote.html) to pull registration reports from the Rocky API and its [VAN connector](https://move-coop.github.io/parsons/stable/van.html) to upsert records into Every Action.
