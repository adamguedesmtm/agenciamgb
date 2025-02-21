"""
Database Models
Author: adamguedesmtm
Created: 2025-02-21 15:38:17
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True)
    steam_id = Column(String, unique=True)
    discord_id = Column(String, unique=True, nullable=True)
    name = Column(String)
    rating = Column(Float, default=1000)
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    last_match = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Estatísticas gerais
    kills = Column(Integer, default=0)
    deaths = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    headshots = Column(Integer, default=0)
    total_damage = Column(Float, default=0)
    rounds_played = Column(Integer, default=0)
    clutches_won = Column(Integer, default=0)
    entry_kills = Column(Integer, default=0)
    
    # Histórico de partidas
    matches = relationship("Match", secondary="player_matches", back_populates="players")

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True)
    demo_path = Column(String)
    map_name = Column(String)
    score_ct = Column(Integer)
    score_t = Column(Integer)
    duration = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    players = relationship("Player", secondary="player_matches", back_populates="matches")
    rounds = relationship("Round", back_populates="match")

class PlayerMatch(Base):
    __tablename__ = "player_matches"
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    match_id = Column(Integer, ForeignKey("matches.id"))
    team = Column(String)  # "CT" ou "T"
    rating_change = Column(Float)
    kills = Column(Integer)
    deaths = Column(Integer)
    assists = Column(Integer)
    kd_ratio = Column(Float)
    adr = Column(Float)
    kast = Column(Float)
    entry_kills = Column(Integer)
    clutches_won = Column(Integer)

class Round(Base):
    __tablename__ = "rounds"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    round_number = Column(Integer)
    winner_side = Column(String)
    end_reason = Column(String)
    duration = Column(Float)
    
    match = relationship("Match", back_populates="rounds")