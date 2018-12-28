#!/usr/bin/env python3

import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key=True)
	name = Column(String(250))
	email = Column(String(250), nullable=False)
	picture = Column(String(250))

class CatalogItem(Base):
	__tablename__ = 'catalogs'

	id = Column(Integer, primary_key = True)
	name = Column(String(80), nullable = False)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
	    """Return object data in easily serializeable format"""
	    return {
	    	'id': self.id,
	        'name': self.name,
	    }

class ItemDetail(Base):
	__tablename__ = 'item_detail'
    
	id = Column(Integer, primary_key = True)
	name = Column(String(80), nullable = False)
	description = Column(String(250))
	catalog_id = Column(Integer, ForeignKey('catalogs.id'))
	catalogs = relationship(CatalogItem)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
	    """Return object data in easily serializeable format"""
	    return {
			'id':self.id,
			'name':self.name,
			'description':self.description,
			'catalog':self.catalogs.name, 
	    }

engine = create_engine('postgresql://catalog:catalog-pw@localhost/catalog')
Base.metadata.create_all(engine)
