from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models import Account, Category, Transaction, db
from datetime import datetime, date
from sqlalchemy import func

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return redirect(url_for('main.show_transactions'))

@bp.route('/transactions')
def show_transactions():
    # Başlangıç query
    query = Transaction.query

    # Filtre parametreleri
    account_id = request.args.get('account', type=int)
    category_id = request.args.get('category', type=int)
    start = request.args.get('start')
    end = request.args.get('end')

    # Filtre uygulama
    if account_id:
        query = query.filter_by(account_id=account_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if start:
        query = query.filter(Transaction.date >= datetime.strptime(start, '%Y-%m-%d').date())
    if end:
        query = query.filter(Transaction.date <= datetime.strptime(end, '%Y-%m-%d').date())

    # Sonuçları tarih desc. olarak al
    transactions = query.order_by(Transaction.date.desc()).all()

    # Filtre formu için hesap ve kategori listesi
    accounts = Account.query.all()
    categories = Category.query.all()

    return render_template(
        'transactions.html',
        transactions=transactions,
        accounts=accounts,
        categories=categories,
        filter={
            'account': account_id,
            'category': category_id,
            'start': start,
            'end': end
        },
        current_date=date.today().isoformat()
    )

@bp.route('/transactions/create', methods=['POST'])
def create_transaction():
    data = request.get_json()
    # Verileri al
    dt = datetime.strptime(data['date'], '%Y-%m-%d').date()
    acct_id = int(data['account'])
    cat_id = int(data['category'])
    amt = float(data['amount'])
    desc = data.get('description', '')

    # Yeni işlem oluştur
    tr = Transaction(date=dt, amount=amt, description=desc,
                     account_id=acct_id, category_id=cat_id)
    db.session.add(tr)

    # Hesap bakiyesini güncelle
    acc = Account.query.get(acct_id)
    acc.balance += amt

    db.session.commit()
    return jsonify(success=True, id=tr.id)

@bp.route('/transactions/<int:tr_id>/update_field', methods=['POST'])
def update_transaction_field(tr_id):
    data = request.get_json()
    field = data.get('field')
    value = data.get('value')
    tr = Transaction.query.get_or_404(tr_id)

    # Eski tutarı sakla (bakiye düzeltme için)
    old_amount = tr.amount

    # Alan güncelleme
    if field == 'amount':
        tr.amount = float(value)
    elif field == 'description':
        tr.description = value
    elif field == 'date':
        tr.date = datetime.strptime(value, '%Y-%m-%d').date()
    elif field == 'account':
        tr.account_id = int(value)
    elif field == 'category':
        tr.category_id = int(value)

    db.session.commit()

    # Tutar değiştiyse hesap bakiyesini düzelt
    if field == 'amount':
        acc = Account.query.get(tr.account_id)
        acc.balance += (tr.amount - old_amount)
        db.session.commit()

    return jsonify(success=True)

@bp.route('/transactions/<int:tr_id>/delete', methods=['POST'])
def delete_transaction(tr_id):
    tr = Transaction.query.get_or_404(tr_id)
    # Silmeden önce bakiyeyi geri al
    acc = Account.query.get(tr.account_id)
    acc.balance -= tr.amount

    db.session.delete(tr)
    db.session.commit()
    return redirect(url_for('main.show_transactions'))

@bp.route('/accounts')
def show_accounts():
    accounts = Account.query.all()
    return render_template('accounts.html', accounts=accounts)

@bp.route('/transactions/add', methods=['GET', 'POST'])
def add_transaction():
    # Artık inline ekleme olduğu için opsiyonel
    if request.method == 'POST':
        account_id = request.form.get('account')
        category_id = request.form.get('category')
        date_ = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        tr = Transaction(date=date_, amount=amount, description=description,
                         account_id=account_id, category_id=category_id)
        db.session.add(tr)
        acc = Account.query.get(account_id)
        acc.balance += amount
        db.session.commit()
        return redirect(url_for('main.show_transactions'))

    accounts = Account.query.all()
    categories = Category.query.all()
    return render_template('add_transaction.html', accounts=accounts, categories=categories)

@bp.route('/transactions/suggest')
def suggest_transactions():
    q = request.args.get('q','').strip()
    if len(q) < 2:
        return jsonify([])
    matches = (Transaction.query
               .filter(Transaction.description.ilike(f"%{q}%"))
               .order_by(Transaction.date.desc())
               .limit(10)
               .all())
    result = []
    for tr in matches:
        result.append({
            'id': tr.id,
            'description': tr.description,
            'account_id': tr.account_id,
            'category_id': tr.category_id,
            'amount': tr.amount
        })
    return jsonify(result)

@bp.route('/dashboard')
def dashboard():
    # toplam bakiye, gelir, gider hesapla
    income = db.session.query(func.sum(Transaction.amount))\
               .filter(Transaction.amount >= 0).scalar() or 0
    expense = abs(db.session.query(func.sum(Transaction.amount))\
               .filter(Transaction.amount < 0).scalar() or 0)
    balance = income - expense

    # kategori dağılımı
    data = (db.session.query(Category.name, func.sum(Transaction.amount).label('total'))
            .join(Transaction)
            .group_by(Category.id)
            .all())
    labels = [row[0] for row in data]
    values = [abs(row[1]) for row in data]

    return render_template(
      'dashboard.html',
      income=income,
      expense=expense,
      balance=balance,
      chart_labels=labels,
      chart_values=values
    )