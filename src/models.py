from sqlalchemy import Column, Integer, Float
from database import Base

class Node(Base):
    __tablename__ = "nodes"

    node_id = Column(Integer, primary_key=True, index=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
