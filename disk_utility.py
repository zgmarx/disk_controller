#!/usr/bin/python
# encoding=utf-8

"""
Aimed to read LogicDisk and PhysicalDisk data.
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
import pprint

import storcli
import sas
import megacli


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


def pd_stat():

    pci_type = get_pci_type()

    if pci_type == 'SAS':
        pass

    elif pci_type == 'STORCLI':
        # data = storcli.get_ldpd()
        data = storcli.get_pd_detail()
        pprint.pprint(data)

    elif pci_type == 'MEGACLI':
        pass


def main():
    pd_stat()


if __name__ == "__main__":

    main()
