from rest_framework.response import Response


def success_response(*,message,data=None,status_code=200):

    return Response({"status":True,
                     "message":message,
                     "data":data if data is not None else {}
                    },
                    status = status_code
                   )




def error_response(*,message,data=None,status_code=400):
    
    return Response({"status":False,
                     "message":message,
                     "data":data if data is not None else {},
                    },
                    status = status_code
                   )




def normalize_validation_errors(detail):

    if isinstance(detail,dict) and "message" in detail:
        return detail.get("message"),detail.get("data")
    
    if isinstance(detail,dict):
        return "Validation failed.",detail
    
    return "Validation failed.",{"errors":detail}