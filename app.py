from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from flask_alembic import Alembic
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "super_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
db = SQLAlchemy(app)




class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String)
    parameters = db.Column(db.String)


class Storage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String)
    product_price = db.Column(db.Integer)
    product_quantity = db.Column(db.Integer)


class AccountBalance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Integer)


with app.app_context():
    db.create_all()


def save_to_history(action_name, action_parameters):

    save_record = History(
        action=action_name,
        parameters=str(action_parameters)
    )

    db.session.add(save_record)
    db.session.commit()

def openFlashModal(message, message_type):
    flash_message = message
    flash_type = message_type
    return render_template("flash_modal.html", flash_message=flash_message, flash_type=flash_type)

@app.route("/", methods=["GET", "POST"])
def index():

    #Wyświetlenie aktualnego stanu konta oraz stanu magazynowego
    account_balance = AccountBalance.query.get(1)
    balance = account_balance.balance
    storage = Storage.query.all()

    form = request.form
    if form:
        if form["submit_button"] == "buy_submit":
            product_name = form["product_name_buy"]
            product_price = form["product_price_buy"]
            product_quantity = form["product_quantity_buy"]

            if product_name != "":
                if int(product_price) and int(product_quantity):
                    if int(product_price) > 0:
                        if int(product_quantity) > 0:

                            if int(balance):
                                if int(balance) >= (int(product_price) * int(product_quantity)):
                                    balance -= (int(product_price) * int(product_quantity))

                                    account_balance.balance = balance
                                    db.session.add(account_balance)
                                    db.session.commit()

                                    search_for_item = Storage.query.filter(Storage.product_name == product_name).first()

                                    if search_for_item:

                                        # Zmiana ilości produktu istniejącego w magazynie
                                        search_for_item.product_quantity += int(product_quantity)
                                        db.session.add(search_for_item)
                                        db.session.commit()

                                        storage = Storage.query.all()

                                        par_action = "buy"
                                        par_list = [product_name, product_price, product_quantity]

                                        # zapis do historii operacji zakupu
                                        save_to_history(par_action, par_list)

                                    else:
                                        # Dodanie nowego produktu do magazynu
                                        buy_product = Storage(
                                            product_name=product_name,
                                            product_price=product_price,
                                            product_quantity=product_quantity
                                        )

                                        db.session.add(buy_product)
                                        db.session.commit()

                                        storage = Storage.query.all()

                                        par_action = "buy"
                                        par_list = [product_name, product_price, product_quantity]

                                        # zapis do historii operacji zakupu
                                        save_to_history(par_action, par_list)

                                        return openFlashModal("Zakupiono produkt.", "info")
                                else:
                                    return openFlashModal("Nie ma wystarczających środków na koncie na zakup produktu!", "error")
                        else:
                            return openFlashModal("Ilość powinna być większa od zera! Żadne zmiany nie zostaną zapisane!", "error")
                    else:
                        return openFlashModal("Cena powinna być większa od zera! Żadne zmiany nie zostaną zapisane!", "error")
                else:
                    return openFlashModal("Wprowadzona cena / liczba sztuk musi być liczbą całkowitą!", "error")
            else:
                return openFlashModal("Nie wprowadzono nazwy produktu!", "error")

        if form["submit_button"] == "sell_submit":
            product_name = form["product_name_sell"]
            product_price = form["product_price_sell"]
            product_quantity = form["product_quantity_sell"]

            if product_name != "":
                if int(product_price) and int(product_quantity):
                    if int(product_price) > 0:
                        if int(product_quantity) > 0:

                            search_for_item = Storage.query.filter(Storage.product_name == product_name).first()

                            if search_for_item:
                                if search_for_item.product_quantity >= int(product_quantity):

                                    balance += (int(product_price) * int(product_quantity))
                                    account_balance.balance = balance
                                    db.session.add(account_balance)
                                    db.session.commit()

                                    # Zmiana ilości produktu istniejącego w magazynie
                                    search_for_item.product_quantity -= int(product_quantity)
                                    db.session.add(search_for_item)
                                    db.session.commit()

                                    storage = Storage.query.all()

                                    par_action = "sell"
                                    par_list = [product_name, product_price, product_quantity]

                                    # zapis do historii operacji sprzedaży
                                    save_to_history(par_action, par_list)

                                    return openFlashModal("Sprzedano produkt.", "info")
                                else:
                                    return openFlashModal(f"Brak wystarczającej ilości produktu w magazynie!", "error")
                            else:
                                return openFlashModal("Brak produktu w magazynie!", "error")
                        else:
                            return openFlashModal("Ilość powinna być większa od zera! Żadne zmiany nie zostaną zapisane!", "error")
                    else:
                        return openFlashModal("Cena powinna być większa od zera! Żadne zmiany nie zostaną zapisane!", "error")
                else:
                    return openFlashModal("Wprowadzona cena / liczba sztuk musi być liczbą całkowitą!", "error")
            else:
                return openFlashModal("Nie wprowadzono nazwy produktu!", "error")

        if form["submit_button"] == "balance_submit":
            comment_balance = form["comment_balance_change"]
            balance_change = form["balance_change"]

            if comment_balance != "":
                if int(balance_change):
                    balance += int(balance_change)
                    account_balance.balance = balance
                    db.session.add(account_balance)
                    db.session.commit()

                    par_action = "saldo"
                    par_list = [balance_change, comment_balance]

                    # zapis do historii operacji zmiany salda
                    save_to_history(par_action, par_list)

                    return openFlashModal("Zapisano zmianę salda.", "info")

    return render_template("index.html", balance=balance, storage=storage)


@app.route("/history", methods=["GET", "POST"])
def history_site():

    ask_history = History.query.all()

    form = request.form
    if form:
        start_index = form["start_index"]
        stop_index = form["stop_index"]

        if int(start_index) and int(stop_index):
            if int(start_index) < 1 or int(stop_index) < 1 or int(start_index) > int(stop_index):
                return openFlashModal("Podano niepoprawny zakres!", "error")
            else:
                ask_history = History.query.filter(and_(History.id >= int(start_index), (History.id <= int(stop_index)))).all()

        else:
            return openFlashModal("Podano niepoprawny zakres!", "error")

    return render_template("history_site.html", history=ask_history)

alembic = Alembic()
alembic.init_app(app)


