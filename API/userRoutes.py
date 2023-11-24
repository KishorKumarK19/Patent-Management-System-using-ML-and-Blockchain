import jwt
import torch
import pickle
import datetime
from flask import Blueprint , make_response , jsonify , request
from database import collection_patents , collection_user , collection_transaction
from validateToken import validate_token_and_role
from enums import Roles , PatentStatus
from werkzeug.security import generate_password_hash, check_password_hash
from app import tokenizer , model , app

userRoutes = Blueprint("userRoutes" , __name__)

@userRoutes.route("/patentApply", methods=["POST"])
@validate_token_and_role(Roles.NORMALUSER.value)
def patentUpload():
    response = make_response()
    title = request.form['title']
    abstract = request.form['abstract']

    patent = collection_patents.find_one({'title' : title})
    if patent:
        response.status_code = 401
        response.data = jsonify({'error' : True , 'isTitleAlreadyExist' : True}).response[0]
        return response        

    # Retrieve Aadhar Number from session token
    token = request.cookies.get('token')
    decoded_token = jwt.decode(token , key=app.config['SECRET_KEY'], algorithms=["HS256"])
    aadharNumber = decoded_token.get('aadharNumber')

    # Extracting text content from pdf
    file = request.files['file']

    words = abstract.split()
    abstract = ' '.join(words)

    # Tokenize and encode the target description
    target_input_ids = tokenizer.encode(abstract, add_special_tokens=True)
    target_input_ids = torch.tensor(target_input_ids).unsqueeze(0)

    # Get contextualized embeddings for the target description
    with torch.no_grad():
        target_outputs = model(target_input_ids)
    target_embeddings = target_outputs.last_hidden_state.mean(dim=1)
    
    serialized_target_embeddings = pickle.dumps(target_embeddings.numpy())
    serialized_file = pickle.dumps(file.read())

    collection_patents.insert_one({'title' : title , 'aadharNumber' : aadharNumber , 'abstract' : abstract , 'abstract_bert_embeddings' : serialized_target_embeddings , 'patent_status' : PatentStatus.PENDING.value , 'document' : serialized_file , 'created_at' : datetime.datetime.utcnow() , 'modified_at' : datetime.datetime.utcnow()})
    response.status_code = 200
    response.data = jsonify({'error' : False}).response[0]
    return response
    
@userRoutes.route("/ownedPatents", methods=["POST"])
@validate_token_and_role(Roles.NORMALUSER.value)
def userOwnedPatents():
    token = request.cookies.get("token")
    decoded_token = jwt.decode(token , key=app.config['SECRET_KEY'], algorithms=["HS256"])
    aadharNumber = decoded_token.get('aadharNumber')

    cursor = collection_patents.find({"aadharNumber" : aadharNumber} , {'title' : 1 , 'abstract' : 1 , 'patent_status' : 1 , 'created_at' : 1 , 'modified_at' : 1})
    documents = []
    
    for document in cursor:
        documents.append({"title" : dict(document).get("title") , "abstract" : dict(document).get("abstract") , "patent_status" : dict(document).get("patent_status") , "created_at" : dict(document).get("created_at") , "modified_at" : dict(document).get("modified_at")})

    response = make_response()
    response.status_code = 200
    response.data = jsonify({"documents" : documents}).response[0]
    return response


@userRoutes.route("/patentSearch", methods=["POST"])
@validate_token_and_role(Roles.NORMALUSER.value)
def userPatentSearch():
    search = dict(request.get_json()).get("search")
    cursor = collection_patents.find({"abstract" : {"$regex" : search , "$options": "i"} , "patent_status" : PatentStatus.APPROVED.value})

    documents = []
    
    for document in cursor:
        documents.append({"title" : dict(document).get("title") , "abstract" : dict(document).get("abstract") ,"aadharNumber" : dict(document).get("aadharNumber") , "patent_status" : dict(document).get("patent_status") , "contractAddress" : dict(document).get("contractAddress") , "created_at" : dict(document).get("created_at") , "modified_at" : dict(document).get("modified_at")})

    response = make_response()
    response.status_code = 200
    response.data = jsonify({"documents" : documents}).response[0]
    return response

@userRoutes.route("/connectMetaAccount", methods=["POST"])
@validate_token_and_role(Roles.NORMALUSER.value)
def connectMetaAccount():
    try:
        token = request.cookies.get("token")
        decoded_token = jwt.decode(token , key=app.config['SECRET_KEY'], algorithms=["HS256"])
        aadharNumber = decoded_token.get('aadharNumber')
        metaAddress = dict(request.get_json()).get("metaAddress")
        
        filter_criteria = {"aadharNumber" : aadharNumber}
        update_data = {
            "$set" : {
                "metaAddress" : metaAddress,
                "modified_at" : datetime.datetime.utcnow()
            }
        }
        collection_user.update_one(filter=filter_criteria , update=update_data)
        response = make_response()
        response.status_code = 200
        response.data = jsonify({"error" : False}).response[0]
        return response
    except Exception as e:
        response = make_response()
        response.status_code = 403
        response.data = jsonify({"error" : True , "errorMessage" : f"{e}"}).response[0]
        return response
    
@userRoutes.route("/contractAddress", methods=["POST"])
@validate_token_and_role(Roles.NORMALUSER.value)
def contractAddress():
    try:
        contractAddress = dict(request.get_json()).get("contractAddress")
        title = dict(request.get_json()).get("title")
        
        filter_criteria = {"title" : title}
        update_data = {
            "$set" : {
                "contractAddress" : contractAddress,
                "modified_at" : datetime.datetime.utcnow()
            }
        }
        collection_patents.update_one(filter=filter_criteria , update=update_data)
        response = make_response()
        response.status_code = 200
        response.data = jsonify({"error" : False}).response[0]
        return response
    except Exception as e:
        response = make_response()
        response.status_code = 403
        response.data = jsonify({"error" : True , "errorMessage" : f"{e}"}).response[0]
        return response

@userRoutes.route("/signup", methods=["POST"])
def userSignUp():
    name = dict(request.get_json()).get("name")
    aadharNumber = dict(request.get_json()).get("aadharNumber")
    password = dict(request.get_json()).get("password")

    users = collection_user.find_one({"aadharNumber": aadharNumber})
    response = make_response()

    if users:
        response.status_code = 401
        response.data = jsonify({
            "message": "aadharNumber Already Exists", "error": True}).response[0]
        return response

    hashed_password = generate_password_hash(password)
    collection_user.insert_one(
        {"name" : name, "aadharNumber": aadharNumber, "hashedPassword": hashed_password})
    response.status_code = 200
    response.data = jsonify(
        {"error": False, "message": "Account Created Successfully"}).response[0]
    return response

@userRoutes.route("/login", methods=["POST"])
def userLogin():
    aadharNumber = dict(request.get_json()).get("aadharNumber")
    password = dict(request.get_json()).get("password")

    account = collection_user.find_one({"aadharNumber": aadharNumber})
    response = make_response()

    if account == None:
        response.status_code = 401
        response.data = jsonify(
            {"error": True, "message": "Invalid Aadhar Number"}).response[0]
        return response

    if check_password_hash(account.get("hashedPassword"), password) == False:
        response.status_code = 401
        response.data = jsonify(
            {"error": True, "message": "Invalid Password"}).response[0]
        return response

    expire_date = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    token = jwt.encode(payload={'aadharNumber': aadharNumber , 'role' : Roles.NORMALUSER.value, 'exp': expire_date},
                       key=app.config['SECRET_KEY'], algorithm="HS256")
    response.data = jsonify(
        {"error": False, "message": "Valid Credentials"}).response[0]
    response.status_code = 200
    response.set_cookie('token', token, max_age=60*60*24*7 , secure=True , samesite='None' , httponly=True , path='/')
    return response

@userRoutes.route("/storeTransaction", methods=["POST"])
@validate_token_and_role(Roles.NORMALUSER.value)
def storeTransaction():
    try:
        ownerAadharNumber = dict(request.get_json()).get("ownerAadharNumber")
        token = request.cookies.get("token")
        decoded_token = jwt.decode(token , key=app.config['SECRET_KEY'], algorithms=["HS256"])
        senderAadharNumber = decoded_token.get('aadharNumber')
        title = dict(request.get_json()).get("title")
        months = dict(request.get_json()).get("months")
        amountInWeiPayed = dict(request.get_json()).get("amountInWeiPayed")

        collection_transaction.insert_one({"ownerAadharNumber" : ownerAadharNumber , "senderAadharNumber" : senderAadharNumber , "title" : title , "months" : months , "amountInWeiPayed" : amountInWeiPayed , "created_at" : datetime.datetime.utcnow() , "modified_at" : datetime.datetime.utcnow()})

        response = make_response()
        response.status_code = 200
        response.data = jsonify({"error" : False}).response[0]
        return response        
    except Exception as e:
        response = make_response()
        response.status_code = 403
        response.data = jsonify({"error" : True , "errorMessage" : f"{e}"}).response[0]
        return response
    
@userRoutes.route("/ownerTransaction" , methods=["POST"])
@validate_token_and_role(Roles.NORMALUSER.value)
def ownerTransaction():
    try:
        token = request.cookies.get("token")
        decoded_token = jwt.decode(token , key=app.config['SECRET_KEY'], algorithms=["HS256"])
        ownerAadharNumber = decoded_token.get('aadharNumber')
        
        cursor = collection_transaction.find({"ownerAadharNumber" : ownerAadharNumber})

        documents = []
        
        for document in cursor:
            documents.append({"ownerAadharNumber" : dict(document).get("ownerAadharNumber") , "senderAadharNumber" : dict(document).get("senderAadharNumber") , "title" : dict(document).get("title") , "months" : dict(document).get("months") , "amountInWeiPayed" : dict(document).get("amountInWeiPayed") , "created_at" : dict(document).get("created_at") , "modified_at" : dict(document).get("modified_at")})

        response = make_response()
        response.status_code = 200
        response.data = jsonify({"error" : False , "documents" : documents}).response[0]
        return response
    except Exception as e:
        response = make_response()
        response.status_code = 403
        response.data = jsonify({"error" : True , "errorMessage" : f"{e}"}).response[0]
        return response
    
@userRoutes.route("/senderTransaction" , methods=["POST"])
@validate_token_and_role(Roles.NORMALUSER.value)
def senderTransaction():
    try:
        token = request.cookies.get("token")
        decoded_token = jwt.decode(token , key=app.config['SECRET_KEY'], algorithms=["HS256"])
        senderAadharNumber = decoded_token.get('aadharNumber')
        cursor = collection_transaction.find({"senderAadharNumber" : senderAadharNumber})

        documents = []
        
        for document in cursor:
            documents.append({"ownerAadharNumber" : dict(document).get("ownerAadharNumber") , "senderAadharNumber" : dict(document).get("senderAadharNumber") , "title" : dict(document).get("title") , "months" : dict(document).get("months") , "amountInWeiPayed" : dict(document).get("amountInWeiPayed") , "created_at" : dict(document).get("created_at") , "modified_at" : dict(document).get("modified_at")})

        response = make_response()
        response.status_code = 200
        response.data = jsonify({"error" : False , "documents" : documents}).response[0]
        return response
    except Exception as e:
        response = make_response()
        response.status_code = 403
        response.data = jsonify({"error" : True , "errorMessage" : f"{e}"}).response[0]
        return response