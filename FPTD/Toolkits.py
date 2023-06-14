from phe import paillier
import json


def serialize(encrypted):
    msg = [(str(x.ciphertext()), x.exponent) for x in encrypted]
    return bytes(json.dumps(msg), encoding='utf-8')


def deserialize(msg, pk):
    recv_dict = json.loads(str(msg,encoding='utf-8'))
    encrypted_secret = [
        paillier.EncryptedNumber(pk, int(x[0]), int(x[1]))
        for x in recv_dict]
    return encrypted_secret


