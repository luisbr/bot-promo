curl -X POST http://18.215.242.60:5000/webhook/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "from": {"number":"5215525596591"},
    "message_type": "reply",
    "reply": { "id": "SI", "title": "Sí" }
  }'
curl -X POST http://18.215.242.60:5000/webhook/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "from": {"number":"5215525596591"},
    "message_type": "reply",
    "reply": { "id": "EVT_1", "title": "Domingo 17 agosto 2025" }
  }'


  curl -X POST http://18.215.242.60:5000/webhook/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "from": {"number":"5215525596591"},
    "message_type": "reply",
    "reply": { "id": "NOMBRE_OK", "title": "Sí, es correcto" }
  }'