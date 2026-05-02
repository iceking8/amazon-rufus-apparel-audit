#!/usr/bin/env python3
"""
amazon-rufus-apparel-audit 环境配置(可选)

只在新 VPS 上跑一次。会安装:
- google-chrome(从官方 deb)
- xvfb(无头虚拟显示)
- uv(Python 包管理器)
- browser-harness(浏览器自动化工具)

跟原 qa skill 的区别:
1. 不自毁 — 留着方便再跑/排查
2. 不强制 sudo — 检测权限,缺权限时给清晰指引
3. 不收凭据 — 凭据走环境变量,这里只装环境
4. 详细日志 — 失败时给可定位的错误信息
"""
import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path


def check_command(cmd):
    return shutil.which(cmd) is not None


def need_root_or_explain():
    if os.geteuid() != 0:
        print("⚠ 这个脚本需要 root 权限来安装系统包(apt-get install)。")
        print("  请用 sudo 跑:  sudo python3 scripts/setup_env.py")
        print("  或单独装好下面四件事再跳过这个脚本:")
        print("    1) google-chrome(非 snap 版)")
        print("    2) xvfb")
        print("    3) uv")
        print("    4) browser-harness  (uv tool install browser-harness)")
        sys.exit(1)


def install_chrome():
    print("\n[1/4] Google Chrome")
    if check_command('google-chrome'):
        print("  已安装,跳过")
        return True
    
    deb_path = '/tmp/google-chrome-stable_current_amd64.deb'
    print("  下载 Chrome deb 包...")
    try:
        subprocess.run(
            ['wget', '-q',
             'https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb',
             '-O', deb_path],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"  ✗ wget 失败:{e}")
        return False
    
    print("  apt-get install...")
    try:
        subprocess.run(['apt-get', 'install', '-y', deb_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"  ✗ apt-get 失败:{e}")
        print("    可能缺依赖,试试: apt-get install -y -f")
        return False
    
    if check_command('google-chrome'):
        print("  ✓ 安装成功")
        return True
    print("  ✗ 安装失败")
    return False


def install_xvfb():
    print("\n[2/4] Xvfb")
    if check_command('Xvfb'):
        print("  已安装,跳过")
        return True
    try:
        subprocess.run(['apt-get', 'update', '-qq'], check=True)
        subprocess.run(['apt-get', 'install', '-y', 'xvfb'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"  ✗ apt-get 失败:{e}")
        return False
    
    ok = check_command('Xvfb')
    print("  ✓ 安装成功" if ok else "  ✗ 安装失败")
    return ok


def install_uv():
    print("\n[3/4] uv")
    if check_command('uv'):
        print("  已安装,跳过")
        return True
    try:
        subprocess.run(
            ['sh', '-c', 'curl -LsSf https://astral.sh/uv/install.sh | sh'],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"  ✗ uv 安装失败:{e}")
        return False
    
    # 把 uv 加到 PATH
    home = os.path.expanduser('~')
    uv_bin = f'{home}/.local/bin'
    if uv_bin not in os.environ.get('PATH', ''):
        os.environ['PATH'] = f"{uv_bin}:{os.environ.get('PATH', '')}"
    
    if check_command('uv'):
        print("  ✓ 安装成功")
        print(f"  注意:把 {uv_bin} 加到你的 ~/.bashrc PATH")
        return True
    print("  ✗ 安装失败,可能需要手动 source ~/.bashrc 后重试")
    return False


def install_browser_harness():
    print("\n[4/4] browser-harness")
    if check_command('browser-harness'):
        print("  已安装,跳过")
        return True
    try:
        subprocess.run(['uv', 'tool', 'install', 'browser-harness'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"  ✗ 安装失败:{e}")
        return False
    
    ok = check_command('browser-harness')
    print("  ✓ 安装成功" if ok else "  ✗ 安装失败")
    return ok


def print_next_steps():
    print("\n" + "=" * 60)
    print("✓ 环境配置完成")
    print("=" * 60)
    print("\n下一步:")
    print("1. 设置环境变量(凭据)")
    print("   export AMAZON_BUYER_EMAIL='your-email@example.com'")
    print("   export AMAZON_BUYER_PASSWORD='your-password'")
    print("   # 如果用 TOTP 二次验证:")
    print("   export AMAZON_BUYER_OTP_SECRET='your-totp-secret'")
    print()
    print("2. 首次登录 Amazon(把 cookie 写进 /tmp/chrome-profile)")
    print("   python3 scripts/login_amazon.py")
    print()
    print("3. 抓取一个 ASIN 试试")
    print("   python3 scripts/capture_rufus.py \\")
    print("       --asin B0XXXXXXX \\")
    print("       --role own \\")
    print("       --depth 20")
    print()
    print("4. 出报告")
    print("   python3 scripts/build_report.py \\")
    print("       --capture out/capture_baseline.csv \\")
    print("       --profile out/product_profile.json \\")
    print("       --output out/report_cn.md")


def main():
    parser = argparse.ArgumentParser(description='amazon-rufus-apparel-audit 环境配置')
    parser.add_argument('--skip-chrome', action='store_true', help='跳过 Chrome 安装')
    parser.add_argument('--skip-xvfb', action='store_true', help='跳过 Xvfb 安装(本地有图形界面时)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("amazon-rufus-apparel-audit 环境配置")
    print("=" * 60)
    
    need_root_or_explain()
    
    ok = True
    if not args.skip_chrome:
        ok &= install_chrome()
    if not args.skip_xvfb:
        ok &= install_xvfb()
    ok &= install_uv()
    ok &= install_browser_harness()
    
    if not ok:
        print("\n✗ 部分步骤失败,看上面的具体错误")
        sys.exit(1)
    
    print_next_steps()


if __name__ == '__main__':
    main()
