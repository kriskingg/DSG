# Beest Cloud Deployment Guide (GitHub Actions Only)

This guide explains how to run Beest entirely in GitHub Actions (no local runs). It covers prerequisites, secrets, enabling workflows, deploying, monitoring, and best practices.

---

## 1) Required Accounts and Credentials

To operate Beest in the cloud, ensure you have:

- GitHub repository access: admin/maintainer to configure Actions and Secrets
- AWS account (DynamoDB):
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - AWS_DEFAULT_REGION (e.g., ap-south-1)
  - DynamoDB tables created per your schema (stock data, transaction history)
- Trading platform account with API access:
  - TRADING_API_KEY
  - Any additional required credentials for the broker SDK you use
- Two-Factor Auth (TOTP):
  - TOTP_SECRET (raw base32 secret used to generate one-time codes)

Optional (if used by your setup):
- Notification/alert service keys (Slack/Webhook/Email) – not required by default

Security reminders:
- Use least-privilege AWS IAM user for DynamoDB (table-specific permissions only)
- Never commit secrets to the repo; store them as GitHub Secrets only

---

## 2) Set Up GitHub Secrets

GitHub Secrets are required for workflows to authenticate. In your repository:

1. Go to: Settings > Secrets and variables > Actions > New repository secret
2. Create the following secrets:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_DEFAULT_REGION (e.g., ap-south-1)
   - TRADING_API_KEY
   - TOTP_SECRET
3. If your code expects any other environment variables, add them here as secrets

Reference in workflows (example):

- name: Export secrets
  run: |
    echo "AWS_DEFAULT_REGION=${{ secrets.AWS_DEFAULT_REGION }}" >> $GITHUB_ENV
  shell: bash

Most official actions accept secrets via env: or with: blocks. Never echo secrets to logs.

---

## 3) Enable and Configure GitHub Actions Workflows

The repository includes workflows under .github/workflows/:
- Trade_Script_with_DB.yml – Production trading run (scheduled market hours)
- additional_quantity_logic.yml – Logic tests (manual)
- login_with_generated_totp.yml – Auth/TOTP checks (scheduled + manual)

Steps to enable:
1. Navigate to the repo > Actions tab
2. If workflows are commented out for safety, open each YAML and uncomment relevant jobs/steps (via PR)
3. Ensure each workflow references the required secrets in env: or with:
4. Confirm schedules (cron) match your market hours (e.g., 3:45 AM UTC for 9:15 AM IST)

Cron example (Mon–Fri, 9:15 AM IST):

schedule:
  - cron: '45 3 * * 1-5'

Note: GitHub Actions cron uses UTC time.

---

## 4) Cloud-Only Deployment Steps (No Local Runs)

Follow this sequence to deploy and run solely in GitHub Actions:

A. Prepare Infrastructure (one-time)
- In AWS, create DynamoDB tables required by Beest:
  - Table 1: stock data (partition/sort keys per your code)
  - Table 2: transaction history
  - Add GSIs if referenced in code
- Create an IAM user restricted to these tables. Generate access key/secret.

B. Configure Repo
- Add all required secrets (Section 2)
- Verify requirements.txt includes all dependencies
- Review rupeezy_instruments_list.txt and strategy thresholds in code

C. Enable Workflows
- In .github/workflows/, ensure the following are enabled as desired:
  - login_with_generated_totp.yml: to continuously validate auth
  - Trade_Script_with_DB.yml: production trading during market hours
  - additional_quantity_logic.yml: manual test of threshold logic

D. Dry Runs (Safe Validation)
- Run login_with_generated_totp.yml manually (Actions > select workflow > Run workflow)
- Review logs to ensure TOTP generation and session handling are healthy
- Optionally run additional_quantity_logic.yml for logic verification (no real trades)

E. Production Scheduling
- Confirm Trade_Script_with_DB.yml schedule aligns with market hours and holidays
- Merge the uncommented/updated workflow to main
- The bot will run automatically at the scheduled times without any local machine

F. Manual Dispatch (Optional)
- For ad-hoc runs (testing windows), use workflow_dispatch if defined in the YAML

---

## 5) Monitor, Manage, and Review Runs

Monitoring in GitHub:
- Actions tab: view current/previous workflow runs
- Click a run to see logs for each job/step
- Use job summary annotations to identify failures quickly

Operational checks:
- DynamoDB: confirm records are written/updated for prices, eligibility, and executed orders
- Broker platform: verify orders (in paper/sandbox first, then live)

Handling failures:
- Open the failed run > Review step logs and stack traces
- Common causes: invalid TOTP, expired API keys, denied IAM permissions, rate limits
- Fix configuration/secrets, then re-run failed jobs or re-dispatch the workflow

Auditing and history:
- Use Actions run history to analyze patterns
- Export logs (download artifacts if configured) for archival

Alerting (optional):
- Add steps to send Slack/Webhook notifications on failure/success
- Use actions/upload-artifact for key logs/outputs

---

## 6) Best Practices and Safety Reminders

Safety first:
- Start in paper trading/sandbox; only switch to live trading after extensive validation
- Keep Trade_Script_with_DB.yml commented or behind a feature flag until ready
- Implement maximum position size, per-stock limits, and kill switches in code

Secrets and IAM hygiene:
- Rotate TOTP_SECRET (if broker supports regeneration) and API keys periodically
- Restrict IAM to only the necessary DynamoDB tables and actions
- Never print secrets; mask sensitive outputs

Reliability:
- Add retries with backoff for network/API calls
- Validate broker session before placing orders
- Log key decisions (threshold hit, quantities, order IDs) without exposing secrets

Observability:
- Use clear logging and step names in workflows
- Capture important run metadata as artifacts (e.g., executed orders CSV/JSON)
- Consider CloudWatch metric filters if routing logs to AWS

Change management:
- Test logic changes via additional_quantity_logic.yml
- Use PRs and required reviews before enabling production changes
- Update schedules for market holidays or maintenance windows

Compliance and risk:
- Understand and obey local regulations
- Do not exceed capital/risk limits
- Trading involves substantial risk of loss; use at your own discretion

---

## Quick Reference: Secrets Mapping

Required GitHub Secrets and typical usage:
- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION -> AWS auth for DynamoDB
- TRADING_API_KEY -> Broker API auth
- TOTP_SECRET -> 2FA code generation for login

Example env wiring in a job:

jobs:
  run-beest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Set env
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: ${{ secrets.AWS_DEFAULT_REGION }}
          TRADING_API_KEY: ${{ secrets.TRADING_API_KEY }}
          TOTP_SECRET: ${{ secrets.TOTP_SECRET }}
        run: |
          echo "Environment set"
      - name: Run Beest
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: ${{ secrets.AWS_DEFAULT_REGION }}
          TRADING_API_KEY: ${{ secrets.TRADING_API_KEY }}
          TOTP_SECRET: ${{ secrets.TOTP_SECRET }}
        run: python rupeezy/main.py

---

If you follow this guide, Beest will run fully in GitHub Actions without any local execution.
