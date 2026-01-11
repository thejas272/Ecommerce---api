from rest_framework.response import Response


# converts normalized data to success response

def success_response(*,message,data=None,status_code=200):

    return Response({"status":True,
                     "message":message,
                     "data":data if data is not None else {}
                    },
                    status = status_code
                   )



# converts normalized data to error response

def error_response(*,message,data=None,status_code=400):
    
    return Response({"status":False,
                     "message":message,
                     "data":data if data is not None else {},
                    },
                    status = status_code
                   )





def normalize_validation_errors(detail):

    # to catch and normalize exceptions raised delibarately. includes view, validate, create, update based exceptions.
    if isinstance(detail,dict) and "error_message" in detail:

        error_message = detail.get("error_message")
        data          = detail.get("data") if detail.get("data") else {} 

        if isinstance(error_message,list):     # to handle non field errors
            error_message = error_message[0]     

        return error_message,data 
    

    # to catch and normalize field level exceptions raised by drf automatically.
    if isinstance(detail,dict):
        return "Validation failed.",detail 
    
    
    # to catch and normalize exceptions that aren't returned as a dict
    return "Validation failed.",{"errors":detail}