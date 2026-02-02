from dataclasses import dataclass, field

@dataclass
class WorkdaySimulationConfig:
    # Latency simulation
    base_latency_ms: int = 50
    latency_variance_ms: int = 50
    write_latency_multiplier: float = 3.0
    
    # Failure injection
    failure_rate: float = 0.0  # 0-1, percentage of requests that fail
    timeout_rate: float = 0.0  # 0-1, percentage that timeout
    
    # Data
    fixture_path: str = "src/adapters/workday/fixtures/"
    
    # Feature flags
    enforce_manager_chain: bool = True  # For approve operations
    enforce_balance_check: bool = True  # For time off requests

    # Concurrency
    # Mode: single-threaded asyncio (atomic dictionary updates, no locks required)
    concurrency_mode: str = "asyncio"

    # Idempotency Cache
    idempotency_cache_max_size: int = 10000
    idempotency_cache_ttl: int = 3600  # seconds (1 hour)
