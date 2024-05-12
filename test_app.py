import pytest
from main import (  # Replace 'your_application_module' with the actual name of your module
    is_username_taken,
    is_password_strong,
    check_password_hash,
    generate_password_hash,
    add_userdata,
    login_user,
    logout_user,
    add_data,
    create_users_table,
    create_table,
    execute_clickhouse_query,
)
from unittest.mock import patch

# Sample data for tests
SAMPLE_USERNAME = "admin"
SAMPLE_PASSWORD = "TestPass@123"
WEAK_PASSWORD = "weak"

# Mocking database responses
MOCK_USER_EXISTS = [[(1)]]
MOCK_USER_NOT_EXISTS = [[(0)]]
MOCK_PASSWORD_HASH = "hashed_pass"

@patch('main.execute_clickhouse_query')
def test_is_username_taken(mock_execute):
    mock_execute.return_value = MOCK_USER_EXISTS
    assert is_username_taken(SAMPLE_USERNAME) == True

    mock_execute.return_value = MOCK_USER_NOT_EXISTS
    assert is_username_taken("newuser") == False

def test_is_password_strong():
    assert is_password_strong(SAMPLE_PASSWORD) == True
    assert is_password_strong("short") == False
    assert is_password_strong("NoSpecial123") == False
    assert is_password_strong("nospecial@123") == False

@patch('main.bcrypt.hashpw')
@patch('main.bcrypt.gensalt')
def test_generate_password_hash(mock_gensalt, mock_hashpw):
    mock_hashpw.return_value = b'hashed_pass'
    assert generate_password_hash(SAMPLE_PASSWORD) == 'hashed_pass'

@patch('main.bcrypt.checkpw')
def test_check_password_hash(mock_checkpw):
    mock_checkpw.return_value = True
    assert check_password_hash(SAMPLE_PASSWORD, MOCK_PASSWORD_HASH) == True

    mock_checkpw.return_value = False
    assert check_password_hash("WrongPass", MOCK_PASSWORD_HASH) == False

# Integration Tests
@patch('main.execute_clickhouse_query')
def test_user_registration_workflow(mock_execute):
    # Assuming user doesn't exist yet
    mock_execute.side_effect = [MOCK_USER_NOT_EXISTS, None, None]  # Check user, create table, insert user
    assert add_userdata(SAMPLE_USERNAME, SAMPLE_PASSWORD) == True

    # Assuming user already exists
    mock_execute.side_effect = [MOCK_USER_EXISTS]
    assert add_userdata(SAMPLE_USERNAME, SAMPLE_PASSWORD) == False

@patch('main.execute_clickhouse_query')
def test_user_login_workflow(mock_execute):
    # Assuming correct login
    mock_execute.return_value = [(SAMPLE_USERNAME, generate_password_hash(SAMPLE_PASSWORD), 'user')]
    assert login_user(SAMPLE_USERNAME, SAMPLE_PASSWORD) == (SAMPLE_USERNAME, 'user')

    # Assuming incorrect login
    mock_execute.return_value = []
    assert login_user(SAMPLE_USERNAME, "WrongPass") == False
