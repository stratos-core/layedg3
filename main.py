import os
import sys
import time
import web3
import json
import random
import requests
import ua_generator
from datetime import datetime, timedelta
from eth_account.messages import encode_defunct
from base64 import b64decode


# Fungsi untuk menambahkan warna pada teks
def colored_text(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"


# Daftar kode warna ANSI
COLORS = [
    31,  # Merah
    32,  # Hijau
    33,  # Kuning
    34,  # Biru
    35,  # Ungu
    36,  # Cyan
]


def log(msg):
    now = datetime.now().isoformat(" ").split(".")[0]
    print(f"[{now}] {msg}")


def http(ses: requests.Session, url, data=None):
    attemp = 0
    while True:
        try:
            if attemp == 3:
                return None
            if data is None:
                res = ses.get(url=url)
            elif data == "":
                res = ses.post(url=url)
            else:
                res = ses.post(url=url, data=data)
            if "<title>502 Bad Gateway</title>" in res.text:
                log("error : 502 bad gateway !")
                time.sleep(3)
                continue
            if "<title>504 Gateway Time-out</title>" in res.text:
                log("error : 504 gateway timeout !")
                time.sleep(3)
                continue
            return res
        except (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ProxyError,
        ):
            log(f"connection error !")
            attemp += 1


class Start:
    def __init__(self, privatekey, proxy):
        headers = {"user-agent": ua_generator.generate().text}
        proxy = {"http": proxy, "https": proxy}
        self.ses = requests.Session()
        self.ses.headers.update(headers)
        self.ses.proxies.update(proxy)
        self.wallet = web3.Account.from_key(private_key=privatekey)
        self.hostname = b64decode("bGF5ZXJlZGdlLmlv").decode()

    def start(self):
        try:
            res = http(ses=self.ses, url="https://ipv4.webshare.io")
            if res is None:
                return None
            log(f"start with ip {res.text}")
            self.ses.headers.update(
                {
                    "host": f"referralapi.{self.hostname}",
                    "connection": "keep-alive",
                    "sec-ch-ua-platform": '"Windows"',
                    "accept": "application/json, text/plain, */*",
                    "content-type": "application/json",
                    "sec-ch-ua-mobile": "?0",
                    "origin": f"https://dashboard.{self.hostname}",
                    "sec-fetch-site": "same-site",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-dest": "empty",
                    "referer": f"https://dashboard.{self.hostname}/",
                    "accept-language": "en-US,en;q=0.9",
                }
            )
            # Log wallet address dengan warna random
            color_code = random.choice(COLORS)
            wallet_addr_colored = colored_text(self.wallet.address, color_code)
            log(f"wallet addr : {wallet_addr_colored}")
            wallet_detail_url = f"https://referralapi.layeredge.io/api/referral/wallet-details/{self.wallet.address}"
            node_status_url = f"https://referralapi.{self.hostname}/api/light-node/node-status/{self.wallet.address}"
            daily_claim_url = (
                f"https://referralapi.{self.hostname}/api/light-node/claim-node-points"
            )
            res = http(ses=self.ses, url=wallet_detail_url)
            ref_code = res.json().get("data", {}).get("referralCode")
            point = res.json().get("data", {}).get("nodePoints")
            last_claim = res.json().get("data", {}).get("lastClaimed")
            if last_claim is None:
                last_claim = (datetime.now() - timedelta(days=1)).isoformat()
            last_claim_day = last_claim.split("T")[0]
            log(f"referral code : {ref_code}")
            log(f"node point : {point}")
            now = datetime.now()
            message_claim = f"I am claiming my daily node point for {self.wallet.address} at {int(now.timestamp() * 1000)}"
            daily_claim_data = {
                "walletAddress": self.wallet.address,
                "timestamp": int(now.timestamp() * 1000),
                "sign": "",
            }
            if last_claim_day != now.isoformat().split("T")[0]:
                enmessage = encode_defunct(text=message_claim)
                sign = web3.Account.sign_message(enmessage, private_key=self.wallet.key)
                signature = f"0x{sign.signature.hex()}"
                daily_claim_data["sign"] = signature
                res = http(
                    ses=self.ses, url=daily_claim_url, data=json.dumps(daily_claim_data)
                )
                if res.json().get("message") == "node points claimed successfully":
                    log(f"success claim daily point !")
                else:
                    log(f"failed claim daily point !")
            res = http(ses=self.ses, url=node_status_url)
            if res is None:
                return None
            start_time = res.json().get("data", {}).get("startTimestamp")
            if start_time is None:
                start_url = f"https://referralapi.{self.hostname}/api/light-node/node-action/{self.wallet.address}/start"
                timet = int(datetime.now().timestamp() * 1000)
                message = (
                    f"Node activation request for {self.wallet.address} at {timet}"
                )
                enmessage = encode_defunct(text=message)
                sign = web3.Account.sign_message(enmessage, private_key=self.wallet.key)
                signature = f"0x{sign.signature.hex()}"
                data = {
                    "sign": signature,
                    "timestamp": timet,
                }
                res = http(ses=self.ses, url=start_url, data=json.dumps(data))
                if res is None:
                    return None
                if not "node action executed successfully" in res.json().get("message"):
                    log(f"failed start node !")
                    log(f"http response : {res.text}")
                    return None
                log("success start node !")
                return True
            log("node already started !")
            return True
        except Exception as e:
            log(f"error : {e}")
            return None


def get_proxy(i, p):
    if len(p) <= 0:
        return None
    proxy = p[i % len(p)]
    return proxy


def main():
    os.system("cls" if os.name == "nt" else "clear")
    print(">\n> active node l a y e r e d g e !\n>")
    print()
    privatekeys = open("privatekeys.txt").read().splitlines()
    proxies = open("proxies.txt").read().splitlines()
    if len(proxies) <= 0:
        q = input(f"Do you want to continue without a proxy? [y/n] ")
        if q.lower() == "n":
            sys.exit()
    print(f"total private key : {len(privatekeys)}")
    print(f"total proxy : {len(proxies)}")
    print()
    for i, privatekey in enumerate(privatekeys):
        proxy = get_proxy(i, proxies)
        while True:
            st = Start(proxy=proxy, privatekey=privatekey).start()
            if st is None:
                proxy = get_proxy(random.randint(1, len(privatekeys)), proxies)
                continue
            break

        print("~" * 50)

        # Delay acak 20-50 detik sebelum akun berikutnya
        if i < len(privatekeys) - 1:  # Tidak perlu delay setelah akun terakhir
            delay = random.randint(20, 50)  # <-- Delay acak 20-50 detik
            log(f"Waiting {delay} seconds before next account...")
            time.sleep(delay)  # <-- Gunakan variabel delay


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
