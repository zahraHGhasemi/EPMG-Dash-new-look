# import os
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base

# # --- Database URL (reuse your existing one if needed) ---
# DATABASE_URL = os.getenv(
#     "APP_DB_URL",
#     'postgresql://neondb_owner:npg_R7ugMkq3NQFO@ep-fragrant-truth-ab92jg3a-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
# )

# # --- Engine and ORM setup ---
# engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()
