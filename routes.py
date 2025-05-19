from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models import Account, Category, Transaction, db
from datetime import datetime, date
from sqlalchemy import func

bp = Blueprint('main', __name__)

# En üstte, diğer importlardan sonra global değişkeni tanımlayalım
lastAction = None

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

    # Sonuçları tarih ve id desc. olarak al
    transactions = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()

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

@bp.route('/transactions/<int:tr_id>/update_field', methods=['POST'])
def update_transaction_field(tr_id):
    global lastAction
    data = request.get_json()
    field = data.get('field')
    value = data.get('value')
    
    if value is None:
        return jsonify(success=False, error="Value cannot be None")
        
    tr = Transaction.query.get_or_404(tr_id)

    # Değişiklik öncesi tüm değerleri sakla
    old_data = {
        'date': tr.date.isoformat(),
        'amount': float(tr.amount),
        'description': tr.description,
        'account': tr.account_id,
        'category': tr.category_id
    }

    try:
        # Alan güncelleme
        if field == 'amount':
            old_amount = tr.amount
            tr.amount = float(value)
            acc = Account.query.get(tr.account_id)
            acc.balance = acc.balance - old_amount + float(value)
        elif field == 'account':
            old_account_id = tr.account_id
            new_account_id = int(value)
            if new_account_id != old_account_id:
                old_acc = Account.query.get(old_account_id)
                new_acc = Account.query.get(new_account_id)
                old_acc.balance -= tr.amount
                new_acc.balance += tr.amount
                tr.account_id = new_account_id
        elif field == 'category':
            tr.category_id = int(value)
        elif field == 'description':
            tr.description = value
        elif field == 'date':
            tr.date = datetime.strptime(value, '%Y-%m-%d').date()

        # Son işlemi sakla
        lastAction = {
            'type': 'update',
            'id': tr_id,
            'old_data': old_data
        }

        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e))

@bp.route('/transactions/<int:tr_id>/delete', methods=['POST'])
def delete_transaction(tr_id):
    global lastAction
    tr = Transaction.query.get_or_404(tr_id)
    
    # Son işlemi sakla
    lastAction = {
        'type': 'delete',
        'data': {
            'date': tr.date.isoformat(),
            'amount': tr.amount,
            'description': tr.description,
            'account': tr.account_id,
            'category': tr.category_id
        }
    }
    
    # Hesap bakiyesini güncelle
    acc = Account.query.get(tr.account_id)
    acc.balance -= tr.amount
    
    db.session.delete(tr)
    db.session.commit()
    return jsonify(success=True)

@bp.route('/transactions/create', methods=['POST'])
def create_transaction():
    global lastAction
    data = request.get_json()

    # Geri alma işlemi kontrolü
    if data.get('type') == 'update':
        try:
            tr = Transaction.query.get(int(data['id']))
            if not tr:
                return jsonify(success=False, error="Transaction not found")

            old_data = data['oldData']
            
            # Önce hesap bakiyelerini güncelle
            if tr.account_id != int(old_data['account']):
                current_acc = Account.query.get(tr.account_id)
                target_acc = Account.query.get(int(old_data['account']))
                
                if current_acc:
                    current_acc.balance -= tr.amount
                if target_acc:
                    target_acc.balance += float(old_data['amount'])
            
            elif tr.amount != float(old_data['amount']):
                acc = Account.query.get(tr.account_id)
                if acc:
                    acc.balance = acc.balance - tr.amount + float(old_data['amount'])

            # Tüm alanları eski değerlerine döndür
            tr.date = datetime.strptime(old_data['date'], '%Y-%m-%d').date()
            tr.amount = float(old_data['amount'])
            tr.description = old_data['description']
            tr.account_id = int(old_data['account'])
            tr.category_id = int(old_data['category'])

            db.session.commit()
            lastAction = None
            return jsonify(success=True)

        except Exception as e:
            db.session.rollback()
            print(f"Hata: {str(e)}")  # Debug için
            return jsonify(success=False, error=str(e))

    # Normal işlem oluşturma
    try:
        tr = Transaction(
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            amount=float(data['amount']),
            description=data.get('description', ''),
            account_id=int(data['account']),
            category_id=int(data['category'])
        )
        db.session.add(tr)
        
        # Hesap bakiyesini güncelle
        acc = Account.query.get(tr.account_id)
        if acc:
            acc.balance += tr.amount
        
        db.session.commit()
        
        # Yeni işlem için lastAction'ı güncelle
        lastAction = {
            'type': 'create',
            'id': tr.id,
            'data': {
                'date': tr.date.isoformat(),
                'amount': tr.amount,
                'description': tr.description,
                'account': tr.account_id,
                'category': tr.category_id
            }
        }
        
        return jsonify(success=True, id=tr.id)
        
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e))

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