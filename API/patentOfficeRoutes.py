import jwt
import pickle
import datetime
import io
from flask import Blueprint , make_response , jsonify , request , send_file
from database import collection_patents
from validateToken import validate_token_and_role
from enums import Roles , PatentStatus
from app import app
from sklearn.metrics.pairwise import cosine_similarity

patentOfficeRoutes = Blueprint("patentOfficeRoutes" , __name__)

@patentOfficeRoutes.route("/login", methods=["POST"])
def patentOfficeLogin():
    username = dict(request.get_json()).get('username')
    password = dict(request.get_json()).get('password')
    response = make_response()

    if (username != 'username'):
        response.data = jsonify(
            {"error": True, "message": "Invalid Username"}).response[0]
        response.status_code = 401
        return response
    elif password != 'password':
        response.data = jsonify(
            {"error": True, "message": "Invalid Password"}).response[0]
        response.status_code = 401
        return response
    else:
        expire_date = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        token = jwt.encode(payload={'username': 'username', 'role' : Roles.PATENTOFFICE.value, 'exp': expire_date},
                           key=app.config['SECRET_KEY'], algorithm="HS256")

        response.set_cookie('token', token, max_age=60*60*24*7 , secure=True , samesite='None' , httponly=True , path='/')
        response.data = jsonify(
            {"error": False, "message": "Valid Credentials"}).response[0]
        response.status_code = 200
        return response

@patentOfficeRoutes.route("/acceptPatent", methods=["POST"])
@validate_token_and_role(Roles.PATENTOFFICE.value)
def patentOfficeAcceptPatent():
    response = make_response()

    title = dict(request.get_json()).get("title")
    result = collection_patents.find_one({"title" : title})

    if result:
        filter_criteria = {"title" : title}
        update_data = {
            "$set" : {
                "patent_status" : PatentStatus.APPROVED.value,
                "modified_at" : datetime.datetime.utcnow()
            }
        }
        collection_patents.update_one(filter=filter_criteria , update=update_data)
        response.status_code = 200
        response.data = jsonify({"error" : False}).response[0]
        return response    
    else:
        response.status_code = 401
        response.data = jsonify({"error" : True , "isNoTitle" : True}).response[0]
        return response 

@patentOfficeRoutes.route("/rejectPatent", methods=["POST"])
@validate_token_and_role(Roles.PATENTOFFICE.value)
def patentOfficeRejectPatent():
    response = make_response()

    title = dict(request.get_json()).get("title")
    result = collection_patents.find_one({"title" : title})

    if result:
        filter_criteria = {"title" : title}
        update_data = {
            "$set" : {
                "patent_status" : PatentStatus.REJECTED.value,
                "modified_at" : datetime.datetime.utcnow()
            }
        }
        collection_patents.update_one(filter=filter_criteria , update=update_data)
        response.status_code = 200
        response.data = jsonify({"error" : False}).response[0]
        return response    
    else:
        response.status_code = 401
        response.data = jsonify({"error" : True , "isNoTitle" : True}).response[0]
        return response 

@patentOfficeRoutes.route("/downloadPatentByTitle", methods=["POST"])
@validate_token_and_role(Roles.PATENTOFFICE.value)
def patentOfficeDownloadPatentByTitle():
    title = dict(request.get_json()).get("title")
    pdf_data = collection_patents.find_one({"title" : title} , {"document" : 1})

    if not pdf_data:
        response = make_response()
        response.status_code = 404
        response.data = jsonify({"error" : True}).response[0]
        return response
    
    pdf_bytes = pickle.loads(pdf_data.get("document"))
    
    return send_file(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        download_name="document.pdf",
        mimetype="application/pdf"
    )

@patentOfficeRoutes.route("/validatePatent", methods=["POST"])
@validate_token_and_role(Roles.PATENTOFFICE.value)
def patentOfficeValidatePatent():
    title = dict(request.get_json()).get("title")
    print(title)
    current_document = collection_patents.find_one({"title" : title})

    serialized_abstract_bert_embeddings = dict(current_document).get('abstract_bert_embeddings')
    abstract_bert_embeddings = pickle.loads(serialized_abstract_bert_embeddings)

    cursor = collection_patents.find({"title" : {"$not" : {"$eq" : title}} , "patent_status" : PatentStatus.APPROVED.value} , {"abstract_bert_embeddings" : 1})
    documents = []

    for document in cursor:
        serialized_document_embeddings = dict(document).get("abstract_bert_embeddings")
        document_embeddings = pickle.loads(serialized_document_embeddings)
        probability = cosine_similarity(abstract_bert_embeddings , document_embeddings)[0][0]

        if probability >= 0.90:
            doc = collection_patents.find_one({"_id": dict(document).get("_id")} , {"_id" : 0 , "title" : 1 , "abstract" : 1 , "created_at" : 1 , "modified_at" : 1})
            doc["probability"] = float(probability)
            documents.append(doc)

    # Sorting Documents based on probability of matching
    documents = sorted(documents , key=lambda x : x["probability"] , reverse=True)
    response = make_response()
    response.status_code = 200
    response.data = jsonify({"documents" : documents}).response[0]
    return response

@patentOfficeRoutes.route("/pendingPatents", methods=["POST"])
# @validate_token_and_role(Roles.PATENTOFFICE.value)
def pendingPatents():
    cursor = collection_patents.find({'patent_status' : PatentStatus.PENDING.value} , {"title" : 1 , "abstract" : 1 , 'contractAddress' : 1, 'created_at' : 1 , 'modified_at' : 1})
    documents = []

    for document in cursor:
        documents.append({'title' : document.get("title") , 'abstract' : document.get("abstract") , 'contractAddress' : document.get("contractAddress") , 'created_at' : document.get("created_at") , 'modified_at' : document.get("modified_at")})

    response = make_response()
    response.status_code = 200
    response.data = jsonify({"documents" : documents}).response[0]
    return response