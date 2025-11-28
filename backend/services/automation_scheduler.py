"""
Serviço de Agendamento de Automação
Executa disparos automáticos mensais conforme configuração do cliente
"""

import os
import sys
import json
from datetime import datetime, time
from typing import Dict, List
import pytz

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from models.database import db, log_sistema
from services.automation_service import automation_service


class AutomationScheduler:
    """Gerencia o agendamento de disparos automáticos mensais"""

    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone='America/Campo_Grande')  # Timezone de MS
        self.running = False

    def verificar_e_executar_automacoes(self):
        """
        Verifica quais clientes têm automação agendada para hoje
        e executa entre 08:00 e 18:00 (horário de MS)
        """
        try:
            agora = datetime.now(pytz.timezone('America/Campo_Grande'))
            hora_atual = agora.time()
            dia_atual = agora.day

            # Verifica se está no horário comercial (08:00 às 18:00)
            horario_inicio = time(8, 0)
            horario_fim = time(18, 0)

            if not (horario_inicio <= hora_atual <= horario_fim):
                log_sistema('info',
                           f'Fora do horário comercial ({hora_atual.strftime("%H:%M")}). Aguardando.',
                           'scheduler')
                return

            log_sistema('info',
                       f'Verificando automações agendadas para dia {dia_atual}',
                       'scheduler')

            # Busca clientes com automação habilitada para hoje
            clientes_para_processar = db.execute_query("""
                SELECT
                    ca.cliente_nexus_id,
                    ca.dia_do_mes,
                    ca.mensagem_antibloqueio,
                    ca.intervalo_min_segundos,
                    ca.intervalo_max_segundos,
                    cn.nome_empresa,
                    cn.whatsapp_numero
                FROM configuracoes_automacao ca
                JOIN clientes_nexus cn ON ca.cliente_nexus_id = cn.id
                WHERE ca.disparo_automatico_habilitado = true
                AND ca.dia_do_mes = %s
                AND cn.ativo = true
            """, (dia_atual,))

            if not clientes_para_processar:
                log_sistema('info',
                           f'Nenhum cliente com automação agendada para dia {dia_atual}',
                           'scheduler')
                return

            log_sistema('info',
                       f'Encontrados {len(clientes_para_processar)} clientes para processamento',
                       'scheduler',
                       {'clientes': [c['cliente_nexus_id'] for c in clientes_para_processar]})

            # Verifica se já foi executado hoje para cada cliente
            for cliente_config in clientes_para_processar:
                cliente_nexus_id = cliente_config['cliente_nexus_id']

                # Verifica se já executou hoje
                ja_executado = db.execute_query("""
                    SELECT COUNT(*) as count
                    FROM historico_disparos
                    WHERE cliente_nexus_id = %s
                    AND tipo_disparo = 'automatico_mensal'
                    AND DATE(horario_execucao) = CURRENT_DATE
                """, (cliente_nexus_id,))

                if ja_executado and ja_executado[0]['count'] > 0:
                    log_sistema('info',
                               f'Automação já executada hoje para cliente {cliente_nexus_id}',
                               'scheduler',
                               {'cliente_nexus_id': cliente_nexus_id})
                    continue

                # Executa a automação
                self._executar_automacao_cliente(cliente_config)

        except Exception as e:
            log_sistema('error',
                       f'Erro ao verificar automações: {str(e)}',
                       'scheduler')

    def _executar_automacao_cliente(self, cliente_config: Dict):
        """Executa a automação para um cliente específico"""
        cliente_nexus_id = cliente_config['cliente_nexus_id']
        nome_empresa = cliente_config['nome_empresa']

        try:
            log_sistema('info',
                       f'Iniciando automação mensal para {nome_empresa}',
                       'scheduler',
                       {'cliente_nexus_id': cliente_nexus_id})

            # Executa a automação completa
            stats = automation_service.executar_automacao_completa(cliente_nexus_id)

            # Registra no histórico de disparos
            db.execute_update("""
                INSERT INTO historico_disparos
                (cliente_nexus_id, tipo_disparo, total_envios, envios_sucesso,
                 envios_erro, horario_execucao, executado_por, status, detalhes)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s::jsonb)
            """, (
                cliente_nexus_id,
                'automatico_mensal',
                stats.get('clientes_processados', 0),
                stats.get('boletos_enviados', 0),
                stats.get('erros', 0),
                'scheduler_automatico',
                'concluido',
                json.dumps(stats)
            ))

            log_sistema('success',
                       f'Automação mensal concluída para {nome_empresa}',
                       'scheduler',
                       {
                           'cliente_nexus_id': cliente_nexus_id,
                           'stats': stats
                       })

        except Exception as e:
            log_sistema('error',
                       f'Erro ao executar automação para {nome_empresa}: {str(e)}',
                       'scheduler',
                       {'cliente_nexus_id': cliente_nexus_id})

            # Registra erro no histórico
            db.execute_update("""
                INSERT INTO historico_disparos
                (cliente_nexus_id, tipo_disparo, horario_execucao,
                 executado_por, status, detalhes)
                VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s, %s::jsonb)
            """, (
                cliente_nexus_id,
                'automatico_mensal',
                'scheduler_automatico',
                'erro',
                json.dumps({'erro': str(e)})
            ))

    def iniciar(self):
        """Inicia o scheduler"""
        if self.running:
            log_sistema('warning', 'Scheduler já está rodando', 'scheduler')
            return

        # Executa a cada hora durante o horário comercial (08:00 às 18:00)
        # Isso garante que mesmo que o sistema inicie fora do horário,
        # ele vai executar quando entrar no horário comercial
        self.scheduler.add_job(
            self.verificar_e_executar_automacoes,
            CronTrigger(hour='8-18', minute='0'),  # A cada hora das 8h às 18h
            id='verificar_automacoes_mensais',
            name='Verificar Automações Mensais',
            replace_existing=True
        )

        self.scheduler.start()
        self.running = True

        log_sistema('success',
                   'Scheduler de automação iniciado',
                   'scheduler',
                   {'trigger': 'A cada hora das 8h às 18h (horário de MS)'})

        print("[OK] Scheduler de automação iniciado - Verificações a cada hora (08:00-18:00)")

    def parar(self):
        """Para o scheduler"""
        if not self.running:
            return

        self.scheduler.shutdown()
        self.running = False

        log_sistema('info', 'Scheduler de automação parado', 'scheduler')
        print("[INFO] Scheduler de automação parado")

    def executar_agora(self, cliente_nexus_id: int = None):
        """
        Executa a verificação imediatamente (útil para testes)

        Args:
            cliente_nexus_id: Se informado, executa apenas para este cliente
        """
        if cliente_nexus_id:
            # Busca configuração do cliente
            config = db.execute_query("""
                SELECT
                    ca.cliente_nexus_id,
                    ca.dia_do_mes,
                    ca.mensagem_antibloqueio,
                    ca.intervalo_min_segundos,
                    ca.intervalo_max_segundos,
                    cn.nome_empresa,
                    cn.whatsapp_numero
                FROM configuracoes_automacao ca
                JOIN clientes_nexus cn ON ca.cliente_nexus_id = cn.id
                WHERE ca.cliente_nexus_id = %s
                AND ca.disparo_automatico_habilitado = true
                AND cn.ativo = true
            """, (cliente_nexus_id,))

            if config:
                self._executar_automacao_cliente(config[0])
            else:
                log_sistema('warning',
                           f'Cliente {cliente_nexus_id} não possui automação habilitada',
                           'scheduler')
        else:
            # Executa verificação normal
            self.verificar_e_executar_automacoes()

    def status(self) -> Dict:
        """Retorna o status do scheduler"""
        jobs = []
        if self.running:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                })

        return {
            'running': self.running,
            'jobs': jobs,
            'timezone': 'America/Campo_Grande'
        }


# Instância global
automation_scheduler = AutomationScheduler()
