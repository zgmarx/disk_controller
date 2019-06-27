#!/usr/bin/python
# encoding=utf-8

import commands
import json
import pprint

STORECLI = "/opt/MegaRAID/storcli/storcli64"


def get_controller():

    _cmd = " show all J"
    _cmd = STORECLI + _cmd

    code, out = commands.getstatusoutput(_cmd)
    if code != 0:
        return []

    out = json.loads(out)
    controller_number = out["Controllers"][0]["Response Data"][
        "Number of Controllers"]

    _controller_list = list(xrange(0, controller_number))

    return _controller_list


def get_vdpd():

    vdpd_list = []

    key_list = [
        'PD LIST',
        'VD LIST',
        'Virtual Drives',
        'Physical Drives',
    ]

    _cmd = " /call  show all  J"
    cmd = STORECLI + _cmd

    return_code, out = commands.getstatusoutput(cmd)
    if return_code != 0:
        return []

    data = json.loads(out)
    for ctl in data['Controllers']:
        vdpd = {}
        for _key in key_list:
            vdpd[_key] = ctl['Response Data'][_key]
        vdpd_list.append(vdpd)

    return vdpd_list


def get_pd_detail():

    _cmd = " /call/eall/sall  show all  J"
    cmd = STORECLI + _cmd
    return_code, out = commands.getstatusoutput(cmd)
    if return_code != 0:
        return []

    data = json.loads(out)
    pd_stats = {}
    for ctl in data['Controllers']:
        for k in ctl['Response Data']:
            if "Detailed" in k:
                for kk in ctl['Response Data'][k]:
                    if 'State' in kk:
                        pd_stats[kk] = ctl['Response Data'][k][kk]

    return pd_stats


def drive_led(controller, enclosureid, slotid, action):
    # storcli /cx[/ex]/sx start/stop locate
    cmd = " /c{c}/e{eid}/s{sid} {action} locate".format(
        action=action,
        eid=enclosureid,
        sid=slotid,
        c=controller,
    )
    cmd = STORECLI + cmd
    _response, _out = commands.getstatusoutput(cmd)

    if _response != 0:
        return False

    return True


def main():

    data = get_pd_detail()
    pprint.pprint(data)


if __name__ == "__main__":

    main()
