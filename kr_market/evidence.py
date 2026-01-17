#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KR Evidence Ledger (Palantir Mini)
Records structured evidence for every signal decision.
"""
import json
import os
from datetime import datetime
from dataclasses import asdict
from typing import Dict, Any

import numpy as np

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super(NumpyEncoder, self).default(obj)

class EvidenceLedger:
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.dirname(os.path.abspath(__file__))
        self.evidence_dir = os.path.join(self.data_dir, 'data', 'evidence')
        os.makedirs(self.evidence_dir, exist_ok=True)
        
    def log_signal(self, ticker: str, gate_results: Dict[str, Any], plan: Any, final_score: int):
        """
        Log complete evidence packet for a signal.
        """
        # Convert dataclasses to dict
        plan_dict = asdict(plan) if hasattr(plan, '__dataclass_fields__') else plan
        
        # Serialize Gate Results
        serialized_gates = {}
        for k, v in gate_results.items():
            if hasattr(v, '__dataclass_fields__'):
                serialized_gates[k] = asdict(v)
            else:
                serialized_gates[k] = v
                
        packet = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "ticker": ticker,
            "final_score": final_score,
            "gates": serialized_gates,
            "execution_plan": plan_dict,
            "metadata": {
                "engine": "KR-NICE-vPerfect",
                "gate_weights": "standard" 
            }
        }
        
        # Save to JSON (Daily partitioned)
        date_str = datetime.now().strftime("%Y%m%d")
        daily_dir = os.path.join(self.evidence_dir, date_str)
        os.makedirs(daily_dir, exist_ok=True)
        
        filename = f"{ticker}_{datetime.now().strftime('%H%M%S')}.json"
        filepath = os.path.join(daily_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(packet, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
        except Exception as e:
            print(f"Failed to log evidence for {ticker}: {e}")
            
        return filepath
