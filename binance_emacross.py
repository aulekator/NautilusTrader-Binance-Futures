from decimal import Decimal

from nautilus_trader.adapters.binance import BINANCE
from nautilus_trader.adapters.binance import BinanceAccountType
from nautilus_trader.adapters.binance import BinanceDataClientConfig
from nautilus_trader.adapters.binance import BinanceExecClientConfig
from nautilus_trader.adapters.binance import BinanceLiveDataClientFactory
from nautilus_trader.adapters.binance import BinanceLiveExecClientFactory
from nautilus_trader.cache.config import CacheConfig
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.config import LiveRiskEngineConfig
from nautilus_trader.config import LiveExecEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.examples.strategies.ema_cross import EMACross
from nautilus_trader.examples.strategies.ema_cross import EMACrossConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import TraderId

import os
from dotenv import load_dotenv

load_dotenv()


# *** TRADE WITH REAL MONEY AT YOUR OWN RISK. ***

# Strategy config params
symbol = "BTCUSDT-PERP" #you can change to ETHUSDT-PERP
instrument_id = InstrumentId.from_str(f"{symbol}.{BINANCE}")
order_qty = Decimal("1.10") # SET TRADE SIZE FROM 0.01, 0.02, 0.04 , 0.1 ETC

# Configure the trading node
config_node = TradingNodeConfig(
    trader_id=TraderId("GABRIEL-001"),
    logging=LoggingConfig(log_level="INFO"),
    exec_engine=LiveExecEngineConfig(
        reconciliation=True,
        reconciliation_lookback_mins=1440,
    ),

    cache=CacheConfig(
        # database=DatabaseConfig(timeout=2),
        timestamps_as_iso8601=True,
        flush_on_start=False,
    ),
    # message_bus=MessageBusConfig(
    #     database=DatabaseConfig(timeout=2),
    #     timestamps_as_iso8601=True,
    #     use_instance_id=False,
    #     # types_filter=[QuoteTick],
    #     stream_per_topic=False,
    #     external_streams=["bybit"],
    #     autotrim_mins=30,
    # ),
    data_clients={
        BINANCE: BinanceDataClientConfig(
            api_key=os.getenv('BINANCE_API_KEY'),  # 'BINANCE_API_KEY' env var
            api_secret=os.getenv('BINANCE_API_SECRET'),
            account_type=BinanceAccountType.USDT_FUTURES,
            base_url_http=None,  # Override with custom endpoint
            base_url_ws=None,  # Override with custom endpoint
            us=False,  # If client is for Binance US
            testnet=True,  # If client uses the testnet
            instrument_provider=InstrumentProviderConfig(load_all=True),
        ),
    },
    risk_engine=LiveRiskEngineConfig(
        # qsize = 100_000
        debug=True,
        bypass=False,
        graceful_shutdown_on_exception=True
        # max_notional_per_order=1.2

    ),
    exec_clients={
        BINANCE: BinanceExecClientConfig(
            api_key=os.getenv('BINANCE_API_KEY'),  # 'BINANCE_API_KEY' env var
            api_secret=os.getenv('BINANCE_API_SECRET'),
            account_type=BinanceAccountType.USDT_FUTURES,
            base_url_http=None,  # Override with custom endpoint
            base_url_ws=None,  # Override with custom endpoint
            us=False,  # If client is for Binance US
            testnet=True,  # If client uses the testnet
            instrument_provider=InstrumentProviderConfig(load_all=True),
            max_retries=3,
            use_position_ids=False,
        ),
    },
    timeout_connection=30.0,
    timeout_reconciliation=10.0,
    timeout_portfolio=10.0,
    timeout_disconnection=10.0,
    timeout_post_stop=5.0,
)

# Instantiate the node with a configuration
node = TradingNode(config=config_node)

# Configure your strategy
strat_config = EMACrossConfig(
    instrument_id=instrument_id,
    external_order_claims=[instrument_id],
    bar_type=BarType.from_str(f"{instrument_id}-1-MINUTE-LAST-EXTERNAL"),
    fast_ema_period=10,
    slow_ema_period=20,
    trade_size=order_qty,
    order_id_tag="001",
    oms_type="HEDGING",
    subscribe_trade_ticks=True,
    subscribe_quote_ticks=True,
)

# Instantiate your strategy
strategy = EMACross(config=strat_config)

# Add your strategies and modules
node.trader.add_strategy(strategy)

# Register your client factories with the node (can take user-defined factories)
node.add_data_client_factory(BINANCE, BinanceLiveDataClientFactory)
node.add_exec_client_factory(BINANCE, BinanceLiveExecClientFactory)
node.build()


# Stop and dispose of the node with SIGINT/CTRL+C
if __name__ == "__main__":
    try:
        node.run()
    finally:
        node.dispose()