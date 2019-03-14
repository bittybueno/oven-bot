from flask import Flask, request, jsonify, render_template
import threading


app = Flask(__name__)

import os
import redis
import json

APPLIANCES = ['oven', 'timer', 'light']

USE_LOCAL = not 'ON_HEROKU' in os.environ


def connectToDatabase():		
	db = redis.from_url(os.environ.get("REDIS_URL"))
	return db

def init(db):
	for app in APPLIANCES:
		db.set(app, 'off')

def setOven(db, value):
	db.set('oven', value)

def setLight(db, value):
	db.set('light', value)

def setTimer(db, time, value):
	string = str(time) + ' ' + str(value)
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


@app.route("/set/oven/<value>")
def webSetOven(value):
	db = connectToDatabase()
	setOven(db, value)
	return "The oven is now set to " + str(value)

@app.route("/set/light/<value>")
def webSetLight(value):
	db = connectToDatabase()
	setLight(db, value)
	return "The oven light is now " + str(value)

@app.route("/set/timer/<time>/<value>")
def webSetTimer(value, time):
	db = connectToDatabase()
	setTimer(db, time, value)
	return "The oven timer is now set for "  + str(time) + " " + str(value)

@app.route("/chatbot")
def bot_page():
	return render_template('chatbot.html')


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

@app.route("/dialog", methods=["POST"])
def handleDialog():
	data = request.get_json()
	
	db = connectToDatabase()
	db.set("lastRequest", json.dumps(data))

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
		if (data['queryResult']['parameters']['celsius']):
			response = "Sorry, I'm American"
		elif (data['queryResult']['parameters']['number']):	
			number = data['queryResult']['parameters']['number']
			response = webSetOven(number)
		else:
			status = data['queryResult']['parameters']['oven-status']
			response = webSetOven(status)
		print(response)
		return jsonify({'fulfillmentText': response})
	elif data['queryResult']['intent']['displayName'] == "setLight":
		value = data['queryResult']['parameters']['light-status']
		response = webSetLight(value)
		print(response)
		return jsonify({'fulfillmentText': response})
	elif data['queryResult']['intent']['displayName'] == "setTimer":
		value = data['queryResult']['parameters']['duration']['unit']
		time = data['queryResult']['parameters']['duration']['amount']
		response = webSetTimer(value, time)
		print(response)
		return jsonify({'fulfillmentText': response})


if __name__ == '__main__':
    app.debug = True
    app.run()