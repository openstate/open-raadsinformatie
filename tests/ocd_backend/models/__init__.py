# Import test modules here so the noserunner can pick them up, and the
# ModelsTestCase is parsed. Add additional testcases when required
from .model import ModelTestCase
from .database import DatabaseTestCase
from .postgres_database import PostgresDatabaseTestCase
from .serializers import SerializersTestCase
