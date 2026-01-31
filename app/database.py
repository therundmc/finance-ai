"""
Module de base de données SQLite pour le stockage des analyses financières.
Remplace le stockage JSON pour une meilleure maintenabilité.
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', '/app/data/finance.db')
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, echo=False, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================
# MODÈLES
# ============================================

class Analysis(Base):
    """Table principale des analyses"""
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    price = Column(Float)
    change_1d = Column(Float)
    change_1mo = Column(Float)
    model = Column(String(50))
    analysis_time = Column(Float)
    signal = Column(String(20), index=True)
    confidence = Column(String(20))
    summary = Column(Text)
    news_analyzed = Column(Integer, default=0)
    analysis = Column(Text)
    raw_response = Column(Text)
    sector = Column(String(50), index=True)  # NEW: sector field
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    indicators = relationship("Indicator", back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    structured_data = relationship("StructuredData", back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'analyse en dictionnaire (format compatible JSON legacy)"""
        result = {
            'id': self.id,
            'ticker': self.ticker,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'price': self.price,
            'change_1d': self.change_1d,
            'change_1mo': self.change_1mo,
            'model': self.model,
            'analysis_time': self.analysis_time,
            'signal': self.signal,
            'confidence': self.confidence,
            'summary': self.summary,
            'news_analyzed': self.news_analyzed,
            'analysis': self.analysis,
            'raw_response': self.raw_response,
            'sector': self.sector,
        }
        
        # Ajouter les indicateurs si présents
        if self.indicators:
            result['indicators'] = self.indicators.to_dict()
        else:
            result['indicators'] = {}
            
        # Ajouter les données structurées si présentes
        if self.structured_data:
            result['structured_data'] = self.structured_data.data
        else:
            result['structured_data'] = None
            
        return result


class Indicator(Base):
    """Table des indicateurs techniques"""
    __tablename__ = 'indicators'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    rsi = Column(Float)
    ma_20 = Column(Float)
    ma_50 = Column(Float)
    ma_200 = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    bb_upper = Column(Float)
    bb_middle = Column(Float)
    bb_lower = Column(Float)
    bb_position = Column(Float)
    volume_avg = Column(Float)
    volume_current = Column(Float)
    volume_ratio = Column(Float)
    atr = Column(Float)
    atr_percent = Column(Float)
    stoch_k = Column(Float)
    stoch_d = Column(Float)
    resistance = Column(Float)
    support = Column(Float)
    
    # Relation inverse
    analysis = relationship("Analysis", back_populates="indicators")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit les indicateurs en dictionnaire"""
        return {
            'rsi': self.rsi,
            'ma_20': self.ma_20,
            'ma_50': self.ma_50,
            'ma_200': self.ma_200,
            'macd': self.macd,
            'macd_signal': self.macd_signal,
            'macd_histogram': self.macd_histogram,
            'bb_upper': self.bb_upper,
            'bb_middle': self.bb_middle,
            'bb_lower': self.bb_lower,
            'bb_position': self.bb_position,
            'volume_avg': self.volume_avg,
            'volume_current': self.volume_current,
            'volume_ratio': self.volume_ratio,
            'atr': self.atr,
            'atr_percent': self.atr_percent,
            'stoch_k': self.stoch_k,
            'stoch_d': self.stoch_d,
            'resistance': self.resistance,
            'support': self.support,
        }


class StructuredData(Base):
    """Table des données structurées (JSON flexible)"""
    __tablename__ = 'structured_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id', ondelete='CASCADE'), nullable=False, unique=True)
    data = Column(JSON)  # SQLite supporte JSON via TEXT
    
    # Relation inverse
    analysis = relationship("Analysis", back_populates="structured_data")


class NewsArticle(Base):
    """Table des articles d'actualité"""
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(100), unique=True, index=True)  # ID externe Finnhub
    ticker = Column(String(20), index=True, nullable=True)  # Null si news générale
    category = Column(String(50), index=True)  # company, market, sector_tech, etc.
    headline = Column(String(500), nullable=False)
    summary = Column(Text)
    source = Column(String(100))
    url = Column(String(500))
    image_url = Column(String(500))
    published_at = Column(DateTime, index=True)
    related_tickers = Column(String(200))  # CSV des tickers liés
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'external_id': self.external_id,
            'ticker': self.ticker,
            'category': self.category,
            'headline': self.headline,
            'summary': self.summary,
            'source': self.source,
            'url': self.url,
            'image_url': self.image_url,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'related_tickers': self.related_tickers.split(',') if self.related_tickers else [],
            'fetched_at': self.fetched_at.isoformat() if self.fetched_at else None,
            'time_ago': self._get_time_ago()
        }
    
    def _get_time_ago(self) -> str:
        """Retourne une représentation lisible du temps écoulé"""
        if not self.published_at:
            return ""
        
        now = datetime.utcnow()
        diff = now - self.published_at
        
        if diff.days > 0:
            return f"il y a {diff.days}j"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"il y a {hours}h"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"il y a {minutes}min"
        else:
            return "à l'instant"


class NewsSummary(Base):
    """Table des résumés d'actualités générés par IA"""
    __tablename__ = 'news_summaries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False, index=True)  # my_stocks, market, tech
    summary = Column(Text, nullable=False)
    article_count = Column(Integer, default=0)
    sources = Column(String(500))  # CSV des sources
    is_fallback = Column(Boolean, default=False)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'category': self.category,
            'summary': self.summary,
            'article_count': self.article_count,
            'sources': self.sources.split(',') if self.sources else [],
            'is_fallback': self.is_fallback,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }


class PortfolioAnalysis(Base):
    """Table des analyses AI du portefeuille - conseils quotidiens"""
    __tablename__ = 'portfolio_analyses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    
    # Résumé global
    portfolio_state = Column(String(20))  # Sain, Attention, Critique
    portfolio_trend = Column(String(20))  # Haussière, Baissière, Mixte
    health_score = Column(Integer)  # 0-100
    summary = Column(Text)  # Synthèse globale
    
    # Actions du jour (stockées en JSON)
    actions_high_priority = Column(JSON)  # Liste des actions urgentes
    actions_watch = Column(JSON)  # Points à surveiller
    actions_opportunities = Column(JSON)  # Opportunités
    
    # Plan d'action (JSON array of strings - numbered steps)
    plan_action = Column(JSON)  # ["Vendre GCTS...", "Acheter NOC...", ...]

    # Achats recommandés (JSON array)
    achats_recommandes = Column(JSON)  # [{ticker, raison, budget_suggere, prix_entree, stop_loss, objectif, conviction}]

    # Ventes recommandées (JSON array)
    ventes_recommandees = Column(JSON)  # [{ticker, raison, prix_actuel, stop_loss, urgence}]

    # Conseils par position (JSON array)
    position_advice = Column(JSON)  # [{ticker, action, conseil, urgence, raison}]

    # Projections (JSON)
    projections = Column(JSON)  # {expected_pnl_1w, expected_pnl_1m, expected_pnl_1y, confidence_level, commentary}

    # Baseline for projection tracking
    baseline_portfolio_value = Column(Float)  # Portfolio value at time of projection
    baseline_pnl_pct = Column(Float)  # P&L % at time of projection

    # Risques et allocation
    allocation_comment = Column(Text)
    main_risk = Column(Text)
    
    # Conclusion
    conclusion = Column(Text)
    
    # Métadonnées
    analysis_time = Column(Float)  # Temps d'analyse en secondes
    model = Column(String(50))  # Modèle utilisé
    positions_count = Column(Integer)  # Nombre de positions analysées
    raw_response = Column(JSON)  # Réponse brute complète
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'portfolio_state': self.portfolio_state,
            'portfolio_trend': self.portfolio_trend,
            'health_score': self.health_score,
            'resume_global': {
                'etat_portfolio': self.portfolio_state,
                'tendance': self.portfolio_trend,
                'score_sante': self.health_score,
                'resume': self.summary or ''
            },
            'summary': self.summary,
            'plan_action': self.plan_action or [],
            'actions_high_priority': self.actions_high_priority or [],
            'actions_watch': self.actions_watch or [],
            'actions_opportunities': self.actions_opportunities or [],
            'achats_recommandes': self.achats_recommandes or [],
            'ventes_recommandees': self.ventes_recommandees or [],
            'position_advice': self.position_advice or [],
            'projections': self.projections or {},
            'allocation_comment': self.allocation_comment,
            'main_risk': self.main_risk,
            'conclusion': self.conclusion,
            'analysis_time': self.analysis_time,
            'model': self.model,
            'positions_count': self.positions_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Favorite(Base):
    """Table des favoris utilisateur"""
    __tablename__ = 'favorites'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'ticker': self.ticker,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Position(Base):
    """Table des positions (achats suivis)"""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=True)
    
    # Détails de l'entrée
    entry_price = Column(Float, nullable=False)
    entry_date = Column(DateTime, nullable=False)
    quantity = Column(Float, default=1)
    
    # Niveaux de trading
    stop_loss = Column(Float)
    take_profit_1 = Column(Float)
    take_profit_2 = Column(Float)
    
    # Commissions (stored in position's currency)
    buy_commission = Column(Float, default=0)
    sell_commission = Column(Float, default=0)
    
    # Statut et sortie
    status = Column(String(20), default='open', index=True)  # open, closed, stopped
    exit_price = Column(Float)
    exit_date = Column(DateTime)
    
    # Notes
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relation avec l'analyse source
    analysis = relationship("Analysis")
    
    def to_dict(self, current_price: float = None) -> Dict[str, Any]:
        buy_comm = self.buy_commission or 0
        sell_comm = self.sell_commission or 0
        total_commission = buy_comm + sell_comm
        
        result = {
            'id': self.id,
            'ticker': self.ticker,
            'analysis_id': self.analysis_id,
            'entry_price': self.entry_price,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'quantity': self.quantity,
            'stop_loss': self.stop_loss,
            'take_profit_1': self.take_profit_1,
            'take_profit_2': self.take_profit_2,
            'buy_commission': buy_comm,
            'sell_commission': sell_comm,
            'total_commission': total_commission,
            'status': self.status,
            'exit_price': self.exit_price,
            'exit_date': self.exit_date.isoformat() if self.exit_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        # Calculer P&L si prix actuel fourni et position ouverte
        if current_price and self.status == 'open':
            pnl_gross = (current_price - self.entry_price) * (self.quantity or 1)
            pnl_net = pnl_gross - total_commission
            pnl_percent = (pnl_net / (self.entry_price * (self.quantity or 1))) * 100
            
            result['current_price'] = current_price
            result['pnl_gross'] = pnl_gross
            result['pnl_value'] = pnl_net  # Net P&L after commissions
            result['pnl_percent'] = pnl_percent
            
            # Statut par rapport aux niveaux
            if self.stop_loss and current_price <= self.stop_loss:
                result['level_status'] = 'danger'
            elif self.take_profit_1 and current_price >= self.take_profit_1:
                result['level_status'] = 'target_1'
            elif self.take_profit_2 and current_price >= self.take_profit_2:
                result['level_status'] = 'target_2'
            else:
                result['level_status'] = 'normal'
        
        return result


class PortfolioSnapshot(Base):
    """Table des snapshots quotidiens du portfolio pour les graphiques de performance"""
    __tablename__ = 'portfolio_snapshots'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)  # Date du snapshot
    total_value = Column(Float, nullable=False)          # Valeur totale du portfolio
    total_invested = Column(Float, nullable=False)       # Capital total investi
    total_pnl = Column(Float, default=0)                 # P&L en devise (positions ouvertes)
    total_pnl_percent = Column(Float, default=0)         # P&L en pourcentage (positions ouvertes)
    realized_pnl = Column(Float, default=0)              # P&L réalisé (positions fermées)
    global_pnl = Column(Float, default=0)                # P&L global (open + realized)
    global_pnl_percent = Column(Float, default=0)        # P&L global en pourcentage
    open_positions_count = Column(Integer, default=0)    # Nombre de positions ouvertes
    closed_positions_count = Column(Integer, default=0)  # Positions fermées ce jour
    total_closed_count = Column(Integer, default=0)      # Total positions fermées
    daily_change = Column(Float, default=0)              # Changement par rapport à la veille
    daily_change_percent = Column(Float, default=0)      # Changement en %
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d %H:%M') if self.date else None,
            'total_value': self.total_value,
            'total_invested': self.total_invested,
            'total_pnl': self.total_pnl,
            'total_pnl_percent': self.total_pnl_percent,
            'realized_pnl': self.realized_pnl or 0,
            'global_pnl': self.global_pnl or self.total_pnl,  # Fallback to total_pnl
            'global_pnl_percent': self.global_pnl_percent or self.total_pnl_percent,
            'open_positions_count': self.open_positions_count,
            'closed_positions_count': self.closed_positions_count,
            'total_closed_count': self.total_closed_count or 0,
            'daily_change': self.daily_change,
            'daily_change_percent': self.daily_change_percent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def init_db():
    """Initialise la base de données (crée les tables)"""
    # Créer le dossier si nécessaire
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    Base.metadata.create_all(bind=engine)

    # Migrations for existing databases
    import sqlite3
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    for col in ['achats_recommandes', 'projections', 'plan_action', 'ventes_recommandees']:
        try:
            cursor.execute(f"ALTER TABLE portfolio_analyses ADD COLUMN {col} TEXT")
            conn.commit()
            print(f"  Migration: {col} column added to portfolio_analyses")
        except sqlite3.OperationalError:
            pass  # Column already exists
    # Baseline columns for projection tracking
    for col in [('baseline_portfolio_value', 'REAL'), ('baseline_pnl_pct', 'REAL')]:
        try:
            cursor.execute(f"ALTER TABLE portfolio_analyses ADD COLUMN {col[0]} {col[1]}")
            conn.commit()
            print(f"  Migration: {col[0]} column added to portfolio_analyses")
        except sqlite3.OperationalError:
            pass
    conn.close()

    print(f"✅ Base de données initialisée: {DATABASE_PATH}")


def get_db() -> Session:
    """Retourne une session de base de données"""
    return SessionLocal()


def save_analysis(data: Dict[str, Any]) -> Optional[Analysis]:
    """
    Sauvegarde une analyse dans la base de données.
    
    Args:
        data: Dictionnaire avec les données de l'analyse (format legacy JSON)
        
    Returns:
        L'objet Analysis créé ou None en cas d'erreur
    """
    db = get_db()
    try:
        # Créer l'analyse principale
        analysis = Analysis(
            ticker=data.get('ticker'),
            timestamp=datetime.fromisoformat(data['timestamp']) if isinstance(data.get('timestamp'), str) else data.get('timestamp', datetime.now()),
            price=data.get('price'),
            change_1d=data.get('change_1d'),
            change_1mo=data.get('change_1mo'),
            model=data.get('model'),
            analysis_time=data.get('analysis_time'),
            signal=data.get('signal'),
            confidence=data.get('confidence'),
            summary=data.get('summary'),
            news_analyzed=data.get('news_analyzed', 0),
            analysis=data.get('analysis'),
            raw_response=data.get('raw_response'),
            sector=data.get('sector'),
        )
        
        db.add(analysis)
        db.flush()  # Pour obtenir l'ID
        
        # Ajouter les indicateurs si présents
        indicators_data = data.get('indicators', {})
        if indicators_data:
            indicator = Indicator(
                analysis_id=analysis.id,
                rsi=indicators_data.get('rsi'),
                ma_20=indicators_data.get('ma_20'),
                ma_50=indicators_data.get('ma_50'),
                ma_200=indicators_data.get('ma_200'),
                macd=indicators_data.get('macd'),
                macd_signal=indicators_data.get('macd_signal'),
                macd_histogram=indicators_data.get('macd_histogram'),
                bb_upper=indicators_data.get('bb_upper'),
                bb_middle=indicators_data.get('bb_middle'),
                bb_lower=indicators_data.get('bb_lower'),
                bb_position=indicators_data.get('bb_position'),
                volume_avg=indicators_data.get('volume_avg'),
                volume_current=indicators_data.get('volume_current'),
                volume_ratio=indicators_data.get('volume_ratio'),
                atr=indicators_data.get('atr'),
                atr_percent=indicators_data.get('atr_percent'),
                stoch_k=indicators_data.get('stoch_k'),
                stoch_d=indicators_data.get('stoch_d'),
                resistance=indicators_data.get('resistance'),
                support=indicators_data.get('support'),
            )
            db.add(indicator)
        
        # Ajouter les données structurées si présentes
        structured = data.get('structured_data')
        if structured:
            structured_obj = StructuredData(
                analysis_id=analysis.id,
                data=structured
            )
            db.add(structured_obj)
        
        db.commit()
        db.refresh(analysis)
        
        print(f"💾 Sauvegardé en DB: {analysis.ticker} (ID: {analysis.id})")
        return analysis
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur sauvegarde DB: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


def get_analyses(ticker: Optional[str] = None, days: int = 7, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Récupère les analyses depuis la base de données.
    
    Args:
        ticker: Filtrer par ticker (optionnel)
        days: Nombre de jours à récupérer
        limit: Limite du nombre de résultats
        
    Returns:
        Liste de dictionnaires d'analyses
    """
    from datetime import timedelta
    
    db = get_db()
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = db.query(Analysis).filter(Analysis.timestamp >= cutoff_date)
        
        if ticker:
            query = query.filter(Analysis.ticker == ticker)
        
        query = query.order_by(Analysis.timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        analyses = query.all()
        return [a.to_dict() for a in analyses]
        
    finally:
        db.close()


def get_latest_by_ticker(hours: int = 24) -> Dict[str, Dict[str, Any]]:
    """
    Récupère la dernière analyse de chaque ticker.
    
    Args:
        hours: Nombre d'heures à considérer
        
    Returns:
        Dictionnaire {ticker: analyse}
    """
    from datetime import timedelta
    from sqlalchemy import func
    
    db = get_db()
    try:
        cutoff_date = datetime.now() - timedelta(hours=hours)
        
        # Sous-requête pour obtenir la dernière analyse par ticker
        subquery = db.query(
            Analysis.ticker,
            func.max(Analysis.timestamp).label('max_timestamp')
        ).filter(
            Analysis.timestamp >= cutoff_date
        ).group_by(Analysis.ticker).subquery()
        
        # Requête principale
        analyses = db.query(Analysis).join(
            subquery,
            (Analysis.ticker == subquery.c.ticker) & 
            (Analysis.timestamp == subquery.c.max_timestamp)
        ).all()
        
        return {a.ticker: a.to_dict() for a in analyses}
        
    finally:
        db.close()


def get_latest_analyses(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Récupère la dernière analyse pour une liste de tickers spécifiques.
    
    Args:
        tickers: Liste des tickers à récupérer
        
    Returns:
        Dictionnaire {ticker: analyse}
    """
    from sqlalchemy import func
    
    if not tickers:
        return {}
    
    db = get_db()
    try:
        # Sous-requête pour obtenir la dernière analyse par ticker
        subquery = db.query(
            Analysis.ticker,
            func.max(Analysis.timestamp).label('max_timestamp')
        ).filter(
            Analysis.ticker.in_(tickers)
        ).group_by(Analysis.ticker).subquery()
        
        # Requête principale
        analyses = db.query(Analysis).join(
            subquery,
            (Analysis.ticker == subquery.c.ticker) & 
            (Analysis.timestamp == subquery.c.max_timestamp)
        ).all()
        
        return {a.ticker: a.to_dict() for a in analyses}
        
    finally:
        db.close()


def get_last_analysis_times(tickers: List[str] = None) -> Dict[str, datetime]:
    """
    Récupère le timestamp de la dernière analyse pour chaque ticker.
    
    Args:
        tickers: Liste des tickers à vérifier (optionnel, sinon tous)
        
    Returns:
        Dictionnaire {ticker: last_analysis_timestamp}
    """
    from sqlalchemy import func
    
    db = get_db()
    try:
        query = db.query(
            Analysis.ticker,
            func.max(Analysis.timestamp).label('last_analysis')
        ).group_by(Analysis.ticker)
        
        if tickers:
            query = query.filter(Analysis.ticker.in_(tickers))
        
        results = query.all()
        return {r.ticker: r.last_analysis for r in results}
        
    finally:
        db.close()


def get_last_batch_analysis_date() -> Optional[str]:
    """
    Get the date of the last full batch analysis.
    Stored in a simple key-value style using the NewsSummary table with a special category.
    
    Returns:
        Date string (YYYY-MM-DD) or None if never run
    """
    db = get_db()
    try:
        record = db.query(NewsSummary).filter(
            NewsSummary.category == '_system_last_batch_analysis'
        ).first()
        
        if record:
            return record.summary  # We store the date in summary field
        return None
    finally:
        db.close()


def set_last_batch_analysis_date(date_str: str) -> bool:
    """
    Set the date of the last full batch analysis.
    
    Args:
        date_str: Date string (YYYY-MM-DD)
        
    Returns:
        True if saved successfully
    """
    db = get_db()
    try:
        record = db.query(NewsSummary).filter(
            NewsSummary.category == '_system_last_batch_analysis'
        ).first()
        
        if record:
            record.summary = date_str
            record.generated_at = datetime.utcnow()
        else:
            record = NewsSummary(
                category='_system_last_batch_analysis',
                summary=date_str,
                article_count=0,
                is_fallback=False
            )
            db.add(record)
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error saving batch analysis date: {e}")
        return False
    finally:
        db.close()


def get_stats() -> Dict[str, Any]:
    """
    Récupère les statistiques générales.
    
    Returns:
        Dictionnaire avec les stats
    """
    from sqlalchemy import func
    
    db = get_db()
    try:
        total = db.query(func.count(Analysis.id)).scalar()
        tickers = db.query(Analysis.ticker).distinct().all()
        ticker_list = [t[0] for t in tickers]
        
        return {
            'total_analyses': total,
            'unique_tickers': len(ticker_list),
            'tickers': ticker_list
        }
        
    finally:
        db.close()


def get_ticker_history(ticker: str, days: int = 30) -> Dict[str, Any]:
    """
    Récupère l'historique d'un ticker spécifique.
    
    Args:
        ticker: Le ticker à rechercher
        days: Nombre de jours d'historique
        
    Returns:
        Dictionnaire avec analyses et historique des prix
    """
    analyses = get_analyses(ticker=ticker, days=days)
    
    prices = [{'date': a['timestamp'], 'price': a['price']} for a in analyses]
    prices.sort(key=lambda x: x['date'])
    
    return {
        'ticker': ticker,
        'analyses': analyses,
        'price_history': prices
    }


# ============================================
# GESTION DES FAVORIS
# ============================================

def get_favorites() -> List[str]:
    """Récupère la liste des tickers favoris"""
    db = get_db()
    try:
        favorites = db.query(Favorite).order_by(Favorite.created_at.desc()).all()
        return [f.ticker for f in favorites]
    finally:
        db.close()


def add_favorite(ticker: str) -> bool:
    """Ajoute un ticker aux favoris"""
    db = get_db()
    try:
        existing = db.query(Favorite).filter(Favorite.ticker == ticker).first()
        if existing:
            return True  # Déjà favori
        
        fav = Favorite(ticker=ticker)
        db.add(fav)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur ajout favori: {e}")
        return False
    finally:
        db.close()


def remove_favorite(ticker: str) -> bool:
    """Supprime un ticker des favoris"""
    db = get_db()
    try:
        fav = db.query(Favorite).filter(Favorite.ticker == ticker).first()
        if fav:
            db.delete(fav)
            db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur suppression favori: {e}")
        return False
    finally:
        db.close()


def is_favorite(ticker: str) -> bool:
    """Vérifie si un ticker est favori"""
    db = get_db()
    try:
        return db.query(Favorite).filter(Favorite.ticker == ticker).first() is not None
    finally:
        db.close()


# ============================================
# GESTION DES POSITIONS
# ============================================

def create_position(data: Dict[str, Any]) -> Optional[Position]:
    """Crée une nouvelle position"""
    db = get_db()
    try:
        # Load default commissions from config (with fallback)
        default_buy_comm = 10.0
        default_sell_comm = 12.0
        try:
            from config import load_config
            config = load_config()
            trading_config = config.get('trading', {})
            default_buy_comm = trading_config.get('buy_commission', 10.0)
            default_sell_comm = trading_config.get('sell_commission', 12.0)
        except (ImportError, ModuleNotFoundError):
            # Config module not available (e.g., in dashboard container)
            pass
        
        # Parse entry_date properly
        entry_date = data.get('entry_date')
        if isinstance(entry_date, str):
            # Try ISO format first (with time)
            try:
                entry_date = datetime.fromisoformat(entry_date)
            except ValueError:
                # Try date-only format (YYYY-MM-DD)
                from datetime import date
                date_obj = date.fromisoformat(entry_date)
                entry_date = datetime.combine(date_obj, datetime.min.time())
        elif entry_date is None:
            entry_date = datetime.now()
        
        position = Position(
            ticker=data['ticker'],
            analysis_id=data.get('analysis_id'),
            entry_price=data['entry_price'],
            entry_date=entry_date,
            quantity=data.get('quantity', 1),
            stop_loss=data.get('stop_loss'),
            take_profit_1=data.get('take_profit_1'),
            take_profit_2=data.get('take_profit_2'),
            buy_commission=data.get('buy_commission', default_buy_comm),
            sell_commission=data.get('sell_commission', default_sell_comm),
            notes=data.get('notes'),
            status='open'
        )
        db.add(position)
        db.commit()
        db.refresh(position)
        return position
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur création position: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


def get_positions(status: str = None, ticker: str = None) -> List[Dict[str, Any]]:
    """Récupère les positions avec calcul P&L"""
    db = get_db()
    try:
        query = db.query(Position)
        
        if status:
            query = query.filter(Position.status == status)
        if ticker:
            query = query.filter(Position.ticker == ticker)
        
        query = query.order_by(Position.entry_date.desc())
        positions = query.all()
        
        # Récupérer les prix actuels pour calcul P&L
        from sqlalchemy import func
        latest_prices = {}
        
        tickers = list(set(p.ticker for p in positions if p.status == 'open'))
        if tickers:
            for t in tickers:
                latest = db.query(Analysis).filter(
                    Analysis.ticker == t
                ).order_by(Analysis.timestamp.desc()).first()
                if latest:
                    latest_prices[t] = latest.price
        
        return [p.to_dict(current_price=latest_prices.get(p.ticker)) for p in positions]
        
    finally:
        db.close()


def get_position(position_id: int) -> Optional[Dict[str, Any]]:
    """Récupère une position par ID"""
    db = get_db()
    try:
        position = db.query(Position).filter(Position.id == position_id).first()
        if not position:
            return None
        
        # Prix actuel
        current_price = None
        if position.status == 'open':
            latest = db.query(Analysis).filter(
                Analysis.ticker == position.ticker
            ).order_by(Analysis.timestamp.desc()).first()
            if latest:
                current_price = latest.price
        
        return position.to_dict(current_price=current_price)
    finally:
        db.close()


def update_position(position_id: int, data: Dict[str, Any]) -> bool:
    """Met à jour une position"""
    db = get_db()
    try:
        position = db.query(Position).filter(Position.id == position_id).first()
        if not position:
            return False
        
        for key, value in data.items():
            if hasattr(position, key):
                if key in ['entry_date', 'exit_date'] and isinstance(value, str):
                    value = datetime.fromisoformat(value)
                setattr(position, key, value)
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur mise à jour position: {e}")
        return False
    finally:
        db.close()


def close_position(position_id: int, exit_price: float, status: str = 'closed') -> bool:
    """Clôture une position"""
    db = get_db()
    try:
        position = db.query(Position).filter(Position.id == position_id).first()
        if not position:
            return False
        
        position.exit_price = exit_price
        position.exit_date = datetime.now()
        position.status = status  # 'closed' ou 'stopped'
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur clôture position: {e}")
        return False
    finally:
        db.close()


def partial_close_position(position_id: int, exit_price: float, sell_percent: float, status: str = 'closed') -> Optional[Dict[str, Any]]:
    """
    Clôture partielle d'une position.
    - Crée une nouvelle position fermée avec la quantité vendue
    - Réduit la quantité de la position originale
    - Ajuste les commissions proportionnellement
    
    Returns: dict with 'closed_position' and 'remaining_position' or None on error
    """
    db = get_db()
    try:
        position = db.query(Position).filter(Position.id == position_id).first()
        if not position or position.status != 'open':
            return None
        
        if sell_percent <= 0 or sell_percent >= 100:
            return None
        
        sell_ratio = sell_percent / 100.0
        original_qty = position.quantity or 1
        sold_qty = original_qty * sell_ratio
        remaining_qty = original_qty - sold_qty
        
        # Ajuster les commissions
        # Commission d'achat: proportionnelle à la quantité vendue
        # Commission de vente: uniquement sur la partie vendue
        buy_comm = position.buy_commission or 0
        sell_comm = position.sell_commission or 0
        
        sold_buy_comm = buy_comm * sell_ratio
        remaining_buy_comm = buy_comm * (1 - sell_ratio)
        
        # Load default sell commission for new closed position
        default_sell_comm = 12.0
        try:
            from config import load_config
            config = load_config()
            default_sell_comm = config.get('trading', {}).get('sell_commission', 12.0)
        except:
            pass
        
        # Créer la position fermée (partie vendue)
        closed_position = Position(
            ticker=position.ticker,
            analysis_id=position.analysis_id,
            entry_price=position.entry_price,
            entry_date=position.entry_date,
            quantity=sold_qty,
            stop_loss=position.stop_loss,
            take_profit_1=position.take_profit_1,
            take_profit_2=position.take_profit_2,
            buy_commission=sold_buy_comm,
            sell_commission=default_sell_comm,  # Apply sell commission to closed position
            status=status,
            exit_price=exit_price,
            exit_date=datetime.now(),
            notes=f"Vente partielle ({sell_percent}%) - Position originale #{position_id}"
        )
        db.add(closed_position)
        
        # Mettre à jour la position originale
        position.quantity = remaining_qty
        position.buy_commission = remaining_buy_comm
        position.sell_commission = 0  # Reset sell commission for remaining position
        if position.notes:
            position.notes += f"\n[{datetime.now().strftime('%Y-%m-%d')}] Vente partielle {sell_percent}% à {exit_price}"
        else:
            position.notes = f"[{datetime.now().strftime('%Y-%m-%d')}] Vente partielle {sell_percent}% à {exit_price}"
        
        db.commit()
        db.refresh(closed_position)
        
        return {
            'closed_position': closed_position.to_dict(),
            'remaining_position': position.to_dict(),
            'sold_quantity': sold_qty,
            'remaining_quantity': remaining_qty
        }
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur clôture partielle: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


def delete_position(position_id: int) -> bool:
    """Supprime une position"""
    db = get_db()
    try:
        position = db.query(Position).filter(Position.id == position_id).first()
        if position:
            db.delete(position)
            db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur suppression position: {e}")
        return False
    finally:
        db.close()


def get_positions_summary() -> Dict[str, Any]:
    """Résumé des positions ouvertes"""
    db = get_db()
    try:
        open_positions = db.query(Position).filter(Position.status == 'open').all()
        
        total_invested = sum(p.entry_price * (p.quantity or 1) for p in open_positions)
        total_pnl = 0
        
        # Calculer P&L total
        for p in open_positions:
            latest = db.query(Analysis).filter(
                Analysis.ticker == p.ticker
            ).order_by(Analysis.timestamp.desc()).first()
            if latest:
                pnl = (latest.price - p.entry_price) * (p.quantity or 1)
                total_pnl += pnl
        
        return {
            'open_count': len(open_positions),
            'total_invested': total_invested,
            'total_pnl': total_pnl,
            'total_pnl_percent': (total_pnl / total_invested * 100) if total_invested > 0 else 0
        }
    finally:
        db.close()


# ============================================
# FONCTIONS NEWS
# ============================================

def save_news_article(article_data: Dict[str, Any]) -> Optional[NewsArticle]:
    """
    Sauvegarde un article d'actualité dans la base de données.
    Évite les doublons via external_id.
    
    Args:
        article_data: Dictionnaire avec les données de l'article
        
    Returns:
        L'objet NewsArticle créé ou existant
    """
    db = get_db()
    try:
        external_id = article_data.get('external_id') or article_data.get('id')
        
        # Vérifier si l'article existe déjà
        existing = db.query(NewsArticle).filter(
            NewsArticle.external_id == str(external_id)
        ).first()
        
        if existing:
            return existing
        
        # Parser la date
        published_at = article_data.get('published_at') or article_data.get('datetime')
        if isinstance(published_at, str):
            try:
                published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            except:
                published_at = datetime.utcnow()
        elif isinstance(published_at, (int, float)):
            published_at = datetime.fromtimestamp(published_at)
        
        # Créer l'article
        article = NewsArticle(
            external_id=str(external_id),
            ticker=article_data.get('ticker'),
            category=article_data.get('category', 'general'),
            headline=article_data.get('headline', '')[:500],
            summary=article_data.get('summary', ''),
            source=article_data.get('source', ''),
            url=article_data.get('url', ''),
            image_url=article_data.get('image') or article_data.get('image_url'),
            published_at=published_at,
            related_tickers=','.join(article_data.get('related', [])) if article_data.get('related') else None
        )
        
        db.add(article)
        db.commit()
        db.refresh(article)
        
        return article
        
    except Exception as e:
        db.rollback()
        print(f"⚠️ Erreur sauvegarde article: {e}")
        return None
    finally:
        db.close()


def save_news_articles(articles: List[Dict[str, Any]]) -> int:
    """
    Sauvegarde plusieurs articles en batch.
    
    Returns:
        Nombre d'articles sauvegardés
    """
    count = 0
    for article_data in articles:
        if save_news_article(article_data):
            count += 1
    return count


def get_news_articles(
    ticker: Optional[str] = None,
    category: Optional[str] = None,
    days: int = 7,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Récupère les articles d'actualité depuis la base de données.
    
    Args:
        ticker: Filtrer par ticker (optionnel)
        category: Filtrer par catégorie (optionnel)
        days: Nombre de jours à récupérer
        limit: Limite du nombre de résultats
        
    Returns:
        Liste de dictionnaires d'articles
    """
    from datetime import timedelta
    
    db = get_db()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(NewsArticle).filter(NewsArticle.published_at >= cutoff_date)
        
        if ticker:
            query = query.filter(
                (NewsArticle.ticker == ticker) | 
                (NewsArticle.related_tickers.contains(ticker))
            )
        
        if category:
            query = query.filter(NewsArticle.category == category)
        
        query = query.order_by(NewsArticle.published_at.desc()).limit(limit)
        
        articles = query.all()
        return [a.to_dict() for a in articles]
        
    finally:
        db.close()


def get_news_for_tickers(tickers: List[str], days: int = 3, limit_per_ticker: int = 5) -> Dict[str, List[Dict]]:
    """
    Récupère les news pour plusieurs tickers.
    
    Returns:
        Dict {ticker: [articles]}
    """
    result = {}
    for ticker in tickers:
        result[ticker] = get_news_articles(ticker=ticker, days=days, limit=limit_per_ticker)
    return result


def cleanup_old_news(days: int = 30):
    """Supprime les news plus anciennes que X jours"""
    from datetime import timedelta
    
    db = get_db()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = db.query(NewsArticle).filter(
            NewsArticle.published_at < cutoff_date
        ).delete()
        db.commit()
        print(f"🗑️ {deleted} anciens articles supprimés")
        return deleted
    except Exception as e:
        db.rollback()
        print(f"⚠️ Erreur cleanup news: {e}")
        return 0
    finally:
        db.close()


# ============================================
# FONCTIONS RÉSUMÉS D'ACTUALITÉS
# ============================================

def save_news_summary(category: str, summary_data: Dict[str, Any]) -> bool:
    """
    Sauvegarde un résumé d'actualités généré par IA.
    
    Args:
        category: Catégorie (my_stocks, market, tech)
        summary_data: Dict avec summary, article_count, sources, is_fallback
    """
    db = get_db()
    try:
        news_summary = NewsSummary(
            category=category,
            summary=summary_data.get('summary', ''),
            article_count=summary_data.get('article_count', 0),
            sources=','.join(summary_data.get('sources', [])),
            is_fallback=summary_data.get('is_fallback', False),
            generated_at=datetime.utcnow()
        )
        db.add(news_summary)
        db.commit()
        print(f"💾 Résumé '{category}' sauvegardé (ID: {news_summary.id})")
        return True
    except Exception as e:
        db.rollback()
        print(f"⚠️ Erreur sauvegarde résumé: {e}")
        return False
    finally:
        db.close()


def save_all_news_summaries(summaries: Dict[str, Dict[str, Any]]) -> int:
    """
    Sauvegarde tous les résumés générés.
    
    Args:
        summaries: Dict {category: summary_data}
    
    Returns:
        Nombre de résumés sauvegardés
    """
    count = 0
    for category, summary_data in summaries.items():
        if save_news_summary(category, summary_data):
            count += 1
    return count


def get_latest_news_summaries(max_age_minutes: int = 60) -> Dict[str, Any]:
    """
    Récupère les résumés les plus récents (un par catégorie).
    
    Args:
        max_age_minutes: Âge maximum des résumés en minutes
    
    Returns:
        Dict avec success, summaries, generated_at
    """
    from datetime import timedelta
    from sqlalchemy import func
    
    db = get_db()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        
        # Sous-requête pour obtenir le dernier résumé de chaque catégorie
        subquery = db.query(
            NewsSummary.category,
            func.max(NewsSummary.generated_at).label('max_date')
        ).filter(
            NewsSummary.generated_at >= cutoff
        ).group_by(NewsSummary.category).subquery()
        
        # Récupérer les résumés correspondants
        summaries = db.query(NewsSummary).join(
            subquery,
            (NewsSummary.category == subquery.c.category) & 
            (NewsSummary.generated_at == subquery.c.max_date)
        ).all()
        
        if not summaries:
            return {
                'success': False,
                'error': 'No recent summaries available',
                'summaries': {}
            }
        
        result = {
            'success': True,
            'summaries': {s.category: s.to_dict() for s in summaries},
            'generated_at': max(s.generated_at for s in summaries).isoformat()
        }
        
        return result
        
    except Exception as e:
        print(f"⚠️ Erreur récupération résumés: {e}")
        return {
            'success': False,
            'error': str(e),
            'summaries': {}
        }
    finally:
        db.close()


# ============================================
# FONCTIONS PORTFOLIO SNAPSHOTS
# ============================================

def save_portfolio_snapshot(snapshot_data: Dict[str, Any]) -> Optional[PortfolioSnapshot]:
    """
    Sauvegarde un snapshot du portfolio. Met à jour si existe déjà pour cette date/heure.
    
    Args:
        snapshot_data: Dict avec date, total_value, total_invested, etc.
        
    Returns:
        L'objet PortfolioSnapshot créé ou mis à jour
    """
    db = get_db()
    try:
        snapshot_date = snapshot_data.get('date')
        if isinstance(snapshot_date, str):
            # Try parsing with time first, then without
            try:
                snapshot_date = datetime.strptime(snapshot_date, '%Y-%m-%d %H:%M')
            except ValueError:
                try:
                    snapshot_date = datetime.strptime(snapshot_date, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    snapshot_date = datetime.strptime(snapshot_date, '%Y-%m-%d')
        elif not snapshot_date:
            snapshot_date = datetime.now()
        
        # Vérifier si snapshot existe déjà pour cette date/heure exacte
        existing = db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.date == snapshot_date
        ).first()
        
        if existing:
            # Mettre à jour
            existing.total_value = snapshot_data.get('total_value', existing.total_value)
            existing.total_invested = snapshot_data.get('total_invested', existing.total_invested)
            existing.total_pnl = snapshot_data.get('total_pnl', existing.total_pnl)
            existing.total_pnl_percent = snapshot_data.get('total_pnl_percent', existing.total_pnl_percent)
            existing.realized_pnl = snapshot_data.get('realized_pnl', existing.realized_pnl or 0)
            existing.global_pnl = snapshot_data.get('global_pnl', existing.global_pnl or existing.total_pnl)
            existing.global_pnl_percent = snapshot_data.get('global_pnl_percent', existing.global_pnl_percent or existing.total_pnl_percent)
            existing.open_positions_count = snapshot_data.get('open_positions_count', existing.open_positions_count)
            existing.closed_positions_count = snapshot_data.get('closed_positions_count', existing.closed_positions_count)
            existing.total_closed_count = snapshot_data.get('total_closed_count', existing.total_closed_count or 0)
            existing.daily_change = snapshot_data.get('daily_change', existing.daily_change)
            existing.daily_change_percent = snapshot_data.get('daily_change_percent', existing.daily_change_percent)
            db.commit()
            db.refresh(existing)
            print(f"📊 Snapshot portfolio mis à jour: {snapshot_date.strftime('%Y-%m-%d %H:%M')}")
            return existing
        
        # Créer nouveau snapshot
        snapshot = PortfolioSnapshot(
            date=snapshot_date,
            total_value=snapshot_data.get('total_value', 0),
            total_invested=snapshot_data.get('total_invested', 0),
            total_pnl=snapshot_data.get('total_pnl', 0),
            total_pnl_percent=snapshot_data.get('total_pnl_percent', 0),
            realized_pnl=snapshot_data.get('realized_pnl', 0),
            global_pnl=snapshot_data.get('global_pnl', snapshot_data.get('total_pnl', 0)),
            global_pnl_percent=snapshot_data.get('global_pnl_percent', snapshot_data.get('total_pnl_percent', 0)),
            open_positions_count=snapshot_data.get('open_positions_count', 0),
            closed_positions_count=snapshot_data.get('closed_positions_count', 0),
            total_closed_count=snapshot_data.get('total_closed_count', 0),
            daily_change=snapshot_data.get('daily_change', 0),
            daily_change_percent=snapshot_data.get('daily_change_percent', 0)
        )
        
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        
        print(f"📊 Nouveau snapshot portfolio: {snapshot_date.strftime('%Y-%m-%d')} - Valeur: {snapshot.total_value:.2f}")
        return snapshot
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur sauvegarde snapshot: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


def get_portfolio_history(days: int = 30) -> List[Dict[str, Any]]:
    """
    Récupère l'historique des snapshots du portfolio.
    
    Args:
        days: Nombre de jours d'historique (0 = tout)
        
    Returns:
        Liste de snapshots triés par date croissante
    """
    from datetime import timedelta
    
    db = get_db()
    try:
        query = db.query(PortfolioSnapshot)
        
        if days > 0:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = query.filter(PortfolioSnapshot.date >= cutoff_date)
        
        snapshots = query.order_by(PortfolioSnapshot.date.asc()).all()
        return [s.to_dict() for s in snapshots]
        
    finally:
        db.close()


def get_portfolio_performance() -> Dict[str, Any]:
    """
    Calcule les métriques de performance du portfolio.
    
    Returns:
        Dict avec total_return, best_day, worst_day, max_drawdown, etc.
    """
    db = get_db()
    try:
        snapshots = db.query(PortfolioSnapshot).order_by(
            PortfolioSnapshot.date.asc()
        ).all()
        
        if not snapshots:
            return {
                'total_return': 0,
                'total_return_percent': 0,
                'best_day': None,
                'worst_day': None,
                'max_drawdown': 0,
                'max_drawdown_percent': 0,
                'current_value': 0,
                'total_invested': 0,
                'days_tracked': 0
            }
        
        # Métriques de base
        first = snapshots[0]
        last = snapshots[-1]
        
        total_return = last.total_pnl
        total_return_percent = last.total_pnl_percent
        
        # Meilleur/pire jour
        best_day = max(snapshots, key=lambda s: s.daily_change_percent or 0)
        worst_day = min(snapshots, key=lambda s: s.daily_change_percent or 0)
        
        # Max Drawdown (plus grande perte depuis un pic)
        peak_value = 0
        max_drawdown = 0
        max_drawdown_percent = 0
        
        for s in snapshots:
            if s.total_value > peak_value:
                peak_value = s.total_value
            
            if peak_value > 0:
                drawdown = peak_value - s.total_value
                drawdown_percent = (drawdown / peak_value) * 100
                
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    max_drawdown_percent = drawdown_percent
        
        return {
            'total_return': total_return,
            'total_return_percent': total_return_percent,
            'best_day': {
                'date': best_day.date.strftime('%Y-%m-%d'),
                'change': best_day.daily_change,
                'change_percent': best_day.daily_change_percent
            } if best_day.daily_change_percent else None,
            'worst_day': {
                'date': worst_day.date.strftime('%Y-%m-%d'),
                'change': worst_day.daily_change,
                'change_percent': worst_day.daily_change_percent
            } if worst_day.daily_change_percent else None,
            'max_drawdown': max_drawdown,
            'max_drawdown_percent': max_drawdown_percent,
            'current_value': last.total_value,
            'total_invested': last.total_invested,
            'days_tracked': len(snapshots),
            'start_date': first.date.strftime('%Y-%m-%d'),
            'end_date': last.date.strftime('%Y-%m-%d')
        }
        
    finally:
        db.close()


def get_latest_snapshot() -> Optional[Dict[str, Any]]:
    """Récupère le dernier snapshot du portfolio"""
    db = get_db()
    try:
        snapshot = db.query(PortfolioSnapshot).order_by(
            PortfolioSnapshot.date.desc()
        ).first()
        
        return snapshot.to_dict() if snapshot else None
    finally:
        db.close()


def cleanup_old_snapshots(days: int = 365):
    """Supprime les snapshots plus anciens que X jours"""
    from datetime import timedelta
    
    db = get_db()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.date < cutoff_date
        ).delete()
        db.commit()
        print(f"🗑️ {deleted} anciens snapshots supprimés")
        return deleted
    except Exception as e:
        db.rollback()
        print(f"⚠️ Erreur cleanup snapshots: {e}")
        return 0
    finally:
        db.close()


def cleanup_old_summaries(days: int = 7):
    """Supprime les résumés plus anciens que X jours"""
    from datetime import timedelta
    
    db = get_db()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = db.query(NewsSummary).filter(
            NewsSummary.generated_at < cutoff_date
        ).delete()
        db.commit()
        print(f"🗑️ {deleted} anciens résumés supprimés")
        return deleted
    except Exception as e:
        db.rollback()
        print(f"⚠️ Erreur cleanup summaries: {e}")
        return 0
    finally:
        db.close()


def migrate_snapshots_add_global_pnl():
    """
    Migration: Calcule et ajoute global_pnl à tous les snapshots existants.
    Utilise les positions fermées pour calculer le P&L réalisé.
    """
    db = get_db()
    try:
        # Get all closed positions to calculate realized P&L
        closed_positions = db.query(Position).filter(
            Position.status.in_(['closed', 'stopped'])
        ).all()
        
        # Calculate total realized P&L from all closed positions (in USD)
        # We need to calculate this based on exit_date to know which snapshot it affects
        realized_pnl_by_date = {}
        cumulative_realized = 0
        
        # Sort closed positions by exit_date
        sorted_closed = sorted(
            [p for p in closed_positions if p.exit_date],
            key=lambda p: p.exit_date
        )
        
        # Calculate cumulative realized P&L
        for p in sorted_closed:
            entry_price = p.entry_price or 0
            exit_price = p.exit_price or entry_price
            quantity = p.quantity or 1
            commission = (p.buy_commission or 0) + (p.sell_commission or 0)
            
            # Simple P&L calculation (assuming USD or close to it for now)
            pnl = (exit_price - entry_price) * quantity - commission
            cumulative_realized += pnl
            
            # Store cumulative realized P&L at each exit date
            exit_date_str = p.exit_date.strftime('%Y-%m-%d') if p.exit_date else None
            if exit_date_str:
                realized_pnl_by_date[exit_date_str] = cumulative_realized
        
        # Get all snapshots ordered by date
        snapshots = db.query(PortfolioSnapshot).order_by(PortfolioSnapshot.date.asc()).all()
        
        print(f"🔄 Migration: Mise à jour de {len(snapshots)} snapshots avec global_pnl...")
        
        current_realized = 0
        updated_count = 0
        
        for snapshot in snapshots:
            snapshot_date_str = snapshot.date.strftime('%Y-%m-%d') if snapshot.date else None
            
            # Check if any position was closed on or before this date
            for date_str, realized in realized_pnl_by_date.items():
                if date_str <= snapshot_date_str:
                    current_realized = realized
            
            # Calculate global P&L
            total_pnl = snapshot.total_pnl or 0
            global_pnl = total_pnl + current_realized
            total_invested = snapshot.total_invested or 0
            
            # Calculate global P&L percent (based on total invested including closed)
            # For simplicity, use total_invested as base
            global_pnl_percent = (global_pnl / total_invested * 100) if total_invested > 0 else 0
            
            # Update snapshot
            snapshot.realized_pnl = current_realized
            snapshot.global_pnl = global_pnl
            snapshot.global_pnl_percent = global_pnl_percent
            snapshot.total_closed_count = len([p for p in sorted_closed if p.exit_date and p.exit_date.strftime('%Y-%m-%d') <= snapshot_date_str])
            
            updated_count += 1
        
        db.commit()
        print(f"✅ Migration terminée: {updated_count} snapshots mis à jour")
        print(f"   P&L réalisé total: {current_realized:.2f}")
        
        return updated_count
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur migration snapshots: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        db.close()


# ============================================
# PORTFOLIO ANALYSIS FUNCTIONS
# ============================================

def save_portfolio_analysis(analysis_data: Dict[str, Any], model: str, elapsed_time: float, positions_count: int, baseline_portfolio_value: float = 0, baseline_pnl_pct: float = 0) -> Optional[PortfolioAnalysis]:
    """
    Sauvegarde une analyse de portefeuille en DB.

    Args:
        analysis_data: Données JSON de l'analyse
        model: Modèle utilisé
        elapsed_time: Temps d'analyse
        positions_count: Nombre de positions analysées
        baseline_portfolio_value: Portfolio value at time of projection
        baseline_pnl_pct: P&L % at time of projection

    Returns:
        PortfolioAnalysis object or None
    """
    db = get_db()
    try:
        # Extraire les données du JSON
        resume = analysis_data.get('resume_global', {})
        actions = analysis_data.get('actions_du_jour', {})
        risques = analysis_data.get('risques_portfolio', {})
        allocation = analysis_data.get('allocation', {})

        portfolio_analysis = PortfolioAnalysis(
            date=datetime.now(),
            portfolio_state=resume.get('etat_portfolio', 'N/A'),
            portfolio_trend=resume.get('tendance', 'N/A'),
            health_score=resume.get('score_sante', 50),
            summary=resume.get('resume', resume.get('synthese', '')),  # Use 'resume' field, fallback to 'synthese'
            plan_action=analysis_data.get('plan_action', []),
            actions_high_priority=actions.get('priorite_haute', []),
            actions_watch=actions.get('a_surveiller', []),
            actions_opportunities=actions.get('opportunites', []),
            achats_recommandes=analysis_data.get('achats_recommandes', []),
            ventes_recommandees=analysis_data.get('ventes_recommandees', []),
            position_advice=analysis_data.get('conseils_positions', []),
            projections=analysis_data.get('projections', {}),
            baseline_portfolio_value=baseline_portfolio_value,
            baseline_pnl_pct=baseline_pnl_pct,
            allocation_comment=allocation.get('commentaire', ''),
            main_risk=risques.get('risque_principal', ''),
            conclusion=analysis_data.get('conclusion', ''),
            analysis_time=elapsed_time,
            model=model,
            positions_count=positions_count,
            raw_response=analysis_data
        )
        
        db.add(portfolio_analysis)
        db.commit()
        db.refresh(portfolio_analysis)
        
        print(f"💾 Analyse portefeuille sauvegardée (ID: {portfolio_analysis.id})")
        return portfolio_analysis
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur sauvegarde analyse portefeuille: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


def get_latest_portfolio_analysis() -> Optional[Dict[str, Any]]:
    """Récupère la dernière analyse de portefeuille."""
    db = get_db()
    try:
        analysis = db.query(PortfolioAnalysis).order_by(
            PortfolioAnalysis.date.desc()
        ).first()
        
        if analysis:
            return analysis.to_dict()
        return None
    finally:
        db.close()


def get_portfolio_analysis_by_date(date_str: str) -> Optional[Dict[str, Any]]:
    """Récupère l'analyse de portefeuille pour une date donnée."""
    db = get_db()
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        analysis = db.query(PortfolioAnalysis).filter(
            PortfolioAnalysis.date >= datetime.combine(target_date, datetime.min.time()),
            PortfolioAnalysis.date < datetime.combine(target_date, datetime.max.time())
        ).order_by(PortfolioAnalysis.date.desc()).first()
        
        if analysis:
            return analysis.to_dict()
        return None
    finally:
        db.close()


def get_portfolio_analyses_history(days: int = 30, limit: int = None) -> List[Dict[str, Any]]:
    """Récupère l'historique des analyses de portefeuille."""
    db = get_db()
    try:
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        
        query = db.query(PortfolioAnalysis).filter(
            PortfolioAnalysis.date >= cutoff
        ).order_by(PortfolioAnalysis.date.desc())
        
        if limit:
            query = query.limit(limit)
        
        analyses = query.all()
        
        return [a.to_dict() for a in analyses]
    finally:
        db.close()


# Initialiser la DB au chargement du module
init_db()
