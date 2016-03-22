#!/usr/bin/env python
#
# Parse 
#

import urllib
import urllib2
from bs4 import BeautifulSoup
import pickle
import smtplib
import sys
import random
import re


# URL
url = "https://developers.google.com/android/nexus/images"

# User Agents - will be picked randomly
user_agents = [
			"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
			"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
			"Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16",
			"Mozilla/5.0 (Windows NT 6.0; rv:2.0) Gecko/20100101 Firefox/4.0 Opera 12.14",
			"Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25"
		]

# Mail
mail_server = "localhost"
mail_sender = "Android Notifier <you@your-email-server>"
mail_recipients = [ "youremail@some-email-server" ]
mail_subject = "New android image"

# Nexus models to follow
follow_models = [ 'shamu', 'mantaray', 'occam' ]

# File to store data, to be able to compare at next run
store_file = "new_android_notifier.dat"

# Initialise dictionaries
_dict = {}
_models = {}

class CheckAndroid(object):

	def parsePage(self, url):
		reload(sys)
		headers = { 'User-Agent' : user_agents[random.randrange(0,len(user_agents))] }
		request = urllib2.Request(url, None, headers)
		response = urllib2.urlopen(request)
		content = response.read()
		content_soup = BeautifulSoup(content)

		for model in content_soup.find_all('h2', {'id': re.compile('^(' + '|'.join(follow_models) + ')')}):
			m = re.match(r'\"(.*)\" for (.*)', model.string)
			if m:
				model_code = m.group(1)
				model_name = m.group(2)
				_models[model_code] = model_name

		for tr in content_soup.find_all('tr', {'id': re.compile('^(' + '|'.join(follow_models) + ')')}):
			iid = tr['id']
			model_code = iid[:-6]
			_dict[iid] = {}
			_dict[iid]['model_code'] = model_code			
			if model_code in _models:
				_dict[iid]['model_name'] = _models[model_code]
			_dict[iid]['version'] = tr.td.string.strip()
			for a in tr.find_all('a', href=True):
				_dict[iid]['link'] = a['href']



if __name__ == "__main__":

	print "-> Get results from the last run"
	olddict = pickle.load(open(store_file, "rb"))

	ca = CheckAndroid()

	print "-> Parse page"
	r = ca.parsePage(url)

	print "-> Compare data"

	msg = ""
	for n_id in sorted(_dict):
		if n_id not in olddict:
			msg += """
New Android image for %s (%s)
ID: %s
Version: %s
Link: %s

----------------------------------------------------------------
			""" % (_dict[n_id]['model_name'], _dict[n_id]['model_code'], n_id, _dict[n_id]['version'], _dict[n_id]['link'])


	if msg != "":
		print msg
		msg = "From: " + mail_sender + "\nTo: " + ', '.join(mail_recipients) + "\nSubject: " + mail_subject + "\n\n" + msg + "\n"
		
		# Send email
		s = smtplib.SMTP(mail_server)
		smtpres = s.sendmail(mail_sender, mail_recipients, msg)
		s.quit()

		if smtpres:
			errstr = ""
			for recip in smtpres.keys():
				errstr = """Could not delivery mail to: %s

				Server said: %s
			  	%s

			  	%s""" % (recip, smtpres[recip][0], smtpres[recip][1], errstr)

			raise smtplib.SMTPException, errstr

	else:
		print "    Nothing new"

	print "-> Save data"
	pickle.dump(_dict, open(store_file, "wb"))

