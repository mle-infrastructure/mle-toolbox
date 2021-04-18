import random, string
from typing import Union
import base64
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random

# Credential encryption based on Stack Overflow discussion:
# stackoverflow.com/questions/42568262/how-to-encrypt-text-with-a-password-in-python

def get_random_string(length):
    """ Sample a random string. """
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


def encrypt(key: Union[str, bytes],
            source: Union[str, bytes],
            encode: bool=True):
    """ Encrypt ssh credentials based on CBC mode including PKCS#7 padding. """
    # Make sure key and source data are in bytes format
    if type(key) is not bytes:
        key = key.encode("latin-1")
    if type(source) is not bytes:
        source = source.encode("latin-1")
    key = SHA256.new(key).digest()  # use SHA-256 over key - proper-sized AES k
    IV = Random.new().read(AES.block_size)  # generate IV
    encryptor = AES.new(key, AES.MODE_CBC, IV)
    padding = AES.block_size - len(source) % AES.block_size  #calculate padding
    source += bytes([padding]) * padding
    data = IV + encryptor.encrypt(source)  # store IV at beginning and encrypt
    return base64.b64encode(data).decode("latin-1") if encode else data


def decrypt(key: Union[str, bytes],
            source: Union[str, bytes],
            decode: bool=True):
    """ Decrypt ssh credentials based on CBC mode including PKCS#7 padding. """
    # Make sure key and source data are in bytes format
    if type(key) is not bytes:
        key = key.encode("latin-1")
    if decode:
        source = base64.b64decode(source.encode("latin-1"))
    key = SHA256.new(key).digest()  # use SHA-256 over key - proper-sized AES k
    IV = source[:AES.block_size]  # extract the IV from the beginning
    decryptor = AES.new(key, AES.MODE_CBC, IV)
    data = decryptor.decrypt(source[AES.block_size:])  # decrypt
    padding = data[-1]  # pick the padding value from the end
    if data[-padding:] != bytes([padding]) * padding:
        raise ValueError("Invalid padding...")
    return data[:-padding].decode()


def encrypt_ssh_credentials(user_name: Union[str, bytes],
                            password: Union[str, bytes]):
    """ Generate an AES key and encrypt user name and password. """
    random_key = get_random_string(32)
    encrypt_user_name = encrypt(random_key, user_name)
    encrypt_password = encrypt(random_key, password)
    return random_key, encrypt_user_name, encrypt_password


def decrypt_ssh_credentials(aes_key: Union[str, bytes],
                            encrypt_user_name: Union[str, bytes],
                            encrypt_password: Union[str, bytes]):
    """ Decrypt user name and password based on encryption and AES key. """
    decrypt_user_name = decrypt(aes_key, encrypt_user_name)
    decrypt_password = decrypt(aes_key, encrypt_password)
    return decrypt_user_name, decrypt_password


if __name__ == "__main__":
    user_name = 'user'
    password = 'pass!'
    aes_key, enc_user_name, enc_password = encrypt_ssh_credentials(user_name,
                                                                   password)
    print(aes_key, enc_user_name, enc_password)
    dec_user_name, dec_password = decrypt_ssh_credentials(aes_key,
                                                          enc_user_name,
                                                          enc_password)
    print(dec_user_name, dec_password)
