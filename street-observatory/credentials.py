"""Browser-profile scoped API credentials, encrypted with Windows user DPAPI.

The browser holds only an opaque HttpOnly profile token. Keys are never returned
through read APIs. This local desktop profile is not a public website account.
"""
from contextvars import ContextVar
import ctypes
from ctypes import wintypes
import hashlib
import os
import re

CURRENT_PROFILE=ContextVar('street_profile',default=None)

class Blob(ctypes.Structure):
    _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]

def crypt(data:bytes,owner:str,decrypt=False)->bytes:
    if os.name!='nt':raise ValueError('持久保存密钥目前仅支持 Windows 桌面版。')
    crypt32=ctypes.WinDLL('crypt32',use_last_error=True)
    kernel32=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel32.LocalFree.argtypes=[ctypes.c_void_p];kernel32.LocalFree.restype=ctypes.c_void_p
    source_buffer=ctypes.create_string_buffer(data)
    entropy_buffer=ctypes.create_string_buffer(hashlib.sha256(owner.encode()).digest())
    source=Blob(len(data),ctypes.cast(source_buffer,ctypes.POINTER(ctypes.c_ubyte)))
    entropy=Blob(32,ctypes.cast(entropy_buffer,ctypes.POINTER(ctypes.c_ubyte)))
    output=Blob()
    function=crypt32.CryptUnprotectData if decrypt else crypt32.CryptProtectData
    function.restype=wintypes.BOOL
    function.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    if not function(ctypes.byref(source),None,ctypes.byref(entropy),None,None,1,ctypes.byref(output)):
        raise ValueError('无法读取本用户的加密密钥，请重新填写并保存。' if decrypt else 'Windows 无法加密保存密钥，请检查当前用户环境。')
    try:return ctypes.string_at(output.data,output.size)
    finally:kernel32.LocalFree(ctypes.cast(output.data,ctypes.c_void_p))

def owner_hash(token):return hashlib.sha256(token.encode()).hexdigest()

def resolve_config():
    from app import conn
    owner=CURRENT_PROFILE.get()
    if owner is None:
        # Developer CLI calls can still use environment configuration; browser
        # requests always have their own profile and never inherit this key.
        return {'api_key':os.environ.get('DEEPSEEK_API_KEY',''),
                'model':os.environ.get('DEEPSEEK_MODEL','deepseek-flash'),
                'base_url':os.environ.get('DEEPSEEK_BASE_URL','https://api.deepseek.com')}
    with conn() as c:
        row=c.execute('SELECT encrypted_key,model FROM ai_credentials WHERE owner_hash=?',(owner,)).fetchone()
    if not row:return {'api_key':'','model':os.environ.get('DEEPSEEK_MODEL','deepseek-flash'),'base_url':'https://api.deepseek.com'}
    return {'api_key':crypt(bytes(row['encrypted_key']),owner,decrypt=True).decode(),
            'model':row['model'],'base_url':'https://api.deepseek.com'}

def public_config():
    config=resolve_config();key=config.pop('api_key')
    return {**config,'configured':bool(key),'key_hint':'••••'+key[-4:] if key else '',
            'storage':'Windows 用户加密存储','scope':'当前 Windows 用户 / 浏览器配置',
            'profile_scoped':CURRENT_PROFILE.get() is not None}

def save_config(body):
    from app import conn
    owner=CURRENT_PROFILE.get()
    if not owner:raise ValueError('请从 App 设置界面保存密钥。')
    model=body.get('model','deepseek-flash')
    if not isinstance(model,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,99}',model):raise ValueError('模型名称不正确。')
    key=body.get('api_key','')
    if not isinstance(key,str):raise ValueError('API Key 格式不正确。')
    key=key.strip()
    if not key:
        old=resolve_config()['api_key']
        if not old:raise ValueError('请先填写 DeepSeek API Key。')
        key=old
    if not key.startswith('sk-') or not 16<=len(key)<=512 or any(ord(c)<33 or ord(c)>126 for c in key):
        raise ValueError('请填写完整的 DeepSeek API Key（以 sk- 开头，不能包含空格）。')
    encrypted=crypt(key.encode(),owner)
    with conn() as c:
        c.execute('INSERT INTO ai_credentials(owner_hash,encrypted_key,model) VALUES(?,?,?) ON CONFLICT(owner_hash) DO UPDATE SET encrypted_key=excluded.encrypted_key,model=excluded.model',
                  (owner,encrypted,model))
    return public_config()

def delete_config():
    from app import conn
    owner=CURRENT_PROFILE.get()
    if not owner:raise ValueError('当前配置不存在。')
    with conn() as c:c.execute('DELETE FROM ai_credentials WHERE owner_hash=?',(owner,))
    return public_config()

def config_fingerprint():
    config=resolve_config()
    return hashlib.sha256((config['model']+'\0'+config['api_key']).encode()).hexdigest()[:16]
