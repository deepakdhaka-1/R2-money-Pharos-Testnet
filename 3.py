import json
from web3 import Web3

# RPC for Pharos testnet
RPC_URL = "https://testnet.dplabs-internal.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# R2USD contract
R2USD_ADDRESS = Web3.to_checksum_address("0x4f5b54d4af2568cefafa73bb062e5d734b55aa05")

# ERC20 ABI fragment (approve)
ERC20_ABI = json.loads("""
[
  {
    "constant": false,
    "inputs": [
      {"name": "spender", "type": "address"},
      {"name": "amount", "type": "uint256"}
    ],
    "name": "approve",
    "outputs": [{"name": "", "type": "bool"}],
    "type": "function"
  }
]
""")

# spender from txn logs
SPENDER = Web3.to_checksum_address("0xf8694d25947a0097cb2cea2fc07b071bdf72e1f8")
MAX_UINT256 = 2**256 - 1

contract = w3.eth.contract(address=R2USD_ADDRESS, abi=ERC20_ABI)

# load private keys from pvt.txt
with open("pvt.txt") as f:
    private_keys = [line.strip() for line in f if line.strip()]

for pk in private_keys:
    acct = w3.eth.account.from_key(pk)
    wallet = acct.address
    print(f"\nWallet: {wallet}")

    # build tx
    tx = contract.functions.approve(SPENDER, MAX_UINT256).build_transaction({
        "from": wallet,
        "nonce": w3.eth.get_transaction_count(wallet),
        "gas": 150000,
        "gasPrice": w3.to_wei("46", "gwei"),  # as per your txn
        "chainId": w3.eth.chain_id
    })

    # sign and send
    signed = w3.eth.account.sign_transaction(tx, pk)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"✅ Sent approve tx: {w3.to_hex(tx_hash)}")
