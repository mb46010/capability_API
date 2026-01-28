# Show stakeholders that every action is logged
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/audit/recent | jq .