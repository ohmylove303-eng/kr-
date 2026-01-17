#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KR Market - Automated Scheduler
Based on BLUEPRINT_09_SUPPORTING_MODULES.md

Automated scheduling for:
- Daily price updates (16:00 KST)
- Institutional data updates (16:10 KST)
- VCP signal scans (16:20 KST)
- Daily report generation (16:30 KST)
- Saturday history collection (10:00 KST)
"""

import os
import sys
import time
import signal
import logging
import subprocess
import schedule
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Config:
    """Deployment configuration"""
    
    BASE_DIR = os.environ.get('KR_MARKET_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    LOG_DIR = os.environ.get('KR_MARKET_LOG_DIR', os.path.join(BASE_DIR, 'logs'))
    DATA_DIR = os.path.join(BASE_DIR, 'kr_market')
    
    # Schedule times (KST)
    PRICE_UPDATE_TIME = os.environ.get('PRICE_UPDATE_TIME', '16:00')
    INST_UPDATE_TIME = os.environ.get('INST_UPDATE_TIME', '16:10')
    SIGNAL_SCAN_TIME = os.environ.get('SIGNAL_SCAN_TIME', '16:20')
    REPORT_TIME = os.environ.get('REPORT_TIME', '16:30')
    HISTORY_TIME = os.environ.get('HISTORY_TIME', '10:00')
    
    # Timeouts (seconds)
    PRICE_TIMEOUT = 600
    INST_TIMEOUT = 600
    SIGNAL_TIMEOUT = 300
    HISTORY_TIMEOUT = 900
    REPORT_TIMEOUT = 180
    
    PYTHON_PATH = sys.executable
    
    @classmethod
    def ensure_dirs(cls):
        """Ensure required directories exist"""
        os.makedirs(cls.LOG_DIR, exist_ok=True)
        os.makedirs(cls.DATA_DIR, exist_ok=True)


def run_command(cmd, task_name, timeout=300):
    """Execute command with timeout and logging"""
    logger.info(f"🚀 Starting: {task_name}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=Config.BASE_DIR,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"✅ Completed: {task_name} ({elapsed:.1f}s)")
            if result.stdout:
                logger.debug(f"Output: {result.stdout[:500]}")
            return True
        else:
            logger.error(f"❌ Failed: {task_name} (code {result.returncode})")
            if result.stderr:
                logger.error(f"Error: {result.stderr[:500]}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️ Timeout: {task_name} (>{timeout}s)")
        return False
    except Exception as e:
        logger.error(f"💥 Exception in {task_name}: {e}")
        return False


def update_daily_prices():
    """Update daily price data"""
    script = f"""
import sys
sys.path.insert(0, '{Config.BASE_DIR}')
from kr_market.scripts.create_daily_prices import main
main()
"""
    return run_command(
        [Config.PYTHON_PATH, '-c', script],
        'Daily price update',
        timeout=Config.PRICE_TIMEOUT
    )


def update_institutional_data():
    """Update institutional flow data"""
    script = f"""
import sys
sys.path.insert(0, '{Config.BASE_DIR}')
from kr_market.scripts.create_institutional_data import main
main()
"""
    return run_command(
        [Config.PYTHON_PATH, '-c', script],
        'Institutional data update',
        timeout=Config.INST_TIMEOUT
    )


def run_vcp_signal_scan():
    """Run VCP signal scan"""
    script = f"""
import sys
sys.path.insert(0, '{Config.BASE_DIR}')
from kr_market.signal_tracker import SignalTracker

tracker = SignalTracker()
signals = tracker.scan_today_signals()
print(f'Found {{len(signals)}} VCP signals')
"""
    return run_command(
        [Config.PYTHON_PATH, '-c', script],
        'VCP signal scan',
        timeout=Config.SIGNAL_TIMEOUT
    )


def generate_daily_report():
    """Generate daily report JSON"""
    script = f"""
import sys
import json
import pandas as pd
from datetime import datetime
sys.path.insert(0, '{Config.BASE_DIR}')

# Read signals log
signals_path = '{Config.DATA_DIR}/signals_log.csv'
if not os.path.exists(signals_path):
    print('No signals log found')
    sys.exit(0)

df = pd.read_csv(signals_path)
today_str = datetime.now().strftime('%Y-%m-%d')
today_signals = df[df['signal_date'] == today_str]

report = {{
    'date': today_str,
    'total_signals': len(today_signals),
    'open_signals': len(today_signals[today_signals['status'] == 'OPEN']),
    'closed_signals': len(today_signals[today_signals['status'] == 'CLOSED']),
    'generated_at': datetime.now().isoformat()
}}

# Save report
report_path = '{Config.DATA_DIR}/data/daily_report.json'
with open(report_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f'Generated daily report: {{report}}')
"""
    return run_command(
        [Config.PYTHON_PATH, '-c', script],
        'Daily report generation',
        timeout=Config.REPORT_TIMEOUT
    )


def collect_historical_institutional():
    """Collect historical institutional data (Saturday only)"""
    logger.info("📚 Collecting historical institutional data...")
    script = f"""
import sys
sys.path.insert(0, '{Config.BASE_DIR}')
from kr_market.scripts.all_institutional_trend_data import main
main(max_stocks=100)
"""
    return run_command(
        [Config.PYTHON_PATH, '-c', script],
        'Historical institutional data collection',
        timeout=Config.HISTORY_TIMEOUT
    )


def run_full_update():
    """Run all update tasks in sequence"""
    logger.info("=" * 60)
    logger.info("🔄 Running FULL UPDATE sequence")
    logger.info("=" * 60)
    
    tasks = [
        update_daily_prices,
        update_institutional_data,
        run_vcp_signal_scan,
        generate_daily_report
    ]
    
    results = []
    for task in tasks:
        success = task()
        results.append(success)
        time.sleep(5)  # Brief delay between tasks
    
    success_count = sum(results)
    logger.info("=" * 60)
    logger.info(f"✅ Full update complete: {success_count}/{len(tasks)} tasks succeeded")
    logger.info("=" * 60)
    
    return all(results)


class Scheduler:
    """Main scheduler class"""
    
    def __init__(self):
        self.running = True
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        logger.info("📅 Scheduler initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, shutting down...")
        self.running = False
    
    def setup_schedules(self):
        """Register scheduled tasks"""
        logger.info("⏰ Setting up schedules...")
        
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        
        # Weekday schedules
        for day in weekdays:
            getattr(schedule.every(), day).at(Config.PRICE_UPDATE_TIME).do(update_daily_prices)
            getattr(schedule.every(), day).at(Config.INST_UPDATE_TIME).do(update_institutional_data)
            getattr(schedule.every(), day).at(Config.SIGNAL_SCAN_TIME).do(run_vcp_signal_scan)
            getattr(schedule.every(), day).at(Config.REPORT_TIME).do(generate_daily_report)
        
        # Saturday history collection
        schedule.every().saturday.at(Config.HISTORY_TIME).do(collect_historical_institutional)
        
        logger.info(f"   📍 Prices: Weekdays at {Config.PRICE_UPDATE_TIME}")
        logger.info(f"   📍 Institutional: Weekdays at {Config.INST_UPDATE_TIME}")
        logger.info(f"   📍 Signals: Weekdays at {Config.SIGNAL_SCAN_TIME}")
        logger.info(f"   📍 Reports: Weekdays at {Config.REPORT_TIME}")
        logger.info(f"   📍 History: Saturdays at {Config.HISTORY_TIME}")
        logger.info("✅ Schedules configured")
    
    def run(self):
        """Run scheduler loop"""
        logger.info("🚀 Scheduler started (checking every 30s)")
        logger.info("Press Ctrl+C to stop")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
        
        logger.info("👋 Scheduler stopped")


def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='KR Market Scheduler')
    parser.add_argument('--now', action='store_true', help='Run full update immediately')
    parser.add_argument('--prices', action='store_true', help='Update prices only')
    parser.add_argument('--inst', action='store_true', help='Update institutional data only')
    parser.add_argument('--signals', action='store_true', help='Run signal scan only')
    parser.add_argument('--report', action='store_true', help='Generate report only')
    parser.add_argument('--history', action='store_true', help='Collect historical data')
    
    args = parser.parse_args()
    
    # Ensure directories exist
    Config.ensure_dirs()
    
    # Handle immediate tasks
    if args.now:
        run_full_update()
        return
    
    if args.prices:
        update_daily_prices()
        return
    
    if args.inst:
        update_institutional_data()
        return
    
    if args.signals:
        run_vcp_signal_scan()
        return
    
    if args.report:
        generate_daily_report()
        return
    
    if args.history:
        collect_historical_institutional()
        return
    
    # Default: run scheduler daemon
    scheduler = Scheduler()
    scheduler.setup_schedules()
    scheduler.run()


if __name__ == '__main__':
    main()
