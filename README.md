# Rocky → Every Action Sync

This project connects Rock the Vote's Rocky civic engagement platform with EveryAction, a CRM used by many partner organizations.

When someone uses a Rock the Vote tool, this integration extends how partners can use that data — making it easier to connect with existing systems.

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
| Home phone | Phone (type: Home) |
| Date of birth | Date of birth |
| Street address | Address |
| Zip code | Zip code |

---

## Before you start

Gather these four credentials before you begin. You will paste them into GitHub in Step 3.

**From Rock the Vote:**
- **Partner ID**
- **API Key** — reach out to support for this key

**From Every Action:**
- **API Key** — request one by logging into EA → Administrative Menu → Integrations → API Integrations → **Request an API Key**. Leave the integration dropdown blank (this is a custom integration). You may see a message that says *"Didn't find what you were looking for? Submit a Support Request"* — ignore it and proceed. Your EA admin will receive an approval request — once approved, your key will be available in the API Keys section of that same page.
- **Database name** — almost always `EveryAction`. Use `MyCampaign` if your EA rep told you so.

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

**How far back does it look on each run?**
By default, 1 day. This creates a small overlap between runs so no registrations are missed. You can change `lookback_days` in `config.yml`.

**What if the same person is synced twice?**
Every Action's upsert logic matches on name + email. If the person already exists they are updated, not duplicated.

**Does this sync registration status (submitted, under 18, etc.)?**
Not by default — it syncs contact information only. If you need to filter by status, contact Rock the Vote for guidance on which status values to include or exclude.

**Is there a cost?**
GitHub's free plan includes 2,000 Actions minutes per month. An hourly sync uses roughly 120 minutes per month, well within the free limit.

**What if I want to stop the sync?**
Go to Actions → Rocky → Every Action Sync → the three-dot menu (⋯) → **Disable workflow**.

---

## Need help?

Contact your Rock the Vote partner representative.

---

## Built with

[Parsons](https://github.com/move-coop/parsons) — an open source data connector library maintained by the [Movement Cooperative](https://movementcooperative.org) and the progressive tech community. This project uses Parsons' [RockTheVote connector](https://move-coop.github.io/parsons/stable/rockthevote.html) to pull registration reports from the Rocky API and its [VAN connector](https://move-coop.github.io/parsons/stable/van.html) to upsert records into Every Action.
