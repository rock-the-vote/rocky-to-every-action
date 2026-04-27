"""
Rocky → Every Action sync
Docs: https://move-coop.github.io/parsons/stable/
"""

import os
import yaml
import logging
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", RuntimeWarning)
    from parsons import RockTheVote, VAN
    import parsons.rockthevote.rtv as _rtv_module

# Parsons only validates 'extended' but the Rocky API supports more report types.
# Patch the list so our additional tools aren't blocked.
_rtv_module.VALID_REPORT_TYPES = [
    "extended",
    "alert_request_report",
    "abr_report",
    "lookup_report",
]

load_dotenv()

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger(__name__)

# Maps config tool names to Rocky API report_type values.
# None = standard OVR report (no report_type param).
TOOL_REPORT_TYPES = {
    "registration":          None,
    "registration_extended": "extended",
    "pledge":                "alert_request_report",
    "absentee":              "abr_report",
    "lookup":                "lookup_report",
}


def load_config():
    with open("config.yml") as f:
        return yaml.safe_load(f)


def split_street(address):
    """Split '123 Main St' into ('123', 'Main St'). Returns (None, None) if blank."""
    if not address:
        return None, None
    parts = address.strip().split(" ", 1)
    if len(parts) == 2 and parts[0].rstrip(".,").isdigit():
        return parts[0], parts[1]
    return None, address


PHONE_TYPE_MAP = {
    "mobile": "C", "cell": "C",
    "home": "H",
    "work": "W",
}

LANGUAGE_MAP = {
    "en": "English",   "english": "English",
    "es": "Spanish",   "spanish": "Spanish",
    "zh": "Chinese",   "chinese": "Chinese",
    "ko": "Korean",    "korean": "Korean",
    "vi": "Vietnamese","vietnamese": "Vietnamese",
    "tl": "Tagalog",   "tagalog": "Tagalog",
    "ar": "Arabic",    "arabic": "Arabic",
    "fr": "French",    "french": "French",
    "ht": "Haitian Creole", "haitian creole": "Haitian Creole",
}


def parse_bool(value):
    """Normalize Rocky's Yes/No/True/False fields to Python bool."""
    return str(value).strip().lower() in ("yes", "true", "1")


def normalize_row(row):
    """Map report-type-specific column names to a common set."""
    return {
        "first_name":              row.get("first_name")             or row.get("first"),
        "last_name":               row.get("last_name")              or row.get("last"),
        "email_address":           row.get("email_address")          or row.get("email"),
        "phone":                   row.get("phone"),
        "phone_type":              row.get("phone_type"),
        "date_of_birth":           row.get("date_of_birth")          or row.get("birthdate"),
        "home_address":            row.get("home_address")           or row.get("address"),
        "home_zip_code":           row.get("home_zip_code")          or row.get("zip"),
        "optin_to_partner_email":  row.get("optin_to_partner_email") or row.get("partner_opt_in_email"),
        "language":                row.get("language"),
    }


def validate_dob(raw_dob):
    """Return raw_dob string if plausible, else None. Rejects future dates and pre-1900."""
    if not raw_dob:
        return None
    try:
        dob = datetime.strptime(str(raw_dob).strip(), "%Y-%m-%d")
    except ValueError:
        return None
    today = datetime.now()
    if dob > today:
        return None
    if dob < datetime(1900, 1, 1):
        return None
    return str(raw_dob).strip()


def build_person(row):
    row = normalize_row(row)
    street_number, street_name = split_street(row.get("home_address"))
    rocky_phone_type = (row.get("phone_type") or "").lower().strip()

    # Wrap email with partner opt-in status so EA respects subscription preference
    email_address = row.get("email_address")
    email = None
    if email_address:
        email = [{"email": email_address, "isSubscribed": parse_bool(row.get("optin_to_partner_email"))}]

    # Map Rocky language code/name to EA's expected label
    rocky_lang = (row.get("language") or "").lower().strip()
    language = LANGUAGE_MAP.get(rocky_lang)

    dob = validate_dob(row.get("date_of_birth"))

    person = {
        "first_name":    row.get("first_name"),
        "last_name":     row.get("last_name"),
        # Uncomment to pass additional name fields if your EA instance uses them:
        # "middle_name": row.get("middle_name"),
        # "prefix":      row.get("title"),   # e.g. "Mr.", "Ms.", "Dr."
        # "suffix":      row.get("suffix"),   # e.g. "Jr.", "III"
        "email":         email,
        "phone":         row.get("phone"),
        "phone_type":    PHONE_TYPE_MAP.get(rocky_phone_type, "H"),
        "date_of_birth": dob,
        "street_number": street_number,
        "street_name":   street_name,
        "zip":           row.get("home_zip_code"),
    }
    if language:
        person["preferred_language"] = language

    # Drop None values — upsert_person is strict about unexpected nulls
    return {k: v for k, v in person.items() if v is not None}


def sync_tool(tool_name, tool_config, rtv, van, dry_run):
    lookback_days = tool_config.get("lookback_days", 1)
    activist_code_id = tool_config.get("activist_code_id")
    report_type = TOOL_REPORT_TYPES[tool_name]

    since = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    log.info(f"[{tool_name}] Fetching records since {since}...")

    table = rtv.run_registration_report(
        since=since,
        report_type=report_type,
        poll_interval_seconds=15,
        report_timeout_seconds=600,
    )

    if not table or len(table) == 0:
        log.info(f"[{tool_name}] No records found in lookback window.")
        return 0, 0

    log.info(f"[{tool_name}] Found {len(table)} records to sync.")

    if os.environ.get("LOG_LEVEL", "").upper() == "DEBUG":
        log.debug(f"[{tool_name}] Columns: {table.columns}")

    success, errors = 0, 0

    for row in table:
        email = row.get("email", "—")
        try:
            person = build_person(row)

            has_email = bool(person.get("email"))
            if not has_email and not person.get("phone"):
                log.warning(f"[{tool_name}] Skipping {email}: no email or phone — cannot match in EA")
                errors += 1
                continue

            if dry_run:
                email_display = person.get("email")
                if isinstance(email_display, list):
                    email_display = email_display[0].get("email")
                log.debug(
                    f"[{tool_name}] [DRY RUN] Would upsert: "
                    f"{person.get('first_name')} {person.get('last_name')} <{email_display}>"
                )
                log.info(f"[{tool_name}] [DRY RUN] Would sync 1 record")
                success += 1
                continue

            result = van.upsert_person(**person)
            van_id = result.get("vanId") if result else None
            log.debug(f"[{tool_name}] Synced: {person.get('first_name')} {person.get('last_name')} → VAN ID {van_id}")
            log.info(f"[{tool_name}] Synced VAN ID {van_id}")

            if activist_code_id and van_id:
                van.toggle_activist_code(van_id, activist_code_id, "Apply")

            # ── Optional customizations ───────────────────────────────────────
            # Uncomment and fill in your EA IDs to enable any of the following.
            #
            # Tag volunteers:
            # if van_id and parse_bool(row.get("volunteer_for_partner")):
            #     van.toggle_activist_code(van_id, YOUR_VOLUNTEER_CODE_ID, "Apply")
            #
            # Tag SMS opt-ins (EA has no native SMS field — activist code is the
            # standard workaround):
            # if van_id and parse_bool(row.get("optin_to_partner_smsrobocall")):
            #     van.toggle_activist_code(van_id, YOUR_SMS_OPTIN_CODE_ID, "Apply")
            #
            # Tag registrants who completed the state submission ("finish_with_state"):
            # if van_id and parse_bool(row.get("finish_with_state")):
            #     van.toggle_activist_code(van_id, YOUR_FINISH_WITH_STATE_CODE_ID, "Apply")
            #
            # Record Rocky custom survey responses in EA:
            # Rocky supports two survey question/answer pairs per registration.
            # Map your Rocky question text to your EA survey question ID, and
            # your answer text to your EA survey response ID.
            # survey_answer = row.get("survey_answer_1")
            # if van_id and survey_answer:
            #     van.apply_survey_response(van_id, YOUR_SURVEY_QUESTION_ID,
            #                               YOUR_SURVEY_ANSWER_IDS.get(survey_answer))
            # Repeat for survey_question_2 / survey_answer_2 if needed.
            #
            # Tag by tracking source (useful if you run multiple campaigns):
            # source = row.get("tracking_source")
            # if van_id and source:
            #     van.toggle_activist_code(van_id, YOUR_SOURCE_CODE_IDS.get(source), "Apply")
            #
            # Link the EA contact back to Rocky using the Rocky UID as an external
            # identifier. Useful if you query EA and need to cross-reference Rocky.
            # uid = row.get("rocky_request_id") or row.get("uid")
            # if van_id and uid:
            #     van.upsert_person(vanId=van_id,
            #                       identifiers=[{"type": "rockyId", "externalId": str(uid)}])
            #
            # Store tracking fields as EA custom field values.
            # Replace the integer keys with your actual EA custom field IDs.
            # YOUR_CUSTOM_FIELD_IDS = {
            #     "tracking_source": 11111,
            #     "tracking_id":     22222,
            #     "partner_id":      33333,
            # }
            # custom_fields = []
            # for rocky_field, ea_field_id in YOUR_CUSTOM_FIELD_IDS.items():
            #     val = row.get(rocky_field)
            #     if val:
            #         custom_fields.append({"customFieldId": ea_field_id, "assignedValue": str(val)})
            # if van_id and custom_fields:
            #     van.upsert_person(vanId=van_id, customFieldValues=custom_fields)
            # ─────────────────────────────────────────────────────────────────

            success += 1

        except Exception as e:
            log.error(f"[{tool_name}] Failed to sync {email}: {e}")
            errors += 1

    return success, errors


def run():
    config = load_config()
    dry_run = config.get("dry_run", True)
    tools = config.get("tools", {})

    enabled = [name for name, cfg in tools.items() if cfg.get("enabled", False)]
    if not enabled:
        log.info("No tools enabled in config.yml. Nothing to sync.")
        return

    log.info(f"Tools enabled: {', '.join(enabled)}")

    rtv = RockTheVote(
        partner_id=os.environ["ROCKY_PARTNER_ID"],
        partner_api_key=os.environ["ROCKY_API_KEY"],
    )

    van = VAN(
        api_key=os.environ["EA_API_KEY"],
        db=os.environ.get("EA_DATABASE", "EveryAction"),
    )
    # EA_LOGIN_NAME is the HTTP Basic Auth username (EA calls it the "login name").
    # Parsons defaults to "default" — override it if a login name is provided.
    login_name = os.environ.get("EA_LOGIN_NAME", "default")
    if login_name != "default":
        db_code = van.connection.db_code
        van.connection.api.auth = (login_name, f"{van.connection.api_key}|{db_code}")

    total_success, total_errors = 0, 0

    for tool_name in enabled:
        if tool_name not in TOOL_REPORT_TYPES:
            log.warning(f"Unknown tool '{tool_name}' in config — skipping.")
            continue
        s, e = sync_tool(tool_name, tools[tool_name], rtv, van, dry_run)
        total_success += s
        total_errors += e

    log.info(f"All tools complete — {total_success} synced, {total_errors} errors.")

    if total_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
