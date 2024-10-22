from werkzeug.security import generate_password_hash
if __name__ =='__main__':
    for pwd in {'hy','cyy',''}:
        print(pwd,'\n',generate_password_hash(pwd))