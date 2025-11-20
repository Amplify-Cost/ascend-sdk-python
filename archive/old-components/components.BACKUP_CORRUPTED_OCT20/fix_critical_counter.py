with open('AgentAuthorizationDashboard.jsx', 'r') as f:
    content = f.read()

# Fix the Critical Risk counter calculation (80+ is critical)
old_counter = r'<p className="text-2xl font-bold">{dashboardData\?\.enterprise_kpis\?\.high_risk_pending \|\| 0}</p>'
new_counter = r'<p className="text-2xl font-bold">{pendingActions.filter(a => a.ai_risk_score >= 80).length}</p>'
content = content.replace(old_counter, new_counter)

# Also fix if it uses a different field name
old_counter2 = r'{dashboardData\?\.enterprise_kpis\?\.critical_pending \|\| 0}'
new_counter2 = r'{pendingActions.filter(a => a.ai_risk_score >= 80).length}'
content = content.replace(old_counter2, new_counter2)

with open('AgentAuthorizationDashboard.jsx', 'w') as f:
    f.write(content)

print("✅ Fixed critical risk counter")
