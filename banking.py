# Программа использует SQLite таблицу, ней хранятся данные пользователей. И к этой таблице программа постоянно
# обращется в процессе работы

import random
import sqlite3 as sql
import sys


class Bank:
    logged_in = False
    logged_card_number = ''

    def open_table(func):
        """Декоратор, отвечает за открытие таблицы с данными клиентов"""
        def wrapper(self, *args):
            con = sql.connect('card.s3db')
            cursor = con.cursor()
            return_value = func(self, cursor, *args)
            con.commit()
            con.close()
            return return_value
        return wrapper

    def main_menu(self):
        """Открывает соответсвующее меню в зависимости от статуса (залогинен или нет)"""
        self.create_database()
        while True:
            if self.logged_in:
                self.logged_menu()
            else:
                self.initial_menu()

    def initial_menu(self):
        """Меню для незалогиненных пользователей. Можно создать карту, войти или закрыть приложение"""
        print('''1. Create an account
2. Log into account
0. Exit''')
        user_option = input()
        if user_option == '1':
            print(f'\n{self.create_card()}\n')
        elif user_option == '2':
            print(f'\n{self.log_in()}\n')
        elif user_option == '0':
            print('\nBye!')
            sys.exit()

    def logged_menu(self):
        """Меню для авторизованного пользователя. Можно посмотреть баланс, добавить средства, отправить средства
        на другую карту, выйти из аккаунта и выйти из программы."""
        print('''1. Balance
2. Add income
3. Do transfer
4. Close account
5. Log out
0. Exit''')
        user_option = input()
        if user_option == '1':
            print(f'\n{self.balance()}\n')
        elif user_option == '2':
            print(self.add_income())
        elif user_option == '3':
            print(f'{self.do_transfer()}')
        elif user_option == '4':
            print(f'\n{self.close_account()}\n')
        elif user_option == '5':
            self.logged_in = False
            print('\nYou have successfully logged out!\n')
        elif user_option == '0':
            print('\nBye!')
            sys.exit()

    def create_card(self):
        """Фунцкия отвечает за создание карты и пина к ней. Номер карты создается, использую алгоритм Луна"""
        while True:
            numbers_for_card = [str(random.randrange(0, 10)) for i in range(9)]
            user_id = "".join(numbers_for_card)
            half_card_number = f'400000{user_id}'
            card_number = f'{half_card_number}{self.luhn_alg(half_card_number)}'
            if not self.card_in_table(card_number):
                break
        numbers_for_pin = [str(random.randrange(0, 10)) for i in range(4)]
        pin = ''.join(numbers_for_pin)
        self.update_table(user_id, card_number, pin)
        return f'''Your card has been created
Your card number:
{card_number}
Your card PIN:
{pin}'''

    def luhn_alg(self, card_number):
        """Алгоритм Луна. Вычисляет последнюю цифру карточки, это контрольная сумма всех прошлых цифр"""
        numbers = [int(i) for i in card_number]
        luhn_numbers = []
        x = 0
        for num, i in enumerate(numbers, 1):
            if num % 2 == 1:
                i = i * 2
                if i > 9:
                    i -= 9
            luhn_numbers.append(i)
        luhn_sum = sum(luhn_numbers)
        while (luhn_sum + x) % 10 != 0:
            x += 1
        return x

    def log_in(self):
        """Функция отвечает за авторизацию пользователя. Если введены неверные данные, выдает ошибку"""
        user_card_number = input('Enter your card number:\n')
        user_pin = input('Enter your PIN:\n')
        if not self.check_card(user_card_number, user_pin):
            return 'Wrong card number or PIN!'
        else:
            self.logged_in = True
            self.logged_card_number = user_card_number
            return 'You have successfully logged in!'

    # Все функции ниже отвечают за работу с SQLite таблицей

    @open_table
    def create_database(self, cursor):
        """Создает датабазу и таблицу, если еще не создана"""
        cursor.execute('CREATE TABLE IF NOT EXISTS card('
                       'id INTEGER,'
                       'number TEXT,'
                       'pin TEXT,'
                       'balance INTEGER DEFAULT 0)')
        return

    @open_table
    def balance(self, cursor):
        """Выводит баланс авторизованного пользователя"""
        cursor.execute(f'SELECT balance FROM card WHERE number={self.logged_card_number}')
        res = cursor.fetchall()
        return res[0][0]

    @open_table
    def update_table(self, cursor, id, card_number, pin):
        """Добавляет в таблицу созданную карту"""
        cursor.execute(f'INSERT INTO card (id, number, pin) '
                       f'VALUES ({id}, {card_number}, {pin})')
        return

    @open_table
    def card_in_table(self, cursor, card):
        """Проверяет, есть ли в таблице такой номер карты"""
        cursor.execute(f'SELECT * FROM card WHERE number={card}')
        res = cursor.fetchall()
        return res

    @open_table
    def check_card(self, cursor, card, pin):
        """Проверяет, правильно ли введены номер карты и пин"""
        cursor.execute(f'SELECT * FROM card WHERE number={card} and pin={pin}')
        res = cursor.fetchall()
        return res

    @open_table
    def add_income(self, cursor):
        """Добавляет средства на счет"""
        income = input('\nEnter income:\n')
        cursor.execute(f'UPDATE card SET balance = balance + {income} WHERE number = {self.logged_card_number}')
        return 'Income was added!\n'

    @open_table
    def close_account(self, cursor):
        """Закрывает аккаунт (удаляет из датабазы)"""
        cursor.execute(f'DELETE FROM card where number = {self.logged_card_number}')
        self.logged_in = False
        return 'The account has been closed!'

    @open_table
    def do_transfer(self, cursor):
        """Отправляет средства на счет другой карты"""
        print('\nTransfer')
        card_to_transfer = input('Enter card number:\n')
        numbers_for_luhn = card_to_transfer[:-1]
        if self.luhn_alg(numbers_for_luhn) != int(card_to_transfer[-1]):
            """Проверяет номер карты на соответсвие алгоритму Луна"""
            return 'Probably you made mistake in the card number. Please try again!\n'
        elif not self.card_in_table(card_to_transfer):
            """Проверяет на наличие карты в датабазе"""
            return 'Such a card does not exist.\n'
        elif card_to_transfer == self.logged_card_number:
            """Проверяет, что введена не своя карта"""
            return "You can't transfer money to the same account!\n"
        money_to_transfer = int(input('Enter how much money you want to transfer:\n'))
        cursor.execute(f'SELECT balance FROM card WHERE number = {self.logged_card_number}')
        balance_money = int(cursor.fetchall()[0][0])
        if money_to_transfer > balance_money:
            return 'Not enough money!\n'
        cursor.execute(f'UPDATE card SET balance = balance - {money_to_transfer} WHERE number = {self.logged_card_number}')
        cursor.execute(f'UPDATE card SET balance = balance + {money_to_transfer} WHERE number = {card_to_transfer}')
        return 'Success!\n'


if __name__ == '__main__':
    tinkoff = Bank()
    tinkoff.main_menu()
