import streamlit as st
import pandas as pd
import sqlite3
import joblib
from datetime import datetime, date
import plotly.express as px
import os.path
from app.config import getConfig

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
        st.header('Ввод данных для обработки')

        # Создаем ряды и колонки для полей ввода
        col1, col2 = st.columns(2)
        with col1:
            field1 = st.text_input('Описание данных 1:')
            field3 = st.text_input('Описание данных 3:')
            field5 = st.text_input('Описание данных 5:')
            field7 = st.text_input('Описание данных 7:')
            field9 = st.text_input('Описание данных 9:')
        with col2:
            field2 = st.text_input('Описание данных 2:')
            field4 = st.text_input('Описание данных 4:')
            field6 = st.text_input('Описание данных 6:')
            field8 = st.text_input('Описание данных 8:')
            field10 = st.text_input('Описание данных 10:')

        # Кнопка для обработки ввода
        if st.button('Обработать'):
            # Обработка введенных данных
            user_input = [field1, field2, field3, field4, field5, field6, field7, field8, field9, field10]
            # Здесь код для обработки данных
            prediction = " ".join(user_input)
            # Вывод результата и запись в базу данных
            st.write('Результат предсказания:', prediction)
            create_table()
            add_data(", ".join(user_input), prediction)

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