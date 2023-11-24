from flask import make_response, jsonify
from app import app
from userRoutes import userRoutes
from patentOfficeRoutes import patentOfficeRoutes

app.register_blueprint(userRoutes , url_prefix="/user")
app.register_blueprint(patentOfficeRoutes , url_prefix="/patentOffice")

@app.route("/logout" , methods=["POST"])
def logout():
    response = make_response()
    response.set_cookie('token', '', expires=0 , secure=True , samesite='None' , httponly=True , path='/')
    response.status_code = 200
    response.data = jsonify({"error" : False , "message" : "Logged Out Successfully"}).response[0]
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000 , debug=True)