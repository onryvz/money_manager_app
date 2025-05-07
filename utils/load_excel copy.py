import sys
import os
# Üst dizini modül yolu olarak ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from models import db, Account, Category, Transaction
from app import app
from datetime import datetime

# Excel dosyası yolu
EXCEL_FILE = os.path.join(os.path.dirname(__file__), '..', 'money-manager.xlsx')

with app.app_context():
    # Accounts sayfasını oku
    df_accounts = pd.read_excel(EXCEL_FILE, sheet_name='Accounts', header=0)
    for _, row in df_accounts.iterrows():
        name = row.get('Account List')
        if pd.isna(name):
            continue
        acc = Account(
            name=str(name).strip(),
            type='',
            balance=0.0
        )
        db.session.add(acc)
    db.session.commit()

    # Categories sayfasını oku
    df_categories = pd.read_excel(EXCEL_FILE, sheet_name='Categories', header=0)
    for _, row in df_categories.iterrows():
        cat_name = row.get('[Categories]')
        if pd.isna(cat_name) or isinstance(cat_name, str) and ('*****' in cat_name or '[' in cat_name):
            continue
        cat = Category(
            name=str(cat_name).strip(),
            type=''  # isterseniz gelir/gider ayrımı ekleyin
        )
        db.session.add(cat)
    db.session.commit()

    # Transactions sayfasını oku, header=3 ile doğru başlığı al
    df_trans = pd.read_excel(EXCEL_FILE, sheet_name='Transactions', header=3)
    for _, row in df_trans.iterrows():
        acct_name = row.get('Account')
        date = row.get('Date')
        category_name = row.get('Category')
        if pd.isna(acct_name) or pd.isna(date) or pd.isna(category_name):
            continue
        # Hesap ve kategori nesnelerini al
        acc = Account.query.filter_by(name=str(acct_name).strip()).first()
        cat = Category.query.filter_by(name=str(category_name).strip()).first()
        if not acc or not cat:
            continue
        # Tutarı belirle (PAYMENT negatif, DEPOSIT pozitif)
        payment = row.get('PAYMENT')
        deposit = row.get('DEPOSIT')
        if not pd.isna(deposit):
            amount = float(deposit)
        elif not pd.isna(payment):
            amount = -float(payment)
        else:
            amount = 0.0
        # Açıklama
        payee = row.get('Payee') or ''
        memo = row.get('Memo') or ''
        description = f"{payee} {memo}".strip()

        tr = Transaction(
            date=pd.to_datetime(date).date(),
            amount=amount,
            description=description,
            account_id=acc.id,
            category_id=cat.id
        )
        db.session.add(tr)
    db.session.commit()

    print("Excel verileri başarıyla içe aktarıldı.")
