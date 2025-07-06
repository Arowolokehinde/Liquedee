import asyncio
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solana.publickey import PublicKey
from typing import Dict, Optional, List
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class SolanaClient:
    """Client for Solana RPC operations"""
    
    def __init__(self):
        self.rpc_url = settings.solana_rpc_url
        self.commitment = Commitment(settings.solana_commitment)
        self.client = AsyncClient(self.rpc_url, commitment=self.commitment)
        
    async def get_account_info(self, address: str) -> Optional[Dict]:
        """Get account information"""
        try:
            pubkey = PublicKey(address)
            response = await self.client.get_account_info(pubkey)
            if response.value:
                return {
                    'address': address,
                    'lamports': response.value.lamports,
                    'owner': str(response.value.owner),
                    'executable': response.value.executable,
                    'rent_epoch': response.value.rent_epoch
                }
            return None
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    async def get_token_accounts(self, owner: str) -> List[Dict]:
        """Get token accounts for an owner"""
        try:
            owner_pubkey = PublicKey(owner)
            response = await self.client.get_token_accounts_by_owner(owner_pubkey)
            
            accounts = []
            for account in response.value:
                accounts.append({
                    'address': str(account.pubkey),
                    'mint': account.account.data.parsed['info']['mint'],
                    'amount': account.account.data.parsed['info']['tokenAmount']['amount'],
                    'decimals': account.account.data.parsed['info']['tokenAmount']['decimals']
                })
            return accounts
        except Exception as e:
            logger.error(f"Error getting token accounts: {e}")
            return []
    
    async def get_token_supply(self, mint: str) -> Optional[Dict]:
        """Get token supply information"""
        try:
            mint_pubkey = PublicKey(mint)
            response = await self.client.get_token_supply(mint_pubkey)
            if response.value:
                return {
                    'mint': mint,
                    'amount': response.value.amount,
                    'decimals': response.value.decimals,
                    'ui_amount': response.value.ui_amount
                }
            return None
        except Exception as e:
            logger.error(f"Error getting token supply: {e}")
            return None
    
    async def close(self):
        """Close RPC client"""
        await self.client.close()