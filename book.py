from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from register import login_required
from db import connect_db
import psycopg2

bp = Blueprint('book', __name__)


@bp.route('/book', methods=('GET', 'POST'))  
def index():  
    current_page = request.form.get('page',1)
    error = None
    if not current_page:
        current_page = 1
    else:
        current_page = int(current_page) 
    try:
        db = connect_db()
        cur = db.cursor()
        cur.execute(
            'SELECT * FROM book_list ORDER BY bid'
        )
        books = cur.fetchall()
        num_books = len(books)
    except (Exception,psycopg2.Error) as e:
        # Handle the error gracefully
        flash(e)    
    else:
        if current_page > num_books//2 + 1:
            current_page = 1
            error = '页数无效,跳转回第一页'
        if error is not None:
            flash(error)
        return render_template('booklist/index.html', posts=books, num_books=num_books, i=current_page)

@bp.route('/book/search/<string:type>:<string:search>', methods=('GET', 'POST'))
@login_required
def search(type, search):
    if g.user is None:
         return redirect(url_for('register.login'))
    current_page = request.form.get('page',1)
    error = None
    if not current_page:
        current_page = 1
    else:
        current_page = int(current_page) 
    db = connect_db()
    cur = db.cursor()
    books = []
    try:
        if g.is_admin:
            if type=="ID":
                cur.execute(
                    "SELECT * FROM book_list WHERE bid = %s ORDER BY bid",
                    (search,))
            elif type=="ISBN":
                cur.execute(
                    "SELECT * FROM book_list WHERE isbn = %s ORDER BY bid",
                    (search,))
            elif type=="书名":
                cur.execute(
                    "SELECT * FROM book_list WHERE bname like %s ORDER BY bid",
                    ('%'+search+'%',))
            elif type=="作者名":
                cur.execute(
                    "SELECT * FROM book_list WHERE auther like %s ORDER BY bid",
                    ('%'+search+'%',))
            elif type=="出版社":
                cur.execute(
                    "SELECT * FROM book_list WHERE press like %s ORDER BY bid",
                    ('%'+search+'%',))
        books = cur.fetchall()
        num_books = len(books)
    except:
        books = []
        num_books = 0
    if request.method == 'POST':
        type = request.form['type']
        search = request.form['search']
        if g.user is None:
            error = "请先登录"
        if current_page > num_books//10 + 1:
            current_page = 1
            error = '页数无效,跳转回第一页'
        if error is not None:
            flash(error)
        else:
            return redirect(url_for('book.search',type=type,search=search))
    return render_template('booklist/index.html', posts=books, type=type, search=search, num_books=num_books, i=current_page)

@bp.route('/book/create', methods=('GET', 'POST'))
@login_required
def create():
    if g.user is None:
        return redirect(url_for('register.login'))
    db = connect_db()
    cur = db.cursor()

    if g.is_admin==False:
        abort(403)
    book = request.args.get('book', default=1, type=int)
    if request.method == 'POST':
        if book ==0:
            bid = request.form['bid']
        else:
            isbn = request.form['isbn']
            bname = request.form['bname']
            author = request.form['author']
            publisher = request.form['press']
            outprice = request.form['outprice']
        inprice = request.form['inprice']
        amount = request.form['amount']
        error = None

        if not inprice:
            error = '请输入单价'
        elif not amount:
            error = '请输入数量'
        if error is not None:
            flash(error)
        else:
            db = connect_db()
            cur = db.cursor()
            # if bid:
            #     cur.execute(
            #         'SELECT bid FROM book_list WHERE bid = %s',
            #         (bid,)
            #     )
            #     if cur.fetchone():
            if book==0:
                    cur.execute(
                        'select insert_purchase_list(%s, %s, %s)',
                        ( bid, inprice, amount)
                    )
                    return render_template('booklist/create.html',book=0)
            cur.execute(
                'select insert_purchase_list(%s, %s, %s, %s, %s, %s, %s)',
                    (isbn, bname, author, publisher, inprice, outprice, amount)
                )
            db.commit()
            return redirect(url_for('book.purchase_list'))
    return render_template('booklist/create.html',book=book)

@bp.route('/book/purchase_list')
def purchase_list():
    if g.user is None:
        return redirect(url_for('register.login'))
    if g.is_admin==False:
        abort(403)
    super = g.is_super
    db = connect_db()
    cur = db.cursor()
    if g.is_admin:
        cur.execute(
            'SELECT * FROM purchase_list ORDER BY pid',
        )
    lists = cur.fetchall()
    return render_template('booklist/purchase_list.html', posts=lists)

@bp.route('/book/bill', methods=['GET', 'POST'])
def bill():
    if g.user is None:
        return redirect(url_for('register.login'))
    if g.is_admin==False:
        abort(403)
    if request.method == 'POST':
        db = connect_db()
        cur = db.cursor()
        error = None
        start_date = request.form.get('startDate')
        end_date = request.form.get('endDate')
        if not start_date:
            error = '请输入起始日期'
        elif not end_date:
            error = '请输入终止日期'
        elif start_date > end_date:
            error = '起始日期应该在终止日期之前'
        if error is None:
            cur.execute(
                'SELECT * FROM bill '
                ' WHERE time BETWEEN %s AND %s ORDER BY billid',
                (start_date, end_date)
            )
            bills = cur.fetchall()
            return render_template('booklist/bill.html', posts=bills)
        else:
            flash(error)
        return render_template('booklist/bill.html')
    db = connect_db()
    cur = db.cursor()
    cur.execute(
        'SELECT * FROM bill ORDER BY billid',
    )
    bills = cur.fetchall()
    return render_template('booklist/bill.html',posts=bills)
    
@bp.route('/book/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    if g.user is None:
        return redirect(url_for('register.login'))
    cur = connect_db().cursor()
    if g.is_admin==False:
        abort(403)
    cur.execute(
        'SELECT *'
        ' FROM book_list'
        ' WHERE bid = %s',
        (id,)
    )
    book = cur.fetchone()

    if request.method == 'POST':
        isbn = request.form['isbn']
        bname = request.form['bname']
        author = request.form['author']
        publisher = request.form['publisher']
        price = request.form['price']
        amount = request.form['amount']
        db = connect_db()
        cur = db.cursor()
        try:
            cur.execute(
                'UPDATE book_list SET isbn = %s, bname = %s, author = %s, press = %s, price = %s, amount = %s'
                ' WHERE bid = %s',
                (isbn, bname, author, publisher, price, amount, id)
            )
            db.commit()
            return redirect(url_for('book.update', id=book['bid']))
        except(Exception, psycopg2.Error) as error:
            flash(error)
    return render_template('booklist/update.html', book=book)
'''
@bp.route('/book/<int:id>/takeon')
@login_required
def takeon(id):
    if g.is_admin==False:
        abort(403)
    db = connect_db()
    cur = db.cursor()
    #cur.execute('UPDATE book_list SET available = true WHERE bid = %s', (id,))
    #db.commit()
    return redirect(url_for('book.index'))

@bp.route('/<int:id>/takedown')
@login_required
def takedown(id):
    if g.is_admin==False:
        abort(403)
    db = connect_db()
    cur = db.cursor()
    #cur.execute('UPDATE book SET available = false WHERE bid = %s', (id,))
    #db.commit()
    return redirect(url_for('book.index'))
'''
@bp.route('/book/purchase/<string:id>:<string:amount>', methods=('GET', 'POST'))
@login_required
def purchase(id,amount):
    if g.user is None:
        return redirect(url_for('register.login'))
    db = connect_db()
    cur = db.cursor()
    if g.is_admin == False:
        abort(403)
    
    if request.method == 'POST':
        amount = request.form['amount']
        error = None
        if not amount or int(amount) <=0:
            error = '请输入正确的购买量'
        cur.execute(
            'SELECT amount'
            ' FROM book_list WHERE bid = %s',
                (id,)
        )
        books = cur.fetchone() # 库存书籍数量
        number = books['amount'] 
        if number < int(amount):
            error = 'Not enough books.'

        if error is not None:
            flash(error)
        else:
            db = connect_db()
            cur = db.cursor()
            cur.execute(
                'SELECT sell_book(%s,%s)',
                (id,amount)
            )
        book = cur.fetchone()
        db.commit()
        return redirect(url_for('book.index',amount=amount))
    return redirect(url_for('book.index',amount=amount))

@bp.route('/book/paybill/<int:id>')
@login_required
def paybill(id):
    if g.user is None:
            return redirect(url_for('register.login'))
    db = connect_db()
    cur = db.cursor()
    if g.is_admin==False:
        abort(403)
    cur.execute(
        "UPDATE purchase_list SET state = 'paid' WHERE pid = %s",
        (id,)
    )
    db.commit() 
    return redirect(url_for('book.purchase_list'))

@bp.route('/book/refund/<int:id>')
@login_required
def refund(id):
    if g.user is None:
        return redirect(url_for('register.login'))
    db = connect_db()
    cur = db.cursor()
    if g.is_admin==False:
        abort(403)
    cur.execute("UPDATE purchase_list SET state = 'refund' WHERE pid = %s", (id,))
    flash("操作成功")
    db.commit()
    return redirect(url_for('book.purchase_list'))

@bp.route('/<int:id>/bookreach')
@login_required
def bookreach(id):
    if g.user is None:
        return redirect(url_for('register.login'))
    db = connect_db()
    cur = db.cursor()
    if g.is_admin==False:
        abort(403)
    cur.execute("UPDATE purchase_list SET state = 'reach' WHERE pid = %s", (id,))
    db.commit()
    return redirect(url_for('book.purchase_list'))
