import asyncio
import hashlib
import os
import shutil
import tempfile
import unittest.mock
from unittest.mock import AsyncMock

import aiohttp
import pytest

from main import calc, fetch_files, save_files


@pytest.mark.asyncio
async def test_fetch_files():
    expected_data = [{'name': 'file1.txt',
                      'download_url': 'https://example.com/file1.txt',
                      'type': 'file'},
                     {'name': 'file2.txt',
                      'download_url': 'https://example.com/file2.txt',
                      'type': 'file'}]

    mock_session = AsyncMock()
    mock_session.get.return_value.json = AsyncMock(return_value=expected_data)

    all_files = await fetch_files(mock_session, [], 'https://example.com')

    assert all_files == [
        ('file1.txt',
         'https://example.com/file1.txt'),
        ('file2.txt',
         'https://example.com/file2.txt')]


@pytest.mark.asyncio
async def test_save_files():
    directory = tempfile.mkdtemp()
    filename = 'file1.txt'
    url = 'https://test.com/file1.txt'

    mock_session = unittest.mock.MagicMock(spec=aiohttp.ClientSession)

    response = unittest.mock.AsyncMock()
    response.text.return_value = 'test content'
    mock_session.get.return_value.__aenter__.return_value = response

    semaphore = asyncio.Semaphore(3)

    await save_files(mock_session, filename, url, directory, semaphore)

    file_path = os.path.join(directory, filename)
    assert os.path.isfile(file_path), f'Файл {filename} не был создан'

    with open(file_path, 'r') as f:
        file_content = f.read()
    assert file_content == 'test content', 'Содержимое файла не соответствует ожидаемому'


def test_calc(capsys):
    temp_dir = tempfile.mkdtemp()
    try:
        file1_path = os.path.join(temp_dir, 'file1.txt')
        file2_path = os.path.join(temp_dir, 'file2.txt')
        with open(file1_path, 'w') as file1, open(file2_path, 'w') as file2:
            file1.write('Content of file 1')
            file2.write('Content of file 2')

        calc(temp_dir)

        expected_hash1 = hashlib.sha256(
            'Content of file 1'.encode()).hexdigest()
        expected_hash2 = hashlib.sha256(
            'Content of file 2'.encode()).hexdigest()
        out = capsys.readouterr().out
        assert expected_hash1 in out
        assert expected_hash2 in out

    finally:
        shutil.rmtree(temp_dir)
