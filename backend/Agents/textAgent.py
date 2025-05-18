from twilio.rest import Client

account_sid = 'AC0923197f89d84fd8c24dc20aca627b38'
auth_token = 'ba46a8996a78992c68abd7387aedef05'
client = Client(account_sid, auth_token)

message = client.messages.create(
  from_='+16282328792',
  body='Hello from Sorhan',
  to='+19038516387'
)

print(f"Message SID: {message.sid}")
print(f"Message Status: {message.status}")

