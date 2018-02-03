import time
import pygeoip,os
from irassh.insults.dao import *

class Action(object):
    def __init__(self, write):
        self.write = write

    def process(self):
        self.log(None)
        self.isAllowed = True

    def isPass(self):
        return self.isAllowed

    def log(self, case):
        getIRasshDao().saveCase(case)

    def write(self, text):
        self.write(text)


class BlockedAction(Action):
    def process(self):
        self.isAllowed = False
        self.write("Blocked command!\n")


class DelayAction(Action):
    def process(self):
        time.sleep(3)
        self.isAllowed = True
        self.write("delay ...\n")


class AllowAction(Action):
    def process(self):
        super.isAllowed = True


class InsultAction(Action):
    def __init__(self, clientIp, write):
        super(InsultAction, self).__init__(write)

        self.clientIp = clientIp

    def process(self):
        self.isAllowed = False

        location = self.getCountryCode()
        self.write("Insult Message! IP= %s/location=%s\n" % (self.clientIp, location))
        self.write(getIRasshDao().getInsultMsg(location))

    def getCountryCode(self):
        path,file = os.path.split(__file__)
        fileName = os.path.join(path, "GeoIP.dat")
        geoIp = pygeoip.GeoIP(fileName)
        return geoIp.country_code_by_addr(self.clientIp)


class FakeAction(Action):
    def __init__(self, command, terminal):
        super(FakeAction, self).__init__(terminal)

        self.command = command

    def process(self):
        self.isAllowed = False

        fakeOutput = getIRasshDao().getFakeOutput(self.command)
        if fakeOutput is not None:
            self.write(fakeOutput + "\n")


class ActionFactory():
    def getAction(self):
        return Action


class ActionValidator(object):
    def validate(self):
        action = ActionFactory.getAction(self)
        action.log(None)
        action.process(self)
        return action.isPass(self)

