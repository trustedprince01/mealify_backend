#!/usr/bin/env python
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.request
import urllib.error
import urllib.parse
import json
import sys

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')  # 24 hours
        SimpleHTTPRequestHandler.end_headers(self)

    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()
        
    def do_GET(self):
        # Forward the request to the actual API
        url = f"http://localhost:8000{self.path}"
        print(f"Proxying GET request to {url}")
        
        try:
            with urllib.request.urlopen(url) as response:
                # Read the response
                content = response.read()
                content_type = response.getheader('Content-Type', 'application/json')
                
                # Return it to the client with CORS headers
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(content)
                
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
    
    def do_POST(self):
        # Get the request body length
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''
        
        # Forward the request to the actual API
        url = f"http://localhost:8000{self.path}"
        print(f"Proxying POST request to {url}")
        
        try:
            req = urllib.request.Request(
                url, 
                data=body,
                headers={
                    'Content-Type': self.headers.get('Content-Type', 'application/json')
                },
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                # Read the response
                content = response.read()
                content_type = response.getheader('Content-Type', 'application/json')
                
                # Return it to the client with CORS headers
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(content)
                
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

def run_proxy_server(port=8001):
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSRequestHandler)
    print(f"Starting CORS proxy server on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    run_proxy_server(port) 