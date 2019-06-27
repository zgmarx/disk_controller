#!/usr/bin/python
# encoding=utf-8

"""
Aimed to read VirtualDisk and PhysicalDisk data.
If RAID controller found, use `storeCLI` first, then `Megacli`,
If SAS controller found use `sas3ircu`.

https://supportex.net/blog/2010/11/determine-raid-controller-type-model/

工具的应用场景：
1、换盘的时候可以根据需要闪灯，比如传参数，check，会检查哪些盘有问题；
检查完后如果有异常的盘，会提示哪些有异常了，盘点号，slot等
提示要对异常的哪块盘进行操作，操作什么，闪灯？

2、更新cmdb，记录磁盘状态
3、监控数据汇报
"""

import commands
import json
import time
import argparse

import storcli
import sas
import megacli
import config


def get_pci_type():

    shell_cmd = 'lspci | grep RAID'

    return_code, out = commands.getstatusoutput(shell_cmd)

    if return_code != 0:
        _pci_type = 'SAS'

    else:
        if storcli.get_controller():
            _pci_type = 'STORCLI'
        else:
            _pci_type = 'MEGACLI'

    return _pci_type


def vdpd_stat(pci_type):
    """
    vd = virtual disk
    # ld = logic disk
    """
    if pci_type == 'SAS':
        _list = sas.get_vdpd_storcli_format()

    elif pci_type == 'STORCLI':
        _list = storcli.get_vdpd()

    elif pci_type == 'MEGACLI':
        _list = megacli.get_vdpd_storcli_format()

    return _list


def pd_media_stat(pci_type):
    """
    pd = physic disk
    """
    pci_type = get_pci_type()

    if pci_type == 'SAS':  # 10.101.1.39
        data = {}  # SAS controller pd detail has no media error info.

    elif pci_type == 'STORCLI':  # 10.101.0.28
        data = storcli.get_pd_detail()

    elif pci_type == 'MEGACLI':  # 10.104.17.152
        data = megacli.get_pd_detail_storcli_format()

    return data


def check():
    """
    check all vd and pd, display pd vd in not ok condition and pd errors.
    """

    pci_type = get_pci_type()

    pd_not_ok = []
    vd_not_ok = []
    vdpd_list = vdpd_stat(pci_type)

    for adapter in vdpd_list:
        for xd in adapter["PD LIST"]:
            if xd["State"] not in config.GOOD_PD:
                xd['Adapter'] = vdpd_list.index(adapter)
                pd_not_ok.append(xd)

        for xd in adapter["VD LIST"]:
            if xd["State"] not in config.GOOD_VD:
                xd['Adapter'] = vdpd_list.index(adapter)
                vd_not_ok.append(xd)

    pd_media = pd_media_stat(pci_type)
    pd_errors = {}

    for k, media in pd_media.items():
        for check_key, warn_value in config.CHECK_LIST:
            value_on_host = int(media[check_key])
            if value_on_host >= warn_value:
                if k not in pd_errors:
                    pd_errors[k] = {}
                pd_errors[k][check_key] = value_on_host

    return {
        "PD Not ok": pd_not_ok,
        "VD Not ok": vd_not_ok,
        "PD Errors": pd_errors,
    }


def list_all():
    """
    display all pd vd information in json format
    """
    pci_type = get_pci_type()

    vdpd_list = vdpd_stat(pci_type)
    pd_media = pd_media_stat(pci_type)

    return {
        "VDPD Details": vdpd_list,
        "PD Errors Details": pd_media,
    }


def active_led():
    """
    first display the result of `check`
    then help to locate the disk drive on an enclosure.
    """

    data = check()
    data.pop("VD Not ok")

    disks = data['PD Not ok']
    for d in disks:
        print "disk No.:", disks.index(d)
        print json.dumps(d, default=repr, indent=4, sort_keys=True)

    # ask which one u want to change
    try:
        change_which = int(
            raw_input('input the number of which disk you want to change: '))
    except ValueError:
        print "Not a number, plz input the number of the disk."

    # run led blink
    pci_type = get_pci_type()

    if pci_type == 'STORCLI':

        disk = disks[change_which]
        controller = disk['Adapter']
        eid, sid = disk['EID:Slt'].split(':')

        print "start to blink led on {eid}:{sid} result is: {r}".format(
            eid=eid,
            sid=sid,
            r=storcli.drive_led(controller, eid, sid, 'start'),
        )
        time.sleep(10)
        print "stop to blink led on {eid}:{sid} result is: {r}".format(
            eid=eid,
            sid=sid,
            r=storcli.drive_led(controller, eid, sid, 'stop'),
        )

    elif pci_type == 'MEGACLI':

        disk = disks[change_which]
        controller = disk['Adapter']
        eid = disk['EnclosureID']
        sid = disk['SlotID']

        print "start to blink led on {eid}:{sid} result is: {r}".format(
            eid=eid,
            sid=sid,
            r=megacli.drive_led(controller, eid, sid, 'start'),
        )
        time.sleep(10)
        print "stop to blink led on {eid}:{sid} result is: {r}".format(
            eid=eid,
            sid=sid,
            r=megacli.drive_led(controller, eid, sid, 'stop'),
        )

    return data


def main():

    parser = argparse.ArgumentParser(description='disk utility')

    for short, dest, help in (
        ('-c', 'check', 'check all vd and pd'),
        ('-l', 'list_all', 'display all pd vd information in json format'),
        ('-a', 'active_led', 'locate the disk drive on an enclosure'),
    ):
        parser.add_argument(short,
                            action='store_true',
                            default=False,
                            dest=dest,
                            help=help)

    args = parser.parse_args()

    if args.check:
        data = check()
        print json.dumps(data, default=repr, indent=4, sort_keys=True)

    elif args.list_all:
        data = list_all()
        print json.dumps(data, default=repr, indent=4, sort_keys=True)

    elif args.active_led:
        active_led()


if __name__ == "__main__":

    main()
