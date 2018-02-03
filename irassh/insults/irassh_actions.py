import time

import os
import pygeoip

from irassh.insults import irassh_dao


class Action(object):
    def __init__(self, write):
        self.is_allowed = True
        self.write = write

    def process(self):
        """
        """

    def is_pass(self):
        return self.is_allowed

    def write(self, text):
        self.write(text)


class BlockedAction(Action):
    def __init__(self, write):
        super(BlockedAction, self).__init__(write)
        super.is_allowed = False

    def process(self):
        self.write("Blocked command!\n")


class DelayAction(Action):
    def process(self):
        time.sleep(3)
        super.is_allowed = True
        self.write("delay ...\n")


class AllowAction(Action):
    def process(self):
        super.is_allowed = True


class InsultAction(Action):
    def __init__(self, clientIp, write):
        super(InsultAction, self).__init__(write)

        self.clientIp = clientIp

    def process(self):
        super.is_allowed = False

        location = self.get_country_code()
        self.write("Insult Message! IP= %s/location=%s\n" % (self.clientIp, location))
        self.write(irassh_dao.getIRasshDao().getInsultMsg(location))

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
        super.is_allowed = False

        fake_output = irassh_dao.getIRasshDao().getFakeOutput(self.command)
        if fake_output is not None:
            self.write(fake_output + "\n")


class ActionFactory():
    def __init__(self):
        pass

    def getAction(self):
        return Action


class ActionValidator(object):
    def validate(self):
        action = ActionFactory.getAction(self)
        action.process(self)
        return action.is_pass(self)


class CasePersister(object):
    def log(self, case):
        if "initial_cmd" in case.keys():
            irassh_dao.getIRasshDao().saveCase(case)

    def saveState(self, case, cmd):
        if "initial_cmd" in case.keys():
            case["next_cmd"] = cmd
        case["initial_cmd"] = cmd
