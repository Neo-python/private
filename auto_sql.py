class AppDatabaseInit:
    """应用数据库初始化"""

    def __init__(self, app_name: str):
        self.app_name = app_name
        self.db = self.connect()

    def connect(self):
        """创建数据库连接"""
        db = connect(host=config.mysql_host, user=config.mysql_account, password=config.mysql_password,
                     charset=config.mysql_charset, cursorclass=cursors.DictCursor)
        return db

    def create_database(self) -> bool:
        """创建数据库"""
        with self.db.cursor() as cursor:
            try:
                cursor.execute(f'create database {self.app_name}')
                self.db.commit()
            except BaseException as err:
                print(err)
                return True
        return False

    def init_tables(self):
        """初始化表结构"""
        with self.db.cursor() as cursor:
            try:
                cursor.execute(f'show databases;')
                cursor.execute(f'use {self.app_name}')
                for sql in self.format_sql():
                    cursor.execute(f'{sql};')
            except BaseException as err:
                raise err

    def format_sql(self) -> list:
        """格式化sql文件
        替换 \n 回车 为空格
        删除sql注释
        删除语句前空格
        :return: [sql1, sql2, sql3]
        """
        with open('init.sql', mode='r', encoding='utf-8') as file:
            sql = file.read()
            sql = sql.replace('\n', ' ')
            sql = re.sub('\/\*(.*?)\*\/', '', sql)
            sql = sql.split(';')
            return [i for i in sql if i.strip()]

    def run(self):
        self.create_database()
        self.init_tables()


if __name__ == '__main__':
    AppDatabaseInit('app_name').run()