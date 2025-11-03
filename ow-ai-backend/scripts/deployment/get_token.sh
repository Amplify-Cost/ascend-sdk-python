export TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@owkai.com&password=SecureAdmin123!" \
  | jq -r '.access_token')
echo "Token: $TOKEN"
