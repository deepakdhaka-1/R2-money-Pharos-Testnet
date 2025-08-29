
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue"/>
  <img src="https://img.shields.io/badge/Web3.js%2FPython-✅-green"/>
  <img src="https://img.shields.io/badge/Dependencies-Installed-yellow"/>
  <img src="https://img.shields.io/badge/Last_Update-August%2029%2C%202025-blueviolet"/>
</p>

--- 

<p align="center">
  Automate staking of <b>R2USD</b> tokens into <b>sR2USD</b> contract using multiple wallets with random amounts.  
  🚀 Works with multiple wallets, random amounts, and fully interactive colored outputs.
</p>


## 📌 Features

- ✅ Works with **all wallets** listed in `pvt.txt`  
- ✅ Sends **multiple transactions per wallet**  
- ✅ Randomizes staking amounts between **min and max values** (up to 2 decimals)  
- ✅ Customizable **delay** between transactions  
- ✅ **Dry-run simulation** of calldata before sending tx  
- ✅ **No waiting** for transaction receipts  
- ✅ **Interactive colored output** using Colorama  
- ✅ Supports **auto-approval** for maximum token allowance (optional)  

---

## ⚙️ Requirements

- **Python 3.8+**  
- `web3`  
- `eth_account`  
- `colorama`  

Install dependencies:

```bash
pip install web3 eth-account colorama
```
# Installation
```
git clone https://github.com/deepakdhaka-1/R2-money-Pharos-Testnet/
cd R2-money-Pharos-Testnet
```
---

# Workflow 
Claim faucet from their discord channel - (https://discord.com/invite/eVU4s2ZCF7)
. Then Run each script one by one. 

## Script 1 - 
Approve USDC Spending on the account 
```
pythono3 approve.py 
```
## Script 2 - 
Covert USDC to R2USDC on the account 
``` 
pythono3 Convert.py
```
## Script 3 - 
Approve R2USDC Spending on the account 
```
pythono3 approve2.py 
```
## Script 4 - 
Main Task staking of R2USDC - frequency 91 times for maximum points 
```
python3 main.py
```
--- 
Recommended Delay in main.py - 480 Seconds, because RPC is skipping many transactions if those are being sent subsquently. 
