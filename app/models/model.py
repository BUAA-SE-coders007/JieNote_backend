from sqlalchemy import Column, Integer, String, Boolean, Table, ForeignKey, UniqueConstraint, CheckConstraint, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# 多对多关系表
user_group = Table(
    'user_group', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    Column('is_admin', Boolean, default=False)
)

enter_application = Table(
    'enter_application', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
)

self_recycle_bin = Table(
    'self_recycle_bin', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('type', Integer, primary_key=True),      # 1: folder 2: article 3: note
    Column('id', Integer, primary_key=True),
    Column('name', Text, nullable=False),           # 回收站显示
    Column('create_time', DateTime, default=func.now(), nullable=False),    # 加入回收站的时间
    Column('article_id', Integer, ForeignKey('articles.id', ondelete="CASCADE")),               
    Column('folder_id', Integer, ForeignKey('folders.id', ondelete="CASCADE"))
    # 最后两列为有上级时的上级节点信息，用于恢复时检查是否有上级节点在回收站中，和彻底删除时的级联删除
)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(30), unique=True, index=True, nullable=False)
    username = Column(String(30), index=True, nullable=False)
    password = Column(String(60), nullable=False)
    avatar = Column(String(100))
    address = Column(String(100))
    university = Column(String(100))
    introduction = Column(Text)
    create_time = Column(DateTime, default=func.now(), nullable=False)  # 创建时间
    groups = relationship('Group', secondary=user_group, back_populates='users')
    folders = relationship('Folder', back_populates='user')

class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    leader = Column(Integer)
    name = Column(String(30), nullable=False)
    description = Column(String(200), nullable=False)
    create_time = Column(DateTime, default=func.now(), nullable=False)  # 创建时间
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)  # 更新时间
    users = relationship('User', secondary=user_group, back_populates='groups')
    folders = relationship('Folder', back_populates='group')

class Folder(Base):
    __tablename__ = 'folders'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(30), nullable=False)
    
    user_id = Column(Integer, ForeignKey('users.id'))
    group_id = Column(Integer, ForeignKey('groups.id'))

    create_time = Column(DateTime, default=func.now(), nullable=False)  # 创建时间
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)  # 更新时间
    
    visible = Column(Boolean, default=True, nullable=False) # 是否可见 False表示在回收站中
    
    # 关系定义
    user = relationship('User', back_populates='folders')
    group = relationship('Group', back_populates='folders')
    articles = relationship('Article', back_populates='folder', cascade="all, delete-orphan")

    __table_args__ = (
        # 不能同时为空
        UniqueConstraint('user_id', 'group_id', name='uq_user_group_folder'), # SQL中认为null 和 null 不相等
        CheckConstraint('user_id IS NOT NULL OR group_id IS NOT NULL', name='check_user_or_group'),
    )    

class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(Text, nullable=False)
    folder_id = Column(Integer, ForeignKey('folders.id', ondelete="CASCADE"))
    create_time = Column(DateTime, default=func.now(), nullable=False)  # 创建时间
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)  # 更新时间

    visible = Column(Boolean, default=True, nullable=False) # 是否可见 False表示在回收站中
    
    folder = relationship('Folder', back_populates='articles', lazy='selectin')
    notes = relationship('Note', back_populates='article', cascade="all, delete-orphan")
    tags = relationship('Tag', back_populates='article')

class Note(Base):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    content = Column(Text)  # 将 content 字段类型改为 Text，以支持存储大量文本
    article_id = Column(Integer, ForeignKey('articles.id', ondelete="CASCADE"))
    create_time = Column(DateTime, default=func.now(), nullable=False)  # 创建时间
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)  # 更新时间
    creator_id = Column(Integer, ForeignKey('users.id'))  # 创建者ID
    visible = Column(Boolean, default=True, nullable=False) # 是否可见 False表示在回收站中

    article = relationship('Article', back_populates='notes')

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(String(30))
    article_id = Column(Integer, ForeignKey('articles.id'))
    create_time = Column(DateTime, default=func.now(), nullable=False)  # 创建时间
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)  # 更新时间
    article = relationship('Article', back_populates='tags')

class ArticleDB(Base):
    __tablename__ = 'articleDB'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    title = Column(String(200), nullable=False)
    url = Column(String(200), nullable=False)
    author = Column(String(300), nullable=False)
    file_path = Column(String(200), nullable=False)
    
    create_time = Column(DateTime, default=func.now(), nullable=False)  # 创建时间
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)  # 更新时间