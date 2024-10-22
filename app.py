from flask import Flask,render_template,request,session,redirect,url_for,current_app,g
import register
import book
import db

def create_app():
    app = Flask(__name__)
    app.secret_key='any random string'
  
    @app.route('/')  
    def home():  
        msg = ""
        return  render_template("home.html",data=msg)

    db.init_app(app)

    app.register_blueprint(register.bp)


    app.register_blueprint(book.bp)

    return app
if __name__ == "__main__":
    app = create_app()
    app.run(port=5000,host="127.0.0.1",debug=True)
