import time

import os
import pygeoip

from irassh.insults.dao import *


class Action(object):
    def __init__(self, write):
        self.isAllowed = True
        self.write = write

    def process(self):
        self.log(None)

    def is_pass(self):
        return self.isAllowed

    def log(self, case):
        getIRasshDao().save_case(case)

    def write(self, text):
        self.write(text)


class BlockedAction(Action):
    def __init__(self, write):
        super(BlockedAction, self).__init__(write)
        self.isAllowed = False

    def process(self):
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

        location = self.get_country_code()
        self.write("Insult Message! IP= %s/location=%s\n" % (self.clientIp, location))
        self.write(getIRasshDao().get_insult_msg(location))

    def get_country_code(self):
        path, file = os.path.split(__file__)
        file_name = os.path.join(path, "GeoIP.dat")
        geo_ip = pygeoip.GeoIP(file_name)
        return geo_ip.country_code_by_addr(self.clientIp)


class FakeAction(Action):
    def __init__(self, command, terminal):
        super(FakeAction, self).__init__(terminal)

        self.command = command

    def process(self):
        self.isAllowed = False

        fake_output = getIRasshDao().get_fake_output(self.command)
        if fake_output is not None:
            self.write(fake_output + "\n")


class ActionFactory():
    def __init__(self):
        pass

    def get_action(self):
        return Action


class ActionValidator(object):
    def validate(self):
        action = ActionFactory.get_action(self)
        action.log(None)
        action.process(self)
        return action.is_pass(self)
