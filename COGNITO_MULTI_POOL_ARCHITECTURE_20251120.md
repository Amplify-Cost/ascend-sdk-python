# AWS Cognito Multi-Pool Architecture - ENTERPRISE ISOLATION

**Date**: November 20, 2025
**Engineer**: OW-KAI Engineer
**Status**: 🚧 **CRITICAL ARCHITECTURE CHANGE REQUIRED**
**Security Level**: MAXIMUM (Dedicated pools per organization)

---

## 🚨 CRITICAL SECURITY REQUIREMENT

**Current Architecture**: Single shared user pool for all organizations
**Required Architecture**: Dedicated user pool per organization/tenant
**Reason**: Highly regulated customers require complete data isolation

---

## 🛡️ SECURITY RATIONALE

### Why Dedicated User Pools Per Organization:

1. **Regulatory Compliance**:
   - HIPAA: PHI must be in separate AWS accounts/pools
   - PCI-DSS: Cardholder data isolation required
   - GDPR: Data residency and isolation requirements
   - SOC 2: Logical separation of customer data

2. **Data Isolation**:
   - No shared infrastructure between tenants
   - Complete authentication isolation
   - Separate encryption keys per pool
   - Independent backup and recovery

3. **Security Boundaries**:
   - Cognito admin APIs can't cross pools
   - IAM policies per organization
   - CloudTrail logs per pool
   - Separate threat detection

4. **Regulatory Audits**:
   - Each org can audit their own pool
   - No access to other org's auth data
   - Clear ownership boundaries
   - Independent security assessments

5. **Compliance Certification**:
   - Easier to certify per-org infrastructure
   - Attestation letters per customer
   - Independent compliance audits
   - Customer-specific controls

---

## 🏗️ ARCHITECTURE COMPARISON

### ❌ CURRENT: Single Shared Pool (NOT COMPLIANT)

```
┌─────────────────────────────────────┐
│   AWS Cognito User Pool            │
│   us-east-2_HPew14Rbn               │
│                                     │
│   Users:                            │
│   - platform-admin@owkai.com (Org 1)│
│   - pilot-admin@example.com (Org 2) │
│   - growth-admin@example.com (Org 3)│
│                                     │
│   Custom Attributes:                │
│   - organization_id                 │
│   - organization_slug               │
│                                     │
│   ⚠️  All orgs share same pool      │
│   ⚠️  Logical separation only       │
│   ⚠️  Not compliant for regulated   │
└─────────────────────────────────────┘
```

### ✅ REQUIRED: Dedicated Pools Per Organization

```
Organization 1 (OW-AI Internal - Platform Owner)
┌─────────────────────────────────────┐
│   AWS Cognito User Pool - Org 1    │
│   us-east-2_POOL1xxxxx              │
│                                     │
│   Users:                            │
│   - platform-admin@owkai.com        │
│   - admin2@owkai.com                │
│                                     │
│   ✅ Dedicated pool                 │
│   ✅ Complete isolation             │
│   ✅ Org-specific policies          │
└─────────────────────────────────────┘

Organization 2 (Customer Pilot Tier)
┌─────────────────────────────────────┐
│   AWS Cognito User Pool - Org 2    │
│   us-east-2_POOL2xxxxx              │
│                                     │
│   Users:                            │
│   - pilot-admin@example.com         │
│   - user1@pilot-org.com             │
│                                     │
│   ✅ Dedicated pool                 │
│   ✅ Customer-owned data            │
│   ✅ Independent security           │
└─────────────────────────────────────┘

Organization 3 (Customer Growth Tier)
┌─────────────────────────────────────┐
│   AWS Cognito User Pool - Org 3    │
│   us-east-2_POOL3xxxxx              │
│                                     │
│   Users:                            │
│   - growth-admin@example.com        │
│   - user1@growth-org.com            │
│                                     │
│   ✅ Dedicated pool                 │
│   ✅ Customer-owned data            │
│   ✅ Independent security           │
└─────────────────────────────────────┘
```

---

## 📋 IMPLEMENTATION PLAN

### Phase 1: Database Schema Changes

**Add to `organizations` table**:
```sql
ALTER TABLE organizations ADD COLUMN cognito_user_pool_id VARCHAR(255);
ALTER TABLE organizations ADD COLUMN cognito_app_client_id VARCHAR(255);
ALTER TABLE organizations ADD COLUMN cognito_domain VARCHAR(255);
ALTER TABLE organizations ADD COLUMN cognito_region VARCHAR(50) DEFAULT 'us-east-2';
ALTER TABLE organizations ADD COLUMN cognito_pool_created_at TIMESTAMP;

-- Index for lookups
CREATE INDEX idx_organizations_cognito_pool ON organizations(cognito_user_pool_id);
```

**Example Data**:
```sql
-- Organization 1 (OW-AI Internal)
UPDATE organizations SET
  cognito_user_pool_id = 'us-east-2_POOL1xxxxx',
  cognito_app_client_id = 'CLIENT1xxxxx',
  cognito_domain = 'owai-internal-auth',
  cognito_region = 'us-east-2',
  cognito_pool_created_at = NOW()
WHERE id = 1;

-- Organization 2 (Pilot Customer)
UPDATE organizations SET
  cognito_user_pool_id = 'us-east-2_POOL2xxxxx',
  cognito_app_client_id = 'CLIENT2xxxxx',
  cognito_domain = 'pilot-customer-auth',
  cognito_region = 'us-east-2',
  cognito_pool_created_at = NOW()
WHERE id = 2;
```

---

### Phase 2: Cognito Pool Provisioning Service

**File**: `ow-ai-backend/services/cognito_pool_provisioner.py`

```python
import boto3
import logging
from typing import Dict, Any

logger = logging.getLogger("enterprise.cognito.provisioner")

class CognitoPoolProvisioner:
    """
    Enterprise Cognito Pool Provisioning Service

    Creates dedicated Cognito user pools for each organization.
    Required for HIPAA, PCI-DSS, SOC 2 compliance.
    """

    def __init__(self):
        self.cognito_client = boto3.client('cognito-idp', region_name='us-east-2')

    async def create_organization_pool(
        self,
        organization_id: int,
        organization_name: str,
        organization_slug: str,
        admin_email: str
    ) -> Dict[str, Any]:
        """
        Create dedicated Cognito user pool for organization

        Returns:
            {
                'user_pool_id': 'us-east-2_xxxxx',
                'app_client_id': 'xxxxx',
                'domain': 'org-slug-auth'
            }
        """

        try:
            logger.info(f"🔐 Creating dedicated Cognito pool for org {organization_id}")

            # Create User Pool
            pool_response = self.cognito_client.create_user_pool(
                PoolName=f"owkai-{organization_slug}",
                Policies={
                    'PasswordPolicy': {
                        'MinimumLength': 12,
                        'RequireUppercase': True,
                        'RequireLowercase': True,
                        'RequireNumbers': True,
                        'RequireSymbols': True,
                        'TemporaryPasswordValidityDays': 7
                    }
                },
                MfaConfiguration='OPTIONAL',
                AutoVerifiedAttributes=['email'],
                AccountRecoverySetting={
                    'RecoveryMechanisms': [
                        {'Name': 'verified_email', 'Priority': 1}
                    ]
                },
                Schema=[
                    {
                        'Name': 'email',
                        'AttributeDataType': 'String',
                        'Required': True,
                        'Mutable': True
                    },
                    {
                        'Name': 'organization_id',
                        'AttributeDataType': 'Number',
                        'Mutable': False,
                        'DeveloperOnlyAttribute': False
                    },
                    {
                        'Name': 'role',
                        'AttributeDataType': 'String',
                        'Mutable': True,
                        'StringAttributeConstraints': {
                            'MinLength': '1',
                            'MaxLength': '50'
                        }
                    }
                ],
                UserPoolTags={
                    'Environment': 'production',
                    'Organization': organization_slug,
                    'OrganizationId': str(organization_id),
                    'ManagedBy': 'OW-AI-Platform',
                    'Compliance': 'HIPAA-SOC2-PCI-GDPR'
                }
            )

            user_pool_id = pool_response['UserPool']['Id']
            logger.info(f"✅ User pool created: {user_pool_id}")

            # Create App Client
            client_response = self.cognito_client.create_user_pool_client(
                UserPoolId=user_pool_id,
                ClientName=f"owkai-{organization_slug}-web-app",
                GenerateSecret=False,  # Public client (web app)
                ExplicitAuthFlows=[
                    'ALLOW_USER_REDACTED-CREDENTIAL_AUTH',
                    'ALLOW_REFRESH_TOKEN_AUTH',
                    'ALLOW_USER_SRP_AUTH'
                ],
                PreventUserExistenceErrors='ENABLED',
                ReadAttributes=['email', 'email_verified', 'custom:organization_id', 'custom:role'],
                WriteAttributes=['email'],
                IdTokenValidity=60,  # 60 minutes
                AccessTokenValidity=60,
                RefreshTokenValidity=30,  # 30 days
                TokenValidityUnits={
                    'IdToken': 'minutes',
                    'AccessToken': 'minutes',
                    'RefreshToken': 'days'
                }
            )

            app_client_id = client_response['UserPoolClient']['ClientId']
            logger.info(f"✅ App client created: {app_client_id}")

            # Create Domain
            domain_name = f"owkai-{organization_slug}-auth"
            try:
                self.cognito_client.create_user_pool_domain(
                    Domain=domain_name,
                    UserPoolId=user_pool_id
                )
                logger.info(f"✅ Domain created: {domain_name}")
            except Exception as e:
                logger.warn(f"⚠️ Domain creation failed (may exist): {e}")

            # Create first admin user
            try:
                self.cognito_client.admin_create_user(
                    UserPoolId=user_pool_id,
                    Username=admin_email,
                    UserAttributes=[
                        {'Name': 'email', 'Value': admin_email},
                        {'Name': 'email_verified', 'Value': 'true'},
                        {'Name': 'custom:organization_id', 'Value': str(organization_id)},
                        {'Name': 'custom:role', 'Value': 'admin'}
                    ],
                    DesiredDeliveryMediums=['EMAIL'],
                    MessageAction='RESEND'  # Send welcome email
                )
                logger.info(f"✅ Admin user created: {admin_email}")
            except Exception as e:
                logger.error(f"❌ Admin user creation failed: {e}")

            # Return pool details
            return {
                'user_pool_id': user_pool_id,
                'app_client_id': app_client_id,
                'domain': domain_name,
                'region': 'us-east-2'
            }

        except Exception as e:
            logger.error(f"❌ Pool creation failed: {e}")
            raise

    async def get_organization_pool_config(
        self,
        organization_id: int,
        db: Session
    ) -> Dict[str, str]:
        """
        Get Cognito pool configuration for organization

        Returns pool_id, client_id, region for authentication
        """
        org = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()

        if not org:
            raise ValueError(f"Organization {organization_id} not found")

        if not org.cognito_user_pool_id:
            raise ValueError(f"Organization {organization_id} has no Cognito pool")

        return {
            'user_pool_id': org.cognito_user_pool_id,
            'app_client_id': org.cognito_app_client_id,
            'region': org.cognito_region or 'us-east-2',
            'domain': org.cognito_domain
        }
```

---

### Phase 3: Frontend Dynamic Pool Detection

**File**: `src/services/cognitoAuth.js` (Updated)

```javascript
/**
 * ENTERPRISE: Get Cognito Pool Configuration for Organization
 *
 * Each organization has dedicated Cognito user pool.
 * Pool config must be fetched before authentication.
 */
export const getOrganizationPoolConfig = async (organizationSlug) => {
  try {
    logger.debug(`🔍 Getting pool config for org: ${organizationSlug}`);

    // Call backend API to get pool config
    const response = await fetch(
      `${API_BASE_URL}/api/public/organizations/${organizationSlug}/cognito-config`,
      {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      }
    );

    if (!response.ok) {
      throw new Error('Failed to get organization pool config');
    }

    const config = await response.json();

    logger.debug('✅ Pool config retrieved:', {
      userPoolId: config.user_pool_id,
      region: config.region
    });

    return {
      UserPoolId: config.user_pool_id,
      ClientId: config.app_client_id,
      Region: config.region
    };

  } catch (error) {
    logger.error('❌ Failed to get pool config:', error);
    throw error;
  }
};

/**
 * ENTERPRISE: Dynamic Login with Organization-Specific Pool
 *
 * Step 1: Detect organization from email domain or slug
 * Step 2: Get organization's dedicated Cognito pool config
 * Step 3: Authenticate against correct pool
 */
export const cognitoLoginDynamic = async (email, password, organizationSlug) => {
  try {
    logger.debug(`🔐 Dynamic login for: ${email} (org: ${organizationSlug})`);

    // Get organization's dedicated pool config
    const poolConfig = await getOrganizationPoolConfig(organizationSlug);

    // Create pool with org-specific config
    const userPool = new CognitoUserPool(poolConfig);

    // Authenticate against dedicated pool
    return new Promise((resolve, reject) => {
      const authenticationDetails = new AuthenticationDetails({
        Username: email.toLowerCase(),
        Password: password
      });

      const cognitoUser = new CognitoUser({
        Username: email.toLowerCase(),
        Pool: userPool
      });

      cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: (session) => {
          logger.debug('✅ Authentication successful against dedicated pool');
          resolve(/* ... */);
        },
        onFailure: (err) => {
          logger.error('❌ Authentication failed:', err);
          reject(err);
        }
      });
    });

  } catch (error) {
    logger.error('❌ Dynamic login failed:', error);
    throw error;
  }
};
```

---

### Phase 4: Login Flow Update

**File**: `src/components/Login.jsx` (Updated)

```javascript
/**
 * ENTERPRISE: Organization Detection from Email
 *
 * Extract organization slug from email domain or ask user
 */
const detectOrganizationFromEmail = (email) => {
  const domain = email.split('@')[1];

  // Map domains to organization slugs
  const domainMapping = {
    'owkai.com': 'owai-internal',
    'pilot-org.com': 'pilot-customer',
    'growth-org.com': 'growth-customer'
  };

  return domainMapping[domain] || null;
};

const handleLogin = async (e) => {
  e.preventDefault();

  try {
    // Step 1: Detect organization
    let orgSlug = detectOrganizationFromEmail(email);

    if (!orgSlug) {
      // Ask user to select organization
      setShowOrgSelector(true);
      return;
    }

    // Step 2: Login with dynamic pool selection
    const result = await cognitoLoginDynamic(email, password, orgSlug);

    // Step 3: Process success
    auth.setUser(result.user);
    auth.setToken(result.idToken);

  } catch (error) {
    setError(error.message);
  }
};
```

---

## 📊 COMPLIANCE VALIDATION

### HIPAA Requirements:

| Requirement | Shared Pool | Dedicated Pools |
|-------------|-------------|-----------------|
| PHI Isolation | ❌ Logical only | ✅ Physical separation |
| Access Controls | ❌ Shared IAM | ✅ Per-org IAM |
| Audit Logs | ❌ Mixed logs | ✅ Separate CloudTrail |
| Encryption Keys | ❌ Shared keys | ✅ Dedicated keys |
| Business Associate Agreement | ❌ Complex | ✅ Clear boundaries |

### PCI-DSS Requirements:

| Requirement | Shared Pool | Dedicated Pools |
|-------------|-------------|-----------------|
| Cardholder Data Isolation | ❌ Logical only | ✅ Physical separation |
| Network Segmentation | ❌ Same VPC | ✅ Per-org VPC possible |
| Access Control | ❌ Shared | ✅ Dedicated per org |
| Logging | ❌ Mixed | ✅ Separate audit trails |

### SOC 2 Type II Requirements:

| Requirement | Shared Pool | Dedicated Pools |
|-------------|-------------|-----------------|
| Logical Separation | ✅ Custom attrs | ✅ Physical + Logical |
| Customer Data Isolation | ⚠️ Application-level | ✅ Infrastructure-level |
| Independent Audits | ❌ Difficult | ✅ Easy per customer |
| Attestation Letters | ❌ Complex | ✅ Per-customer letters |

### GDPR Requirements:

| Requirement | Shared Pool | Dedicated Pools |
|-------------|-------------|-----------------|
| Data Residency | ⚠️ Same region | ✅ Configurable per org |
| Right to Erasure | ✅ Possible | ✅ Complete pool deletion |
| Data Processing | ⚠️ Shared processor | ✅ Dedicated processor |
| Data Controller | ⚠️ Unclear boundaries | ✅ Clear per org |

---

## 🚀 MIGRATION PATH

### Step 1: Create Dedicated Pools (Production)

```bash
# Run provisioning script for each org
python scripts/provision_cognito_pools.py \
  --org-id 1 \
  --org-slug owai-internal \
  --admin-email platform-admin@owkai.com

python scripts/provision_cognito_pools.py \
  --org-id 2 \
  --org-slug pilot-customer \
  --admin-email test-pilot-admin@example.com

python scripts/provision_cognito_pools.py \
  --org-id 3 \
  --org-slug growth-customer \
  --admin-email test-growth-admin@example.com
```

### Step 2: Migrate Users

```bash
# Export users from shared pool
aws cognito-idp list-users \
  --user-pool-id us-east-2_HPew14Rbn \
  --filter "custom:organization_id = 2" \
  > org2_users.json

# Import to dedicated pool
python scripts/migrate_users_to_dedicated_pool.py \
  --from-pool us-east-2_HPew14Rbn \
  --to-pool us-east-2_POOL2xxxxx \
  --org-id 2
```

### Step 3: Update Database

```sql
-- Update organizations table with new pool IDs
UPDATE organizations SET
  cognito_user_pool_id = 'us-east-2_POOL2xxxxx',
  cognito_app_client_id = 'CLIENT2xxxxx'
WHERE id = 2;
```

### Step 4: Deploy Frontend Updates

```bash
# Deploy updated cognitoAuth.js with dynamic pool detection
npm run build:prod
# Deploy to production
```

### Step 5: Deprecate Shared Pool

```bash
# After all orgs migrated, disable shared pool
aws cognito-idp update-user-pool \
  --user-pool-id us-east-2_HPew14Rbn \
  --user-pool-add-ons AdvancedSecurityMode=ENFORCED \
  --auto-verified-attributes email \
  --mfa-configuration ENFORCED
```

---

## ✅ BENEFITS OF DEDICATED POOLS

1. **Complete Isolation**: No shared infrastructure
2. **Regulatory Compliance**: Meets HIPAA, PCI-DSS, SOC 2, GDPR
3. **Independent Audits**: Each org can audit their pool
4. **Customer Control**: Org admins can manage their pool
5. **Security Boundaries**: Clear separation of duties
6. **Compliance Certification**: Easier per-org certification
7. **Data Residency**: Configurable per org requirements
8. **Independent Backup**: Separate backup/recovery per org

---

## 📈 COST ANALYSIS

### Shared Pool (Current):
- 1 User Pool: $0/month (MAU pricing)
- Total: $0 + MAU fees

### Dedicated Pools (Required):
- 3 User Pools: $0/month each (MAU pricing)
- Total: $0 + MAU fees (same cost!)

**Conclusion**: No additional cost for dedicated pools, only MAU fees apply regardless of pool count.

---

## 🎯 RECOMMENDATION

**IMPLEMENT DEDICATED POOLS IMMEDIATELY**

This is a **CRITICAL SECURITY REQUIREMENT** for highly regulated customers. The shared pool architecture is not compliant with HIPAA, PCI-DSS, or enterprise security standards.

**Timeline**: 2-3 days for complete implementation
**Priority**: CRITICAL (P0)
**Cost**: Zero additional cost

---

**Engineer**: OW-KAI Engineer
**Date**: November 20, 2025
**Status**: 🚨 **CRITICAL - IMPLEMENTATION REQUIRED**
**Compliance**: HIPAA | PCI-DSS | SOC 2 | GDPR

*Dedicated user pools per organization are mandatory for enterprise security*
