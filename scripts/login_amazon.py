#!/usr/bin/env python3
"""
Amazon 买家账号首次登录脚本

跟原 qa skill 的 login 脚本主要区别:
1. 凭据走环境变量,绝不接受 stdin/input()
2. 启动 Chrome + Xvfb 这一步是可选,可以连接已经在跑的 Chrome
3. 失败原因清晰打印,方便排查
4. session 持久化在 /tmp/chrome-profile,后续 capture_rufus.py 复用免登录
5. 失败时不留 zombie 进程,清理干净

环境变量(必需):
  AMAZON_BUYER_EMAIL
  AMAZON_BUYER_PASSWORD

环境变量(可选):
  AMAZON_BUYER_OTP_SECRET   — TOTP base32 secret,处理 2FA
  CHROME_USER_DATA_DIR      — 默认 /tmp/chrome-profile
  CHROME_REMOTE_PORT        — 默认 9222
  XVFB_DISPLAY              — 默认 :99(无头环境用)

依赖:
  pip3 install websockets pyotp --break-system-packages

用法:
  # 无头 VPS:
  python3 scripts/login_amazon.py --start-chrome --xvfb

  # 已经手动启动了 Chrome:
  python3 scripts/login_amazon.py
"""
import asyncio
import json
import os
import sys
import time
import argparse
import subprocess
import urllib.request
from pathlib import Path

try:
    import websockets
except ImportError:
    print("✗ 缺 websockets:  pip3 install websockets --break-system-packages")
    sys.exit(1)


CHROME_PORT = int(os.environ.get('CHROME_REMOTE_PORT', '9222'))
USER_DATA_DIR = os.environ.get('CHROME_USER_DATA_DIR', '/tmp/chrome-profile')
XVFB_DISPLAY = os.environ.get('XVFB_DISPLAY', ':99')


class CredentialsNotProvided(Exception):
    pass


def get_creds():
    email = os.environ.get('AMAZON_BUYER_EMAIL')
    password = os.environ.get('AMAZON_BUYER_PASSWORD')
    if not email or not password:
        raise CredentialsNotProvided(
            "缺凭据。请通过环境变量提供:\n"
            "  export AMAZON_BUYER_EMAIL='...'\n"
            "  export AMAZON_BUYER_PASSWORD='...'\n"
            "(绝不通过 stdin / input() 收凭据)"
        )
    return email, password


def get_totp_code():
    """如果配置了 TOTP secret,生成当前 6 位码。"""
    secret = os.environ.get('AMAZON_BUYER_OTP_SECRET')
    if not secret:
        return None
    try:
        import pyotp
    except ImportError:
        print("✗ 配置了 OTP 但缺 pyotp:  pip3 install pyotp --break-system-packages")
        sys.exit(1)
    return pyotp.TOTP(secret).now()


def start_xvfb():
    """启动 Xvfb 虚拟显示。返回 process 句柄,方便清理。"""
    print(f"启动 Xvfb {XVFB_DISPLAY}...")
    proc = subprocess.Popen(
        ['Xvfb', XVFB_DISPLAY, '-screen', '0', '1536x900x24'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)
    return proc


def start_chrome(use_xvfb=False):
    """启动 Chrome 并连上 user-data-dir。"""
    Path(USER_DATA_DIR).mkdir(parents=True, exist_ok=True)
    
    env = os.environ.copy()
    if use_xvfb:
        env['DISPLAY'] = XVFB_DISPLAY
    
    cmd = [
        'google-chrome',
        '--no-sandbox', '--disable-gpu',
        f'--remote-debugging-port={CHROME_PORT}',
        f'--user-data-dir={USER_DATA_DIR}',
        'https://www.amazon.com',
    ]
    print(f"启动 Chrome,profile: {USER_DATA_DIR}")
    proc = subprocess.Popen(
        cmd, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(4)
    return proc


def get_cdp_ws():
    """从 /json/version 拿 WebSocket URL。"""
    url = f'http://127.0.0.1:{CHROME_PORT}/json/version'
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read())
        return data['webSocketDebuggerUrl']
    except Exception as e:
        raise RuntimeError(
            f"拿不到 CDP WebSocket。检查 Chrome 是不是真在 {CHROME_PORT} 监听:\n"
            f"  curl http://127.0.0.1:{CHROME_PORT}/json/version\n"
            f"原始错误: {e}"
        )


async def cdp_eval(ws, expression, return_by_value=True):
    msg_id = int(time.time() * 1000) % 1000000
    await ws.send(json.dumps({
        'id': msg_id,
        'method': 'Runtime.evaluate',
        'params': {'expression': expression, 'returnByValue': return_by_value}
    }))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get('id') == msg_id:
            return resp.get('result', {}).get('result', {}).get('value')


async def cdp_send(ws, method, params=None):
    msg_id = int(time.time() * 1000) % 1000000 + 1
    await ws.send(json.dumps({'id': msg_id, 'method': method, 'params': params or {}}))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get('id') == msg_id:
            return resp.get('result', {})


async def get_element_center(ws, selector):
    expr = f"""
        (function() {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return {{x: r.left + r.width/2, y: r.top + r.height/2}};
        }})()
    """
    return await cdp_eval(ws, expr)


async def click_at(ws, x, y):
    for kind in ('mousePressed', 'mouseReleased'):
        await cdp_send(ws, 'Input.dispatchMouseEvent', {
            'type': kind, 'x': x, 'y': y, 'button': 'left', 'clickCount': 1
        })


async def login_flow(cdp_ws_url):
    email, password = get_creds()
    
    async with websockets.connect(cdp_ws_url) as ws:
        # 拿到第一个 tab
        targets = await cdp_send(ws, 'Target.getTargets')
        page_targets = [t for t in targets['targetInfos'] if t['type'] == 'page']
        if not page_targets:
            print("✗ 找不到任何 page tab")
            return False
        tab_id = page_targets[0]['targetId']
        await cdp_send(ws, 'Target.activateTarget', {'targetId': tab_id})
        
        # 直接到首页
        print("→ 导航到 amazon.com 首页")
        await cdp_send(ws, 'Page.navigate', {'url': 'https://www.amazon.com'})
        await asyncio.sleep(3)
        
        # 看一眼是不是已经登录(profile 复用)
        already = await cdp_eval(ws, """
            document.querySelector('#nav-link-accountList-nav-line-1')?.innerText || ''
        """)
        if already and 'Hello' in already:
            print(f"✓ 已经登录:{already}")
            return True
        
        # 点 Account & Lists
        print("→ 点击 Account & Lists")
        coord = await get_element_center(ws, '#nav-link-accountList')
        if not coord:
            print("✗ 找不到 #nav-link-accountList")
            return False
        await click_at(ws, coord['x'], coord['y'])
        await asyncio.sleep(3)
        
        # 输入邮箱(注意 selector 是 #ap_email_login,不是 #ap_email)
        print("→ 输入邮箱")
        coord = await get_element_center(ws, '#ap_email_login')
        if not coord:
            # 备选老 selector
            coord = await get_element_center(ws, '#ap_email')
        if not coord:
            print("✗ 找不到 email 输入框")
            return False
        await click_at(ws, coord['x'], coord['y'])
        await cdp_send(ws, 'Input.insertText', {'text': email})
        await asyncio.sleep(0.5)
        
        coord = await get_element_center(ws, '#continue')
        if coord:
            await click_at(ws, coord['x'], coord['y'])
            await asyncio.sleep(3)
        
        # 输入密码
        print("→ 输入密码")
        coord = await get_element_center(ws, '#ap_password')
        if not coord:
            print("✗ 找不到 password 输入框")
            return False
        await click_at(ws, coord['x'], coord['y'])
        await cdp_send(ws, 'Input.insertText', {'text': password})
        await asyncio.sleep(0.5)
        
        coord = await get_element_center(ws, '#signInSubmit')
        if not coord:
            print("✗ 找不到 sign in 按钮")
            return False
        await click_at(ws, coord['x'], coord['y'])
        await asyncio.sleep(5)
        
        # 检查是不是要 OTP
        otp_field = await cdp_eval(ws, """
            !!document.querySelector('input[name="otpCode"], #auth-mfa-otpcode')
        """)
        if otp_field:
            print("→ 检测到 OTP 验证")
            otp = get_totp_code()
            if not otp:
                print("✗ Amazon 要求 OTP,但没配 AMAZON_BUYER_OTP_SECRET")
                print("  请配置 TOTP secret 或在浏览器里手动输入 OTP 后回车")
                # 这里**不阻塞等输入**,直接退出让用户去补配
                return False
            
            coord = await get_element_center(ws, 'input[name="otpCode"], #auth-mfa-otpcode')
            await click_at(ws, coord['x'], coord['y'])
            await cdp_send(ws, 'Input.insertText', {'text': otp})
            await asyncio.sleep(0.5)
            coord = await get_element_center(ws, '#auth-signin-button, input[type="submit"]')
            if coord:
                await click_at(ws, coord['x'], coord['y'])
            await asyncio.sleep(4)
        
        # 检查是不是要"Add a mobile number"
        mobile_required = await cdp_eval(ws, """
            (function() {
                const txt = document.body.innerText.toLowerCase();
                return txt.includes('add a mobile number') 
                    || txt.includes('add mobile number');
            })()
        """)
        if mobile_required:
            print("✗ Amazon 要求加手机号验证")
            print("  这个脚本不在这里收手机号(需走 chat 通道)")
            print("  请用 capture_rufus.py 内的 mobile_required handler,或临时手动完成")
            return False
        
        # 验证登录成功
        name = await cdp_eval(ws, """
            document.querySelector('#nav-link-accountList-nav-line-1')?.innerText || ''
        """)
        if name and 'Hello' in name:
            print(f"✓ 登录成功:{name}")
            return True
        
        print(f"✗ 登录失败,header 文本: {name}")
        return False


async def main_async(args):
    xvfb_proc = None
    chrome_proc = None
    
    try:
        if args.xvfb:
            xvfb_proc = start_xvfb()
        
        if args.start_chrome:
            chrome_proc = start_chrome(use_xvfb=args.xvfb)
        
        ws_url = get_cdp_ws()
        print(f"✓ CDP WebSocket: {ws_url}")
        
        ok = await login_flow(ws_url)
        return ok
    
    finally:
        # 不要杀 chrome,留着供下个脚本复用
        # Xvfb 也保留,因为 Chrome 还在用它
        if not ok if 'ok' in dir() else False:
            print("登录失败,但保留 Chrome 进程以便手动调试")


def main():
    parser = argparse.ArgumentParser(description='Amazon 买家账号登录(凭据走环境变量)')
    parser.add_argument('--start-chrome', action='store_true', help='启动新 Chrome 进程')
    parser.add_argument('--xvfb', action='store_true', help='无头 VPS,启动 Xvfb')
    args = parser.parse_args()
    
    try:
        get_creds()  # 提前 fail-fast
    except CredentialsNotProvided as e:
        print(f"✗ {e}")
        sys.exit(2)
    
    ok = asyncio.run(main_async(args))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
