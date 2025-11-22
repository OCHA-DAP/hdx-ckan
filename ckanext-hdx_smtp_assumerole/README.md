# ckanext-hdx_smtp_assumerole

CKAN plugin for AWS SES API with AssumeRole support.

## Overview

This plugin enables CKAN to send emails via AWS SES (Simple Email Service) **API** using temporary credentials obtained through AWS STS AssumeRole. It uses the SES API instead of SMTP because SES SMTP does not support session tokens from temporary credentials.

**Why SES API instead of SMTP?**
- SMTP only supports username/password authentication
- Temporary credentials from AssumeRole include access key, secret key, AND session token
- SES SMTP cannot use session tokens → authentication fails with temporary credentials
- SES API supports full temporary credentials including session tokens ✅

This is particularly useful when running CKAN on EC2 instances with instance profiles, following AWS security best practices.

## Pattern

```
EC2 Instance Profile → AssumeRole → Temporary Credentials → SES API (boto3)
```

## Features

- **SES API Not SMTP**: Emails sent via boto3 SES API with full support for session tokens
- **Automatic Credential Refresh**: Credentials auto-refresh when < 5 minutes to expiry (no restart!)
- **Backward Compatible**: Disable `use_assume_role` to use traditional static SMTP credentials
- **Account ID Deduction**: Automatically deduces AWS account ID from STS if only role name provided
- **Per-Container Independent**: Each container manages its own credentials (multi-container setups)
- **Thread-Safe**: Safe for multi-threaded WSGI servers
- **Lazy Loading**: Credentials only refresh when sending email (minimal overhead)
- **Secure**: Uses temporary credentials that expire (default: 1 hour)
- **Patches Both Mailers**: Works with both `ckan.lib.mailer` and `ckanext-hdx_users` mailer

## Email Features

The plugin supports all standard email features through the patched mailers:

### HTML Email Support

Send emails with HTML formatting alongside plain text:

- **Plain text only**: Pass only the `body` parameter (traditional emails)
- **HTML only**: Pass only `body_html` parameter (modern HTML emails)
- **Both versions**: Pass both `body` and `body_html` for multipart/alternative emails (recommended)
  - Email clients that support HTML will show the HTML version
  - Fallback to plain text for simple email clients

**Example:**
```python
# HTML email with plain text fallback
mail_user(
    recipient=user,
    subject='Welcome!',
    body='Welcome to our platform.',
    body_html='<h1>Welcome!</h1><p>Welcome to our platform.</p>'
)
```

### File Attachments

Send emails with file attachments using the `attachments` parameter:

**Format:** List of tuples containing:
- `(filename, file_object)` - media type auto-detected
- `(filename, file_object, media_type)` - explicit media type

**Example:**
```python
with open('report.pdf', 'rb') as f:
    attachments = [
        ('report.pdf', f),  # Auto-detect as application/pdf
        ('data.csv', csv_file, 'text/csv'),  # Explicit media type
    ]
    mail_recipient(
        recipient_name='John Doe',
        recipient_email='john@example.com',
        subject='Monthly Report',
        body='Please find attached the monthly report.',
        attachments=attachments
    )
```

**Limits:**
- Maximum total email size: 10 MB (including all attachments)
- All file types supported by AWS SES
- Attachments are automatically base64 encoded
- Multiple attachments per email supported

### Advanced: Pre-built MIME Messages

For complex email structures (used internally by `ckanext-hdx_users`), you can pass a pre-built MIME message object via the `mime_message` parameter to `send_email_via_ses()`. This is useful for:

- Custom MIME structures
- Complex multipart messages
- Special email headers
- Advanced attachment handling

When `mime_message` is provided, other parameters like `body`, `body_html`, and `subject` are ignored.

**Example:**
```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Build complex MIME message
msg = MIMEMultipart()
msg['From'] = 'sender@example.com'
msg['To'] = 'recipient@example.com'
msg['Subject'] = 'Complex Email'

# Add HTML body
html_part = MIMEText('<html><body><h1>Hello</h1></body></html>', 'html', 'utf-8')
msg.attach(html_part)

# Add attachment
attachment = MIMEBase('application', 'pdf')
attachment.set_payload(pdf_data)
encoders.encode_base64(attachment)
attachment.add_header('Content-Disposition', 'attachment; filename=report.pdf')
msg.attach(attachment)

# Send via SES
send_email_via_ses(
    smtp_from='sender@example.com',
    recipients=['recipient@example.com'],
    subject='Ignored when mime_message provided',
    mime_message=msg,  # Use pre-built message
    access_key=..., secret_key=..., session_token=..., region='us-east-1'
)
```

## Installation

1. Install the plugin:
   ```bash
   cd ckanext-hdx_smtp_assumerole
   pip install -e .
   ```

2. Add to your CKAN plugins list in `.ini` file:
   ```ini
   ckan.plugins = ... hdx_smtp_assumerole
   ```

## Configuration

### With AssumeRole (SES API - recommended for production)

```ini
# Enable SES API with AssumeRole
ckanext.hdx_smtp_assumerole.use_assume_role = true

# Role name (account ID auto-deduced) or full ARN
ckanext.hdx_smtp_assumerole.role_arn = HdxSesSmtpAccessRole
# OR full ARN:
# ckanext.hdx_smtp_assumerole.role_arn = arn:aws:iam::123456789012:role/HdxSesSmtpAccessRole

# AWS region for SES API
ckanext.hdx_smtp_assumerole.region = us-east-1

# Optional: Email domain for default addresses
ckanext.hdx_smtp_assumerole.smtp_domain = humdata.org

# Optional: STS session name (default: ckan-ses-session)
ckanext.hdx_smtp_assumerole.session_name = ckan-ses-session
```

### Without AssumeRole (Static SMTP - legacy/dev environments)

```ini
# Disable AssumeRole (or omit this setting - defaults to false)
ckanext.hdx_smtp_assumerole.use_assume_role = false

# Use traditional SMTP configuration
smtp.server = smtp.example.com:587
smtp.user = your-smtp-username
smtp.password = your-smtp-password
smtp.starttls = true
smtp.mail_from = noreply@example.com
```

### Configuration Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `use_assume_role` | No | `false` | Enable AssumeRole + SES API (false = use static SMTP) |
| `role_arn` | Yes* | - | IAM role name or full ARN for SES access |
| `region` | Yes* | - | AWS region for SES API (e.g., `us-east-1`) |
| `smtp_domain` | No | - | Email domain for default addresses (e.g., `humdata.org`) |
| `session_name` | No | `ckan-ses-session` | STS session name for CloudTrail auditing |

\* Required when `use_assume_role = true`

## AWS Setup

### 1. IAM Role for SES API

Create an IAM role with SES send permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "arn:aws:ses:us-east-1:123456789012:identity/humdata.org"
    }
  ]
}
```

### 2. EC2 Instance Profile Trust Policy

The SES role must trust your EC2 instance profile:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::123456789012:role/YourEC2InstanceRole",
          "arn:aws:iam::123456789012:role/YourDevServerRole"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### 3. EC2 Instance Profile Assume Permission

Your EC2 instance profile needs permission to assume the SES role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::123456789012:role/HdxSesSmtpAccessRole"
    }
  ]
}
```

### 4. SES Configuration

1. Verify your email domain or addresses in AWS SES
2. If in sandbox mode, verify recipient addresses
3. Request production access for sending to any email address
4. Add appropriate sending authorization policies to SES domain identity

## How It Works

### Initial Startup (AssumeRole Enabled)

1. **Plugin Initialization**: CKAN loads the plugin at startup
2. **Check Config**: Verifies `use_assume_role = true` and required settings
3. **AssumeRole**: Uses EC2 instance profile to assume the configured IAM role
4. **Get Credentials**: Receives temporary credentials (access key + secret key + session token)
5. **Monkey Patch Mailers**: Patches email senders to use SES API instead of SMTP:
   - `ckan.lib.mailer.mail_user` → uses SES API
   - `ckan.lib.mailer.mail_recipient` → uses SES API
   - `ckanext.hdx_users.helpers.mailer._mail_recipient_html` → uses SES API

### Sending Email

When CKAN sends an email:

1. **Intercept**: Patched mailer function is called
2. **Check Expiry**: Checks if credentials expire in < 5 minutes
3. **Auto-Refresh**: If expiring soon, automatically calls AssumeRole for fresh credentials
4. **Build Message**: Constructs MIME email message
5. **Send via SES API**: Calls `boto3.client('ses').send_raw_email()` with temporary credentials
6. **Fallback**: If SES API fails, falls back to original SMTP mailer

### Automatic Refresh (No Restart Needed!)

- **5-minute buffer**: Credentials auto-refresh when < 5 min to expiry
- **Lazy refresh**: Only happens when sending email (minimal overhead)
- **Thread-safe**: Uses RLock for atomic credential updates
- **Per-container**: Each container refreshes independently
- **No restart**: Transparent refresh in background

### Multi-Container Setups

For 3 servers × 3 containers (ckan, api, jobs) = 9 containers:
- Each container loads initial credentials at startup (9 AssumeRole calls)
- Each container refreshes independently every ~55 minutes when sending email
- No coordination or shared state between containers
- Well within AWS STS API limits

## Security Considerations

- ✅ Uses temporary credentials (expire after 1 hour by default)
- ✅ No long-term credentials stored in config files
- ✅ Leverages EC2 instance profiles and IAM roles
- ✅ Automatic refresh prevents expired credentials
- ✅ Thread-safe atomic updates
- ✅ Per-container independent operation
- ✅ Session tokens included in SES API calls (not possible with SMTP)

## Backward Compatibility

The plugin is fully backward compatible:

- **`use_assume_role = false`** (or not set): Uses traditional SMTP with static credentials
- **`use_assume_role = true`**: Uses SES API with AssumeRole temporary credentials

This allows:
- Production: AssumeRole + SES API
- Demo/Dev: Static SMTP credentials
- Gradual migration without breaking changes

## Troubleshooting

### Plugin fails at startup

Check logs:
```bash
tail -f /var/log/ckan/ckan.log | grep hdx_smtp_assumerole
```

Common issues:
- IAM role doesn't exist or is not accessible
- EC2 instance profile lacks permission to assume role
- Region is incorrect or SES not available in that region
- Missing required config parameters

### Email not sending

1. Check SES sending limits and sandbox status
2. Verify email domain/addresses in AWS SES console
3. Check CKAN logs for SES API errors
4. Verify IAM role has `ses:SendRawEmail` permission
5. Check SES domain identity policies

### Permission denied errors

Ensure:
- EC2 instance has an instance profile attached
- Instance profile can assume the SES role (`sts:AssumeRole`)
- SES role has `ses:SendEmail` and `ses:SendRawEmail` permissions
- SES domain identity policy allows the role to send

### Credentials expired

Should not happen with auto-refresh enabled. If it does:
- Check logs for refresh errors
- Verify STS AssumeRole is working
- Restart CKAN to reload credentials

## Environment Variables vs Config File

For Docker deployments, use environment variables in your `.ini` template:

```ini
ckanext.hdx_smtp_assumerole.use_assume_role = ${HDX_SMTP_USE_ASSUME_ROLE}
ckanext.hdx_smtp_assumerole.role_arn = ${HDX_SMTP_ASSUME_ROLE}
ckanext.hdx_smtp_assumerole.region = ${REGION_NAME}
ckanext.hdx_smtp_assumerole.smtp_domain = ${HDX_SMTP_DOMAIN}
```

## License

AGPLv3

## Authors

HDX Team - OCHA Centre for Humanitarian Data

## Related Documentation

- [AWS SES API Documentation](https://docs.aws.amazon.com/ses/latest/APIReference/API_SendRawEmail.html)
- [AWS STS AssumeRole](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html)
- [Why SES SMTP doesn't work with temporary credentials](https://docs.aws.amazon.com/ses/latest/dg/smtp-credentials.html)
- [Boto3 SES Client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses.html)
