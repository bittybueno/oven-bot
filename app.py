from flask import Flask, request, jsonify, render_template
import threading


app = Flask(__name__)

import os
import redis
import json

# available light settings
# LIGHTS = ['kitchen', 'livingroom', 'bedroom']
APPLIANCES = ['oven', 'timer', 'light']

# use local settings for connecting to the database
# example from https://stackoverflow.com/questions/9383450/how-can-i-detect-herokus-environment
USE_LOCAL = not 'ON_HEROKU' in os.environ

# database functions go here

# connect to the database and return the db handle
def connectToDatabase():
	# db = None
	# if USE_LOCAL:
	# 	db = redis.Redis(host='localhost', port=6379, db=0)
	# else:
	# 	db = redis.from_url(os.environ.get("REDIS_URL"))

	# # initialize if we need to
	# for light in LIGHTS:
	# 	if not db.exists(light):
	# 		db.set(light, 'off')		
	db = redis.from_url(os.environ.get("REDIS_URL"))
	#db = redis.Redis(host='localhost', port=6379, db=0)
	return db

def init(db):
	for app in APPLIANCES:
		db.set(app, 'off')

def setOven(db, value):
	db.set('oven', value)

def setLight(db, value):
	db.set('light', value)

def setTimer(db, time, value):
	string = value + ' ' + time
	db.set('timer', string)

def getApp(db, app):
	if not app in APPLIANCES:
		raise Error("Invalid appliance")
	return db.get(app)
	

def getStatus(db):
	status = {}
	for app in APPLIANCES:
		status[app] = getApp(db, app)
	return status


@app.route("/")
def root():
	db = connectToDatabase()
	status = getStatus(db)
	ovenStatus = status['oven']
	timerStatus = status['timer']
	lightStatus = status['light']
	return render_template('overview.html', oven=ovenStatus, timer=timerStatus, light=lightStatus)


@app.route("/get/<light>")
def webGetLight(light):
	db = connectToDatabase()
	value = getLight(db, light)
	return "The " + light + " light is " + value

# @app.route("/set/<light>/<value>")
# def webSetLight(light, value):
# 	db = connectToDatabase()
# 	setLight(db, light, value)
# 	return "The " + light + " light is now " + value
@app.route("/set/oven/<value>")
def webSetOven(value):
	db = connectToDatabase()
	setOven(db, value)
	return "The oven is now set to " + str(value)

@app.route("/set/light/<value>")
def webSetLight(value):
	db = connectToDatabase()
	setLight(db, value)
	return "The oven light is now " + value

@app.route("/set/timer/<time>/<value>")
def webSetTimer(value, time):
	db = connectToDatabase()
	setTimer(db, time, value)
	return "The oven timer is now set for "  + value + " " + time


# for readability's sake, here we represent the status as HTML
# below in the webhook section we represent it as a string
# to improve understandability of the text
# if textOnly is true, strip out the html

@app.route("/status")
def webStatus(textOnly=False):
	db = connectToDatabase()
	status = getStatus(db)
	
	# return status as a string (to work with dialogflow)
	statusString = ""
	for app in APPLIANCES:
		if textOnly:
			statusString += str(app) + " - " + str(status[app]) + ". "
			
		else:
			statusString += str(app) + " - " + str(status[app]) + "<br/>"
			
	return statusString

@app.route("/reset")
def webReset():
	db = connectToDatabase()
	initialize(db)
	return "ok"

# this is for debugging the webhook code
# it just prints out the json of the last webhook request
@app.route("/lastRequest")
def lastRequest():
	db = connectToDatabase()
	req = db.get("lastRequest")
	return req

# webhook code goes here
# this is set to receive a webhook request from DialogFlow
# see https://dialogflow.com/docs/fulfillment/how-it-works for details
# 
# basically, the url /dialog will expect a JSON object as described above
# and will parse the attached JSON object, then do stuff

@app.route("/dialog", methods=["POST"])
def handleDialog():
	data = request.get_json()
	
	# save this request for debugging
	db = connectToDatabase()
	db.set("lastRequest", json.dumps(data))
	
	# debug
	# print data
	
	# now, do stuff based on the JSON data
	# in particular we want to look at the queryResult.intent.displayName to
	# see which intent is triggered, and queryResult.parameters to see params
	
	# if data['queryResult']['intent']['displayName'] == "getOverallStatus":
	# 	response = webStatus(True)
	# 	print(response)
	# 	return jsonify({'fulfillmentText': response})
	# elif data['queryResult']['intent']['displayName'] == "getLightStatus":
	# 	lightName = data['queryResult']['parameters']['light-name']
	# 	response = webGetLight(lightName)
	# 	print(response)
	# 	return jsonify({'fulfillmentText': response})
	# elif data['queryResult']['intent']['displayName'] == "setLightStatus":
	# 	lightName = data['queryResult']['parameters']['light-name']
	# 	lightStatus = data['queryResult']['parameters']['light-status']
	# 	# set the light and get the response
	# 	response = webSetLight(lightName, lightStatus)
	# 	print(response)
	# 	return jsonify({'fulfillmentText': response})

	if data['queryResult']['intent']['displayName'] == "getOverallStatus":
		response = webStatus(True)
		print(response)
		return jsonify({'fulfillmentText': response})
	elif data['queryResult']['intent']['displayName'] == "getLightStatus":
		lightName = data['queryResult']['parameters']['light-name']
		response = webGetLight(lightName)
		print(response)
		return jsonify({'fulfillmentText': response})
	elif data['queryResult']['intent']['displayName'] == "setOven":
		number = data['queryResult']['parameters']['number']
		# set the light and get the response
		response = webSetOven(number)
		print(response)
		return jsonify({'fulfillmentText': response})
	elif data['queryResult']['intent']['displayName'] == "setLight":
		value = data['queryResult']['parameters']['light-status']
		# set the light and get the response
		response = webSetLight(value)
		print(response)
		return jsonify({'fulfillmentText': response})
	elif data['queryResult']['intent']['displayName'] == "setTimer":
		value = data['queryResult']['parameters']['duration']['unit']
		time = data['queryResult']['parameters']['duration']['amount']
		# set the light and get the response
		response = webSetTimer(value, time)
		print(response)
		return jsonify({'fulfillmentText': response})


if __name__ == '__main__':
    app.debug = True
    app.run()