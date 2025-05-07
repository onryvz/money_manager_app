# routes.py
from flask import Blueprint, render_template, request, redirect, url_for
from models import Account, Category, Transaction, db
from datetime import datetime

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return redirect(url_for('main.dashboard'))

@bp.route('/dashboard')
def dashboard():
    # Genel özet
    accounts = Account.query.all()
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    total_balance = sum(acc.balance for acc in accounts)
    # Gelir ve gider toplamları
    income = sum(tr.amount for tr in transactions if tr.amount > 0)
    expense = -sum(tr.amount for tr in transactions if tr.amount < 0)
    # Kategori bazlı dağılım
    cat_data = db.session.query(Category.name, db.func.sum(Transaction.amount)) \
        .join(Transaction).group_by(Category.id).all()
    labels = [c[0] for c in cat_data]
    data = [abs(c[1]) for c in cat_data]
    return render_template('dashboard.html', total_balance=total_balance,
                           income=income, expense=expense,
                           labels=labels, data=data)

@bp.route('/accounts')
def show_accounts():
    accounts = Account.query.all()
    total_balance = sum(acc.balance for acc in accounts)
    return render_template('accounts.html', accounts=accounts, total_balance=total_balance)

@bp.route('/transactions')
def show_transactions():
    account_id = request.args.get('account', type=int)
    category_id = request.args.get('category', type=int)
    start = request.args.get('start')
    end = request.args.get('end')

    query = Transaction.query
    if account_id:
        query = query.filter_by(account_id=account_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if start:
        query = query.filter(Transaction.date >= datetime.strptime(start, '%Y-%m-%d').date())
    if end:
        query = query.filter(Transaction.date <= datetime.strptime(end, '%Y-%m-%d').date())

    transactions = query.order_by(Transaction.date.desc()).all()
    accounts = Account.query.all()
    categories = Category.query.all()
    return render_template('transactions.html', transactions=transactions,
                           accounts=accounts, categories=categories,
                           filter={'account': account_id, 'category': category_id, 'start': start, 'end': end})

@bp.route('/transactions/add', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        account_id = int(request.form['account'])
        category_id = int(request.form['category'])
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        amount = float(request.form['amount'])
        description = request.form.get('description','')
        tr = Transaction(date=date, amount=amount, description=description,
                         account_id=account_id, category_id=category_id)
        db.session.add(tr)
        acc = Account.query.get(account_id)
        acc.balance += amount
        db.session.commit()
        return redirect(url_for('main.show_transactions'))
    accounts = Account.query.all()
    categories = Category.query.all()
    return render_template('add_transaction.html', accounts=accounts, categories=categories)

@bp.route('/transactions/<int:tr_id>/edit', methods=['GET', 'POST'])
def edit_transaction(tr_id):
    tr = Transaction.query.get_or_404(tr_id)
    if request.method == 'POST':
        old_amount = tr.amount
        tr.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        tr.amount = float(request.form['amount'])
        tr.description = request.form.get('description','')
        new_account_id = int(request.form['account'])
        if tr.account_id != new_account_id:
            old_acc = Account.query.get(tr.account_id)
            old_acc.balance -= old_amount
            new_acc = Account.query.get(new_account_id)
            new_acc.balance += tr.amount
            tr.account_id = new_account_id
        else:
            acc = Account.query.get(tr.account_id)
            acc.balance += tr.amount - old_amount
        tr.category_id = int(request.form['category'])
        db.session.commit()
        return redirect(url_for('main.show_transactions'))
    accounts = Account.query.all()
    categories = Category.query.all()
    return render_template('edit_transaction.html', tr=tr, accounts=accounts, categories=categories)

@bp.route('/transactions/<int:tr_id>/delete', methods=['POST'])
def delete_transaction(tr_id):
    tr = Transaction.query.get_or_404(tr_id)
    acc = Account.query.get(tr.account_id)
    acc.balance -= tr.amount
    db.session.delete(tr)
    db.session.commit()
    return redirect(url_for('main.show_transactions'))