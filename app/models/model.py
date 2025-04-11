from sqlalchemy import Column, Integer, String, Boolean, Table, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base_class import Base

# 多对多关系表
user_group = Table(
    'user_group', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    Column('is_admin', Boolean, default=False)  # 是否是管理员
)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(30), index=True, nullable=False, unique=True)
    username = Column(String(30), index=True, nullable=False)
    hash_password = Column(String(60), nullable=False)
    avatar = Column(String(100), nullable=True)  # 头像的url
    groups = relationship('Group', secondary=user_group, back_populates='users')

class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    leader = Column(Integer)    # the id of the leader
    users = relationship('User', secondary=user_group, back_populates='groups')

class Folder(Base): # 文件夹
    __tablename__ = 'folders'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(30))
    user_id = Column(Integer, ForeignKey('users.id'))
    group_id = Column(Integer, ForeignKey('groups.id'))
    user = relationship('User', back_populates='folders')
    group = relationship('Group', back_populates='folders')

    __table_args__ = (
        UniqueConstraint('user_id', 'group_id', name='uq_user_group_folder'),
    )

class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(30))
    folder_id = Column(Integer, ForeignKey('folders.id'))
    folder = relationship('Folder', back_populates='articles')

class Note(Base):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(30))
    article_id = Column(Integer, ForeignKey('articles.id'))
    article = relationship('Article', back_populates='notes')

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(String(30))
    article_id = Column(Integer, ForeignKey('articles.id'))
    article = relationship('Article', back_populates='tags')

# 添加反向关系
User.folders = relationship('Folder', back_populates='users')
Group.folders = relationship('Folder', back_populates='groups')
Folder.articles = relationship('Article', back_populates='folders')
Article.notes = relationship('Note', back_populates='articles')
Article.tags = relationship('Tag', back_populates='articles')


