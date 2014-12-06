import cookielib
import urllib2
import urllib
from urlparse import urlparse
from HTMLParser import HTMLParser

class FormParser(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)

		self.url = None
		self.params = {}
		self.in_form = False
		self.form_parsed = False
		self.method = 'GET'

	def handle_starttag(self, tag, attrs):
		tag = tag.lower()

		if tag == 'form':
			if self.form_parsed:
				raise RuntimeError('Two <form>s on the page.')

			if self.in_form:
				raise RuntimeError('Nested <form>s.')

			self.in_form = True

		if not self.in_form:
			return

		attrs = dict((name.lower(), value) for name, value in attrs)

		if tag == 'form':
			self.url = attrs['action']

			if 'method' in attrs:
				self.method = attrs['method']
		elif tag == 'input' and attrs.viewkeys() >= {'type', 'name'} and \
			attrs['type'] in ['hidden', 'text', 'password']:
			self.params[attrs['name']] = attrs['value'] if 'value' in attrs else ''

	def handle_endtag(self, tag):
		tag = tag.lower()

		if tag == 'form':
			if not self.in_form:
				raise RuntimeError('Unexpected end of <form>.')

			self.in_form = False
			self.form_parsed = True

def auth_user2(client_id, scope, opener):
	response = opener.open(
		"https://oauth.vk.com/authorize?" + \
		"client_id=%s&scope=%s&redirect_uri=http://oauth.vk.com/blank.html&display=wap&response_type=token" 
		% (client_id, ",".join(scope))
		)
	doc = response.read()

	parser = FormParser()
	parser.feed(doc)
	parser.close()

	params = parser.params

	if not parser.form_parsed or parser.url is None:
		raise RuntimeError('Form wasn\'t parsed properly.')

	if not params.viewkeys() >= {'pass', 'email'}:
		print 'params: %s' % params
		# raise RuntimeError('Some essential data is missing in the form.')
		exit()

	#params.update({'email': email, 'pass': password})

	if parser.method.lower() == 'post':
		response = opener.open(parser.url, urllib.urlencode(params))
	else:
		raise NotImplementedError("Method '%s' is not supported" % parser.method)

	return response.read(), response.geturl()

def auth_user(client_id, scope, opener):
	response = urllib2.urlopen(
		"https://oauth.vk.com/authorize?" + \
		"client_id=%s&scope=%s&redirect_uri=http://oauth.vk.com/blank.html&display=wap&response_type=token" 
		% (client_id, ",".join(scope))
		)
	doc = response.read()
	
	return doc.read(), response.geturl()


def give_access(doc, opener):
	parser = FormParser()
	parser.feed(doc)
	parser.close()

	if not parser.form_parsed or parser.url is None:
		  raise RuntimeError('Form wasn\'t parsed properly.')

	if parser.method.lower() == 'post':
		response = opener.open(parser.url, urllib.urlencode(parser.params))
	else:
		raise NotImplementedError("Method '%s' is not supported" % parser.method)

	return response.geturl()


def auth(client_id, scope):
	# Ensuring that scope is a list
	if not isinstance(scope, list):
		scope = [scope]

	opener = urllib2.build_opener(
		urllib2.HTTPCookieProcessor(cookielib.CookieJar()),	urllib2.HTTPRedirectHandler())

	# Entering login data
	doc, url = auth_user(client_id, scope, opener)

	if urlparse(url).path != '/blank.html':
		# Need to give access to requested scope
		url = give_access(doc, opener)

	if urlparse(url).path == '/blank.html':
		raise RuntimeError('Error occured while accessing the requested scope.')

	def split_key_value(kv_pair):
		kv = kv_pair.split('=')
		return kv[0], kv[1]

	url = "http://oauth.vk.com/blank.html#access_token=7ea3ad77e4e6552aa6b7db59fae39ebaada774a67f14bfcfa63a1b6c882a1067ecdc95d0ba344b78380d3&expires_in=86400&user_id=24448927";
	spl = urlparse(url).fragment.split('&');
	answer = dict(split_key_value(kv_pair) for kv_pair in spl)

	if not answer.viewkeys() >= {'access_token', 'user_id'}:
		raise RuntimeError('Authorization failure: did not obtain complete data.')

	return answer['access_token'], answer['user_id']
