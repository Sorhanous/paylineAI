import requests
from sseclient import SSEClient

url = "https://payline.app.n8n.cloud/mcp-test/0f81c920-cac1-49f6-b366-0bebb0f0af9c/sse"
params = { "prompt": "Send an email to John" }

response = requests.get(url, params=params, stream=True)
client = SSEClient(response)

for event in client.events():
    print("MCP response:", event.data)
 