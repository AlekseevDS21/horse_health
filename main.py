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
# model = joblib.load('model.pkl')

# Установка соединения с базой данных SQLite
conn = sqlite3.connect('data.db', check_same_thread=False)  # Добавлен check_same_thread=False для Streamlit
c = conn.cursor()
def create_users_table():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, password TEXT)')
    conn.commit()

def add_userdata(username, password):
    c.execute('INSERT INTO userstable(username, password) VALUES (?, ?)', (username, password))
    conn.commit()

def login_user(username, password):
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ?', (username, password))
    data = c.fetchall()
    return data

def logout_user():
    st.session_state['authenticated'] = False
    st.experimental_rerun()

# Изменение структуры таблицы, добавляем столбец для времени
def create_table():
    c.execute('''
    CREATE TABLE IF NOT EXISTS results(
        hospital_number REAL, lesion_1 REAL, packed_cell_volume REAL, total_protein REAL, pulse REAL, rectal_temp REAL, respiratory_rate REAL, abdomo_protein REAL, nasogastric_reflux_ph REAL, pain REAL, nasogastric_reflux REAL, rectal_exam_feces REAL, abdominal_distention REAL, abdomo_appearance REAL, abdomen REAL, nasogastric_tube REAL, temp_of_extremities REAL, peristalsis REAL, cp_data REAL, capillary_refill_time REAL, surgery REAL, peripheral_pulse REAL, mucous_membrane_bright_red REAL, surgical_lesion REAL, mucous_membrane_pale_pink REAL, mucous_membrane_normal_pink REAL, mucous_membrane_pale_cyanotic REAL, age REAL, is_generated REAL, mucous_membrane_bright_pink REAL,
        prediction TEXT, datestamp TEXT
    )
    ''')


# Modification of the function to add data for saving the date and time
def add_data(hospital_number, lesion_1, packed_cell_volume, total_protein, pulse, rectal_temp, respiratory_rate, abdomo_protein, nasogastric_reflux_ph, pain, nasogastric_reflux, rectal_exam_feces, abdominal_distention, abdomo_appearance, abdomen, nasogastric_tube, temp_of_extremities, peristalsis, cp_data, capillary_refill_time, surgery, peripheral_pulse, mucous_membrane_bright_red, surgical_lesion, mucous_membrane_pale_pink, mucous_membrane_normal_pink, mucous_membrane_pale_cyanotic, age, is_generated, mucous_membrane_bright_pink,
             prediction):
    datestamp = str(datetime.now())  # Formatting current time and date into a string
    c.execute('''
    INSERT INTO results(
        hospital_number, lesion_1, packed_cell_volume, total_protein, pulse, rectal_temp, respiratory_rate, abdomo_protein, nasogastric_reflux_ph, pain, nasogastric_reflux, rectal_exam_feces, abdominal_distention, abdomo_appearance, abdomen, nasogastric_tube, temp_of_extremities, peristalsis, cp_data, capillary_refill_time, surgery, peripheral_pulse, mucous_membrane_bright_red, surgical_lesion, mucous_membrane_pale_pink, mucous_membrane_normal_pink, mucous_membrane_pale_cyanotic, age, is_generated, mucous_membrane_bright_pink,
        prediction, datestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        hospital_number, lesion_1, packed_cell_volume, total_protein, pulse, rectal_temp, respiratory_rate, abdomo_protein, nasogastric_reflux_ph, pain, nasogastric_reflux, rectal_exam_feces, abdominal_distention, abdomo_appearance, abdomen, nasogastric_tube, temp_of_extremities, peristalsis, cp_data, capillary_refill_time, surgery, peripheral_pulse, mucous_membrane_bright_red, surgical_lesion, mucous_membrane_pale_pink, mucous_membrane_normal_pink, mucous_membrane_pale_cyanotic, age, is_generated, mucous_membrane_bright_pink,
        prediction, datestamp
    ))
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
    create_users_table()
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if st.session_state['authenticated']:
        logout_placeholder = st.empty()
        st.title('Прогнозирование состояния здоровья животных')

        with logout_placeholder.container():
            if st.button('Выйти из аккаунта'):
                logout_user()

        # Вкладки
        tab1, tab2, tab3 = st.tabs(['Ввод данных', 'Просмотр БД', 'График'])

        with tab1:
            st.header('Введите данные для анализа')

            # Описание параметров для ввода
            parameters_description = {
                1: "ID лошади",
                2: "Предыдущее посещение (номер, 0 если нет)",
                3: "Объем упакованных клеток (PCV):",
                4: "Общий белок(г/л):",
                5: "Частота пульса (уд/мин)",
                6: "Ректальная температура (°C)",
                7: "Белок брюшной полости(г/л)",
                8: "pH назогастрального рефлюкса",
                9: "Ввести номер соответствующего значения \n ('alert': 0, 'depressed': 1, 'moderate': 2, 'mild_pain': 3, 'severe_pain': 4, 'extreme_pain': 5)",
                10: "Назогастральный рефлюкс ('less_1_liter': 0, 'none': 1, 'more_1_liter': 2)",
                11: "Ректальный осмотр фекалий ('absent': 0, 'decreased': 1, 'normal': 2, 'increased': 3)",
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
                29: "Рефлекс перистальтики (баллы):"
            }

            user_input_list = []
            valid_data = True

            # Создаем форму для ввода данных
            with st.form("input_form"):
                for i in range(1, 30):
                    description = parameters_description.get(i, f"Параметр {i}:")
                    if i in [3, 4, 5, 6, 7, 8, 9, 28]:
                        # Для параметров, представляющих числа с плавающей точкой
                        param = st.text_input(description, key=f'param{i}')
                    else:
                        # Для параметров, представляющих целые числа
                        param = st.text_input(description, key=f'param{i}')

                submit_button = st.form_submit_button(label='Обработать')

            # Кнопка для обработки ввода
            if submit_button:
                for i in range(1, 30):
                    user_input_list.append(st.session_state[f'param{i}'])
                print(user_input_list)
                old_value = user_input_list[28]
                # Заменяем 29-е значение на 'единица'
                user_input_list[28] = '1'
                # Добавляем старое значение в конец списка
                user_input_list.append(old_value)
                # Обработка введенных данных
                # Здесь код для обработки данных
                with open("hist_model.pkl", 'rb') as file:
                    loaded_model = pickle.load(file)
                prediction = loaded_model.predict([user_input_list])

                outcome_mapping = {0: 'смерть', 1: 'эвтаназия', 2: 'живой'}
                # Вывод результата и запись в базу данных
                prediction = outcome_mapping[prediction[0]]
                st.write('Результат предсказания:', prediction)
                create_table()
                add_data(*user_input_list, prediction)

        with tab2:
            st.header('Просмотр данных')
            password = st.text_input('Введите пароль для доступа к данным:', type='password')
            correct_password = config['password']

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
                    data_df = pd.DataFrame(data, columns=['hospital_number', 'lesion_1', 'packed_cell_volume',
                        'total_protein', 'pulse', 'rectal_temp',
                        'respiratory_rate', 'abdomo_protein', 'nasogastric_reflux_ph',
                        'pain', 'nasogastric_reflux', 'rectal_exam_feces',
                        'abdominal_distention', 'abdomo_appearance', 'abdomen',
                        'nasogastric_tube', 'temp_of_extremities', 'peristalsis',
                        'cp_data', 'capillary_refill_time', 'surgery',
                        'peripheral_pulse', 'mucous_membrane_bright_red', 'surgical_lesion',
                        'mucous_membrane_pale_pink', 'mucous_membrane_normal_pink',
                        'mucous_membrane_pale_cyanotic', 'age', 'is_generated',
                        'mucous_membrane_bright_pink', 'Предсказание', 'Дата'])
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

    else:
        with st.sidebar:
            st.subheader("Регистрация и вход")

            menu = ["Вход", "Регистрация"]
            choice = st.selectbox("Меню", menu, key="menu_selectbox")

            if choice == "Регистрация":
                new_username = st.text_input("Имя пользователя", key="new_username")
                new_password = st.text_input("Пароль", type='password', key="new_password")
                confirm_password = st.text_input("Повторите пароль", type='password', key="confirm_password")

                if new_password and confirm_password and st.button("Зарегистрироваться", key="signup_button"):
                    # Проверяем, совпадают ли пароли
                    if new_password == confirm_password:
                        add_userdata(new_username, new_password)
                        st.success("Вы успешно зарегистрировались!")
                    else:
                        st.error("Пароли не совпадают. Попробуйте снова.")

            elif choice == "Вход":
                username = st.text_input("Имя пользователя", key="username_login")
                password = st.text_input("Пароль", type='password', key="password_login")

                if username and password and st.button("Войти", key="login_button"):
                    if login_user(username, password):
                        st.success("Вы успешно вошли в систему!")
                        st.session_state['authenticated'] = True
                        st.experimental_rerun()
                    else:
                        st.error("Неверное имя пользователя или пароль")


if __name__ == '__main__':
    main()
