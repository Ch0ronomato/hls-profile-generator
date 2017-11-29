import os
import errno
import string
from random import choice
from HLSProfile import HLSProfile
from flask import Flask, render_template, jsonify, send_file

def generateProfile(index,template):
    profile = HLSProfile("0" + str(index) + "-", .10)
    profile.setFaxs(''.join(choice(string.ascii_uppercase + string.digits) for _ in range(15)))
    profile.setTargetDuration(8.001)
    profile.setSequenceCount(5)
    profile.setSequenceStart(1234)
    profile.setTemplate(template)
    return profile

def createFile(filename, content):
    if not os.path.exists(filename):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    with open(filename, "w") as f:
        f.write(content)

app = Flask(__name__)

number_of_profiles = 6
mastertemplate = open('./templates/template.master.m3u8')
profiletemplate = open('./templates/template.profile.m3u8')
lines = [line for line in mastertemplate.readlines()]
master = HLSProfile("master_", 0.00)
master.setNumberOfProfiles(number_of_profiles)
master.setTemplate(lines)
createFile("./generated/master.m3u8", master.generateMaster())

lines = [line for line in profiletemplate.readlines()]

profs = [generateProfile(i+1,lines) for i in range(number_of_profiles)]

@app.route("/<path:manifest>")
def fetchMasterManifest(manifest):
    print manifest
    if "master" in manifest:
        return send_file("./generated/master.m3u8")
    else:
        raise Exception("RIP")

@app.route("/profiles/<path:profile>")
def fetchProfile(profile):
    if "/" in profile:
        profile = profile.split("/")[-1]
    index = int(profile.split(".m3u8")[0]) - 1
    createFile("./generated/" + profile, profs[index].generateProfile())
    return send_file("./generated/" + profile)
