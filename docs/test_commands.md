# End-to-End Test Commands

## Start stack
```bash
docker-compose up --build
```

## Health
```bash
curl http://localhost/health
```
→ `{"status":"healthy"}`

## Create customer
```bash
curl -X POST http://localhost/customers \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "firstName": "Alice",
    "lastName": "Smith",
    "phone": "+49123456789",
    "address": {
      "street": "Hauptstr 1",
      "city": "Berlin",
      "postalCode": "10115",
      "country": "Germany"
    }
  }'
```
→ customer JSON with generated `id`

## Get customer
```bash
curl http://localhost/customers/<uuid-from-above>
```

## Create claim
```bash
curl -X POST http://localhost/claims \
  -H "Content-Type: application/json" \
  -d '{
    "customerInfo": {
      "email": "alice@example.com",
      "firstName": "Alice",
      "lastName": "Smith"
    },
    "flightInfo": {
      "flightNumber": "LH100",
      "airline": "Lufthansa",
      "departureDate": "2025-10-01",
      "departureAirport": "FRA",
      "arrivalAirport": "TXL"
    },
    "incidentType": "delay",
    "notes": "3 hours delay"
  }'
```
→ claim JSON with generated `id`

## Get claim
```bash
curl http://localhost/claims/<uuid-from-above>