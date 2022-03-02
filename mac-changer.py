import psutil,logging,winreg,itertools,subprocess
logging.getLogger("scapy.runtime").setLevel(logging.CRITICAL)

from scapy.arch.windows import *


netkey_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"

def get_mac(ad,cAdd):
    return ad[cAdd][0].address #get the mac address of the specified device
def get_guid(cAdd):
    sNif = get_windows_if_list(extended=False) # use scapy to get a list of the devices again, this lets us get the guids
    return [i['guid'] for i in sNif if i['name'] == cAdd][0] # parse out the guid by using the supplied name


def get_reg_value(name,reg_key_path):
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_key_path) as i:
            value, regtype = winreg.QueryValueEx(i, name)
            return value
    except:
        pass
    
def del_reg_value(name, reg_key_path):
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_key_path, 0, winreg.KEY_WRITE) as registry_key:
            winreg.DeleteValue(registry_key, name)
            return True
    except:
        return False

def create_key(name,value,reg_key_path):
    try:
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, reg_key_path):
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_key_path, 0, winreg.KEY_WRITE) as ck:
                winreg.SetValueEx(ck, name, 0, winreg.REG_SZ, value)
        return True
    except:
        return False

def get_subkeys():
    skeys = []
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, netkey_path) as rkey:
        for i in itertools.count(start=0, step=1):
            try:
                subkey_name = winreg.EnumKey(rkey, i)
                if len(subkey_name) == 4:
                    skeys.append(subkey_name)
            except OSError:
                break
    return skeys

def reset_interface(interface_name):
    cmd1 = 'netsh interface set interface name=' + interface_name + ' admin="disabled"'
    subprocess.run(cmd1)
    cmd2 = 'netsh interface set interface name=' + interface_name + ' admin="enabled"'
    subprocess.run(cmd2)

def key_function(mac,guid):
    skeys = get_subkeys()
    name = "NetworkAddress"
    for interface in skeys:
        tmp_path = netkey_path + "\\" + interface
        net_cfg_instance_id = get_reg_value("NetCfgInstanceId", tmp_path)
        if net_cfg_instance_id == guid:
            if del_reg_value(name, tmp_path):
                print("Reset MAC of " + str(guid))
            create_key(name,mac,tmp_path)
            print ("Changed key value of the selected device to: " + mac)
    return


ad = psutil.net_if_addrs() # get the network inteface addresses and info
interfaces = [print ("- {0}".format(i)) for i in ad.keys()]

cAdd = input("Enter the interface name: ")

macAdd = get_mac(ad,cAdd)
cGuid = get_guid(cAdd)
print ("----------------------------------------------------")
print ("Mac Address: {0}".format(macAdd))
print ("Guid: {0}".format(cGuid))
print ("----------------------------------------------------")

print ("IF YOU ARE USING A USB WIRELESS ADAPATER THE FIRST OCTET MUST BE 02")
print ("CORRECT FORMAT: 02-0B-15-10-42-B1:")
print ("----------------------------------------------------")
x = input ("Enter mac address to set: ")

key_function(x, cGuid)
reset_interface(cAdd)
#NetCfgInstanceId is the key we are looking for to verify the guid