# SEC-021: Self-Service Signup Deployment Checklist

**Last Updated:** 2025-12-01
**Status:** Ready for Configuration
**Engineer:** OW-KAI Platform Team

---

## Executive Summary

The self-service signup flow is **code-complete** and ready for production deployment. This checklist covers the AWS and third-party service configurations needed for go-live.

---

## Pre-Deployment Checklist

### 1. AWS SES Production Access (CRITICAL)

**Current Status:** Sandbox Mode (200 emails/day, only to verified addresses)

**Required for Production:** Send to any email address

#### Step 1.1: Request Production Access
```bash
# In AWS Console:
# 1. Go to SES > Account dashboard
# 2. Click "Request production access"
# 3. Fill out the form:
#    - Mail type: Transactional
#    - Website URL: https://ascendowkai.com
#    - Use case: Customer email verification, welcome emails, notifications
#    - How addresses are acquired: Self-service signup (opt-in)
#    - Complaints handling: bounce-handling@ow-kai.com
```

**Approval Time:** Usually 24-48 hours

#### Step 1.2: Verify Domain (Recommended)
```bash
# Verify ow-kai.com domain for better deliverability
aws ses verify-domain-identity --domain ow-kai.com --region us-east-2

# Add the DKIM and SPF records to DNS
aws ses get-identity-dkim-attributes --identities ow-kai.com --region us-east-2
```

#### Step 1.3: Set Up Bounce/Complaint Handling
```bash
# Create SNS topic for bounces
aws sns create-topic --name ses-bounces --region us-east-2

# Create SNS topic for complaints
aws sns create-topic --name ses-complaints --region us-east-2

# Link to SES
aws ses set-identity-notification-topic \
  --identity ow-kai.com \
  --notification-type Bounce \
  --sns-topic arn:aws:sns:us-east-2:ACCOUNT_ID:ses-bounces
```

**Verification Command:**
```bash
aws ses get-send-quota --region us-east-2
# Should show Max24HourSend > 200 when approved
```

---

### 2. Google reCAPTCHA v3 Setup

#### Step 2.1: Create reCAPTCHA Site
1. Go to: https://www.google.com/recaptcha/admin/create
2. Choose **reCAPTCHA v3**
3. Add domains:
   - `ascendowkai.com`
   - `pilot.owkai.app`
   - `localhost` (for development)
4. Accept terms and submit

#### Step 2.2: Get Keys
- **Site Key** (public): Goes in frontend
- **Secret Key** (private): Goes in backend

#### Step 2.3: Configure Frontend
Edit `/owkai-pilot-frontend/.env.production`:
```env
VITE_RECAPTCHA_SITE_KEY=6LcXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

#### Step 2.4: Configure Backend
Add to ECS Task Definition environment variables or Secrets Manager:
```env
RECAPTCHA_SECRET_KEY=6LcXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Verification Command:**
```bash
# Test reCAPTCHA verification
curl -X POST "https://www.google.com/recaptcha/api/siteverify" \
  -d "secret=YOUR_SECRET_KEY" \
  -d "response=TEST_TOKEN"
```

---

### 3. AWS Cognito Permissions

The signup flow creates Cognito user pools dynamically. Ensure the ECS task role has these permissions:

#### Step 3.1: IAM Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CognitoPoolProvisioning",
      "Effect": "Allow",
      "Action": [
        "cognito-idp:CreateUserPool",
        "cognito-idp:CreateUserPoolClient",
        "cognito-idp:CreateUserPoolDomain",
        "cognito-idp:UpdateUserPool",
        "cognito-idp:DeleteUserPool",
        "cognito-idp:DeleteUserPoolClient",
        "cognito-idp:DeleteUserPoolDomain",
        "cognito-idp:DescribeUserPool",
        "cognito-idp:ListUserPools",
        "cognito-idp:AdminCreateUser",
        "cognito-idp:AdminSetUserPassword",
        "cognito-idp:AdminInitiateAuth",
        "cognito-idp:AdminRespondToAuthChallenge"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Step 3.2: Attach to ECS Task Role
```bash
aws iam attach-role-policy \
  --role-name owkai-ecs-task-role \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/CognitoPoolProvisioning
```

---

### 4. Environment Variables

#### Backend (ECS Task Definition)

| Variable | Description | Required |
|----------|-------------|----------|
| `RECAPTCHA_SECRET_KEY` | Google reCAPTCHA v3 secret | Yes |
| `FRONTEND_URL` | Frontend URL for emails | Yes |
| `AWS_REGION` | AWS region for SES/Cognito | Yes |

#### Frontend (Build-time)

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_RECAPTCHA_SITE_KEY` | Google reCAPTCHA v3 site key | Yes |
| `VITE_API_URL` | Backend API URL | Yes |

---

### 5. Database Migration

Ensure the signup tables are created:
```bash
cd /path/to/ow-ai-backend
alembic upgrade head
```

Tables created:
- `signup_requests`
- `signup_attempts`
- `disposable_email_domains`
- `email_verification_audits`
- `admin_invitations`
- `subscription_tiers`

---

### 6. Testing Checklist

#### 6.1: Unit Tests
- [ ] Signup form validation
- [ ] Email verification flow
- [ ] Rate limiting (5/IP/hour)
- [ ] Disposable email detection
- [ ] Fraud scoring algorithm

#### 6.2: Integration Tests
- [ ] Full signup → verify → login flow
- [ ] Email delivery (use verified address first)
- [ ] Cognito pool creation
- [ ] Organization creation

#### 6.3: E2E Tests
- [ ] Complete customer journey
- [ ] Mobile responsiveness
- [ ] Error handling UX
- [ ] Resend verification

---

### 7. Monitoring Setup

#### 7.1: CloudWatch Alarms
```bash
# SES bounce rate alarm (PCI-DSS requirement)
aws cloudwatch put-metric-alarm \
  --alarm-name "SES-HighBounceRate" \
  --metric-name "Bounce" \
  --namespace "AWS/SES" \
  --statistic "Sum" \
  --period 3600 \
  --evaluation-periods 1 \
  --threshold 50 \
  --comparison-operator "GreaterThanThreshold"
```

#### 7.2: Signup Metrics
- Signups per day
- Verification rate
- Drop-off by step
- Fraud block rate

---

## Go-Live Steps

### Phase 1: Staging Deployment
1. Deploy code to staging
2. Configure staging reCAPTCHA
3. Test with verified email addresses
4. Verify Cognito pool creation

### Phase 2: Production Preparation
1. Request SES production access
2. Wait for approval (24-48 hours)
3. Configure production reCAPTCHA
4. Add Cognito IAM permissions

### Phase 3: Production Deployment
1. Deploy backend with env vars
2. Deploy frontend with env vars
3. Run database migration
4. Test with internal email first

### Phase 4: Public Launch
1. Update marketing site with signup link
2. Monitor metrics dashboard
3. Watch for fraud attempts
4. Scale as needed

---

## Rollback Plan

If issues occur:
1. Disable signup button on frontend
2. Return HTTP 503 on `/api/signup` endpoint
3. Investigate logs
4. Fix and redeploy

---

## Support Contacts

- **AWS SES Issues:** AWS Support
- **reCAPTCHA Issues:** Google Cloud Console
- **Cognito Issues:** AWS Support
- **Application Issues:** Internal team

---

## Compliance Notes

| Regulation | Requirement | Implementation |
|------------|-------------|----------------|
| GDPR | Explicit consent | Terms checkbox required |
| GDPR | Right to deletion | Status can be set to "deleted" |
| SOC 2 | Audit trail | `email_verification_audits` table |
| PCI-DSS | Secure storage | Tokens SHA-256 hashed |
| HIPAA | PHI protection | No PHI in signup flow |

---

## Quick Reference Commands

```bash
# Check SES status
aws ses get-send-quota --region us-east-2

# Check recent signups
SELECT email, status, created_at
FROM signup_requests
ORDER BY created_at DESC
LIMIT 10;

# Check fraud blocks
SELECT email, fraud_score, fraud_flags
FROM signup_requests
WHERE status = 'blocked'
ORDER BY created_at DESC;

# Check verification rate
SELECT
  status,
  COUNT(*) as count
FROM signup_requests
GROUP BY status;
```

---

**Document Version:** 1.0
**Prepared By:** Claude Code
**Approved By:** _________________
**Date:** _________________
