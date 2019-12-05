
# INIT ---
# Required
from flask import Flask

# Basic Python extensions --
#
# *Dataclass* allows the use of the @dataclass decorator. 
# this removes the necessity of using the __init__ constructor,
# and it helps with printing and accessing the class in a userfriendly 
# way. In short, dataclasses behave more like structs in C.
from dataclasses import dataclass

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

# TYPES ---
@dataclass
class Item:
	url: str = ''
	replied_to: str = ''
	type: str = ''
	user: str = ''
	content: str = ''

# ROUTES ---
# Index
@app.route('/')
def server():
	# Load the page template
	page = readfile("templates/index.html")

	# html will hold our html response
	html = ''

	# Load items --- 
	# get all items from a location (directory) on the internet
	items = []
	item_urls = get_item_urls("http://www.dwrolvink.com/test")

	# then, convert the item files to Item objects (see above)
	for item_url in item_urls:
		items.append(load_item(item_url))
	
	# Build reply tree (post is 0)
	# The tree will allow us to parse the replies without further replies first.
	# This is done in get_nested_items. 
	# It will take the post, then load its 
	# replies. Of each reply it will load further replies, and so on.
	# then, when a reply is found without further replies, the html code of that reply
	# is returned. The replied code will get inserted in the parent item (reply or post)
	# and then that reply's code will get returned, working it's way up the tree, 
	# until we have a post with all its replies in the correct hierarchical order,
	# even if the replies in the folder aren't in that order (or come from different
	# sources).

	# Build reply tree (post is 0)
	tree = {}
	for i in range(len(items)):
		tree[i] = []
		for r in range(len(items)):
			if items[r].replied_to == items[i].url:
				tree[i].append(r)
	
	# Get page content
	#print(tree)
	content = get_nested_items(0, tree, items).content.replace("{{replies}}",'')
	#print(content)

	# Insert the content into the index template
	page = page.replace("{{ content }}", content)

	# Output html response
	return page

# This route functions allows us to serve static files, such as the 
# style sheet, images, etc. Each file has to be in the static_file_dir
# (see top of page)
@app.route('/static/<path:path>', methods=['GET'])
def serve_static_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = os.path.join(path, 'index.html')
 
    return send_from_directory(static_file_dir, path)

# HELPER FUNCTIONS ---
# recurse through the tree that is compiled in server()
# when an item is found without further replies, the html code gets returned
# this allows the parent item to incorporate this code in its 'replies' block,
# upon which it iself is returned, ad summum unum
def get_nested_items(key, tree, items):
	# get nest list
	nest_list = tree[key]

	# if list is empty, return the item itself
	if len(nest_list) == 0:
		return items[key]

	# if list is not empty, get each item
	# add the result to replies
	replies = ''
	for nested_item in nest_list:
		replies += get_nested_items(nested_item, tree, items).content
	
	# add replies to item code block
	item = items[key]
	item.content = item.content.replace("{{replies}}", replies)

	# return item itself
	return item

# return an array of all the lines in a file
def readlines(path):
	pages = []
	with open(path,"r") as fh: # https://stackoverflow.com/questions/1369526/what-is-the-python-keyword-with-used-for#11783672
		return fh.readlines()

# return the file as one string
def readfile(path):
	with open(path,"r") as fh:
		return fh.read()

# (( another user will have a folder in which all their posts/replies are
# a post or a reply is called an item ))
# Load a directory (i.e. the html page listing the dir contents => list of the items), 
# then split the html so we get a list of item urls in that directory
# return the list of item urls
def get_item_urls(follow_url):
	file_contents = req.get(follow_url).text

	item_urls = []
	for line in file_contents.splitlines():
		parts = line.split('"')
		if len(parts) == 3:
			if parts[1] != '../':
				item_urls.append(follow_url + '/' +parts[1])
	print(item_urls)
	return item_urls

# Open the url of an item, determine if it's a post or a reply,
# then, compile a html block and fill in the contents of the item
# return the html block
def load_item(item_url):
	# Output
	item = Item()

	# Cleanup item_url and add to item
	item.url = item_url.replace("\n",'')

	# Get file contents 
	file_contents = req.get(item.url).text

	# Read file
	mode = 'header'
	for line in file_contents.splitlines():
		if mode == 'content':
			item.content += line + "\n"
			continue
		elif line.startswith("type="):
			item.type = line[5:]
			continue
		elif line.startswith("user="):
			item.user = line[5:]
		elif line.startswith("replied_to="):
			item.replied_to = line[11:]			
		elif line == '---':
			mode = 'content'
			continue

	# Convert markdown to html
	item.content = markdown.markdown(item.content)
	
	# put markdown in appriopriate html wrapper
	if item.type == 'post':
		html = '<div class="block"><div class="post">{{item}}</div>{{replies}}</div>'
		html = html.replace('{{item}}', item.content)
		item.content = html

	elif item.type == 'reply':
		html = '<div class="block"><div class="reply"><div class="user">{{user}}</div>{{item}}</div>{{replies}}</div>'
		item.content = html.replace('{{item}}', item.content)
		item.content = item.content.replace('{{user}}', item.user)

	# return
	return item


