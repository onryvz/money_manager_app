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
    # --- ACCOUNTS ---
    # Gerçek tablo başlığı 6. satırda (0-index header=6)
    df_accounts = pd.read_excel(EXCEL_FILE, sheet_name='Accounts', header=6)
    # Sütun isimlerini temizle
    df_accounts.rename(columns=lambda x: str(x).strip(), inplace=True)
    name_col = df_accounts.columns[0]  # genellikle 'ACCOUNTS'
    balance_col = 'Balance' if 'Balance' in df_accounts.columns else df_accounts.columns[-1]
    for _, row in df_accounts.iterrows():
        acct_name = row.get(name_col)
        if pd.isna(acct_name) or str(acct_name).upper().startswith('TOTAL'):
            continue
        balance = row.get(balance_col, 0.0) or 0.0
        acc = Account(
            name=str(acct_name).strip(),
            type='',  # isteğe bağlı
            balance=float(balance)
        )
        db.session.add(acc)
    db.session.commit()

    # --- CATEGORIES ---
    raw_cat = pd.read_excel(EXCEL_FILE, sheet_name='Categories', header=None)
    current_section = None
    for _, row in raw_cat.iterrows():
        cell = row[0]
        if pd.isna(cell):
            continue
        text = str(cell).strip()
        # Bölüm başlığı mı?
        if text.startswith('*****') and text.endswith('*****'):
            # ***** INCOME ***** → Income
            current_section = text.strip('* ').title()
            continue
        # Köşeli parantezli satırları atla
        if text.startswith('[') and text.endswith(']'):
            continue
        # Normal kategori
        cat = Category(
            name=text,
            type=current_section or ''
        )
        db.session.add(cat)
    db.session.commit()

    # --- TRANSACTIONS ---
    # Gerçek başlık 3. satırda
    df_trans = pd.read_excel(EXCEL_FILE, sheet_name='Transactions', header=3)
    df_trans.rename(columns=lambda x: str(x).strip(), inplace=True)
    for _, row in df_trans.iterrows():
        acct_name = row.get('Account')
        date = row.get('Date')
        category_name = row.get('Category')
        if pd.isna(acct_name) or pd.isna(date) or pd.isna(category_name):
            continue
        acc = Account.query.filter_by(name=str(acct_name).strip()).first()
        cat = Category.query.filter_by(name=str(category_name).strip()).first()
        if not acc or not cat:
            continue
        # PAYMENT ve DEPOSIT ile tutar
        pay = row.get('PAYMENT')
        dep = row.get('DEPOSIT')
        if not pd.isna(dep):
            amount = float(dep)
        elif not pd.isna(pay):
            amount = -float(pay)
        else:
            amount = 0.0
        # Açıklama
        desc = ' '.join(filter(None, [str(row.get('Payee') or '').strip(), str(row.get('Memo') or '').strip()]))
        tr = Transaction(
            date=pd.to_datetime(date).date(),
            amount=amount,
            description=desc,
            account_id=acc.id,
            category_id=cat.id
        )
        db.session.add(tr)
    db.session.commit()

    print("Excel verileri help sayfası kurallarına göre başarıyla içe aktarıldı.")
