"""Provider boundary: UI and report code never hold API credentials."""
import json
import os
import time
from typing import Protocol
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

class AIProvider(Protocol):
    def complete(self,messages:list[dict])->tuple[str,dict]: ...

class DeepSeekProvider:
    def complete(self,messages):
        from credentials import resolve_config
        config=resolve_config()
        key=config['api_key']
        if not key:raise ValueError('尚未配置 DeepSeek API Key。请在 App 的 AI 设置中填写并保存。')
        base=config['base_url'].rstrip('/')
        if not base.startswith('https://'):
            raise ValueError('AI 接口地址必须使用 HTTPS')
        payload={'model':config['model'],
                 'messages':messages,'max_tokens':4000,'stream':False}
        req=Request(base+'/chat/completions',data=json.dumps(payload).encode(),
                    headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        for attempt in range(3):
            try:
                with urlopen(req,timeout=int(os.environ.get('AI_TIMEOUT_SECONDS','120'))) as response:
                    out=json.load(response)
                content=out['choices'][0]['message']['content']
                if not isinstance(content,str) or not content.strip():raise ValueError('AI 返回空内容，请重试。')
                return content,out.get('usage',{})
            except HTTPError as e:
                if (e.code==429 or e.code>=500) and attempt<2:
                    time.sleep(attempt+1);continue
                message={401:'API Key 无效或已过期',402:'DeepSeek 账户余额不足',429:'请求过于频繁，请稍后重试'}.get(e.code,f'AI 服务返回 HTTP {e.code}')
                raise ValueError(message) from None
            except (URLError,TimeoutError):
                if attempt<2:time.sleep(attempt+1);continue
                raise ValueError('无法连接 AI 服务或请求超时，请检查网络与配置。') from None
            except (KeyError,IndexError,json.JSONDecodeError):
                raise ValueError('AI 服务返回格式异常，请检查模型配置。') from None

def get_provider()->AIProvider:
    name=os.environ.get('AI_PROVIDER','deepseek')
    if name=='deepseek':return DeepSeekProvider()
    raise ValueError('尚未实现该 AI 服务商：'+name)
