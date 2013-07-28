#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import urllib, http.cookiejar as cookielib, json
from html.parser import HTMLParser

class FormParser(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.url = None
		self.params = {}
		self.in_form = False
		self.form_parsed = False
		self.method = None
	
	def handle_starttag(self, tag, attrs):
		tag = tag.lower()
		if tag == "form":
			if self.form_parsed:
				raise RuntimeError("Second form on page")
			if self.in_form:
				raise RuntimeError("Already in form")
			self.in_form = True
		if not self.in_form:
			return
		attrs = dict((name.lower(), value) for name, value in attrs)
		if tag == "form":
			self.url = attrs["action"]
			if "method" in attrs:
				self.method = attrs["method"]
		elif tag == "input" and "type" in attrs and "name" in attrs:
			if attrs["type"] in ["hidden", "text", "password"]:
				self.params[attrs["name"]] = attrs["value"] if "value" in attrs else ""

	def handle_endtag(self, tag):
		tag = tag.lower()
		if tag == "form":
			if not self.in_form:
				raise RuntimeError("Unexpected end of <form>")
			self.in_form = False
			self.form_parsed = True

def auth(email, password, client_id, scope):
	def auth_user(email, password, app_id, scope, opener):
		response = opener.open("https://oauth.vk.com/authorize?" + \
							   "redirect_uri=https://oauth.vk.com/blank.html&response_type=token&" + \
							   "client_id={0}&scope={1}&display=wap&v=4.99".format(app_id, ",".join(scope)))
		doc = response.read()
		parser = FormParser()
		parser.feed(doc.decode("utf-8"))
		parser.close()
		if (not parser.form_parsed) or (parser.url is None) or \
			("pass" not in parser.params) or ("email" not in parser.params) or (parser.method != "post"):
			raise RuntimeError("Something is wrong")
		parser.params["email"] = email
		parser.params["pass"] = password
		response = opener.open(parser.url, urllib.parse.urlencode(parser.params).encode())
		return response.read(), response.geturl()
	
	def give_access(doc, opener):
		parser = FormParser()
		parser.feed(doc.decode("utf-8"))
		parser.close()
		if not parser.form_parsed or parser.url is None:
			raise RuntimeError("Something is wrong")
		if parser.method == "post":
			response = opener.open(parser.url, urllib.parse.urlencode(parser.params).encode())
		return response.geturl()
	
	
	if not isinstance(scope, list):
		scope = [scope]
	opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookielib.CookieJar()),
										 urllib.request.HTTPRedirectHandler())
	doc, url = auth_user(email, password, client_id, scope, opener)
	if urllib.parse.urlparse(url).path != "/blank.html":
		url = give_access(doc, opener)
	if urllib.parse.urlparse(url).path != "/blank.html":
		raise RuntimeError("Expected success here. It seems you've entered wrong login or password.")
	
	answer = dict(kv_pair.split("=") for kv_pair in urllib.parse.urlparse(url).fragment.split("&"))
	if "access_token" not in answer or "user_id" not in answer:
		raise RuntimeError("Missing some values in answer")
	
	return answer["access_token"], answer["user_id"]
	
def call_api(method, params, token):
	if isinstance(params, list): params_list = [kv for kv in params]
	elif isinstance(params, dict): params_list = params.items()
	else: params_list = [params]
	
	params_list.append(("access_token", token))
	url = "https://api.vk.com/method/{0}?{1}".format(method, urllib.parse.urlencode(params_list))
	response = json.loads(urllib.request.urlopen(url).read().decode("utf-8"))
	
	if "response" in response: return response["response"]
	else: return None
