import json
from subprocess import Popen, PIPE
import time
from threading import Thread, Lock
import selectors
import requests
from ruamel.yaml import YAML
import platform
import datetime

min_delta = 0.0

default_severity = 4

config_file = "config.yml"

try:
    file_open = open(config_file)
    file = file_open.read()
except:
    file = """
    url: \"https://example.org/\"
    """
    print("No config file found!")
config = YAML().load(file)

webhookUrl = config['url']
# log = logging.getLogger('log2test')
# log.addHandler(journal.JournalHandler())
# log.setLevel(logging.INFO)
# log.info("Starting Log2Discord, URL: {}".format(webhookUrl))

echo "Starting Log2Discord, URL: {}".format(webhookUrl)

def parse(msg):
    txt = "New log message receieved on **{}**, Unit: **{}**, Severity: {}, Timestamp: {}, Message:"
    hostname = msg.get('_HOSTNAME')
    unit = msg.get('_SYSTEMD_UNIT')
    priority = msg.get('PRIORITY')
    timestamp = msg.get('__REALTIME_TIMESTAMP')
    try:
        timestamp = datetime.datetime.utcfromtimestamp(int(timestamp))
        timestamp = str(timestamp)
    except:
        try:
            timestamp = datetime.datetime.utcfromtimestamp(int(timestamp)/1000000)
            timestamp = str(timestamp)
        except:
            pass
    content = "```{}```".format(msg.get('MESSAGE'))
    if unit is None:
        unit = msg.get('SYSLOG_IDENTIFIER')
    try:
        if int(priority) <= 2:
            content += "\n<@800394458771750972>, <@181200309949825024>, @here, @everyone"
    except:
        pass
    message = txt.format(hostname, unit, priority, timestamp, content)
    send(message, content, msg.get('_HOSTNAME'))


def err_handling(msg, supressed):
    title = "Internal error:"
    message = "```{}```".format(msg)
    send(title, message, platform.node())
    if supressed > 0:
        send("Watchdog", f"Found {supressed} supressed messages", platform.node())


def filter(data):
    unit = data.get('_SYSTEMD_UNIT')
    if unit is None:
        unit = data.get('SYSLOG_IDENTIFIER')
    severity = data.get('PRIORITY')

    def default():
        #print("Defaulting {}, severity {}".format(unit, severity)
        if severity is None:
            # print("Accepted unit: {}, severity: {}".format(data.get('_SYSTEMD_UNIT'), data.get('PRIORITY')))
            return True
        try:
            target = config['filters']['priority']
            if int(target) is target and not target >= severity:
                # print("Rejected unit: {}, severity: {}, severity less than priority in config".format(data.get('_SYSTEMD_UNIT'), data.get('PRIORITY')))
                return False
        except:
            if not default_severity >= severity:
                # print("Rejected unit: {}, severity: {}, severity less than {}".format(data.get('_SYSTEMD_UNIT'), data.get('PRIORITY'), default_severity))
                return False
        # print("Accepted unit: {}, severity: {}".format(data.get('_SYSTEMD_UNIT'), data.get('PRIORITY')))
        return True

    try:
        severity = int(severity)
        try:
            try:
                unit_short = unit.removesuffix('.service')
                target = config['filters']['units'][unit_short]
            except KeyError:
                target = config['filters']['units'][unit]
            if int(target) is target and not target >= severity:
                # print("Rejected unit: {}, severity: {}, less severity than unit in config".format(data.get('_SYSTEMD_UNIT'), data.get('PRIORITY')))
                return False
            else:
                # print("{} is not an integet or {} is more than {severity}".format(target, target, severity))
                pass
        except KeyError:
            return default()
        except AttributeError as e:
            print(f"Error while identifying unit: {e}")
            return default()
    except Exception as e:
        print(f"Error while filtering: {e}")
        default()
    # print("Accepted unit: {}, severity: {}".format(data.get('_SYSTEMD_UNIT'), data.get('PRIORITY')))
    return True


def send(title, msg, hostname):
    if platform.node() is not None:
        name = platform.node() + " log monitor"
    else:
        name = "Log monitor"
    dataset = {
        "content": "",
        "embeds": [
            {
                "title": title,
                "description": msg,
                "color": 13191007,
                "footer": {
                    "text": platform.node()
                },
                "timestamp": datetime.datetime.now().astimezone().isoformat(),
            }
        ],
        "username": name,
        "allowed_mentions": {
            "parse": ["everyone", "users"],
        }
    }
    dataset = json.dumps(dataset)
    requests.post(webhookUrl, data=dataset, headers={'Content-type': 'application/json'})


def watchdog():
    global supressed
    global lock
    while True:
        with lock:
            if supressed > 0:
                msg = "Found {} supressed messages".format(str(supressed))
                send("Watchdog:", msg, platform.node())
                supressed = 0
        time.sleep(5)


def processing():
    sel = selectors.DefaultSelector()
    sel.register(subproc.stdout, selectors.EVENT_READ)
    sel.register(subproc.stderr, selectors.EVENT_READ)

    last_out = 0.0
    last_err = 0.0

    global supressed

    while True:
        for out, _ in sel.select():
            data = out.fileobj.readline()
            if not data:
                send("Critical error: Input lost!", "Subprocess terminated", platform.node())
                print(subproc.poll())
                import os
                os._exit(20)
            if out.fileobj is subproc.stdout:
                for line in data.splitlines():
                    line = line.rstrip()
                    try:
                        loaded = json.loads(line)
                        if filter(loaded):
                            if time.time() - last_out >= min_delta:
                                parse(loaded)
                                last_out = time.time()
                            else:
                                with lock:
                                    supressed += 1
                    except Exception as e:
                        print("Error: {}".format(e))
            else:
                if time.time() - last_err >= min_delta:
                    err_handling(data, supressed)
                    last_err = time.time()
                else:
                    with lock:
                        supressed += 1


subproc = Popen(['/usr/bin/journalctl', '-D', '/var/log/journal', '-f', '-o', 'json', '-n', '0'], text=True, stdout=PIPE, stderr=PIPE, bufsize=1)
# subproc = Popen(['/usr/bin/cat', './sample'], text=True, stdout=PIPE, stderr=PIPE, bufsize=1)

supressed = 0
lock = Lock()

if __name__ == '__main__':
    p1 = Thread(target=watchdog)
    p1.start()
    p2 = Thread(target=processing)
    p2.start()
    # print(subproc.poll())
