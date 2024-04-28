import streamlit as st
import pandas as pd
import sqlite3
import joblib
from datetime import datetime, date
import plotly.express as px
import os.path
from app.config import getConfig
from sklearn.experimental import enable_hist_gradient_boosting  # noqa
from sklearn.ensemble import HistGradientBoostingClassifier
import pickle

config = getConfig()


# Загрузка модели машинного обучения
#model = joblib.load('model.pkl')

# Установка соединения с базой данных SQLite
conn = sqlite3.connect('data.db', check_same_thread=False)  # Добавлен check_same_thread=False для Streamlit
c = conn.cursor()

# Изменение структуры таблицы, добавляем столбец для времени
def create_table():
    c.execute('CREATE TABLE IF NOT EXISTS results(input_data TEXT, prediction TEXT, datestamp TEXT)')

# Изменение функции добавления данных, чтобы сохранять дату и время
def add_data(input_data, prediction):
    datestamp = str(datetime.now())  # Форматируем текущее время и дату в строку
    c.execute('INSERT INTO results(input_data, prediction, datestamp) VALUES (?, ?, ?)', (input_data, prediction, datestamp))
    conn.commit()

# Получение данных из базы данных
def view_data(start_date=None, end_date=None, selected_prediction=None):
    query = 'SELECT * FROM results'
    if selected_prediction == 'Все':
        if start_date and end_date:
            query += ' WHERE date(datestamp) BETWEEN ? AND ?'
            params = (start_date, end_date)
        else:
            params = ()
    else:
        if start_date and end_date:
            query += ' WHERE prediction = ? AND date(datestamp) BETWEEN ? AND ?'
            params = (selected_prediction, start_date, end_date)
        else:
            query += ' WHERE prediction = ?'
            params = (selected_prediction,)
    
    c.execute(query, params)
    data = c.fetchall()
    return data

def create_pie_chart(data, column='Предсказание'):
    fig = px.pie(data, names=column, title='Распределение предсказаний')
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.title('Прогнозированипе состояния здоровья лошади')

    # Вкладки
    tab1, tab2, tab3 = st.tabs(['Ввод данных', 'Просмотр БД', 'График'])

    with tab1:
        st.header('Введите данные для анализа')

        # Описание параметров для ввода
        parameters_description = {
            1: "Возраст лошади (лет):",
            2: "Температура тела (градусы Цельсия):",
            3: "Частота пульса (удары в минуту):",
            4: "Частота пульса (удары в минуту):",
            5: "Частота пульса (удары в минуту):",
            6: "Частота пульса (удары в минуту):",
            7: "Частота пульса (удары в минуту):",
            8: "Частота пульса (удары в минуту):",
            9: "Частота пульса (удары в минуту):",
            10: "Частота пульса (удары в минуту):",
            11: "Частота пульса (удары в минуту):",
            12: "Частота пульса (удары в минуту):",
            13: "Частота пульса (удары в минуту):",
            14: "Частота пульса (удары в минуту):",
            15: "Частота пульса (удары в минуту):",
            16: "Частота пульса (удары в минуту):",
            17: "Частота пульса (удары в минуту):",
            18: "Частота пульса (удары в минуту):",
            19: "Частота пульса (удары в минуту):",
            20: "Частота пульса (удары в минуту):",
            21: "Частота пульса (удары в минуту):",
            22: "Частота пульса (удары в минуту):",
            23: "Частота пульса (удары в минуту):",
            24: "Частота пульса (удары в минуту):",
            25: "Частота пульса (удары в минуту):",
            26: "Частота пульса (удары в минуту):",
            27: "Частота пульса (удары в минуту):",
            28: "Общий уровень белка (г/дл):",
            29: "Анамнез или другие заметки:",
            30: "Рефлекс перистальтики (баллы):"
        }

        user_input_list = []
        valid_data = True

        # Создаем форму для ввода данных
        with st.form("input_form"):
            for i in range(1, 31):
                description = parameters_description.get(i, f"Параметр {i}:")
                if i in [3, 4, 5, 6, 7, 8, 9, 28]:
                    # Для параметров, представляющих числа с плавающей точкой
                    param = st.text_input(description, key=f'param{i}')
                elif i == 29:
                    # Для текстовых параметров
                    param = st.text_area(description, key=f'param{i}')
                else:
                    # Для параметров, представляющих целые числа
                    param = st.text_input(description, key=f'param{i}')

            submit_button = st.form_submit_button(label='Обработать')

        # Кнопка для обработки ввода
        if submit_button:
            for i in range(1, 31):
                user_input_list.append(st.session_state[f'param{i}'])
            old_value = user_input_list[28]
            # Заменяем 29-е значение на 'единица'
            user_input_list[28] = 1
            # Добавляем старое значение в конец списка
            user_input_list.append(old_value)
            # Обработка введенных данных
            # Здесь код для обработки данных
            with open("hist_model.pkl", 'rb') as file:
                loaded_model = pickle.load(file)
            prediction = loaded_model.predict([user_input_list[:-1]])
            # Вывод результата и запись в базу данных
            st.write('Результат предсказания:', prediction)
            create_table()
            add_data(", ".join(user_input_list), prediction)

    with tab2:
        st.header('Просмотр данных')
        password = st.text_input('Введите пароль для доступа к данным:', type='password')
        correct_password = config['password']  # Замените 'секрет' на ваш реальный пароль

        if password == correct_password:
            # Фильтр по предсказанию
            c.execute('SELECT DISTINCT prediction FROM results')
            unique_predictions = c.fetchall()
            prediction_options = [pred[0] for pred in unique_predictions]

            selected_prediction = st.selectbox('Фильтр по полю predict:', ['Все'] + prediction_options)
            # Фильтр по дате
            st.subheader('Фильтр по дате')
            start_date = st.date_input('С:', date.today())
            end_date = st.date_input('По:', date.today())

            if st.button('Показать данные'):
                # Получение отфильтрованных данных
                data = view_data(start_date, end_date, selected_prediction)
                # Вывод данных
                data_df = pd.DataFrame(data, columns=['Введенные данные', 'Предсказание', 'Дата'])
                st.dataframe(data_df)
        else:
            if st.button('Проверить пароль'):
                st.error('Неправильный пароль!')
    with tab3:
        st.header('Статистика предсказаний')
        password = st.text_input('Введите пароль для доступа к статистике:', type='password', key='password_tab3')
        correct_password = config['password']  # Замените 'секрет' на ваш реальный пароль

        if password == correct_password:
            # Получаем данные для диаграммы
            c.execute('SELECT prediction FROM results')
            all_predictions = c.fetchall()
            predictions_df = pd.DataFrame(all_predictions, columns=['Предсказание'])
            
            # Создаем и отображаем круговую диаграмму
            create_pie_chart(predictions_df)
        else:
            if st.button('Проверить пароль', key='check_password_tab3'):
                st.error('Неправильный пароль!')


if __name__ == '__main__':
    main()