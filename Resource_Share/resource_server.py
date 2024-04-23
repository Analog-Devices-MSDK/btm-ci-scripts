#! /usr/bin/env python3
#! /usr/bin/env python3
###############################################################################
#
#
# Copyright (C) 2023 Maxim Integrated Products, Inc., All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL MAXIM INTEGRATED BE LIABLE FOR ANY CLAIM, DAMAGES
# OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# Except as contained in this notice, the name of Maxim Integrated
# Products, Inc. shall not be used except as stated in the Maxim Integrated
# Products, Inc. Branding Policy.
#
# The mere transfer of this software does not imply any licenses
# of trade secrets, proprietary technology, copyrights, patents,
# trademarks, maskwork rights, or any other form of intellectual
# property whatsoever. Maxim Integrated Products, Inc. retains all
# ownership rights.
#
##############################################################################
#
# Copyright 2023 Analog Devices, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
##############################################################################
"""
resource_server.py

Description: resource_server

"""
import json
from resource_manager import ResourceManager
from flask import Flask, jsonify, request




rm = ResourceManager()
app = app = Flask(__name__)

def get_resources_from_request():
    body = request.get_json()
    key = 'resources'

    if key in body and isinstance(body[key], list) or isinstance(body[key], set):
        return set(body[key])
    else:
        return 'Could not parse resources', 400


@app.route('/value/<attribute>', methods=['GET'])
def get_item_value(attribute):
    
    try:
        value = rm.get_item_value(attribute)
    except ValueError or KeyError as e:
        return {e.__str__}, 500
    
    return value



@app.route('/lock', methods=['GET','POST'])
def lock_boards():
    
    if request.method == 'GET':
        return jsonify(rm.get_resource_usage())

    body = request.get_json()
    key = 'resources'

    if key in body and isinstance(body[key], list) or isinstance(body[key], set):
        resources = set(body[key])
    else:
        return 'Could not parse resources', 400

    if not rm.lock_resources(resources):
    
        return 'Failed to lock resources !', 500
    

    return jsonify(success=True), 200
    
@app.route('/unlock', methods=['POST'])
def unlock_boards():
    
    body = request.get_json()
    key = 'resources'

    if key in body and isinstance(body[key], list) or isinstance(body[key], set):
        resources = set(body[key])
    else:
        return 'Could not parse resources', 400

    unlock_count = rm.unlock_resources(resources)
    
    if unlock_count != len(resources):
        return f'Failed to unlock resources ! Successfully unlocked {unlock_count} boards', 500
    
    return jsonify(success=True)
    

@app.route('/erase', methods=['POST'])
def erase_boards():
    
    maybe_resources = get_resources_from_request()
    if not isinstance(maybe_resources, set):
        return maybe_resources 
    
    erase_all = True
    for resource in maybe_resources:
        if not rm.resource_erase(resource):
            erase_all = False

    if not erase_all:
        return f'Failed to erase all resources', 500
    
    
    return jsonify(success=True)

@app.route('/reset', methods=['POST'])
def reset_boards():
    
    maybe_resources = get_resources_from_request()
    if not isinstance(maybe_resources, set):
        return maybe_resources 
    
    reset_all = True
    for resource in maybe_resources:
        if not rm.resource_reset(resource):
            reset_all = False

    if not reset_all:
        return f'Failed to reset all resources', 500
    
    return jsonify(success=True)

@app.route('/flash', methods=['POST'])
def flash_boards():
    

    body = request.get_json()
    
    flash_all = True
    for resource in body:
        flash_all = rm.resource_flash(resource, body[resource])
    
    if not flash_all:
        return f'Failed to flash all resources', 500

    
    return jsonify(success=True)

if __name__ == '__main__':
    
    app.run()
