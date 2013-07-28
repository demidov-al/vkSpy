#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import vk, getpass, threading, time

class RepeatTimer(threading.Thread):
	def __init__(self, interval, callable, *args, **kwargs):
		threading.Thread.__init__(self)
		self.interval = interval
		self.callable = callable
		self.args = args
		self.kwargs = kwargs
		self.event = threading.Event()
		self.currentTimer = None
		self.event.set()
	
	def run(self):
		while self.event.is_set():
			self.currentTimer = threading.Timer(self.interval, self.callable, self.args, self.kwargs)
			self.currentTimer.start()
			self.currentTimer.join()
			
	def cancel(self):
		self.event.clear()
		self.currentTimer.cancel()


sleepTime = 100.0
fileName = "log.txt"
startTime = None

def logChanges(dictionary):
	with open(fileName, 'w') as f:
		f.write("{0}\n".format(time.strftime("%d-%m-%Y %H:%M:%S", startTime)))
		for id, user_info in dictionary.items():
			f.write("{0} {1} {2} : {3:.2f} h.\n".format(id,
														user_info['first_name'],
														user_info['last_name'],
														user_info['online_time']/3600.0))

def get_all_friends(user_id, token):
	return vk.call_api("friends.get", [("uid", user_id), ("fields", "first_name,last_name")], token)

def get_online_friends(user_id, token):
	return vk.call_api("friends.getOnline", ("user_id", user_id), token)

def workingThreadRoutine(uemail, upassword, uid, uaccess_token, result):
	resp = get_online_friends(uid, uaccess_token)
	if resp == None:
		print("token has expired")
		uaccess_token, uid = vk.auth(uemail, upassword, "3336140", "friends")
		workingThreadRoutine(uemail, upassword, uid, uaccess_token, result)
		return
	print("{0} {1}".format(time.strftime("%d-%m-%Y %H:%M:%S", time.localtime()), resp))
	for friend in resp:
		result[friend]['online_time'] += sleepTime
	logChanges(result)
	

email = input("Enter your email:")
password = getpass.getpass()
access_token, u_id = vk.auth(email, password, "3336140", "friends")
print("Authorization is successful!\nAccess token: {0}, user id: {1}".format(access_token, u_id))

user_friends = get_all_friends(u_id, access_token)

result_dict = dict()
for friend in user_friends:
	id = friend['user_id']
	result_dict[id] = dict()
	result_dict[id]['first_name'] = friend['first_name']
	result_dict[id]['last_name'] = friend['last_name']
	result_dict[id]['online_time'] = 0.0
user_friends = None

startTime = time.localtime()
t = RepeatTimer(sleepTime, workingThreadRoutine, email, password, u_id, access_token, result_dict)
t.start();
while True:
	cmd = input()
	if cmd == 'exit':
		t.cancel()
		break;
	elif cmd == 'show log':
		for id, user_info in result_dict.items():
			print("{0} {1} {2} : {3:.2f} h.\n".format(id,
													user_info['first_name'],
													user_info['last_name'],
													user_info['online_time']/3600.0))
		
	else: print("Unrecognized command")
print("Terminating...")