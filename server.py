#!/usr/bin/python

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import glob
import os

PORT_NUMBER = 5555

#This class will handles any incoming request from
#the browser

#This class will handles any incoming request from
#the browser 
class myHandler(BaseHTTPRequestHandler):
	
	#Handler for the GET requests
	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-type','text/html')
		self.end_headers()
		# Send the html message
		self.wfile.write("Hello World ! <BR>")
                files = filter(os.path.isdir, os.listdir(os.getcwd()))
                for f in files:
                   self.wfile.write("%s<br>"  % f)
		return

class server():
	
    def __init__(self):
	#Create a web server and define the handler to manage the
	#incoming request
	self.server = HTTPServer(('', PORT_NUMBER), myHandler)
	print 'Started httpserver on port ' , PORT_NUMBER
	
	#Wait forever for incoming htto requests
	self.server.serve_forever()

    def close(self):
	print '^C received, shutting down the web server'
	self.server.socket.close()
	


if __name__ == "__main__":
    try:
        K = server()
    except KeyboardInterrupt:
        K.close()
