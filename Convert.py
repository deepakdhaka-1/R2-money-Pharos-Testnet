from web3 import Web3
from eth_account import Account
import re
from decimal import Decimal, getcontext
from colorama import Fore, Style, init
import time

init(autoreset=True)  # Enable colorama

# ---------- Config ----------
RPC_URL = "https://testnet.dplabs-internal.com"

# Contracts
R2USD_ADDR = Web3.to_checksum_address("0x4f5b54d4af2568cefafa73bb062e5d734b55aa05")
USDC_ADDR  = Web3.to_checksum_address("0x8bebfcbe5468f146533c182df3dfbf5ff9be00e2")

# Function selector (0x095e7a95)
FUNC_SELECTOR = "095e7a95"
DECIMALS = 6

# ---------- Setup ----------
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Ask once for the swap amount
amt_str = input("Enter USDC amount to swap for R2USD (e.g., 1000): ").strip()
getcontext().prec = 50
amount_dec = Decimal(amt_str)
amount_wei = int(amount_dec * (10 ** DECIMALS))
if amount_wei <= 0:
    raise ValueError("Amount must be > 0")

# Ask for number of iterations per wallet
n_times_str = input("Enter number of times to repeat the swap per wallet: ").strip()
n_times = int(n_times_str) if n_times_str.isdigit() else 1

# Ask for delay between transactions
delay_str = input("Enter delay between each TX in seconds (e.g., 3): ").strip()
delay_sec = float(delay_str) if delay_str else 0

# Helper to build calldata
def build_calldata(wallet, amount_wei):
    def to_word(hex_no0x: str) -> str:
        return hex_no0x.rjust(64, "0")
    addr_word = to_word(wallet.lower().replace("0x", ""))
    amt_word  = to_word(hex(amount_wei)[2:])
    zero_word = "0" * 64
    data = "0x" + FUNC_SELECTOR + addr_word + amt_word + zero_word*5
    assert len(data.replace("0x", "")) == 456
    return data

# ---------- Process each private key ----------
with open("pvt.txt", "r", encoding="utf-8") as f:
    keys = [line.strip() for line in f if line.strip()]

for idx, raw_key in enumerate(keys, 1):
    m = re.search(r"(0x)?([0-9a-fA-F]{64})", raw_key)
    if not m:
        print(Fore.RED + f"❌ Skipping line {idx}: not a valid private key")
        continue

    PRIVATE_KEY = m.group(2)
    acct = Account.from_key(PRIVATE_KEY)
    WALLET = Web3.to_checksum_address(acct.address)

    print(Fore.CYAN + f"\n[{idx}] Wallet: {WALLET}")

    # Repeat swap n_times
    sent_count = 0
    attempt = 0
    while sent_count < n_times:
        attempt += 1
        calldata = build_calldata(WALLET, amount_wei)

        # Build tx
        nonce = w3.eth.get_transaction_count(WALLET)
        try:
            gas_est = w3.eth.estimate_gas({
                "from": WALLET,
                "to": R2USD_ADDR,
                "data": calldata,
                "value": 0
            })
        except Exception:
            gas_est = 200_000

        tx = {
            "nonce": nonce,
            "to": R2USD_ADDR,
            "value": 0,
            "data": calldata,
            "gas": gas_est,
            "gasPrice": Web3.to_wei(1, "gwei"),
            "chainId": w3.eth.chain_id,
        }

        signed = acct.sign_transaction(tx)
        try:
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            sent_count += 1
            print(Fore.GREEN + f"[{sent_count}/{n_times}] ✅ Submitted TX: {w3.to_hex(tx_hash)}")
            if delay_sec > 0:
                time.sleep(delay_sec)

        except Exception as e:
            # Check if error is TX_REPLAY_ATTACK
            err_msg = str(e)
            if "TX_REPLAY_ATTACK" in err_msg:
                print(Fore.YELLOW + f"[!] TX replay detected, not counting this attempt. Retrying...")
                continue
            else:
                sent_count += 1  # Count other errors
                print(Fore.RED + f"[{sent_count}/{n_times}] ❌ Failed to send TX for {WALLET}: {e}")
                if delay_sec > 0:
                    time.sleep(delay_sec)
