import streamlit as st
import pandas as pd
from clickhouse_driver import Client
import joblib
from datetime import datetime, date, timedelta
import plotly.express as px
import os.path
from app.config import getConfig
from sklearn.experimental import enable_hist_gradient_boosting  # noqa
from sklearn.ensemble import HistGradientBoostingClassifier
import pickle
import bcrypt
import re


config = getConfig()

client = Client(host='localhost', database='health', user='default', password='Andrey41k!')
def execute_clickhouse_query(query, params=None):
    return client.execute(query, params, types_check=True) if params else client.execute(query, types_check=True)

def is_username_taken(username):
    data = execute_clickhouse_query("SELECT COUNT(*) FROM userstable WHERE username = %(username)s", {'username': username})
    return data[0][0] > 0


def is_password_strong(password):
    # Проверка длины пароля
    if len(password) < 8:
        return False
    # Проверка наличия минимум одной заглавной буквы
    if not re.search("[A-Z]", password):
        return False
    # Проверка наличия минимум одного специального символа
    if not re.search("[!@#$%^&*(),.?\":{}|<>\-'/]", password):
        return False
    return True

def generate_password_hash(password):
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode('utf-8')

def check_password_hash(password, hashed_password):
    password_bytes = password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)


def create_users_table():
    execute_clickhouse_query("CREATE TABLE IF NOT EXISTS userstable(username String, \
    password String, role String DEFAULT 'user') ENGINE = MergeTree() ORDER BY username")

def add_userdata(username, password, role='user'):
    if is_username_taken(username):
        return False  # Имя пользователя уже занято
    hashed_password = generate_password_hash(password)
    execute_clickhouse_query('INSERT INTO userstable(username, password, role) VALUES', [(username, hashed_password, role)])
    return True
def login_user(username, password):
    user_data = execute_clickhouse_query('SELECT username, password, role FROM userstable WHERE username = %(username)s', {'username': username})
    if user_data and check_password_hash(password, user_data[0][1]):
        return user_data[0][0], user_data[0][2]  # Возвращаем имя пользователя и его роль
    else:
        return False


def logout_user():
    st.session_state.pop('authenticated', None)  # Удаляем аутентификацию
    st.session_state.pop('current_user', None)   # Удаляем текущего пользователя
    st.experimental_rerun()

def create_table():
    execute_clickhouse_query('''
    CREATE TABLE IF NOT EXISTS results(
    username String,
    hospital_number Int32,
    lesion_1 Int32,
    packed_cell_volume Float32,
    total_protein Float32,
    pulse Float32,
    rectal_temp Float32,
    respiratory_rate Float32,
    abdomo_protein Float32,
    nasogastric_reflux_ph Float32,
    pain Int32,
    nasogastric_reflux Int32,
    rectal_exam_feces Int32,
    abdominal_distention Int32,
    abdomo_appearance Int32,
    abdomen Int32,
    nasogastric_tube Int32,
    temp_of_extremities Int32,
    peristalsis Int32,
    cp_data Int32,
    capillary_refill_time Int32,
    surgery Int32,
    peripheral_pulse Int32,
    mucous_membrane_bright_red Int32,
    surgical_lesion Int32,
    mucous_membrane_pale_pink Int32,
    mucous_membrane_normal_pink Int32,
    mucous_membrane_pale_cyanotic Int32,
    age Int32,
    is_generated Int32,
    mucous_membrane_bright_pink Int32,
    prediction String,
    datestamp DateTime)
    ENGINE = MergeTree() ORDER BY (username, hospital_number, datestamp)
    ''')


def add_data(username, *args):
    datestamp = datetime.now()
    query = 'INSERT INTO results (username, hospital_number, lesion_1, packed_cell_volume, total_protein, pulse, rectal_temp, respiratory_rate, abdomo_protein, nasogastric_reflux_ph, pain, nasogastric_reflux, rectal_exam_feces, abdominal_distention, abdomo_appearance, abdomen, nasogastric_tube, temp_of_extremities, peristalsis, cp_data, capillary_refill_time, surgery, peripheral_pulse, mucous_membrane_bright_red, surgical_lesion, mucous_membrane_pale_pink, mucous_membrane_normal_pink, mucous_membrane_pale_cyanotic, age, is_generated, mucous_membrane_bright_pink, prediction, datestamp) VALUES'
    params = [(username,) + tuple(args) + (datestamp,)]
    execute_clickhouse_query(query, params)

def view_data(username, start_date=None, end_date=None, selected_prediction=None):
    role = st.session_state.get('user_role')
    if role == 'admin':
        query = 'SELECT * FROM results'
        params = {}
    else:
        query = 'SELECT * FROM results WHERE username = %(username)s'
        params = {'username': username}

    # Для администратора добавляем расширенный фильтр
    if role == 'admin':
        if selected_prediction and selected_prediction != 'Все':
            query += ' WHERE prediction = %(prediction)s'
            params['prediction'] = selected_prediction
            formatted_start_date = start_date.strftime('%Y-%m-%d')
            formatted_end_date = end_date.strftime('%Y-%m-%d')
            query += f" AND toDate(datestamp) BETWEEN '{formatted_start_date}' AND '{formatted_end_date}'"
        else:
            formatted_start_date = start_date.strftime('%Y-%m-%d')
            formatted_end_date = end_date.strftime('%Y-%m-%d')
            query += f" WHERE toDate(datestamp) BETWEEN '{formatted_start_date}' AND '{formatted_end_date}'"

    else:
        if selected_prediction and selected_prediction != 'Все':
            query += ' AND prediction = %(prediction)s'
            params['prediction'] = selected_prediction
            formatted_start_date = start_date.strftime('%Y-%m-%d')
            formatted_end_date = end_date.strftime('%Y-%m-%d')
            query += f" AND toDate(datestamp) BETWEEN '{formatted_start_date}' AND '{formatted_end_date}'"
        else:
            formatted_start_date = start_date.strftime('%Y-%m-%d')
            formatted_end_date = end_date.strftime('%Y-%m-%d')
            query += f" AND toDate(datestamp) BETWEEN '{formatted_start_date}' AND '{formatted_end_date}'"

    data = execute_clickhouse_query(query, params)
    return pd.DataFrame(data)

def create_pie_chart(data, column='Предсказание'):
    fig = px.pie(data, names=column, title='Распределение предсказаний')
    st.plotly_chart(fig, use_container_width=True)


def main():
    create_users_table()
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
        st.session_state['current_user'] = ''  # Инициализация текущего пользователя

        # Если пользователь аутентифицирован, присваиваем имя пользователя
    if st.session_state['authenticated']:
        current_user = st.session_state.get('current_user', '')
        logout_placeholder = st.empty()
        st.title('Прогнозирование состояния здоровья животных')

        with logout_placeholder.container():
            if st.button('Выйти из аккаунта'):
                logout_user()

        tab1, tab2, tab3 = st.tabs(['Ввод данных', 'Просмотр БД', 'Дашборд'])

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
                    if i in [3, 4, 5, 6, 7, 8, 9]:
                        # Для параметров, представляющих числа с плавающей точкой
                        param = st.text_input(description, key=f'param{i}')
                    else:
                        # Для параметров, представляющих целые числа
                        param = st.text_input(description, key=f'param{i}')

                submit_button = st.form_submit_button(label='Обработать')

            # Кнопка для обработки ввода
            if submit_button:
                try:
                    for i in range(1, 30):
                        if 3 <= i <= 9:
                            user_input_list.append(float(st.session_state[f'param{i}']))
                        else:
                            user_input_list.append(int(st.session_state[f'param{i}']))
                    print(user_input_list)
                    old_value = user_input_list[28]
                    # Заменяем 29-е значение на 'единица'
                    user_input_list[28] = 1
                    # Добавляем старое значение в конец списка
                    user_input_list.append(old_value)
                    # Обработка введенных данных
                    # Здесь код для обработки данных
                    with open("hist_model.pkl", 'rb') as file:
                        loaded_model = pickle.load(file)
                    prediction = loaded_model.predict([user_input_list])

                    outcome_mapping = {0: 'смерть', 1: 'эвтаназия', 2: 'живой'}
                    # Вывод результата и запись в базу данных
                    username = st.session_state.get('current_user', 'unknown')  # Получаем имя текущего пользователя
                    prediction = outcome_mapping[prediction[0]]
                    st.write('Результат предсказания:', prediction)
                    create_table()
                    add_data(username, *user_input_list, prediction)
                except:
                    st.write('Введены не корректные данные')


        with tab2:
            st.header('Просмотр данных')
            username = st.session_state.get('current_user')  # Получаем имя текущего пользователя из сессии
            prediction_options = ["смерть", "эвтаназия", "живой"]

            if username:
                selected_prediction = st.selectbox('Фильтр по полю predict:', ['Все'] + prediction_options)
                start_date = st.date_input("Выберите начальную дату:", date.today() - timedelta(days=7))
                end_date = st.date_input("Выберите конечную дату:", date.today())
                if st.button('Показать данные'):
                    data_df = view_data(username, start_date, end_date,
                                        selected_prediction)  # Используем функцию view_data
                    st.dataframe(data_df)
            else:
                st.error("Вы не авторизованы!")

        with tab3:
            username = st.session_state.get('current_user')
            if username:
                # Для администратора показываем все данные, для других пользователей — только их данные
                if st.session_state.get('user_role') == 'admin':
                    st.header('Статистика предсказаний')
                    all_predictions = execute_clickhouse_query('SELECT prediction FROM results')
                    predictions_df = pd.DataFrame(all_predictions, columns=['Предсказание'])
                    create_pie_chart(predictions_df)
                else:
                    st.header('Статистика предсказаний')
                    query = 'SELECT prediction FROM results WHERE username = %(username)s'
                    params = {'username': username}
                    all_predictions = execute_clickhouse_query(query, params)
                    predictions_df = pd.DataFrame(all_predictions, columns=['Предсказание'])
                    create_pie_chart(predictions_df)

    else:
        with st.sidebar:
            st.subheader("Регистрация и вход")

            menu = ["Вход", "Регистрация"]
            choice = st.selectbox("Меню", menu, key="menu_selectbox")

            if choice == "Регистрация":
                new_username = st.text_input("Имя пользователя", key="new_username")
                # Проверяем, было ли что-то введено в поле имени пользователя
                if new_username:
                    # Проверяем, занято ли имя пользователя
                    if is_username_taken(new_username):
                        st.error("Имя пользователя уже занято. Пожалуйста, выберите другое имя.")
                        # Останавливаем дальнейший ввод данных, пока не будет выбрано другое имя пользователя
                    else:
                        new_password = st.text_input("Пароль", type='password', key="new_password")
                        if is_password_strong(new_password):
                            confirm_password = st.text_input("Повторите пароль", type='password', key="confirm_password")
                            if new_password and confirm_password and st.button("Зарегистрироваться", key="signup_button"):
                                if new_password == confirm_password:
                                    add_userdata(new_username, new_password)
                                    st.success("Вы успешно зарегистрировались!")
                                else:
                                    st.error("Пароли не совпадают. Попробуйте снова.")
                        else:
                            st.error("Пароль должен быть длинее 8 символов, содержать минимум одну заглавную букву и один специальный символ.")


            elif choice == "Вход":
                username = st.text_input("Имя пользователя", key="username_login")
                password = st.text_input("Пароль", type='password', key="password_login")

                if username and password and st.button("Войти", key="login_button"):
                    user_data = login_user(username, password)
                    if user_data:
                        username, role = user_data
                        st.session_state['authenticated'] = True
                        st.session_state['current_user'] = username  # Здесь сохраняем имя вошедшего пользователя
                        st.session_state['user_role'] = role
                        st.experimental_rerun()
                    else:
                        st.error("Неверное имя пользователя или пароль")


if __name__ == '__main__':
    main()
