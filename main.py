"""main file."""
import asyncio
import hashlib
import os
import tempfile

import aiofiles
import aiohttp

from logger import logger


async def fetch_files(session, all_files, url):
    """Fetch files with their links.
    Args:
    session (Current session): ClientSession
    all_files (List of files): list   
    url (Url to get files): str
    Returns: list
    """
    try:
        response = await session.get(url)   
    except Exception as err:
        logger.error('Can\'t receive response. {}'.format(err))
        raise Exception(err)
    try:
        data = await response.json()   
    except Exception as err:
        logger.error('Can\'t receive data from url. {}'.format(err))
        raise Exception(err)

    for current in data:
        if current.get('type') == 'file':
            all_files.append(
                (current.get('name'), current.get('download_url'))
                )
        elif current.get('type') == 'dir':
            await fetch_files(session,
                              all_files,
                              url + '/' + current.get('name'))
    return all_files


async def save_files(session, filename, url, directory, semaphore):
    """ Save files.
    Args:
    session (Current session): ClientSession
    filename (File name): str   
    url (Url to get files): str
    directory (directory for saving): str
    semaphore (semaphore): Semaphore
    Returns: None
    """
    async with semaphore:
        async with session.get(url) as response:
            content = await response.text()
            try:
                async with aiofiles.open(f'{directory}/{filename}', 'w') as f:
                    await f.write(content)
            except Exception as err:
                logger.error(f'Problem with file: {err}')


def calc(folder):
    """ Save files.
    Args:
    folder (directory for calculating): str
    Returns: None
    """
    logger.info('Calculating hashs.')
    for address, _, files in os.walk(folder):
        for name in files:
            file_path = os.path.join(address, name)
            try:
                with open(file_path, 'r') as file:
                    sha256_hash = hashlib.new('sha256')
                    while True:
                        data = file.read(1024)  # Считываем данные порциями
                        if not data:
                            break
                        sha256_hash.update(data.encode())
                    print('SHA-256: {}'.format(sha256_hash.hexdigest()))
            except Exception as err:
                logger.error('Problem with file: {}'.format(err))


async def main():
    with tempfile.TemporaryDirectory() as tmp:
        logger.info('Temporary directory {} created.'.format(tmp))
        async with aiohttp.ClientSession() as session:
            url = (
                'https://gitea.radium.group/api/v1/'
                'repos/radium/project-configuration/contents'
            )
            files = await fetch_files(session, [], url)
            logger.info('List files received.')
            semaphore = asyncio.Semaphore(3)
            tasks = [
                save_files(session, *file_data, tmp, semaphore)
                for file_data in files
            ]
            logger.info('Start saving files.')
            await asyncio.gather(*tasks)
        calc(tmp)

if __name__ == '__main__':
    logger.info('Start working.')
    asyncio.run(main())
