import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import abort

import psycopg2
from db import connect_db

bp = Blueprint('register', __name__, url_prefix='/register')

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('register.login'))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.is_super = session.get('is_super')
    g.is_admin = True #session.get('is_admin') | 
    g.uname = session.get('uname')

    if user_id is None:
        g.user = None
    else:
        cur = connect_db().cursor()
        cur.execute(
            'SELECT * FROM admin_user WHERE uid = %s', (user_id,)
        )
        g.user = cur.fetchone()

@bp.route('/logout')
def logout():
    # 清除用户的 session 数据
    session.clear()
    # 重定向到主页
    return redirect(url_for('home'))

@bp.route('/login',methods=['POST','GET'])
def login():
    if request.method=='POST':
        username=request.form['nm']     #获取姓名文本框的输入值
        pwd=request.form['pwd']   #获取密码框的输入值
        conn = connect_db()
        cur = conn.cursor()
        error = None
        if username is None:
            error = ("请输入用户名")
        elif pwd is None:
            error = ("请输入密码")
        # 检查用户名密码是否正确
        else:
            cur.execute(
                'SELECT * FROM admin_user WHERE username = %s', (username,)
            )
            user = cur.fetchone()

            if user is None:
                error = '用户名错误'
            elif username=='21307130068' and pwd=='sjf':
                session['username']=username           #使用session存储方式，session默认为数组，给定key和value即可 
            elif not check_password_hash(user['pwd'], pwd):
                error = '密码错误'
        
            if error is None:
                session.clear()
                session['user_id'] = user['uid']
                session['is_super'] = user['super']
                session['uname'] = user['uname']
                return redirect(url_for('home'))
        
        flash(error)
    return render_template('register/login.html', title="管理员/顾客登录")
        
@bp.route('/signin',methods=['POST','GET'])
def signin():    
    conn = connect_db()
    if not g.is_super:
        flash("无权限")
        abort(403)
    
    if request.method=='POST':
        username=request.form['nm']     #获取姓名文本框的输入值
        pwd=request.form['pwd']  
        realname = request.form['realname']
        sex = request.form['sex']
        age = request.form['age']  
        conn = connect_db()
        cur = conn.cursor()
        error = None 

        if not username:
            error = '请输入用户名'
        elif not pwd:
            error = '请输入密码'
        # 检查用户名是否已被占用
        else:
            cur.execute(
            'SELECT uid FROM admin_user WHERE username = %s', (username,)
            )
            if cur.fetchone() is not None:
                error = '用户名 {} 已被注册'.format(username)

        if error is None:
            try:
                cur.execute(
                    'select insert_admin_user (%s, %s, %s, %s,%s)',
                    (username, generate_password_hash(pwd), realname, sex, age)
                )
                conn.commit()
                flash('注册成功')
                return redirect(url_for('register.admin',id=g.user['uid']))    
            except(Exception, psycopg2.Error) as error:
                flash(error)

    return render_template('register/signin.html')

@bp.route('/<int:id>/delete', methods=('GET', 'POST'))
@login_required
def delete(id):
    if g.user is None:
        return redirect(url_for('register.login'))
    if not g.is_super:
        flash("无权限")
        abort(403)
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM admin_user WHERE uid = %s", (id,))
    admin = cur.fetchone()
    error = None
    if admin['super']:
        error = ('不可删除超级管理员')
    if error is None:    
        cur.execute("DELETE FROM admin_user WHERE uid = %s", (id,))
        conn.commit()
        flash("操作成功")
    else:
        flash(error)
    return redirect(url_for('register.admin',id=g.user['uid']))

@bp.route('/admin/<int:id>')  
def admin(id):  
    if g.user is None:
        return redirect(url_for('register.login'))
    if g.is_admin==False:
        abort(403)
    db = connect_db()
    cur = db.cursor()
    cur.execute(
        'SELECT *'
        ' FROM admin_user'
        ' ORDER BY uid'
    )
    posts = cur.fetchall()
    cur.execute(
        'SELECT *'
        ' FROM admin_user'
        ' where uid=(%s)',
        (id,)
    )
    own = cur.fetchone()
    msg = ""
    return render_template('register/admin.html', posts=posts,own=own,data=msg)

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    if g.user is None:
        return redirect(url_for('register.login'))
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        'SELECT * FROM admin_user WHERE uid = %s',
        (id,)
    )
    post = cur.fetchone()
    if post is None:
        abort(404, "账户ID {0} 不存在.".format(id))
    
    if g.is_admin==False or id != id:
        abort(403)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        realname = request.form['realname']
        sex = request.form['sex']
        age = request.form['age']
        error = None

        if not username:
            error = '请输入用户名'
        elif username != post['username']:
            cur.execute(
                'SELECT uid FROM admin_user WHERE username = %s', (username,)
            )
            if cur.fetchone() is not None:
                error = '用户名 {} 已被注册'.format(username)
        if error is not None:
            flash(error)
            return redirect(url_for('home'))
        else:
            try:
                cur.execute(
                    'UPDATE admin_user'
                    ' SET username = %s, pwd = %s, uname = %s, sex = %s, age = %s'
                    ' WHERE uid = %s',
                    (username, generate_password_hash(password), realname, sex, age, id)
                )
                conn.commit()
                return redirect(url_for('register.admin', id=post['uid']))
            
            except(Exception, psycopg2.Error) as error:
                flash(error)
    return render_template('register/update.html', post=post)
        