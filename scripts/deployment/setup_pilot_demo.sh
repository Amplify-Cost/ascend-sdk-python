#!/bin/bash
echo "🚀 Setting up pilot demo environment..."

# Run all fix scripts
python fix_alerts.py
python fix_policies.py
python check_smart_rules.py

echo ""
echo "✅ Pilot environment ready!"
echo "📋 Remember to:"
echo "  1. Test login at https://pilot.owkai.app"
echo "  2. Keep browser console open (F12) to monitor"
echo "  3. Have backup screenshots ready"
echo "  4. Focus on business value, not UI details"
