# Environment Variables for SES API AssumeRole

This document describes the environment variables needed to configure the SES API AssumeRole plugin.

## Key Features

- **SES API Not SMTP**: Uses boto3 SES API (supports temporary credentials with session tokens)
- **Automatic Credential Refresh**: Credentials refresh automatically when < 5 minutes to expiry
- **No Restart Required**: CKAN continues running indefinitely with auto-refreshed credentials
- **Per-Container Independent**: Each container manages its own credentials (perfect for multi-container deployments)
- **Backward Compatible**: Disable to use traditional static SMTP credentials

## Required Environment Variables (when AssumeRole is enabled)

These variables should be set in your Terraform configuration or Docker environment:

### Core Configuration

| Variable | Required | Default | Example | Description |
|----------|----------|---------|---------|-------------|
| `HDX_SMTP_USE_ASSUME_ROLE` | No | `false` | `true` | Enable AssumeRole + SES API (false = use static SMTP) |
| `HDX_SMTP_ASSUME_ROLE` | Yes* | - | `HdxSesSmtpAccessRole` | IAM role name (account ID auto-deduced) or full ARN |
| `REGION_NAME` | Yes* | - | `us-east-1` | AWS region for SES API |
| `HDX_SMTP_DOMAIN` | No | - | `humdata.org` | Email domain for default addresses |

\* Required when `HDX_SMTP_USE_ASSUME_ROLE=true`

### Removed Variables (No Longer Used)

These variables are **NOT** used when AssumeRole is enabled (SES API mode):

- ~~`HDX_SMTP_SES_SERVER`~~ - Not needed, SES API doesn't use SMTP endpoints
- ~~`HDX_SMTP_PORT`~~ - Not needed, SES API doesn't use ports
- ~~`smtp.server`~~ - Not overridden, SES API bypasses SMTP
- ~~`smtp.user`~~ - Not overridden, SES API uses temporary credentials directly
- ~~`smtp.password`~~ - Not overridden, SES API uses AWS signature

## Backward Compatibility (Static SMTP)

When `HDX_SMTP_USE_ASSUME_ROLE=false` or not set, traditional SMTP variables are used:

| Variable | Description |
|----------|-------------|
| `HDX_SMTP_ADDR` | SMTP server address |
| `HDX_SMTP_PORT` | SMTP port |
| `HDX_SMTP_USER` | SMTP username |
| `HDX_SMTP_PASS` | SMTP password |
| `HDX_SMTP_TLS` | Enable TLS/STARTTLS |
| `HDX_SMTP_DOMAIN` | Email domain |

## How It Works

### With AssumeRole Enabled (SES API)

1. Plugin loads at CKAN startup
2. Calls STS AssumeRole to get temporary credentials (access key + secret key + session token)
3. Monkey patches email senders to use SES API instead of SMTP
4. When sending email:
   - Checks if credentials expire in < 5 minutes
   - Auto-refreshes if needed (calls AssumeRole again)
   - Calls `boto3.client('ses').send_raw_email()` with temporary credentials
   - Falls back to SMTP if SES API fails

### With AssumeRole Disabled (Static SMTP)

1. Plugin checks `use_assume_role = false`
2. Exits early without patching
3. CKAN uses standard SMTP with static credentials from config
4. No SES API calls, no AssumeRole

## Example Terraform Configuration

```hcl
# Enable SES API with AssumeRole
resource "aws_ssm_parameter" "smtp_use_assume_role" {
  name  = "/ckan/smtp/use_assume_role"
  type  = "String"
  value = "true"
}

# IAM Role name (account ID will be deduced automatically)
resource "aws_ssm_parameter" "smtp_assume_role" {
  name  = "/ckan/smtp/assume_role"
  type  = "String"
  value = "HdxSesSmtpAccessRole"
}

# AWS Region for SES API
resource "aws_ssm_parameter" "region_name" {
  name  = "/ckan/region_name"
  type  = "String"
  value = "us-east-1"
}

# Email Domain
resource "aws_ssm_parameter" "smtp_domain" {
  name  = "/ckan/smtp/domain"
  type  = "String"
  value = "humdata.org"
}
```

## Example Docker Environment

```bash
# docker-compose.yml or similar
environment:
  - HDX_SMTP_USE_ASSUME_ROLE=true
  - HDX_SMTP_ASSUME_ROLE=HdxSesSmtpAccessRole
  - REGION_NAME=us-east-1
  - HDX_SMTP_DOMAIN=humdata.org
```

## IAM Permissions Required

### EC2 Instance Profile

The EC2 instance running CKAN needs permission to assume the SES role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::YOUR_ACCOUNT_ID:role/HdxSesSmtpAccessRole"
    }
  ]
}
```

### Target SES Role

The role being assumed needs SES API permissions and trust relationship:

**SES Permissions:**
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
      "Resource": "arn:aws:ses:us-east-1:YOUR_ACCOUNT_ID:identity/humdata.org"
    }
  ]
}
```

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::YOUR_ACCOUNT_ID:role/YourEC2InstanceRole",
          "arn:aws:iam::YOUR_ACCOUNT_ID:role/YourDevServerRole"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Auto-Refresh in Multi-Container Deployments

### How It Works

In a typical HDX deployment with multiple servers and containers:

```
Server 1:               Server 2:               Server 3:
├─ ckan (UI)           ├─ ckan (UI)           ├─ ckan (UI)
├─ api (/api reqs)     ├─ api (/api reqs)     ├─ api (/api reqs)
└─ jobs (RQ worker)    └─ jobs (RQ worker)    └─ jobs (RQ worker)
```

**Each container independently:**
1. Loads initial credentials at startup via AssumeRole
2. Stores credentials in memory (no shared state)
3. Checks expiry before sending each email
4. Refreshes automatically if < 5 minutes to expiry
5. Uses thread-safe RLock for atomic updates

**Benefits:**
- No coordination needed between containers
- No distributed locks
- No shared state (Redis, database, etc.)
- Each container can refresh at different times
- Scales horizontally without issues

**AssumeRole Call Frequency:**

For 9 containers (3 servers × 3 containers):
- **Startup**: 9 AssumeRole calls
- **Hourly refresh**: ~9 calls (when credentials near expiry and email is sent)
- **Daily total**: ~225 AssumeRole calls
- **AWS STS limits**: 5,000 requests/second (plenty of headroom)

## Testing

### Verify Configuration

1. Check CKAN logs at startup:
```bash
tail -f /var/log/ckan/ckan.log | grep hdx_smtp_assumerole
```

Expected output at startup:
```
INFO [ckanext.hdx_smtp_assumerole.plugin] SES API with AssumeRole enabled: region=us-east-1, role=HdxSesSmtpAccessRole, expires=2025-01-12 15:30:00+00:00
```

When sending email:
```
INFO [ckanext.hdx_smtp_assumerole.helpers.ses_sender] Email sent via SES API to ['user@example.com'], MessageId: 0100018d1234abcd-12345678-1234-1234-1234-123456789abc-000000
```

2. Test email sending from CKAN admin interface or via API

### Common Issues

**"Role name or ARN is required"**
- Set `HDX_SMTP_ASSUME_ROLE` environment variable

**"Failed to get AWS account ID from STS"**
- EC2 instance doesn't have instance profile
- Instance profile lacks EC2 metadata access

**"Failed to assume role"**
- EC2 instance profile can't assume the target role
- Check trust policy on target role
- Check AssumeRole permission on instance profile

**"Email not sending via SES API"**
- Check SES configuration (sandbox mode, verified domains)
- Check logs for credential refresh errors
- Verify SES sending limits
- Check SES domain identity policies
- Verify IAM role has `ses:SendRawEmail` permission

## Migration from Static SMTP to SES API

To migrate from static SMTP credentials to AssumeRole + SES API:

1. **Setup IAM roles and permissions** (see above)
2. **Test on dev/demo environment first**
3. **Set new environment variables**:
   ```
   HDX_SMTP_USE_ASSUME_ROLE=true
   HDX_SMTP_ASSUME_ROLE=HdxSesSmtpAccessRole
   REGION_NAME=us-east-1
   HDX_SMTP_DOMAIN=humdata.org
   ```
4. **Keep old SMTP variables** for backward compatibility during testing
5. **Restart CKAN** (one-time restart for migration)
6. **Verify** email functionality
7. **Monitor logs** for auto-refresh and SES API calls
8. **Remove old SMTP credentials** from environment/secrets after verification
9. **Enjoy** - no more restarts needed for credential rotation!

## Rollback Plan

If issues arise, simply set:
```
HDX_SMTP_USE_ASSUME_ROLE=false
```

And restart CKAN. It will fall back to using traditional SMTP with static credentials.

## Security Benefits

✅ **No long-term credentials** stored in config files or environment
✅ **Automatic rotation** (credentials expire after 1 hour)
✅ **Auto-refresh** (credentials refresh automatically before expiry)
✅ **No restart required** (CKAN runs indefinitely without manual intervention)
✅ **Least privilege** (role has only SES API permissions)
✅ **Session tokens** (full temporary credential support via SES API)
✅ **Audit trail** (CloudTrail logs all AssumeRole and SES API calls)
✅ **Easy revocation** (update trust policy to revoke access)
✅ **Per-container isolation** (no shared credentials between containers)
✅ **Thread-safe** (atomic credential updates prevent race conditions)
