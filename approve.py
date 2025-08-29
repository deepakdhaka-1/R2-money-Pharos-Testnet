from web3 import Web3
import json

# --- RPC URL for Pharos Testnet ---
RPC_URL = "https://testnet.dplabs-internal.com"   # Replace with actual RPC endpoint
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# --- Contract & Spender Info ---
USDC_ADDRESS = w3.to_checksum_address("0x8bebfcbe5468f146533c182df3dfbf5ff9be00e2")
SPENDER = w3.to_checksum_address("0x4f5b54d4af2568cefafa73bb062e5d734b55aa05")
MAX_UINT256 = int("0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", 16)

# --- USDC ABI fragment (approve only) ---
ERC20_ABI = json.loads("""
[
  {
    "constant": false,
    "inputs": [
      { "name": "spender", "type": "address" },
      { "name": "value", "type": "uint256" }
    ],
    "name": "approve",
    "outputs": [{ "name": "", "type": "bool" }],
    "type": "function"
  }
]
""")

contract = w3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)

# --- Load Private Keys ---
with open("pvt.txt", "r") as f:
    private_keys = [line.strip() for line in f if line.strip()]

for pk in private_keys:
    account = w3.eth.account.from_key(pk)
    address = account.address
    print(f"\n🔑 Using wallet: {address}")

    # Build transaction
    nonce = w3.eth.get_transaction_count(address)
    txn = contract.functions.approve(SPENDER, MAX_UINT256).build_transaction({
        'chainId': w3.eth.chain_id,
        'gas': 300000,
        'gasPrice': w3.to_wei('3', 'gwei'),
        'nonce': nonce,
    })

    # Sign transaction
    signed_txn = w3.eth.account.sign_transaction(txn, private_key=pk)

    # Send transaction
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"✅ Approval sent: {w3.to_hex(tx_hash)}")
