#!/usr/bin/python
# encoding=utf-8

'''
1. install sas2ircu
2. run as root
'''

import re
import commands
import json

ARRAYINFO = [
    'DG/VD',  # 'id',
    'State',  # Status of volume
    'TYPE',   # RAID level 'raid_level',
    'Size',
    'disks',
]

DISKINFO = [
    'DID',      # device id
    'EID:SID',  # EnclosureID:SlotID
    'Size',     # size
    'Intf',     # Protocol
    'Model',    # Model Number
    'SN',       # Serial No
    'State',
    'Med',      # Drive Type
    'Firmware Revision',  # Firmware Revision
]

SAS_CMD = "/usr/local/bin/sas3ircu"


def get_controllers():
    cmd = SAS_CMD + " LIST"
    return_code, out = commands.getstatusoutput(cmd)
    if return_code != 0:
        return []
    controllers = []
    for line in out.split('\n'):
        if re.match(r'^\s+[0-9]+\s+\w+.*', line):
            ctl_index, ctl_type = line.split()[0], line.split()[1]
            controllers.append((ctl_index, ctl_type))
    return controllers


def get_arrays():
    res = []
    _ctl_list = get_controllers()
    for ctl in _ctl_list:
        res.extend(
            [dict(zip(ARRAYINFO, a)) for a in _get_array(ctl[0])]
        )
    return res


def _get_array(ctrlnmbr):
    cmd = SAS_CMD+' '+ctrlnmbr+' DISPLAY'
    return_code, res = commands.getstatusoutput(cmd)
    if return_code != 0:
        return []
    array_list = []

    arrayid = None
    state = ''
    _type = ''
    size = ''
    disklist = []

    for line in res.split('\n'):
        if re.match('^IR volume [0-9]+.*$', line):
            if arrayid is not None:
                array_list.append((arrayid, state, _type, size, disklist))
                disklist = []
            arrayid = re.match('^IR volume ([0-9]+).*$', line).group(1)
        if re.match(r'^\s*Status of volume.*$', line):
            state = line.split(':')[1].strip()
        if re.match(r'^\s*RAID level.*$', line):
            _type = line.split(':')[1].strip()
        if re.match(r'^\s*Size \(in MB\)\s+.*$', line):
            size = line.split(':')[1].strip()
            size = str(int(round((float(size) / 1000))))+'G'
        if re.match(r'^\s*PHY\[[0-9]+\] Enclosure#/Slot#.*$', line):
            disksid = ':'.join(line.split(':')[1:]).strip()
            disklist.append(disksid)
    array_list.append((arrayid, state, _type, size, disklist))
    # ie: [0, 'Okay (OKY)', 'RAID1', '1800G', [['1', '0'], ['1', '1']]]
    return array_list


def get_disks():
    res = []
    _ctl_list = get_controllers()
    for ctl in _ctl_list:
        for d in _get_disks(ctl[0]):
            _disk = dict(zip(DISKINFO, d))
            res.append(_disk)
    return res


def _get_disks(ctrlnmbr):
    cmd = SAS_CMD+' '+ctrlnmbr+' DISPLAY'
    return_code, res = commands.getstatusoutput(cmd)
    if return_code != 0:
        return []
    disk_list = []

    diskid = -1
    enclid = ''
    slotid = ''
    realid = ['', '']
    disksize = ''
    interface = ''
    diskmodel = ''
    diskserial = ''
    state = ''
    dirvetype = ''
    firmwarerevision = ''

    skipped = False

    for line in res.split('\n'):
        if re.match('^Device is a Enclosure services device.*$', line):
            skipped = True
        if re.match('^Device is a Hard disk.*$', line):
            skipped = False
            if diskid == -1:
                diskid = diskid+1
            else:
                disk_list.append(
                    (str(diskid),
                     realid,
                     disksize,
                     interface,
                     diskmodel,
                     diskserial,
                     state,
                     dirvetype,
                     firmwarerevision))
                diskid = diskid+1
        if not skipped:
            if re.match(r'^\s*Enclosure #.*$', line):
                enclid = line.split(':')[1].strip()
            if re.match(r'^\s*Slot #.*$', line):
                slotid = line.split(':')[1].strip()
                realid = ':'.join([enclid, slotid])
            if re.match(r'^\s*State.*$', line):
                state = line.split(':')[1].strip()
            if re.match(r'^\s*Size.*$', line):
                disksize = line.split(':')[1].split('/')[0].strip()
                disksize = str(int(round((float(disksize) / 1000))))+'G'
            if re.match(r'^\s*Model Number.*$', line):
                diskmodel = line.split(':')[1].strip()
            if re.match(r'^\s*Firmware Revision.*$', line):
                firmwarerevision = line.split(':')[1].strip()
            if re.match(r'^\s*Serial No.*$', line):
                diskserial = line.split(':')[1].strip()
            if re.match(r'^\s*Protocol.*$', line):
                interface = line.split(':')[1].strip()
            if re.match(r'^\s*Drive Type.*$', line):
                dirvetype = line.split(':')[1].strip()
    """
    ie:
    {
        "DID": "8",
        "EID:SID": "2:6",
        "Firmware Revision": "TAF0",
        "Intf": "SATA",
        "Med": "SATA_HDD",
        "Model": "HGST HUS726060AL",
        "SN": "NCHRVW4S",
        "Size": "5723G",
        "State": "Ready (RDY)"
    },
    """
    disk_list.append(
        (str(diskid),
         realid,
         disksize,
         interface,
         diskmodel,
         diskserial,
         state,
         dirvetype,
         firmwarerevision))
    return disk_list


def get_sas_storage_info():
    import collections
    res = collections.defaultdict(dict)

    for _r in get_controllers():
        _idx = _r[0]
        res[_idx]['type'] = _r[1]

        res[_idx]['arrays'] = {}
        res[_idx]['disks'] = {}

        for _array in _get_array(_idx):
            _array_id = _array[0]
            res[_idx]['arrays'][_array_id] = {}
            res[_idx]['arrays'][_array_id].update(zip(ARRAYINFO, _array))

        for _disk in _get_disks(_idx):
            _disk_id = _disk[0]
            res[_idx]['disks'][_disk_id] = {}
            res[_idx]['disks'][_disk_id].update(zip(DISKINFO, _disk))

    return dict(res)


def get_vdpd_storcli_format():

    _return = []

    vd_list = get_arrays()
    pd_list = get_disks()

    _return.append(
        {
            'PD LIST': pd_list,
            'VD LIST': vd_list,
            'Physical Drives': len(pd_list),
            'Virtual Drives': len(vd_list),
        }
    )

    return _return


if __name__ == '__main__':
    try:
        print json.dumps(
            get_vdpd_storcli_format(),
            default=repr,
            indent=4,
            sort_keys=True)
    except Exception as ex:
        print ex
        import sys
        sys.exit(1)
