import peewee
from datetime import datetime

from openspade.utility import TEMP_DIR

# 1. 定义数据库（这里使用 SQLite，也可换成 MySQL/PostgreSQL）
db = peewee.SqliteDatabase(TEMP_DIR.joinpath("database.db"))


# 2. 定义基础模型
class BaseModel(peewee.Model):
    class Meta:
        database = db


# 3. 定义用户表
class User(BaseModel):
    username = peewee.CharField(max_length=50, unique=True)
    email = peewee.CharField(max_length=100, unique=True)
    age = peewee.IntegerField(null=True)
    created_at = peewee.DateTimeField(default=datetime.now)

    def __str__(self):
        return f"<User: {self.username}>"


# 4. 定义文章表（外键关联 User）
class Article(BaseModel):
    title = peewee.CharField(max_length=200)
    content = peewee.TextField()
    user = peewee.ForeignKeyField(User, backref='articles')
    pub_date = peewee.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.title


# 5. 连接数据库并创建表
db.connect()
db.create_tables([User, Article])


def create_user(username, email, age=None):
    # 方式1:
    user = User.create(username=username, email=email, age=age)
    return user


# ---------- 测试运行 ----------
if __name__ == '__main__':
    # 插入数据
    user1 = create_user('alice3', 'alice@example2.com', 25)
    user2 = create_user('bob2', 'bob@example2.com', 30)

    # 插入文章
    Article.create(title='Peewee 入门', content='...', user=user1)
    Article.create(title='ORM 最佳实践', content='...', user=user1)


