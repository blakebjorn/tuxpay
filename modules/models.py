import datetime

import databases
from sqlalchemy import MetaData, Column, Integer, DateTime, Unicode, UnicodeText, LargeBinary
from sqlalchemy import create_engine, Index, Table

from modules import config

_db_uri = config.get("database_uri", default="sqlite:///default.db")
metadata = MetaData()
database = databases.Database(_db_uri)

Invoice = Table(
    "invoices", metadata,
    Column("id", Integer, primary_key=True),
    Column("uuid", Unicode(200), unique=True),
    Column("amount_cents", Integer),
    Column("currency", Unicode(20)),
    Column("creation_date", DateTime),
    Column("expiry_date", DateTime),
    Column("payment_date", DateTime),
    Column("name", Unicode(50)),
    Column("customer_name", Unicode(200)),
    Column("customer_email", Unicode(200)),
    Column("notes", UnicodeText),
    Column("notes_html", UnicodeText),
    Column("contents", UnicodeText),
    Column("contents_html", UnicodeText),
    Column("status", Unicode(20)),
)

Payment = Table(
    "payments", metadata,
    Column("id", Integer, primary_key=True),
    Column("invoice_id", Integer),
    Column("symbol", Unicode(20)),
    Column("uuid", Unicode(200), unique=True),
    Column("creation_date", DateTime),
    Column("creation_height", Integer),
    Column("expiry_date", DateTime),
    Column("scripthash", Unicode(60)),
    Column("amount_sats", Integer),
    Column("derivation_path", Unicode(50)),
    Column("derivation_account", Integer),
    Column("derivation_index", Integer),
    Column("address", Unicode(100)),
    Column("paid_amount_sats", Integer),
    Column("payment_date", DateTime),
    Column("last_update", Integer),
    Column("status", Unicode(20)),
    Column("transactions", UnicodeText),
    Index("IX_Invoice", "symbol", "derivation_path", unique=True)
)

SeedPhrase = Table(
    "seeds", metadata,
    Column("id", Integer, primary_key=True),
    Column("checksum", Unicode(64), unique=True),
    Column("date_added", DateTime, default=datetime.datetime.utcnow),
)

User = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("email", Unicode(100), unique=True),
    Column("name", Unicode(100), unique=True),
    Column("password", LargeBinary(100), default=datetime.datetime.utcnow),
)

ElectrumServer = Table(
    "electrum_servers", metadata,
    Column("id", Integer, primary_key=True),
    Column("symbol", Unicode(20)),
    Column("host", Unicode(150)),
    Column("first_seen", DateTime),
    Column("last_check", DateTime),
    Column("last_seen", DateTime),
    Column("connections", Integer),
    Column("failures", Integer),
    Column("latency", Integer),
    Index('idx_hosts', 'symbol', 'host', unique=True)
)


def create_db():
    engine = synchronous_engine()
    metadata.create_all(bind=engine)
    engine.dispose()


def synchronous_engine():
    return create_engine(_db_uri)
