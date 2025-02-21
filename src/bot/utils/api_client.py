"""
API Client for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 11:53:11
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional, Union
import json
from datetime import datetime
from .logger import Logger
from .metrics import MetricsManager
from .error_handler import ErrorHandler

class APIClient:
    def __init__(self,
                 base_url: str,
                 logger: Logger,
                 metrics: MetricsManager,
                 error_handler: ErrorHandler):
        self.base_url = base_url.rstrip('/')
        self.logger = logger
        self.metrics = metrics
        self.error_handler = error_handler
        self._session: Optional[aiohttp.ClientSession] = None
        self._default_headers: Dict = {}
        self._default_timeout = 30
        self._max_retries = 3
        self._retry_delay = 1
        self._rate_limit_delay = 0
        self._last_request_time = None

    async def initialize(self):
        """Inicializar cliente API"""
        try:
            if self._session is None:
                self._session = aiohttp.ClientSession(
                    base_url=self.base_url,
                    headers=self._default_headers
                )
            self.logger.info("API client iniciado")
        except Exception as e:
            await self.error_handler.handle_error(e)
            raise

    async def close(self):
        """Fechar cliente API"""
        try:
            if self._session:
                await self._session.close()
                self._session = None
            self.logger.info("API client fechado")
        except Exception as e:
            await self.error_handler.handle_error(e)

    async def request(self,
                     method: str,
                     endpoint: str,
                     data: Any = None,
                     params: Dict = None,
                     headers: Dict = None,
                     timeout: int = None,
                     retries: int = None) -> Dict:
        """Realizar requisição à API"""
        try:
            # Validar sessão
            if not self._session:
                await self.initialize()
                
            # Preparar parâmetros
            method = method.upper()
            full_url = f"{self.base_url}/{endpoint.lstrip('/')}"
            timeout = timeout or self._default_timeout
            retries = retries or self._max_retries
            
            # Mesclar headers
            request_headers = self._default_headers.copy()
            if headers:
                request_headers.update(headers)
                
            # Serializar dados
            if data is not None:
                if isinstance(data, (dict, list)):
                    data = json.dumps(data)
                    request_headers['Content-Type'] = 'application/json'
                    
            # Respeitar rate limit
            await self._wait_rate_limit()
            
            # Tentar requisição com retries
            attempt = 0
            last_error = None
            
            while attempt < retries:
                try:
                    start_time = datetime.utcnow()
                    
                    async with self._session.request(
                        method=method,
                        url=endpoint,
                        data=data,
                        params=params,
                        headers=request_headers,
                        timeout=timeout
                    ) as response:
                        # Calcular tempo de resposta
                        elapsed = (
                            datetime.utcnow() - start_time
                        ).total_seconds()
                        
                        # Registrar métricas
                        await self._record_metrics(
                            method,
                            endpoint,
                            response.status,
                            elapsed
                        )
                        
                        # Processar resposta
                        response_data = await self._process_response(
                            response,
                            full_url
                        )
                        
                        # Atualizar rate limit
                        self._update_rate_limit(response)
                        
                        return response_data
                        
                except Exception as e:
                    last_error = e
                    attempt += 1
                    
                    if attempt < retries:
                        await asyncio.sleep(
                            self._retry_delay * (2 ** (attempt - 1))
                        )
                        
            # Registrar erro após todas as tentativas
            raise last_error or Exception("Máximo de tentativas excedido")

        except Exception as e:
            error_info = await self.error_handler.handle_error(
                e,
                {
                    'method': method,
                    'endpoint': endpoint,
                    'params': params
                }
            )
            raise APIError(str(e), error_info)

    async def _process_response(self,
                              response: aiohttp.ClientResponse,
                              url: str) -> Dict:
        """Processar resposta da API"""
        try:
            # Verificar status
            if response.status >= 400:
                await self._handle_error_response(response, url)
                
            # Processar corpo da resposta
            content_type = response.headers.get('Content-Type', '')
            
            if 'application/json' in content_type:
                return await response.json()
            else:
                return {
                    'status': response.status,
                    'content': await response.text()
                }

        except Exception as e:
            raise APIError(
                f"Erro ao processar resposta: {e}",
                {
                    'status': response.status,
                    'url': url
                }
            )

    async def _handle_error_response(self,
                                   response: aiohttp.ClientResponse,
                                   url: str):
        """Processar resposta de erro"""
        try:
            error_data = await response.json()
        except:
            error_data = await response.text()
            
        raise APIError(
            f"Erro na requisição: {response.status}",
            {
                'status': response.status,
                'url': url,
                'data': error_data
            }
        )

    async def _record_metrics(self,
                            method: str,
                            endpoint: str,
                            status: int,
                            elapsed: float):
        """Registrar métricas da requisição"""
        try:
            await self.metrics.record_metric(
                'api.requests.total',
                1
            )
            
            await self.metrics.record_metric(
                f'api.requests.{method.lower()}',
                1
            )
            
            await self.metrics.record_metric(
                f'api.status.{status}',
                1
            )
            
            await self.metrics.record_metric(
                'api.response_time',
                elapsed
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar métricas: {e}")

    async def _wait_rate_limit(self):
        """Aguardar rate limit"""
        if self._rate_limit_delay > 0 and self._last_request_time:
            elapsed = (
                datetime.utcnow() - self._last_request_time
            ).total_seconds()
            
            if elapsed < self._rate_limit_delay:
                await asyncio.sleep(
                    self._rate_limit_delay - elapsed
                )

    def _update_rate_limit(self, response: aiohttp.ClientResponse):
        """Atualizar configuração de rate limit"""
        try:
            # Atualizar timestamp
            self._last_request_time = datetime.utcnow()
            
            # Processar headers de rate limit
            remaining = response.headers.get('X-RateLimit-Remaining')
            reset = response.headers.get('X-RateLimit-Reset')
            
            if remaining and reset:
                remaining = int(remaining)
                reset = int(reset)
                
                if remaining == 0:
                    self._rate_limit_delay = max(
                        0,
                        reset - datetime.utcnow().timestamp()
                    )
                    
        except Exception as e:
            self.logger.error(f"Erro ao atualizar rate limit: {e}")

    def set_default_headers(self, headers: Dict):
        """Definir headers padrão"""
        self._default_headers.update(headers)

    def set_timeout(self, timeout: int):
        """Definir timeout padrão"""
        if timeout < 1:
            raise ValueError("Timeout deve ser maior que 0")
        self._default_timeout = timeout

    def set_retry_config(self,
                        max_retries: int = None,
                        retry_delay: int = None):
        """Configurar política de retry"""
        if max_retries is not None:
            if max_retries < 0:
                raise ValueError("max_retries deve ser >= 0")
            self._max_retries = max_retries
            
        if retry_delay is not None:
            if retry_delay < 0:
                raise ValueError("retry_delay deve ser >= 0")
            self._retry_delay = retry_delay

    async def get(self,
                 endpoint: str,
                 params: Dict = None,
                 **kwargs) -> Dict:
        """Realizar requisição GET"""
        return await self.request('GET', endpoint, params=params, **kwargs)

    async def post(self,
                  endpoint: str,
                  data: Any = None,
                  **kwargs) -> Dict:
        """Realizar requisição POST"""
        return await self.request('POST', endpoint, data=data, **kwargs)

    async def put(self,
                 endpoint: str,
                 data: Any = None,
                 **kwargs) -> Dict:
        """Realizar requisição PUT"""
        return await self.request('PUT', endpoint, data=data, **kwargs)

    async def patch(self,
                   endpoint: str,
                   data: Any = None,
                   **kwargs) -> Dict:
        """Realizar requisição PATCH"""
        return await self.request('PATCH', endpoint, data=data, **kwargs)

    async def delete(self,
                    endpoint: str,
                    **kwargs) -> Dict:
        """Realizar requisição DELETE"""
        return await self.request('DELETE', endpoint, **kwargs)

class APIError(Exception):
    """Exceção personalizada para erros da API"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message)
        self.details = details or {}