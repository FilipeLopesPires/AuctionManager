import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def RSAKeyGenerator(password,destination):
	private_key = rsa.generate_private_key(
		public_exponent=65537,
		key_size=4096,
		backend=default_backend()
	)
	private_pem = private_key.private_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PrivateFormat.PKCS8,
		encryption_algorithm=serialization.BestAvailableEncryption(password)
	)

	public_key = private_key.public_key()
	public_pem = public_key.public_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PublicFormat.SubjectPublicKeyInfo
	)

	private_file = open(destination+"_private_key.pem","wb")
	public_file = open(destination+"_public_key.pem","wb")

	private_file.write(private_pem)
	public_file.write(public_pem)

	private_file.close()
	public_file.close()
	return


def SymmetricKeyGenerator():
	key_file = open("symmetric_key.txt","wb")

	key = os.urandom(32)
	iv = os.urandom(16)

	key_file.write(key + b"\n" + iv)
	return


password = b"SIO_85048_85122"
#destination = "manager"
destination = "repository"
#destination = "client"

RSAKeyGenerator(password,destination)
#SymmetricKeyGenerator()