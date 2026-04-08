function jarvis {
  param([string]$cmd)
  curl.exe -s -X POST http://localhost:11436/api/generate -H "Content-Type: application/json" -d "{
    \"model\": \"phi3.5:3.8b-instruct-q4_K_M\",
    \"prompt\": \"JARVIS: $cmd. Access EPOS tools.\",
    \"stream\": false
  }" | jq -r '.response'
}
# Usage: jarvis "Status constellation"
