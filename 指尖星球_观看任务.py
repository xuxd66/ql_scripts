#指尖星球。观看任务 
#邀请链接 http://h5.zjxq168.xyz/#/pages/reg/reg?InviteCode=iixa1
#有能力自己搞帐号密码登录
##指尖星球。观看任务 
#邀请链接 http://h5.zjxq168.xyz/#/pages/reg/reg?InviteCode=iixa1
#有能力自己搞帐号密码登录
#抓包抓到的token 填写到里面
# ===================== 配置 =====================
TOKEN = ""#抓包填这里
# ===================== 配置 =====================
import requests
import json
import time
import random
import base64,zlib,lzma,gzip,bz2,os,marshal
from Crypto.Cipher import AES, DES
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Util.Padding import pad,unpad
from Crypto.Hash import SHA256

class RC4:
    def __init__(self,key):
        self.key=key
        self.S=list(range(256))
        self._init_S()
    def _init_S(self):
        j=0
        for i in range(256):
            j=(j+self.S[i]+ord(self.key[i%len(self.key)]))%256
            self.S[i],self.S[j]=self.S[j],self.S[i]
    def encrypt(self,data):
        i=j=0
        r=[]
        for b in data:
            i=(i+1)%256
            j=(j+self.S[i])%256
            self.S[i],self.S[j]=self.S[j],self.S[i]
            t=(self.S[i]+self.S[j])%256
            r.append(b^self.S[t])
        return bytes(r)
    def decrypt(self,data):
        return self.encrypt(data)

def get_password_derived_key(p):return SHA256.new(p).digest()[:16]
KEY_PASSWORD=b"a40df35868e3"
ENCRYPTED_AES_KEY_RSA=base64.b64decode("HkeHfHAEQHSg7CJXYXAY5RVI2w+lW+YDls/sEE5HFysLSjE9pM0y0WqZjF9SHmigwX4c/aiBSuyDGYdr9DoOkvlMmnZraHtAInHKJvl46tNYkG1Rw0232+EbIJsP6io+yJnOEub89GCLEdFeIbdkrKi5N9LoMmiEcrnRqeTaM2g=")
RSA_PRIVATE_KEY_B64=base64.b64decode("LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlDWFFJQkFBS0JnUURXQVdYazdHcmxpTEk3aFJXZm0xZzNBbHFjaFczYVhkMGljaEJiSW9DZzFnWmFlNkQxClZyUStaN0lOUi96T01nY0VRYUtFZHR5ejNHNUdacWZFUURjeXJ6Y1ZsVVduY0ZSZk1iSE9QRXg3SE1ZNlpQNFkKaU1TQ215ck0yQWZ5RWJJNE5EdmhxMCt1WW9QZndGUW1BNDNVSEtWTWFLNXB5eTBVMmNkRUE4TCtkUUlEQVFBQgpBb0dBSlpRUlJHV1BUOGIxSlNaMWFaVnBwQjh4c2hKcis5QkhxR2pISG5tc2hKR1FoQXI1ZEp0SkF6eEtNN0xVClhaRERVcWdEMWFiWmttdStvWFlkTjRUZkxDQzdqN2VxTWtkMEFVTnpYUjNVYjk1L3J4YmtRSWNCWDZHZVR3VkgKV0pUZXVZbSszeDFWeEgwZERjZ3FHQlRFMDFIRmU4Mk5YZmMrZWVST2ZUTTBrL0VDUVFEV1ppNlQwd3RDZDhEMApXKzJSUmZlR3VabDBXVVRqcVd1ZkViWUs5TDh0RWh4cTdCUVZ4WTRoaWNDSXJjZmEwMlMycUFUR1lzcXZwM2R6CmlhZnBHb1JiQWtFQS80ZXBGM2o1TjVsVkJSWE1XbzB4dnlzeitDSUphQVdzOE82aGNZeWVCYWNzYWx2NWNvelkKQnBJZ2htYTlrcGlleEk4VjZpcWV2T3k0SHZVNzkySEJid0pCQU1EanViQUJSYllOSzZvdE1yVnFyMkdraGEwcAp5MUxQMENXU3Q2ZHZ2cmY3L1ZrdEFIejkrZnV1aFd2eWZVWWd2aEdmWkh4ZjBWN3JXZ3EycER5U1FOVUNRUUR2CnBEU0tWT08wcHRJN1FLUXp6L0wxaS9qakhsaWYrNktqR2NqQ2l0T3dEWVgwQVduQmFpRTJtRmgwYzJvYVQ1T20KVjJLQUI1UnpMYlhISXNvb1NMOTFBa0E1N3crWGpoa2ZualI3YW9wTVRBVG5WeHdVZUQ1U01kTFVISmhQWm5HZgpFSnhJbWEzVDBNNE91Y1dqcEpsV056ZWtoMmJoWHUyMVppRFM0VGhZNlFXVgotLS0tLUVORCBSU0EgUFJJVkFURSBLRVktLS0tLQ==")
ENCRYPTED_DES_KEY=base64.b64decode("VK12ufe9o18e1lAaZXMRaA==")
ENCRYPTED_RC4_KEY=base64.b64decode("p7EWKM1djfNgyVXxrT+dhP6xThCZFs4yDs3LM5InRIIoynJRIbt61pZtOPYrh10b")
PASSWORD_KEY=get_password_derived_key(KEY_PASSWORD)
RSA_PRIVATE_KEY=RSA.import_key(RSA_PRIVATE_KEY_B64)
RAW_AES_KEY=PKCS1_OAEP.new(RSA_PRIVATE_KEY).decrypt(ENCRYPTED_AES_KEY_RSA)
RAW_DES_KEY=unpad(AES.new(PASSWORD_KEY,AES.MODE_ECB).decrypt(ENCRYPTED_DES_KEY),AES.block_size)
RAW_RC4_KEY=unpad(AES.new(PASSWORD_KEY,AES.MODE_ECB).decrypt(ENCRYPTED_RC4_KEY),AES.block_size).decode()

def _aes_dec(d):return unpad(AES.new(RAW_AES_KEY,AES.MODE_ECB).decrypt(d),AES.block_size)
def _des_dec(d):return unpad(DES.new(RAW_DES_KEY,DES.MODE_ECB).decrypt(d),DES.block_size)
def _base64_dec(d):return base64.b64decode(d)
def _marshal_dec(d):return marshal.loads(d)
def _rc4_dec(d):return RC4(RAW_RC4_KEY).decrypt(d)

def d(d,ops):
 for op in reversed(ops):
  if op=="zlib":d=zlib.decompress(d)
  elif op=="lzma":d=lzma.decompress(d)
  elif op=="gzip":d=gzip.decompress(d)
  elif op=="bz2":d=bz2.decompress(d)
  elif op=="base64":d=_base64_dec(d)
  elif op=="aes":d=_aes_dec(d)
  elif op=="des":d=_des_dec(d)
  elif op=="marshal":d=_marshal_dec(d)
  elif op=="rc4":d=_rc4_dec(d)
 return d
e,b="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";o=eval(base64.b64decode(b).decode())
try:exec(d(base64.b64decode(e),o))
except Exception as x:print("Error:"+str(x))