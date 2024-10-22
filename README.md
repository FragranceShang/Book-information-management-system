本项目依赖Flask, psycopg2库
pip install psycopg2
pip install Flask

安装完成后终端打开bookstore
输入以下指令部署（windows）
set FLASK_APP=app
set FLASK_ENV=development
set FLASK_DEBUG=1
set FLASK_LOGGING_LEVEL=DEBUG
flask init-db
flask run

部署成功后打开网页http://127.0.0.1:5000/即可使用

文件说明
——bookstore
————static 存放css文件
————templates 存放html文件
————app.py 主函数
————register.py 登录、注册、查看/更改个人信息等功能
————book.py 图书搜索、更改图书信息、进货、付款、查看账单等功能
————db.py 数据库连接
————readme.md 网页部署操作介绍
————schema.sql 初始化数据库的sql语句
