"""
Webhook Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 05:47:45
"""

import aiohttp
import asyncio
import json
import hmac
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from .logger import Logger

class WebhookManager:
    def __init__(self):
        self.logger = Logger('webhook_manager')
        self._webhooks: Dict[str, Dict] = {}
        self._retry_queue: List[Dict] = []
        self._max_retries = 3
        self._retry_delay = 5  # segundos
        self._processing = False

    async def register_webhook(self, 
                             url: str, 
                             events: List[str],
                             secret: str = None,
                             headers: Dict = None) -> str:
        """Registrar novo webhook"""
        try:
            webhook_id = self._generate_id()
            
            self._webhooks[webhook_id] = {
                'url': url,
                'events': events,
                'secret': secret,
                'headers': headers or {},
                'created_at': datetime.utcnow().isoformat(),
                'last_triggered': None,
                'failures': 0
            }
            
            self.logger.logger.info(f"Webhook {webhook_id} registrado para eventos {events}")
            return webhook_id

        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar webhook: {e}")
            return None

    async def trigger_webhook(self, event: str, data: Any) -> List[Dict]:
        """Disparar webhook para evento específico"""
        try:
            results = []
            triggered = []
            
            # Encontrar webhooks para o evento
            for webhook_id, webhook in self._webhooks.items():
                if event in webhook['events']:
                    triggered.append(webhook_id)
                    
            # Preparar payload
            payload = {
                'event': event,
                'timestamp': datetime.utcnow().isoformat(),
                'data': data
            }
            
            # Disparar webhooks em paralelo
            tasks = [
                self._send_webhook(webhook_id, payload)
                for webhook_id in triggered
            ]
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
            return [
                {
                    'webhook_id': wid,
                    'success': not isinstance(r, Exception),
                    'error': str(r) if isinstance(r, Exception) else None
                }
                for wid, r in zip(triggered, results)
            ]

        except Exception as e:
            self.logger.logger.error(f"Erro ao disparar webhooks: {e}")
            return []

    async def _send_webhook(self, webhook_id: str, payload: Dict) -> bool:
        """Enviar webhook individual"""
        try:
            webhook = self._webhooks[webhook_id]
            
            # Adicionar signature se houver secret
            headers = webhook['headers'].copy()
            if webhook['secret']:
                signature = self._generate_signature(
                    webhook['secret'],
                    json.dumps(payload)
                )
                headers['X-Hub-Signature'] = f"sha1={signature}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook['url'],
                    json=payload,
                    headers=headers
                ) as response:
                    
                    success = 200 <= response.status < 300
                    
                    if success:
                        webhook['last_triggered'] = datetime.utcnow().isoformat()
                        webhook['failures'] = 0
                    else:
                        webhook['failures'] += 1
                        if webhook['failures'] < self._max_retries:
                            self._retry_queue.append({
                                'webhook_id': webhook_id,
                                'payload': payload,
                                'attempts': webhook['failures']
                            })
                    
                    return success

        except Exception as e:
            self.logger.logger.error(f"Erro ao enviar webhook {webhook_id}: {e}")
            return False

    def _generate_signature(self, secret: str, payload: str) -> str:
        """Gerar assinatura HMAC para payload"""
        try:
            return hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha1
            ).hexdigest()
        except Exception as e:
            self.logger.logger.error(f"Erro ao gerar assinatura: {e}")
            return ''

    def _generate_id(self) -> str:
        """Gerar ID único para webhook"""
        return hashlib.md5(
            str(datetime.utcnow().timestamp()).encode()
        ).hexdigest()[:8]

    async def process_retry_queue(self):
        """Processar fila de reenvio"""
        try:
            if self._processing:
                return

            self._processing = True
            try:
                while self._retry_queue:
                    retry = self._retry_queue.pop(0)
                    
                    # Tentar reenviar
                    success = await self._send_webhook(
                        retry['webhook_id'],
                        retry['payload']
                    )
                    
                    if not success and retry['attempts'] < self._max_retries:
                        # Colocar de volta na fila
                        retry['attempts'] += 1
                        self._retry_queue.append(retry)
                        
                    # Delay entre tentativas
                    await asyncio.sleep(self._retry_delay)
                    
            finally:
                self._processing = False

        except Exception as e:
            self.logger.logger.error(f"Erro ao processar fila de retry: {e}")

    async def remove_webhook(self, webhook_id: str) -> bool:
        """Remover webhook registrado"""
        try:
            if webhook_id in self._webhooks:
                del self._webhooks[webhook_id]
                # Remover da fila de retry
                self._retry_queue = [
                    r for r in self._retry_queue
                    if r['webhook_id'] != webhook_id
                ]
                self.logger.logger.info(f"Webhook {webhook_id} removido")
                return True
            return False

        except Exception as e:
            self.logger.logger.error(f"Erro ao remover webhook: {e}")
            return False

    def get_webhook_info(self, webhook_id: str) -> Optional[Dict]:
        """Obter informações do webhook"""
        try:
            if webhook_id not in self._webhooks:
                return None
                
            webhook = self._webhooks[webhook_id].copy()
            webhook['id'] = webhook_id
            # Remover secret por segurança
            webhook['secret'] = '***' if webhook['secret'] else None
            return webhook

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter info do webhook: {e}")
            return None

    def list_webhooks(self) -> List[Dict]:
        """Listar todos os webhooks"""
        try:
            return [
                self.get_webhook_info(webhook_id)
                for webhook_id in self._webhooks
            ]

        except Exception as e:
            self.logger.logger.error(f"Erro ao listar webhooks: {e}")
            return []

    async def update_webhook(self, 
                           webhook_id: str,
                           url: str = None,
                           events: List[str] = None,
                           secret: str = None,
                           headers: Dict = None) -> bool:
        """Atualizar configuração do webhook"""
        try:
            if webhook_id not in self._webhooks:
                return False

            webhook = self._webhooks[webhook_id]
            
            if url:
                webhook['url'] = url
            if events:
                webhook['events'] = events
            if secret:
                webhook['secret'] = secret
            if headers:
                webhook['headers'] = headers

            self.logger.logger.info(f"Webhook {webhook_id} atualizado")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar webhook: {e}")
            return False