#!/bin/bash

echo "🔒 C7: Production Secrets Validation & Generation"
echo "=================================================="
echo ""

# Backup current .env
cp .env .env.backup-$(date +%Y%m%d_%H%M%S)
echo "✅ Backed up current .env"
echo ""

# Generate cryptographically secure secrets (64 characters)
echo "🔐 Generating cryptographically secure secrets..."
NEW_SECRET_KEY=$(openssl rand -hex 32)  # 64 chars
NEW_JWT_SECRET=$(openssl rand -hex 32)  # 64 chars

echo "✅ Generated new secrets:"
echo "   SECRET_KEY: 64 characters (SHA-256 strength)"
echo "   JWT_SECRET_KEY: 64 characters (SHA-256 strength)"
echo ""

# Update .env file
echo "📝 Updating .env file..."

# Replace SECRET_KEY
sed -i '' "s/^SECRET_KEY=.*/SECRET_KEY=${NEW_SECRET_KEY}/" .env

# Replace JWT_SECRET_KEY
sed -i '' "s/^JWT_SECRET_KEY=.*/JWT_SECRET_KEY=${NEW_JWT_SECRET}/" .env

# Update ENVIRONMENT to production
sed -i '' "s/^ENVIRONMENT=.*/ENVIRONMENT=production/" .env

echo "✅ Updated .env with production-grade secrets"
echo ""

# Validate changes
echo "🔍 Validating new configuration..."
echo ""

SECRET_LEN=$(grep "^SECRET_KEY=" .env | cut -d= -f2 | wc -c | tr -d ' ')
JWT_LEN=$(grep "^JWT_SECRET_KEY=" .env | cut -d= -f2 | wc -c | tr -d ' ')
ENV=$(grep "^ENVIRONMENT=" .env | cut -d= -f2)

echo "Validation Results:"
echo "   SECRET_KEY length: $SECRET_LEN chars $([ $SECRET_LEN -ge 32 ] && echo '✅' || echo '❌')"
echo "   JWT_SECRET_KEY length: $JWT_LEN chars $([ $JWT_LEN -ge 32 ] && echo '✅' || echo '❌')"
echo "   ENVIRONMENT: $ENV $([ "$ENV" = "production" ] && echo '✅' || echo '⚠️')"
echo ""

echo "🎉 C7 Complete: Production secrets configured"
echo ""
echo "⚠️  IMPORTANT: These secrets have been changed!"
echo "   - Existing JWT tokens will be invalidated"
echo "   - Users will need to re-authenticate"
echo "   - This is normal and expected for security upgrades"

