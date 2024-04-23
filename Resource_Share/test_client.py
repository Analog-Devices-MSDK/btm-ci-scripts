import requests

lock_args = {
    "resources" : ["max32655_e1"]
}
unlock_args = {
    "resources" : ["max32655_e1"]
}

dev_ep = 'http://127.0.0.1:5000'



def test_get_value(attribute):
    item_ep = f'{dev_ep}/value/{attribute}'
    resp = requests.get(item_ep)
    return resp.content.decode('utf-8')
    

def test_unlock():
    unlock_ep = f"{dev_ep}/unlock"
    resp = requests.post(unlock_ep, json=lock_args)
    if resp.status_code != 200:
        print(resp)
    else:
        print('OK!')

def test_lock():
    lock_ep = f"{dev_ep}/lock"
    resp = requests.post(lock_ep, json=lock_args)

    if resp.status_code != 200:
        print(resp)
    else:
        print('OK!')
def test_reset():

    reset_ep = f"{dev_ep}/reset"
    resp = requests.post(reset_ep, json=lock_args)
    if resp.status_code != 200:
        print(resp)
    else:
        print('OK!')

def test_erase():
    reset_ep = f"{dev_ep}/erase"
    resp = requests.post(reset_ep, json=lock_args)
    if resp.status_code != 200:
        print(resp)
    else:
        print('OK!')

def test_flash():
    flash_ep = f'{dev_ep}/flash'
    args = {
        'max32655_e1' :' ~/Workspace/msdk/Examples/Bluetooth/MAX32655/BLE_dats/build/max32655.elf'
    }
    resp = requests.post(flash_ep, json=args)
    if resp.status_code != 200:
        print(resp)
    else:
        print('OK!')

test_lock()
test_unlock()
test_get_value('max32655_e1.dap_sn')
test_reset()
test_erase()
test_flash()
test_erase()
