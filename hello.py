
# INIT ---
# Required
from flask import Flask

# Get posts from the internet
import requests as req

# Allow markdown posts to be translated to html
import markdown

# Load static files from ./static
import os
from flask import send_from_directory
static_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'style')

# Init app
app = Flask(__name__)

# ROUTES ---
# Index
@app.route('/')
def server():
	page = readfile("templates/index.html")

	html = ''
	item_urls = readlines("pages.txt")
	for item_url in item_urls:
		item_type, item_html = load_page(item_url)
		if item_type == 'post':
			html += '<div class="block post">{{item}}</div>'.replace('{{item}}', item_html)
		elif item_type == 'reply':
			html += '<div class="block reply">{{item}}</div>'.replace('{{item}}', item_html)
	page = page.replace("{{ content }}", html)
	return page

@app.route('/static/<path:path>', methods=['GET'])
def serve_static_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = os.path.join(path, 'index.html')
 
    return send_from_directory(static_file_dir, path)

# HELPER FUNCTIONS ---
def readlines(path):
	pages = []
	with open(path,"r") as fh:
		return fh.readlines()

def readfile(path):
	with open(path,"r") as fh:
		return fh.read()

def load_page(page_url):
	content = req.get(page_url.replace("\n",'')).text
	html = ''
	type = ''
	mode = 'header'
	for line in content.splitlines():
		if mode == 'content':
			html += line + "\n"
			continue
		if line.startswith("type="):
			type = line[5:]
			continue
		elif line == '---':
			mode = 'content'
			continue

	html = markdown.markdown(html)
	return type, html


