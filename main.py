# stake_multi_keys_random.py
from web3 import Web3
from eth_account import Account
from decimal import Decimal, getcontext
import re
import time
import random
from colorama import init, Fore, Style

init(autoreset=True)

# ---------- Config ----------
RPC_URL = "https://testnet.dplabs-internal.com"
R2USD_ADDR  = Web3.to_checksum_address("0x4f5b54d4af2568cefafa73bb062e5d734b55aa05")   # token
SR2USD_ADDR = Web3.to_checksum_address("0xf8694d25947a0097cb2cea2fc07b071bdf72e1f8")   # staking contract

# Provided selector from your txn
STAKE_SELECTOR = "1a5f0f00"   # 0x1a5f0f00

# ERC20 / utility selectors
DECIMALS_SEL   = "313ce567"   # decimals()
ALLOWANCE_SEL  = "dd62ed3e"   # allowance(address,address)
APPROVE_SEL    = "095ea7b"    # note: will add trailing hex below when building data

# helpers
w3 = Web3(Web3.HTTPProvider(RPC_URL))
getcontext().prec = 60

def to_word(hex_no0x: str) -> str:
    return hex_no0x.rjust(64, "0")

def addr_word(addr: str) -> str:
    return to_word(addr.lower().replace("0x",""))

def int_word(value: int) -> str:
    return to_word(hex(value)[2:])

def call_eth(tx):
    """Wrapper returning (success, result_or_error)"""
    try:
        res = w3.eth.call(tx)
        return True, res
    except Exception as e:
        return False, e

# ---------- Read keys ----------
with open("pvt.txt", "r", encoding="utf-8") as f:
    raw_lines = [ln.strip() for ln in f if ln.strip()]

if not raw_lines:
    raise SystemExit(Fore.RED + "No private keys found in pvt.txt")

# ---------- User Inputs ----------
try:
    num_txns = int(input(Fore.CYAN + "Enter number of transactions per wallet: ").strip())
except:
    raise SystemExit(Fore.RED + "Invalid number of transactions")

try:
    min_amt = Decimal(input(Fore.CYAN + "Enter minimum R2USD amount per tx: ").strip())
    max_amt = Decimal(input(Fore.CYAN + "Enter maximum R2USD amount per tx: ").strip())
    if min_amt > max_amt or min_amt <= 0:
        raise ValueError
except:
    raise SystemExit(Fore.RED + "Invalid min/max amounts")

try:
    delay_sec = float(input(Fore.CYAN + "Enter delay between each transaction (in seconds): ").strip())
    if delay_sec < 0:
        raise ValueError
except:
    raise SystemExit(Fore.RED + "Invalid delay value")

# ---------- Detect token decimals ----------
dec_call = {"to": R2USD_ADDR, "data": "0x" + DECIMALS_SEL}
ok, dec_res = call_eth(dec_call)
if not ok:
    print(Fore.YELLOW + "⚠️ Could not fetch decimals() from R2USD token. Defaulting to 6.")
    token_decimals = 6
else:
    token_decimals = int(dec_res.hex(), 16)
    print(Fore.GREEN + f"✅ R2USD token decimals: {token_decimals}")

# ---------- Calldata builders ----------
def cand_single_uint(amount):
    return "0x" + STAKE_SELECTOR + int_word(amount)

def cand_addr_uint(addr, amount):
    return "0x" + STAKE_SELECTOR + addr_word(addr) + int_word(amount)

def cand_uint_addr(amount, addr):
    return "0x" + STAKE_SELECTOR + int_word(amount) + addr_word(addr)

def cand_single_uint_padded(amount, pad_words=5):
    return "0x" + STAKE_SELECTOR + int_word(amount) + ("0"*64*pad_words)

def cand_addr_uint_padded(addr, amount, pad_words=5):
    return "0x" + STAKE_SELECTOR + addr_word(addr) + int_word(amount) + ("0"*64*pad_words)

# ---------- Iterate wallets ----------
for idx, raw in enumerate(raw_lines, start=1):
    m = re.search(r"(0x)?([0-9a-fA-F]{64})", raw)
    if not m:
        print(Fore.YELLOW + f"[{idx}] Skipping invalid line: {raw}")
        continue
    pk = m.group(2)
    acct = Account.from_key(pk)
    wallet = Web3.to_checksum_address(acct.address)
    print("\n" + Fore.MAGENTA + "="*60)
    print(Fore.CYAN + f"[{idx}] Wallet: {wallet}")

    # Check allowance
    allowance_data = "0x" + ALLOWANCE_SEL + addr_word(wallet) + addr_word(SR2USD_ADDR)
    ok, allowance_res = call_eth({"to": R2USD_ADDR, "data": allowance_data})
    allowance_val = int(allowance_res.hex(), 16) if ok else 0
    print(Fore.GREEN + f"Allowance R2USD -> sR2USD: {allowance_val}")

    if allowance_val < 1:  # minimum check, auto-approve optional
        print(Fore.YELLOW + "⚠️ Allowance insufficient. Enable AUTO_APPROVE if needed.")
        continue

    # Send multiple transactions
    for tx_num in range(1, num_txns + 1):
        # random amount between min/max
        rand_amt = round(random.uniform(float(min_amt), float(max_amt)), 2)
        amount_wei = int(Decimal(rand_amt) * (10 ** token_decimals))
        print(Fore.BLUE + f"\n[{tx_num}] Staking {rand_amt} R2USD -> {amount_wei} (raw units)")

        # Build candidate calldata
        candidates = [
            ("single_uint", cand_single_uint(amount_wei)),
            ("single_uint_padded", cand_single_uint_padded(amount_wei, pad_words=5)),
            ("addr_uint", cand_addr_uint(wallet, amount_wei)),
            ("addr_uint_padded", cand_addr_uint_padded(wallet, amount_wei, pad_words=5)),
            ("uint_addr", cand_uint_addr(amount_wei, wallet)),
        ]

        chosen = None
        for name, calldata in candidates:
            ok, res = call_eth({"from": wallet, "to": SR2USD_ADDR, "data": calldata})
            if ok:
                chosen = calldata
                print(Fore.GREEN + f"✅ Candidate OK: {name}")
                break
            else:
                print(Fore.RED + f"✗ Candidate failed (dry-run): {name} - Skip error")

        if not chosen:
            print(Fore.RED + "❌ All candidate encodings failed. Skipping this tx.")
            continue

        # estimate gas
        try:
            gas_est = w3.eth.estimate_gas({"from": wallet, "to": SR2USD_ADDR, "data": chosen, "value": 0})
            print(Fore.GREEN + f"Gas estimate: {gas_est}")
        except Exception as e:
            gas_est = 200_000
            print(Fore.YELLOW + f"Gas estimation failed, defaulting to 200k. Error: {e}")

        # Build and send tx
        nonce = w3.eth.get_transaction_count(wallet)
        tx = {
            "nonce": nonce,
            "to": SR2USD_ADDR,
            "value": 0,
            "data": chosen,
            "gas": gas_est,
            "gasPrice": Web3.to_wei(1.2, "gwei"),
            "chainId": w3.eth.chain_id,
        }
        signed = acct.sign_transaction(tx)
        try:
            txhash = w3.eth.send_raw_transaction(signed.raw_transaction)
            print(Fore.GREEN + f"✅ Staking tx submitted: {w3.to_hex(txhash)}")
        except Exception as e:
            print(Fore.RED + f"❌ Failed to send tx: {e}")

        time.sleep(delay_sec)
