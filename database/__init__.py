from config import Config
from motor.motor_asyncio import AsyncIOMotorClient
import dns.resolver
dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers=['8.8.8.8']


Database = AsyncIOMotorClient(Config.DATABASE_URL)
db = Database.Bot