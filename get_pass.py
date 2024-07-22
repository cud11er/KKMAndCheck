import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

if __name__ == '__main__':
    password = input('Enter your password: ')
    print(f"Your hash password: {hash_password(password)}")
else:
    exit()