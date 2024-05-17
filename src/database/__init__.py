from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import registry

Base = declarative_base()

from src.database.models import *

mapper_registry = registry()
