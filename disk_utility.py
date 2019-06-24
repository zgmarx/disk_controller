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

import storcli
import sas
import megacli

GOOD_PD = [
    'Online, Spun Up',
    'Onln',
]

GOOD_VD = [
    "Optimal",
    "Optl",
]


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


def vdpd_stat():
    """
    vd = virtual disk
    # ld = logic disk
    """

    pci_type = get_pci_type()

    if pci_type == 'SAS':
        data = sas.get_arrays()

    elif pci_type == 'STORCLI':
        data = storcli.get_vdpd()

    elif pci_type == 'MEGACLI':
        data = megacli.get_vdpd_storcli_format()

    return data


def pd_media_stat():
    """
    pd = physic disk
    """

    pci_type = get_pci_type()

    if pci_type == 'SAS':  # 10.101.1.39
        data = sas.get_disks()

    elif pci_type == 'STORCLI':  # 10.101.0.28
        data = storcli.get_pd_detail()

    elif pci_type == 'MEGACLI':  # 10.104.17.152
        data = megacli.get_pd_detail_storcli_format()

    return data


def main():

    pd_not_ok = []
    vd_not_ok = []
    vdpd = vdpd_stat()
    for adapter in vdpd:
        for xd in adapter["PD LIST"]:
            if xd["State"] not in GOOD_PD:
                pd_not_ok.append(xd)

        for xd in adapter["VD LIST"]:
            if xd["State"] not in GOOD_VD:
                vd_not_ok.append(xd)

    print "pd_not_ok", json.dumps(
        pd_not_ok, default=repr, indent=4, sort_keys=True)

    print "vd_not_ok", json.dumps(
        vd_not_ok, default=repr, indent=4, sort_keys=True)

    pd_media = pd_media_stat()
    pd_media_not_0 = {}
    check_list = [
        "Media Error Count",
        "Other Error Count",
        "Predictive Failure Count",
    ]
    for k, media in pd_media.items():
        for _c in check_list:
            _v = int(media[_c])
            if _v != 0:
                if k not in pd_media_not_0:
                    pd_media_not_0[k] = {}
                pd_media_not_0[k][_c] = _v
    print "pd_media_not_0", json.dumps(
        pd_media_not_0, default=repr, indent=4, sort_keys=True)


if __name__ == "__main__":

    main()
