"""
Validation Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 11:35:33
"""

from typing import Dict, Any, Optional, List, Union, Callable
import re
from datetime import datetime
from .logger import Logger
from .metrics import MetricsManager

class ValidationRule:
    def __init__(self,
                 name: str,
                 validator: Union[Callable, str],
                 message: str = None):
        self.name = name
        self.validator = validator
        self.message = message or f"Validação {name} falhou"

class ValidationManager:
    def __init__(self, metrics_manager: MetricsManager):
        self.logger = Logger('validation_manager')
        self.metrics = metrics_manager
        self._rules: Dict[str, ValidationRule] = {}
        self._schemas: Dict[str, Dict] = {}
        
        # Registrar validadores padrão
        self._register_default_rules()

    def _register_default_rules(self):
        """Registrar regras de validação padrão"""
        try:
            # Tipos básicos
            self.register_rule(
                'required',
                lambda v: v is not None and v != '',
                'Campo obrigatório'
            )
            
            self.register_rule(
                'string',
                lambda v: isinstance(v, str),
                'Valor deve ser texto'
            )
            
            self.register_rule(
                'number',
                lambda v: isinstance(v, (int, float)),
                'Valor deve ser número'
            )
            
            self.register_rule(
                'boolean',
                lambda v: isinstance(v, bool),
                'Valor deve ser booleano'
            )
            
            self.register_rule(
                'list',
                lambda v: isinstance(v, list),
                'Valor deve ser lista'
            )
            
            self.register_rule(
                'dict',
                lambda v: isinstance(v, dict),
                'Valor deve ser dicionário'
            )
            
            # Strings
            self.register_rule(
                'min_length',
                lambda v, min_len: len(str(v)) >= min_len,
                'Texto muito curto'
            )
            
            self.register_rule(
                'max_length',
                lambda v, max_len: len(str(v)) <= max_len,
                'Texto muito longo'
            )
            
            self.register_rule(
                'email',
                lambda v: bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', str(v))),
                'Email inválido'
            )
            
            self.register_rule(
                'url',
                lambda v: bool(re.match(r'^https?://[\w\-\.]+(:\d+)?(/.*)?$', str(v))),
                'URL inválida'
            )
            
            # Números
            self.register_rule(
                'min_value',
                lambda v, min_val: float(v) >= min_val,
                'Valor muito baixo'
            )
            
            self.register_rule(
                'max_value',
                lambda v, max_val: float(v) <= max_val,
                'Valor muito alto'
            )
            
            self.register_rule(
                'positive',
                lambda v: float(v) > 0,
                'Valor deve ser positivo'
            )
            
            self.register_rule(
                'negative',
                lambda v: float(v) < 0,
                'Valor deve ser negativo'
            )
            
            # Datas
            self.register_rule(
                'date',
                lambda v: bool(re.match(r'^\d{4}-\d{2}-\d{2}$', str(v))),
                'Data inválida (YYYY-MM-DD)'
            )
            
            self.register_rule(
                'datetime',
                lambda v: bool(re.match(r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', str(v))),
                'Data/hora inválida'
            )
            
            # Listas
            self.register_rule(
                'min_items',
                lambda v, min_items: len(v) >= min_items,
                'Lista muito curta'
            )
            
            self.register_rule(
                'max_items',
                lambda v, max_items: len(v) <= max_items,
                'Lista muito longa'
            )
            
            # Regex
            self.register_rule(
                'pattern',
                lambda v, pattern: bool(re.match(pattern, str(v))),
                'Valor não corresponde ao padrão'
            )
            
        except Exception as e:
            self.logger.logger.error(
                f"Erro ao registrar regras padrão: {e}"
            )

    def register_rule(self,
                     name: str,
                     validator: Union[Callable, str],
                     message: str = None) -> bool:
        """Registrar nova regra de validação"""
        try:
            if name in self._rules:
                return False
                
            self._rules[name] = ValidationRule(
                name,
                validator,
                message
            )
            
            self.logger.logger.info(f"Regra {name} registrada")
            return True

        except Exception as e:
            self.logger.logger.error(
                f"Erro ao registrar regra: {e}"
            )
            return False

    def register_schema(self,
                       name: str,
                       schema: Dict) -> bool:
        """Registrar schema de validação"""
        try:
            if name in self._schemas:
                return False
                
            self._schemas[name] = schema
            self.logger.logger.info(f"Schema {name} registrado")
            return True

        except Exception as e:
            self.logger.logger.error(
                f"Erro ao registrar schema: {e}"
            )
            return False

    async def validate(self,
                      data: Any,
                      rules: Union[str, Dict, List],
                      context: Dict = None) -> Dict:
        """Validar dados contra regras"""
        try:
            context = context or {}
            errors = []
            
            # Se for nome de schema
            if isinstance(rules, str):
                if rules not in self._schemas:
                    raise ValueError(f"Schema {rules} não existe")
                rules = self._schemas[rules]
                
            # Se for lista de regras
            if isinstance(rules, list):
                rules = {'value': rules}
                data = {'value': data}
                
            # Validar cada campo
            for field, field_rules in rules.items():
                value = data.get(field)
                
                if not isinstance(field_rules, list):
                    field_rules = [field_rules]
                    
                for rule in field_rules:
                    # Se for string, é nome de regra
                    if isinstance(rule, str):
                        rule = {'rule': rule}
                        
                    rule_name = rule['rule']
                    if rule_name not in self._rules:
                        errors.append({
                            'field': field,
                            'rule': rule_name,
                            'message': f"Regra {rule_name} não existe"
                        })
                        continue
                        
                    validator = self._rules[rule_name].validator
                    message = rule.get(
                        'message',
                        self._rules[rule_name].message
                    )
                    
                    # Executar validação
                    try:
                        params = rule.get('params', {})
                        if callable(validator):
                            is_valid = validator(value, **params)
                        else:
                            # Validação por expressão
                            is_valid = eval(
                                validator,
                                {'value': value, **params, **context}
                            )
                            
                        if not is_valid:
                            errors.append({
                                'field': field,
                                'rule': rule_name,
                                'message': message.format(
                                    field=field,
                                    value=value,
                                    **params
                                )
                            })
                            
                    except Exception as e:
                        errors.append({
                            'field': field,
                            'rule': rule_name,
                            'message': f"Erro na validação: {e}"
                        })
                        
            # Registrar métricas
            await self.metrics.record_metric(
                'validations.total',
                1
            )
            if errors:
                await self.metrics.record_metric(
                    'validations.failed',
                    1
                )
                
            return {
                'valid': len(errors) == 0,
                'errors': errors
            }

        except Exception as e:
            self.logger.logger.error(f"Erro na validação: {e}")
            return {
                'valid': False,
                'errors': [{
                    'field': None,
                    'rule': None,
                    'message': f"Erro interno: {e}"
                }]
            }

    def get_rule(self, name: str) -> Optional[Dict]:
        """Obter detalhes da regra"""
        try:
            if name not in self._rules:
                return None
                
            rule = self._rules[name]
            return {
                'name': rule.name,
                'message': rule.message,
                'validator': (
                    'function' if callable(rule.validator)
                    else rule.validator
                )
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter regra: {e}")
            return None

    def get_schema(self, name: str) -> Optional[Dict]:
        """Obter schema"""
        try:
            return self._schemas.get(name)
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter schema: {e}")
            return None

    def list_rules(self) -> List[str]:
        """Listar regras disponíveis"""
        try:
            return list(self._rules.keys())
        except Exception as e:
            self.logger.logger.error(f"Erro ao listar regras: {e}")
            return []

    def list_schemas(self) -> List[str]:
        """Listar schemas disponíveis"""
        try:
            return list(self._schemas.keys())
        except Exception as e:
            self.logger.logger.error(f"Erro ao listar schemas: {e}")
            return []

    async def validate_field(self,
                           value: Any,
                           rules: List,
                           context: Dict = None) -> Dict:
        """Validar campo individual"""
        try:
            return await self.validate(
                {'value': value},
                {'value': rules},
                context
            )
        except Exception as e:
            self.logger.logger.error(
                f"Erro ao validar campo: {e}"
            )
            return {
                'valid': False,
                'errors': [{
                    'field': 'value',
                    'rule': None,
                    'message': f"Erro interno: {e}"
                }]
            }