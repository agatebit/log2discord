from http.server import BaseHTTPRequestHandler, HTTPServer
import json

print("starting script")
# Counter to keep track of successful requests
counter = 0

# Define the HTTP request handler
class WebhookHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_POST(self):
        global counter
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data.decode('utf-8'))
        
        # Increment the counter for each successful request
        counter += 1
        
        # Echo the payload to stdout
        print("Received payload:", payload)
        with open('./uploads-count', 'w') as file:
            file.write(str(counter))
        
        # Send a response to the client
        self._set_headers()
        self.wfile.write(b"Webhook received successfully")

# Define the server parameters
server_address = ('', 8080)  # Leave host empty for localhost
httpd = HTTPServer(server_address, WebhookHandler)

# Start the server
print('Starting server...')
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    pass
httpd.server_close()
print('Server stopped')