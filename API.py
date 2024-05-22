import configparser
import LocalSystem
from flask import Flask, jsonify, request
import json
from waitress import serve
from Crypto.Util.Padding import pad, unpad
from Crypto.Cipher import AES
from functools import reduce
from operator import add
from random import choices
import string

KEY = b'_secret_example_'
function_container = []

app = Flask(__name__)


def encrypted(data):
    return cipher.encrypt(pad(data, AES.block_size))

def decrypt_json(data):
    return json.loads(unpad(cipher.decrypt(data), AES.block_size).decode())

def encrypt_json(data):
    return cipher.encrypt(pad(json.dumps(data).encode(), AES.block_size))

def encrypted_traffic(func):
    def res(): 
        kwargs = decrypt_json(request.data)
        result = func(**kwargs)
        print(f'{func.__name__}({kwargs}) -> {result}')
        return encrypt_json(result)
    res.__name__ = 'encrypted_'+func.__name__#reduce(add, choices(string.ascii_letters, k=40), '')
    return res

@app.route('/ls', methods=['GET'])
@encrypted_traffic
def get_ls(path):
    return {'result': LocalSystem.ls(path)}

@app.route('/is_installed', methods=['GET'])
@encrypted_traffic
def get_is_installed(package):
    return {'result': LocalSystem.is_installed(package)}

@app.route('/install', methods=['GET'])
@encrypted_traffic
def get_install(package):
    response_code, stdout = LocalSystem.install(package)
    return {'response_code': response_code, 'success': LocalSystem.is_installed(package)}

@app.route('/purge', methods=['GET'])
@encrypted_traffic
def get_purge(package):
    response_code, stdout = LocalSystem.purge(package)
    return {'response_code': response_code, 'installed': LocalSystem.is_installed(package)}

@app.route('/rm', methods=['GET'])
@encrypted_traffic
def get_rm(path):
    return {'response_code': LocalSystem.rm(path)}

@app.route('/mkdir', methods=['GET'])
@encrypted_traffic
def get_mkdir(path):
    return {'response_code': LocalSystem.mkdir(path)}

@app.route('/hostname_get', methods=['GET'])
@encrypted_traffic
def get_hostname_get():
    return {'hostname': LocalSystem.get_hostname()}

@app.route('/hostname_set', methods=['GET'])
@encrypted_traffic
def get_hostname_set(hostname):
    return {'response_code': LocalSystem.set_hostname(hostname)}

@app.route('/user_list', methods=['GET'])
@encrypted_traffic
def get_user_list():
    return {'result': LocalSystem.user_list()}

@app.route('/user_del', methods=['GET'])
@encrypted_traffic
def get_user_del(username):
    return {'success': LocalSystem.user_del(username)}

@app.route('/user_add', methods=['GET'])
@encrypted_traffic
def get_user_add(username):
    return {'success': LocalSystem.user_add(username)}



if __name__ == '__main__':
    if LocalSystem.whoami() != 'root':
        print('You must run this software as root!')
        exit(-1)
    cipher = AES.new(KEY, AES.MODE_ECB)
    config_parser = configparser.RawConfigParser()
    config_path = './config.txt'
    config_parser.read(config_path)
    if 'SERVER' not in config_parser:
        print(f'Invalid config! Ensure that file "{config_path}" exists and see README!')
        exit(-2)
    if 'Host' not in config_parser['SERVER'] and 'PortNumber' not in config_parser['SERVER']:
        print('Invalid config! See README!')
        exit(-2)
    host = config_parser['SERVER']['Host']
    try:
        port = int(config_parser['SERVER']['PortNumber'])
    except ValueError:
        print('Invalid config! Port number must be a number. See README!')
        exit(-2)
    serve(app, host=host, port=port)